# Module 3: Multi-Agent Orchestration — Agents That Collaborate

## Student: Copy-Paste This Prompt Into a New Agent Session

> Open a **new session** in your AI coding agent and paste this:

```
Read the file course/agent-docs/03-multi-agent.md and follow it step by step.

First complete the Environment Setup section (skip if already done), then build
Labs 3a, 3b, and 3c from scratch in the my-agents/ directory. Run and verify
each lab before moving to the next.

This module builds three multi-agent systems: delegation, parallel execution,
and file-based communication pipelines.

If you get stuck, consult the references at course/labs/lab3a_first_subagent.py,
course/labs/lab3b_parallel_agents.py, and course/labs/lab3c_file_sharing.py.
```

---

## Environment Setup

This is a new agent session, so the environment must be ready. Follow every step — the checks will skip anything already done.

### Step 1: Ensure Python 3.11+ is available

**Action:** `shell`
**OS[mac/linux]:**
```bash
python3 --version
```
**OS[windows]:**
```cmd
python --version
```
**Expected:** `Python 3.11.x` or higher. If not installed, follow the Python installation steps in `course/agent-docs/01-foundations.md` → Environment Setup → Step 1.

### Step 2: Create working directory, venv, install deps, set API key

**Action:** `shell`
**OS[mac/linux]:**
```bash
mkdir -p my-agents
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "deepagents>=0.4.3" "langchain-openai>=1.1.8" "httpx>=0.27.0"
export OPENAI_API_KEY="sk-your-key-here"
```
**OS[windows]:**
```cmd
mkdir my-agents 2>nul
if not exist .venv python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install "deepagents>=0.4.3" "langchain-openai>=1.1.8" "httpx>=0.27.0"
set OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Verify

**Action:** `shell`
```bash
python -c "import sys; assert sys.version_info >= (3,11); print(f'Python {sys.version} OK')"
python -c "from deepagents import create_deep_agent; print('deepagents OK')"
python -c "import httpx; print('httpx OK')"
python -c "import os; assert os.getenv('OPENAI_API_KEY','').startswith('sk-'); print('API key OK')"
```
**Expected:** Four lines of "OK".

### Prerequisites
- Modules 1-2 completed (Labs 0, 1, 2 built and ran successfully)
- Understanding of `create_deep_agent()`, `@tool`, system prompts, and filesystem tools

---

## Concepts

### Sub-Agent Definition

A sub-agent is a dictionary passed to `create_deep_agent(subagents=[...])`:

```python
{
    "name": "researcher",              # Unique name — used by task() routing
    "description": "Searches the web", # Orchestrator reads this to decide when to delegate
    "system_prompt": "You search...",  # Instructions for the sub-agent
    "tools": [web_search],             # Tools ONLY this sub-agent gets
    "model": "openai:gpt-4o-mini",    # Can use a cheaper model
}
```

### Context Isolation

Each sub-agent gets a **fresh, isolated context**. It cannot see the orchestrator's conversation or other sub-agents' work. Only the sub-agent's **final response** returns. This prevents context pollution and bloat.

### Parallel Execution

Call multiple `task()` tools in a **single orchestrator response** for parallel execution:

```
# All three run simultaneously:
task(description="Research tech aspects", subagent_type="tech_researcher")
task(description="Research market aspects", subagent_type="market_researcher")
task(description="Analyze pros/cons", subagent_type="pros_cons_analyst")
```

### Filesystem as Communication Bus

Agents share data through files — not through messages:
- Agent A writes to `/data/output.md`
- Agent B reads from `/data/output.md`
- The orchestrator controls execution order

---

## Lab 3a: Build an Orchestrator + Researcher System

### Goal
Build an orchestrator with **NO tools** that must delegate all research to a `researcher` sub-agent. This forces the delegation pattern.

### Step 1: Create the file with imports and web search tool

**Action:** `create-file`
**File:** `my-agents/lab3a_first_subagent.py`
**Content:**
```python
"""
LAB 3A: Your First Sub-Agent
==============================
Orchestrator delegates research to a sub-agent.
The orchestrator has NO tools — it MUST delegate.
"""
import json
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ─── TOOL: Only the researcher gets this ───────────────

@tool
def web_search(query: str) -> str:
    """Search the web and return results.

    Args:
        query: Search query string
    """
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10
        )
        data = resp.json()
        results = []
        if data.get("Abstract"):
            results.append(f"**{data['Heading']}**: {data['Abstract']}")
        for t in data.get("RelatedTopics", [])[:3]:
            if isinstance(t, dict) and "Text" in t:
                results.append(f"- {t['Text']}")
        return "\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"
```

### Step 2: Define the orchestrator with a researcher sub-agent

**Action:** `append-to-file`
**File:** `my-agents/lab3a_first_subagent.py`
**Content:**
```python


