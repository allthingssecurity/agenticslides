# DeepAgents — Durability via Dapr

> **DeepAgents** are the AI agents (LLM loop, tools, sub-agents, middleware).
> **Dapr** is the infrastructure layer that makes them durable (state persistence, retry, crash recovery).
> This is NOT Dapr Agents — we use Dapr only for its distributed durability primitives.

---

## Table of Contents

1. [Who Does What](#who-does-what)
2. [The Problem](#the-problem)
3. [Architecture](#architecture)
4. [What Is Stored in Each Checkpoint](#what-is-stored-in-each-checkpoint)
5. [Where It's Stored (Dapr Redis Keys)](#where-its-stored-dapr-redis-keys)
6. [How Recovery Works](#how-recovery-works)
7. [Files](#files)
8. [Setup](#setup)
9. [Running the Demo](#running-the-demo)
10. [Verifying in Redis](#verifying-in-redis)
11. [Comparison: Checkpointer Options](#comparison-checkpointer-options)

---

## Who Does What

| Component | Role | What It Does |
|-----------|------|-------------|
| **DeepAgents** | The AI agent | LLM reasoning loop, tool calling, sub-agents, middleware, system prompt |
| **LangGraph** | The agent runtime | State machine that drives the agent, manages checkpoints |
| **DaprCheckpointSaver** | The bridge | Implements LangGraph's `BaseCheckpointSaver` interface, stores data in Dapr |
| **Dapr State Store** | The infrastructure | Abstracts Redis/Postgres/Cosmos — stores the actual bytes |
| **Redis** | The storage backend | Where checkpoint data physically lives (swappable via YAML) |

```
DeepAgent  ──creates agent──▶  LangGraph  ──checkpoints──▶  DaprCheckpointSaver  ──stores──▶  Dapr  ──writes──▶  Redis
(your code)                    (runtime)                     (our bridge)                    (sidecar)           (database)
```

**DeepAgents own the intelligence. Dapr owns the durability.**

---

## The Problem

By default, DeepAgents use `InMemorySaver` — all state lives in Python process memory:

```
Process starts → Agent runs → Messages, tool results, PO numbers stored in RAM
                                    ↓
                              Process crashes
                                    ↓
                              Everything lost ❌
```

With `DaprCheckpointSaver`:

```
Process starts → Agent runs → Every checkpoint saved to Redis via Dapr
                                    ↓
                              Process crashes
                                    ↓
                  New process → Same thread_id → Loads state from Redis → Continues ✅
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  YOUR APPLICATION                                                │
│                                                                  │
│   create_deep_agent(              ← DeepAgents (the AI agent)    │
│     model="openai:gpt-4o-mini",                                  │
│     tools=[sap_check_vendor, ...], ← Your tools                  │
│     system_prompt="...",                                          │
│     checkpointer=DaprCheckpointSaver()  ← The bridge to Dapr     │
│   )                                                              │
│                                                                  │
│   agent.invoke({"messages": [...]}, config={"thread_id": "..."}) │
│     │                                                            │
│     ├── LangGraph runs the state machine                         │
│     ├── Before each node: saves checkpoint                       │
│     ├── After each node: saves checkpoint                        │
│     └── Checkpoints go through DaprCheckpointSaver               │
│           │                                                      │
└───────────┼──────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────┐     ┌──────────────────────┐
│  Dapr Sidecar         │────▶│  Redis (localhost:    │
│  (localhost:50001)    │     │   6379)               │
│  gRPC state store API │     │  Hash keys per        │
│                       │     │  checkpoint           │
└───────────────────────┘     └──────────────────────┘
```

**Layer 1: `DaprCheckpointSaver`** — Plugs into LangGraph's checkpoint system. Every time LangGraph wants to save or load state, it goes through this class which talks to Dapr.

**Layer 2: `DaprWorkflowAgent`** (optional) — Wraps the entire `agent.invoke()` in a Dapr Workflow activity with retry policy. Useful for long-running agents that need activity-level retry on top of state persistence.

---

## What Is Stored in Each Checkpoint

LangGraph creates **3-4 checkpoints per agent turn** (before model call, after model call, after tool calls). Each checkpoint contains:

| Field | What It Contains | Example |
|-------|-----------------|---------|
| **messages** | Full conversation history | User: "Process PO for V-10001" → Agent: calls `sap_check_vendor` → Tool: `{"status": "ACTIVE"}` → Agent: "PO created" |
| **channel_values** | LangGraph state channels | `messages`, `__start__`, `branch:to:model`, `__pregel_tasks` |
| **channel_versions** | Version numbers per channel | `messages: "00000000...00010.0.49088..."` |
| **metadata** | Which node wrote it, step number | `{"source": "loop", "step": 8, "writes": {"model": ...}}` |
| **parent_checkpoint_id** | Link to previous checkpoint | `"1f11dad2-3770-6c96-8009-b839a106f613"` (forms a chain) |
| **pending_writes** | In-flight writes from last node | Tool call results not yet committed |

### Concrete Example (SAP PO Processing)

After the agent processes a purchase order, the latest checkpoint's **messages** contain:

```
 1. human:    "Process this purchase request: Vendor V-10001, Material MAT-5002..."
 2. ai:       → calls: sap_check_vendor, sap_check_material, sap_check_budget
 3. tool:     (sap_check_vendor) {"name": "Acme Industrial", "status": "ACTIVE"...}
 4. tool:     (sap_check_material) {"description": "Hydraulic Valve", "stock": 3...}
 5. tool:     (sap_check_budget) {"available": "€180,000", "sufficient": "YES"...}
 6. ai:       → calls: sap_create_purchase_order
 7. tool:     (sap_create_purchase_order) {"po_number": "PO-4500017006", "status": "CREATED"...}
 8. ai:       "PO-4500017006 created for 10x Hydraulic Valve Assembly from Acme..."
```

All of this survives a process crash because it's in Redis, not RAM.

---

## Where It's Stored (Dapr Redis Keys)

`DaprCheckpointSaver` maps LangGraph's 3 in-memory data structures to Dapr State Store keys:

```
LangGraph InMemorySaver              →  Dapr State Store Key
───────────────────────────────      ──────────────────────────────────
storage[thread][ns][checkpoint_id]   →  cp:{thread}:{ns}:{checkpoint_id}
blobs[(thread, ns, channel, ver)]    →  blob:{thread}:{ns}:{channel}:{version}
writes[(thread, ns, checkpoint_id)]  →  writes:{thread}:{ns}:{checkpoint_id}
(checkpoint index)                   →  idx:{thread}:{ns}
(namespace index)                    →  ns_idx:{thread}
```

### Real Redis Keys (from the SAP demo)

```
sap-agent||cp:sap-po-session-1::1f11dad2-399c-6de4-800a-...      ← checkpoint + metadata
sap-agent||blob:sap-po-session-1::messages:000...010.0.490...     ← conversation messages
sap-agent||blob:sap-po-session-1::__start__:000...012.0.319...    ← start channel state
sap-agent||writes:sap-po-session-1::1f11dad2-399c-...             ← pending writes
sap-agent||idx:sap-po-session-1:                                  ← sorted list of checkpoint IDs
sap-agent||ns_idx:sap-po-session-1                                ← namespace index
```

### Serialization

LangGraph's `serde.dumps_typed()` returns `(type_str, bytes)`. Dapr State Store accepts strings. Bridge:

```json
{"type": "msgpack", "data": "base64-encoded-bytes..."}
```

Dapr stores each key as a Redis hash with a `data` field containing the JSON string.

---

## How Recovery Works

```
Step 1: Agent runs, process exits
──────────────────────────────────
  agent.invoke({"messages": [HumanMessage("Process PO")]}, config={"thread_id": "sap-1"})
    ├── LangGraph runs model → tools → model
    ├── Each step: checkpointer.put() → Dapr → Redis
    └── Process exits (crash, restart, normal exit)

Step 2: New process, same thread_id
────────────────────────────────────
  # Brand new Python process (different PID)
  checkpointer = DaprCheckpointSaver(store_name="agentstore")   ← connects to same Redis
  agent = create_deep_agent(..., checkpointer=checkpointer)

  agent.invoke({"messages": [HumanMessage("What PO was created?")]}, config={"thread_id": "sap-1"})
    ├── LangGraph calls checkpointer.get_tuple(config)
    ├── DaprCheckpointSaver reads idx:sap-1: from Redis → gets latest checkpoint ID
    ├── Reads cp:sap-1::... → deserializes checkpoint + metadata
    ├── Reads blob:sap-1::messages:... → deserializes all 8 messages
    ├── Reads writes:sap-1::... → loads pending writes
    ├── Returns CheckpointTuple with full conversation history
    └── Agent sees all previous messages and continues the conversation
```

**The agent doesn't know it crashed.** It just sees its full conversation history and responds naturally.

---

## Files

| File | What It Is |
|------|-----------|
| `my-agents/dapr_checkpointer.py` | `DaprCheckpointSaver` — the bridge between LangGraph and Dapr State Store |
| `my-agents/dapr_workflow_agent.py` | `DaprWorkflowAgent` — optional wrapper for Dapr Workflow retry/resume |
| `my-agents/sap_tools.py` | Simulated SAP tools (vendor, material, budget, PO) + shared config |
| `my-agents/sap_step1_process.py` | **Demo Step 1**: Processes a purchase order, then process exits |
| `my-agents/sap_step2_recover.py` | **Demo Step 2**: New process recovers full conversation from Redis |
| `my-agents/components/statestore.yaml` | Dapr component config — points to Redis on localhost:6379 |

---

## Setup

### Prerequisites
- Docker (for Redis + Dapr containers)
- Python 3.11+ with the course venv
- OpenAI API key

### 1. Install Dapr CLI + Initialize

```bash
# macOS
brew install dapr/tap/dapr-cli
dapr init    # pulls Redis, Zipkin, Placement containers

# Linux
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
dapr init
```

### 2. Install Python Packages

```bash
cd course
.venv/bin/pip install dapr dapr-ext-workflow
```

### 3. State Store Component

Already configured at `my-agents/components/statestore.yaml`:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: agentstore
spec:
  type: state.redis       # ← swap to state.postgresql, state.azure.cosmosdb, etc.
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    value: ""
  - name: actorStateStore
    value: "true"
```

To switch from Redis to Postgres, change `type: state.redis` to `type: state.postgresql` and update the metadata. No code changes needed.

### 4. Set API Key

```bash
export OPENAI_API_KEY="sk-..."
```

---

## Running the Demo

The demo uses a **real process crash** — two separate scripts, two separate processes.

### Step 1: Process a Purchase Order

```bash
cd course/my-agents
dapr run --app-id sap-agent --dapr-grpc-port 50001 --resources-path ./components -- ../.venv/bin/python sap_step1_process.py
```

The agent will:
1. Check vendor V-10001 in SAP (active? payment terms?)
2. Check material MAT-5002 (stock? price?)
3. Check budget on cost center CC-4100
4. Create purchase order
5. Print summary with PO number
6. **Process exits** — all state in Redis

### Between Steps: Verify Data in Redis

```bash
# How many keys?
docker exec dapr_redis redis-cli KEYS '*sap-po*' | wc -l

# Checkpoint index (list of all checkpoint IDs)
docker exec dapr_redis redis-cli HGET 'sap-agent||idx:sap-po-session-1:' data | python3 -m json.tool
```

### Step 2: Recover in a New Process

```bash
cd course/my-agents
dapr run --app-id sap-agent --dapr-grpc-port 50001 --resources-path ./components -- ../.venv/bin/python sap_step2_recover.py
```

The new agent will:
1. Connect to same Dapr Redis
2. Show the messages recovered from Step 1
3. Answer "What PO was created?" — proving it remembers
4. Process a follow-up order for MAT-5003

### Clean Up

```bash
# Flush Redis (removes all data)
docker exec dapr_redis redis-cli FLUSHALL

# Stop Dapr
dapr stop sap-agent
```

---

## Verifying in Redis

```bash
# List all keys for the SAP session
docker exec dapr_redis redis-cli KEYS '*sap-po*'

# Read the checkpoint index
docker exec dapr_redis redis-cli HGET 'sap-agent||idx:sap-po-session-1:' data | python3 -m json.tool

# Read a specific checkpoint (replace <id> with a real checkpoint ID)
docker exec dapr_redis redis-cli HGET 'sap-agent||cp:sap-po-session-1::<id>' data | python3 -m json.tool

# Decode messages (requires msgpack: pip install msgpack)
docker exec dapr_redis redis-cli HGET 'sap-agent||blob:sap-po-session-1::messages:<version>' data | \
  ../.venv/bin/python3 -c "
import sys,json,base64,msgpack
doc=json.loads(sys.stdin.read().strip())
msgs=msgpack.unpackb(base64.b64decode(doc['data']),raw=False,ext_hook=lambda c,d:msgpack.unpackb(d,raw=False) if c==5 else d)
for i,m in enumerate(msgs):
  cls=m[1] if isinstance(m,(list,tuple)) else '?'
  data=m[2] if isinstance(m,(list,tuple)) and len(m)>2 else {}
  content=str(data.get('content',''))[:80].replace(chr(10),' ')
  name=data.get('name','')
  print(f'{i+1:2d}. {cls:20s} {name:30s} {content}')
"
```

---

## Comparison: Checkpointer Options

| Checkpointer | Storage | Survives Crash | Infrastructure | Use Case |
|--------------|---------|:--------------:|----------------|----------|
| `InMemorySaver` | Process memory | No | None | Testing |
| `DaprCheckpointSaver` (no Dapr) | Process memory | No | None | Development |
| `DaprCheckpointSaver` (with Dapr) | Redis/Postgres/Cosmos | **Yes** | Dapr + state store | **Production** |
| `PostgresSaver` | PostgreSQL | **Yes** | PostgreSQL server | Production (LangGraph native) |

**Why `DaprCheckpointSaver` over `PostgresSaver`?**
- Swap Redis → Cosmos DB → DynamoDB by changing one YAML line — no code changes
- Add Dapr Workflow on top for activity-level retry
- Same sidecar handles pub/sub, secrets, bindings — not just state
