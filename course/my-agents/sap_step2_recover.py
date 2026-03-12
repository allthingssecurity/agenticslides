"""
SAP Durable Agent — STEP 2: Recover After Crash
================================================
This is a BRAND NEW process. No shared memory with Step 1.
The agent recovers its full conversation from Dapr Redis
and continues processing as if nothing happened.

Run (after sap_step1_process.py has exited):
    dapr run --app-id sap-agent \
             --dapr-grpc-port 50001 \
             --resources-path ./components \
             -- ../.venv/bin/python sap_step2_recover.py
"""

from deepagents import create_deep_agent
from trace_utils import run_with_trace
from dapr_checkpointer import DaprCheckpointSaver
from sap_tools import SAP_TOOLS, SAP_SYSTEM_PROMPT, THREAD_ID, STORE_NAME

# ─── ANSI ────────────────────────────────────────────
CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

print("=" * 65)
print(f" SAP DURABLE AGENT — STEP 2: {GREEN}RECOVERY{RESET}")
print(f" This is a NEW process (PID {__import__('os').getpid()})")
print(f" No shared memory with Step 1.")
print(f" Thread: {THREAD_ID}")
print("=" * 65)

# Create a fresh checkpointer — connects to same Dapr Redis
checkpointer = DaprCheckpointSaver(store_name=STORE_NAME)

# Show what's already in Redis from Step 1
config = {"configurable": {"thread_id": THREAD_ID}}
checkpoints = list(checkpointer.list(config, limit=50))

if not checkpoints:
    print(f"\n  {RED}[ERROR]{RESET} No checkpoints found for thread '{THREAD_ID}'!")
    print(f"  Did you run sap_step1_process.py first?")
    exit(1)

print(f"\n  {CYAN}[DAPR REDIS]{RESET} Found {len(checkpoints)} checkpoints from Step 1")

# Show the messages that survived the crash
latest = checkpoints[0]
msgs = latest.checkpoint.get("channel_values", {}).get("messages", [])
print(f"  {CYAN}[DAPR REDIS]{RESET} {len(msgs)} messages recovered from Redis:")
for i, msg in enumerate(msgs):
    msg_type = getattr(msg, "type", type(msg).__name__)
    name = getattr(msg, "name", "")
    content = getattr(msg, "content", "")
    tool_calls = getattr(msg, "tool_calls", None)

    if tool_calls:
        names = [tc.get("name", "?") for tc in tool_calls]
        print(f"    {i+1:2d}. {msg_type:8s} → calls: {', '.join(names)}")
    elif name:
        preview = str(content)[:60].replace("\n", " ")
        print(f"    {i+1:2d}. {msg_type:8s} ({name}): {preview}")
    else:
        preview = str(content)[:60].replace("\n", " ")
        print(f"    {i+1:2d}. {msg_type:8s}: {preview}")

# Create a brand-new agent — NO shared state with Step 1
print(f"\n  {GREEN}[RECOVERY]{RESET} Creating brand-new agent with same checkpointer + thread_id")
print(f"  {GREEN}[RECOVERY]{RESET} LangGraph will load conversation from Dapr Redis\n")

agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=SAP_TOOLS,
    system_prompt=SAP_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

# Ask about the PO created in Step 1
print(f"{BOLD}TEST 1: Does the agent remember the PO from Step 1?{RESET}")
print(f"{DIM}(This proves state was recovered from Redis, not memory){RESET}\n")

run_with_trace(
    agent,
    "What PO number was just created in the previous session? "
    "Who is the vendor, what material, what quantity, and what was the total cost? "
    "Is it still pending approval?",
    thread_id=THREAD_ID,
)

# Follow-up: order another material
print(f"\n{BOLD}TEST 2: Continue the conversation — order another material{RESET}")
print(f"{DIM}(Agent should remember vendor V-10001 and cost center CC-4100){RESET}\n")

run_with_trace(
    agent,
    "Now also order 5 units of MAT-5003 (PLC Controller Module) "
    "from the same vendor V-10001, same cost center CC-4100. "
    "Check material stock and budget first.",
    thread_id=THREAD_ID,
)

# Final stats
config = {"configurable": {"thread_id": THREAD_ID}}
total_cps = list(checkpointer.list(config, limit=50))
latest = total_cps[0] if total_cps else None
total_msgs = 0
if latest:
    total_msgs = len(latest.checkpoint.get("channel_values", {}).get("messages", []))

print(f"""
{'=' * 65}
 {GREEN}RECOVERY COMPLETE{RESET}

 {BOLD}What happened:{RESET}
   Step 1: Agent processed PO (vendor check → material → budget → create PO)
           Process exited. All Python state destroyed.

   Step 2: NEW process, NEW agent (PID {__import__('os').getpid()}).
           Loaded {len(checkpoints)} checkpoints from Dapr Redis.
           Agent remembered the PO number, vendor, cost — everything.
           Continued processing a second order seamlessly.

 {BOLD}Stats:{RESET}
   Checkpoints in Redis: {len(total_cps)}
   Messages in conversation: {total_msgs}
   Thread: '{THREAD_ID}'
   Storage: Dapr → Redis (localhost:6379)

 {BOLD}Verify in Redis:{RESET}
   docker exec dapr_redis redis-cli KEYS '*sap-po*' | wc -l
   docker exec dapr_redis redis-cli HGET \\
     'sap-agent||idx:{THREAD_ID}:' data | python3 -m json.tool
{'=' * 65}
""")