# ─── AGENT: Orchestrator + Researcher Sub-Agent ────────

agent = create_deep_agent(
    model="openai:gpt-4o",
    # Orchestrator has NO tools — it MUST delegate
    tools=[],
    subagents=[
        {
            "name": "researcher",
            "description": (
                "Use this agent to search the web and gather information "
                "on any topic. It has access to web search."
            ),
            "system_prompt": (
                "You are a research agent. Use web_search to find information.\n"
                "Return a concise, well-organized summary of your findings.\n"
                "Always include source URLs when available.\n"
                "Search 2-3 times with different queries for thorough coverage."
            ),
            "tools": [web_search],
            "model": "openai:gpt-4o-mini",  # Cheaper model for sub-agent
        }
    ],
    system_prompt="""You are an orchestrator agent.

You CANNOT search the web yourself — you have no search tools.
You MUST delegate ALL research tasks to the "researcher" sub-agent
using the task tool.

## YOUR WORKFLOW
1. Analyze the user's question
2. Delegate research: task(description="...", subagent_type="researcher")
3. Receive the researcher's findings
4. Synthesize and present a clear answer to the user

Be specific in your task descriptions so the researcher knows
exactly what to search for."""
)
```

**Key design decisions:**
- `tools=[]` on the orchestrator — it literally cannot do anything except delegate
- `"model": "openai:gpt-4o-mini"` on the sub-agent — cheaper for data-fetching work
- The `description` field is what the orchestrator reads to decide which sub-agent to use
- The orchestrator's system prompt says "You CANNOT search" — reinforcing the delegation pattern

### Step 3: Add the runner and main block

**Action:** `append-to-file`
**File:** `my-agents/lab3a_first_subagent.py`
**Content:**
```python


# ─── RUN IT ─────────────────────────────────────────────

def ask(question: str, thread: str = "subagent-demo"):
    print(f"\n{'='*60}")
    print(f" YOU: {question}")
    print(f"{'='*60}\n")
    print("Orchestrator is delegating to researcher sub-agent...\n")

    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"ANSWER:\n{msg.content}")
            return


if __name__ == "__main__":
    print("=" * 60)
    print(" LAB 3A: Your First Sub-Agent")
    print(" Orchestrator → delegates → Researcher → answers")
    print("=" * 60)

    ask("What is LangGraph and how does it relate to LangChain?")

    print(f"\n{'='*60}")
    print(" LAB 3A COMPLETE!")
    print("=" * 60)
```

### Step 4: Run it

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python my-agents/lab3a_first_subagent.py
```

### Step 5: Verify

**Expected:** The orchestrator produces a synthesized answer about LangGraph/LangChain. It delegated to the researcher (not searching itself).

**Success criteria:**
- Answer contains information about LangGraph and LangChain
- No errors — the orchestrator successfully delegated and received results
- The orchestrator synthesized (not just passed through) the researcher's findings

### What You Built
- **An orchestrator** with no tools — forced to delegate via `task()`
- **A sub-agent** with web search and a cheaper model
- **The delegation pattern**: orchestrator analyzes → delegates → synthesizes → presents

---

## Lab 3b: Build Three Parallel Specialist Agents

### Goal
Build an orchestrator that launches **three specialist sub-agents in parallel**, each researching a different angle, then synthesizes all results.

### Step 1: Create the file with imports and web search tool

**Action:** `create-file`
**File:** `my-agents/lab3b_parallel_agents.py`
**Content:**
```python
"""
LAB 3B: Parallel Sub-Agents
=============================
3 specialists research simultaneously, then orchestrator synthesizes.
"""
import json
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ─── TOOL ──────────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query
    """
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10
        )
        data = resp.json()
        parts = []
        if data.get("Abstract"):
            parts.append(data["Abstract"])
        for t in data.get("RelatedTopics", [])[:5]:
            if isinstance(t, dict) and "Text" in t:
                parts.append(f"- {t['Text']}")
        return "\n".join(parts) if parts else "No results found."
    except Exception as e:
        return f"Error: {e}"
```

### Step 2: Define three specialist sub-agents

