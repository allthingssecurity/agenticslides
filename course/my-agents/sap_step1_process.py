"""
SAP Durable Agent — STEP 1: Process a Purchase Order
=====================================================
This script processes a purchase request, then the process EXITS.
All state is persisted to Dapr Redis via DaprCheckpointSaver.

Run:
    dapr run --app-id sap-agent \
             --dapr-grpc-port 50001 \
             --resources-path ./components \
             -- ../.venv/bin/python sap_step1_process.py

After this exits, run sap_step2_recover.py to prove recovery works.
You can also verify data in Redis between runs:
    docker exec dapr_redis redis-cli KEYS '*sap-po*'
"""

from deepagents import create_deep_agent
from trace_utils import run_with_trace
from dapr_checkpointer import DaprCheckpointSaver
from sap_tools import SAP_TOOLS, SAP_SYSTEM_PROMPT, THREAD_ID, STORE_NAME

# ─── ANSI ────────────────────────────────────────────
CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

print("=" * 65)
print(" SAP DURABLE AGENT — STEP 1: Process Purchase Order")
print(f" Thread: {THREAD_ID}")
print(f" State Store: Dapr Redis ({STORE_NAME})")
print("=" * 65)

# Clean up any previous run
checkpointer = DaprCheckpointSaver(store_name=STORE_NAME)
checkpointer.delete_thread(THREAD_ID)

# Create agent with Dapr-backed checkpointer
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=SAP_TOOLS,
    system_prompt=SAP_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

# Process the purchase request
print(f"\n{BOLD}Processing purchase request...{RESET}")
print(f"{DIM}Agent will: check vendor → check material → check budget → create PO{RESET}\n")

run_with_trace(
    agent,
    "Process this purchase request:\n"
    "- Vendor: V-10001 (Acme Industrial Supplies)\n"
    "- Material: MAT-5002 (Hydraulic Valve Assembly)\n"
    "- Quantity: 10 units\n"
    "- Cost Center: CC-4100 (Manufacturing Ops)\n"
    "- Urgency: High — production line waiting",
    thread_id=THREAD_ID,
)

# Show what was persisted
config = {"configurable": {"thread_id": THREAD_ID}}
checkpoints = list(checkpointer.list(config, limit=50))
print(f"\n  {CYAN}[DAPR REDIS]{RESET} {len(checkpoints)} checkpoints persisted")

# Show message count in latest checkpoint
if checkpoints:
    latest = checkpoints[0]
    msgs = latest.checkpoint.get("channel_values", {}).get("messages", [])
    print(f"  {CYAN}[DAPR REDIS]{RESET} {len(msgs)} messages in latest checkpoint:")
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

print(f"""
{'=' * 65}
 {GREEN}STEP 1 COMPLETE — PROCESS EXITING{RESET}

 The Python process is about to die.
 All agent state is in Dapr Redis.

 {BOLD}Verify it's really in Redis:{RESET}
   docker exec dapr_redis redis-cli KEYS '*sap-po*' | wc -l

 {BOLD}Now run Step 2 to recover:{RESET}
   dapr run --app-id sap-agent \\
            --dapr-grpc-port 50001 \\
            --resources-path ./components \\
            -- ../.venv/bin/python sap_step2_recover.py
{'=' * 65}
""")