**Action:** `append-to-file`
**File:** `my-agents/lab3b_parallel_agents.py`
**Content:**
```python


# ─── SPECIALIST SUB-AGENTS ─────────────────────────────

subagents = [
    {
        "name": "tech_researcher",
        "description": (
            "Researches TECHNICAL aspects — architecture, implementation, "
            "APIs, code-level details, technology stack."
        ),
        "system_prompt": (
            "You are a technical research specialist.\n"
            "Focus ONLY on architecture, implementation details, APIs, "
            "and code-level comparisons.\n"
            "Use web_search to find information. Be specific and technical.\n"
            "Write your findings to /research/technical.md"
        ),
        "tools": [web_search],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "market_researcher",
        "description": (
            "Researches MARKET aspects — adoption rates, competitors, "
            "pricing, community size, ecosystem, jobs."
        ),
        "system_prompt": (
            "You are a market research specialist.\n"
            "Focus ONLY on adoption, community, competitors, "
            "ecosystem, and job market.\n"
            "Include numbers and data when available.\n"
            "Write your findings to /research/market.md"
        ),
        "tools": [web_search],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "pros_cons_analyst",
        "description": (
            "Analyzes STRENGTHS and WEAKNESSES — tradeoffs, best/worst "
            "use cases, developer experience, learning curve."
        ),
        "system_prompt": (
            "You are a critical analysis specialist.\n"
            "Provide balanced pros/cons analysis.\n"
            "Be honest about both strengths and weaknesses.\n"
            "Include specific examples for each point.\n"
            "Write your findings to /research/pros_cons.md"
        ),
        "tools": [web_search],
        "model": "openai:gpt-4o-mini",
    },
]
```

**Why three specialists instead of one generalist?**
- Each specialist can go **deep** on their domain without filling each other's context
- Parallel execution = faster overall (3 agents × 30s each = 30s total, not 90s)
- The orchestrator gets three focused perspectives to synthesize

### Step 3: Build the orchestrator

**Action:** `append-to-file`
**File:** `my-agents/lab3b_parallel_agents.py`
**Content:**
```python


# ─── ORCHESTRATOR ──────────────────────────────────────

agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=subagents,
    system_prompt="""You are an orchestrator that produces comprehensive analysis reports.

## WORKFLOW
1. Identify the topic and 3 research angles
2. Launch ALL THREE sub-agents IN PARALLEL:
   - tech_researcher for technical analysis
   - market_researcher for market analysis
   - pros_cons_analyst for strengths/weaknesses
   Call all three task() tools in a SINGLE response for parallel execution!
3. After all results return, read any files they wrote in /research/
4. Synthesize into a unified report and write to /output/report.md
5. Present the report to the user

## CRITICAL: Launch all sub-agents at once for parallel execution!
In your response, include multiple task() calls — one for each sub-agent.
"""
)
```

**Key instruction:** "Call all three task() tools in a SINGLE response" — this triggers parallel execution. Without this, the orchestrator might run them one at a time.

### Step 4: Add the runner and main block

**Action:** `append-to-file`
**File:** `my-agents/lab3b_parallel_agents.py`
**Content:**
```python


# ─── RUN IT ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print(" LAB 3B: Parallel Sub-Agents")
    print(" 3 specialists research simultaneously, then synthesize")
    print("=" * 60)

    question = (
        "Comprehensive analysis: Rust vs Go for building "
        "microservices in 2025"
    )

    print(f"\n QUERY: {question}")
    print(f"\n Launching 3 parallel research agents...\n")

    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": "parallel-lab"}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\n{'─'*60}")
            print("SYNTHESIZED REPORT:")
            print(f"{'─'*60}")
            print(msg.content)
            break

    print(f"\n{'='*60}")
    print(" LAB 3B COMPLETE!")
    print("=" * 60)
```

### Step 5: Run it

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python my-agents/lab3b_parallel_agents.py
```

**Note:** Takes 30-90 seconds — three agents research in parallel.

### Step 6: Verify

**Success criteria:**
- Synthesized report covers **all three angles**: technical, market, and pros/cons
- Report is richer than what one agent could produce (multiple perspectives)
- No errors — all three sub-agents ran and returned results

### What You Built
- **Three specialist sub-agents** — each focused on one research domain
- **Parallel execution** — multiple `task()` calls in one orchestrator response
- **The synthesis pattern** — orchestrator combines all perspectives into one report

---

## Lab 3c: Build a Filesystem Communication Pipeline

### Goal
Build a sequential pipeline where agents communicate **only through files**:
1. `data_collector` writes structured data to `/data/`
2. `analyst` reads `/data/`, performs calculations, writes to `/analysis/`
3. Orchestrator reads `/analysis/` and presents to user

### Step 1: Create the file with imports and calculator tool

**Action:** `create-file`
**File:** `my-agents/lab3c_file_sharing.py`
**Content:**
```python
"""
LAB 3C: Filesystem as Communication Bus
=========================================
Agents communicate through files:
  Data Collector writes → Analyst reads & calculates → Orchestrator presents
"""
import math
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ─── TOOL: Calculator for the analyst ──────────────────

@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression safely.

    Args:
        expression: Math expression like '2+3', 'sqrt(16)', 'round(3.14159, 2)'
    """
    allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed.update({"abs": abs, "round": round, "sum": sum, "max": max, "min": min})
    try:
        return str(eval(expression, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"Error: {e}"
```

### Step 2: Define the sub-agents

**Action:** `append-to-file`
**File:** `my-agents/lab3c_file_sharing.py`
**Content:**
```python


# ─── SUB-AGENTS ────────────────────────────────────────

subagents = [
    {
        "name": "data_collector",
        "description": (
            "Collects and structures raw data. "
            "Writes all data to /data/ directory as markdown tables."
        ),
        "system_prompt": """You are a data collection specialist.

YOUR JOB:
1. When given a data task, create realistic, structured data
2. Write it as MARKDOWN TABLES to /data/[topic].md
3. Always include headers and units
4. Confirm what files you created

IMPORTANT: Write to files — other agents will read your output!

Example file format:
```
# Cloud Pricing Data
| Provider | Service | Specs | Monthly Cost |
|----------|---------|-------|-------------|
| AWS      | EC2     | 2 vCPU, 8GB | $67.00 |
```""",
        "tools": [],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "analyst",
        "description": (
            "Reads data from /data/, performs calculations and analysis, "
            "writes conclusions to /analysis/. Has a calculator tool."
        ),
        "system_prompt": """You are a data analyst with a calculator.

YOUR JOB:
1. Read data files from /data/ using read_file
2. Perform calculations using the calculate tool
3. Write your analysis to /analysis/results.md
4. Include: totals, averages, rankings, percentage differences
5. Provide clear conclusions backed by numbers

ALWAYS show your calculation steps!""",
        "tools": [calculate],
        "model": "openai:gpt-4o",
    },
]
```

**Notice the data flow:**
- `data_collector` writes to `/data/` but **cannot read** from other agents
- `analyst` reads from `/data/` (written by collector) and writes to `/analysis/`
- Neither agent talks to the other directly — files are the communication channel

### Step 3: Build the orchestrator

**Action:** `append-to-file`
**File:** `my-agents/lab3c_file_sharing.py`
**Content:**
```python


# ─── ORCHESTRATOR ──────────────────────────────────────

agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=subagents,
    system_prompt="""You are a project manager orchestrating data analysis.

## WORKFLOW (SEQUENTIAL — each step depends on previous)
1. FIRST: data_collector gathers data → writes to /data/
2. THEN: analyst processes /data/ files → writes to /analysis/
3. FINALLY: You read /analysis/ and present findings to user

## HOW AGENTS COMMUNICATE:
  data_collector → writes /data/*.md
  analyst → reads /data/*.md → writes /analysis/*.md
  you → read /analysis/*.md → present to user

The FILESYSTEM is the communication channel between agents!
"""
)
```

### Step 4: Add the runner and main block

**Action:** `append-to-file`
**File:** `my-agents/lab3c_file_sharing.py`
**Content:**
```python


# ─── RUN IT ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print(" LAB 3C: Filesystem as Communication Bus")
    print(" Collector → files → Analyst → files → Orchestrator")
    print("=" * 60)

    question = """
Compare cloud hosting costs for a standard web application:
- Providers: AWS, Google Cloud, Azure
- Services needed:
  - Compute: 2 vCPU, 8GB RAM
  - Storage: 100GB SSD
  - Database: PostgreSQL, 50GB
  - Bandwidth: 500GB/month
- Calculate total monthly cost for each
- Determine which is cheapest and by how much ($ and %)
    """

    print(f"\n QUERY: {question.strip()}")
    print(f"\n Running pipeline: collect → analyze → present...\n")

    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": "file-sharing-lab"}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\n{'─'*60}")
            print("FINAL ANALYSIS:")
            print(f"{'─'*60}")
            print(msg.content)
            break

    print(f"\n{'='*60}")
    print(" LAB 3C COMPLETE!")
    print("=" * 60)
```

### Step 5: Run it

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python my-agents/lab3c_file_sharing.py
```

### Step 6: Verify

**Success criteria:**
- Cost comparisons for AWS, Google Cloud, and Azure
- Numbers and calculations present (totals, differences, percentages)
- The data flowed: collector → files → analyst → files → orchestrator → user
- No errors

### What You Built
- **A sequential pipeline** — each agent depends on the previous agent's file output
- **The filesystem-as-bus pattern** — agents communicate through files, not messages
- **Specialist agents** — collector (no tools, writes data), analyst (calculator, reads + writes)

### What You Learned Across All Module 3 Labs

| Lab | Pattern | Key Insight |
|-----|---------|-------------|
| 3a | Delegation | `tools=[]` forces orchestrator to delegate via `task()` |
| 3b | Parallel execution | Multiple `task()` calls in one response = parallel |
| 3c | File-based pipeline | The filesystem is the async message bus between agents |

**Design principle:** Agents don't need to know about each other. They only need to know about files. The orchestrator controls the execution order.
