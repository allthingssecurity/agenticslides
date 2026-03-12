"""
DaprWorkflowAgent — Wraps DeepAgent in a Dapr Workflow for Durability
=====================================================================
Wraps ``create_deep_agent()`` invocation inside a Dapr Workflow.  The
agent invocation is a workflow **activity** — checkpointed by Dapr,
retried on failure, resumable after crash.

Architecture:
    DaprWorkflowAgent.run(task, thread_id)
      │
      ├── Has Dapr Workflow? YES:
      │   ├── schedule_new_workflow(agent_workflow, input=...)
      │   ├── Activity: run_agent_step (creates agent, invokes)
      │   │   └── RetryPolicy: 3 attempts, 2s backoff × 2.0
      │   └── wait_for_workflow_completion() → result
      │
      └── Has Dapr Workflow? NO (simulation):
          └── Direct: create agent with DaprCheckpointSaver, invoke

Key design:
    - One activity = one full agent.invoke().
    - LangGraph checkpointing (DaprCheckpointSaver) provides fine-grained
      state within the turn.
    - Dapr Workflow provides coarse-grained durability across turns.
    - Tools via factory pattern — activity calls tools_factory() to get tools.

Usage:
    from dapr_workflow_agent import DaprWorkflowAgent

    agent = DaprWorkflowAgent(
        model="openai:gpt-4o-mini",
        system_prompt="You are a research assistant.",
        tools_factory=lambda: [web_search],
    )
    result = agent.run("Compare Python and Rust", thread_id="session-1")
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import timedelta
from typing import Any, Callable

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from deepagents import create_deep_agent

from dapr_checkpointer import DaprCheckpointSaver

logger = logging.getLogger(__name__)

# ─── ANSI Colors ─────────────────────────────────────────
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BLUE = "\033[94m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ═══════════════════════════════════════════════════════════
# DaprWorkflowAgent
# ═══════════════════════════════════════════════════════════


class DaprWorkflowAgent:
    """Wraps a DeepAgent in a Dapr Workflow for durable execution.

    The agent's ``invoke()`` call runs as a Dapr Workflow activity with
    retry policy.  ``DaprCheckpointSaver`` handles fine-grained state
    persistence within the agent turn.

    When ``dapr-ext-workflow`` is unavailable, runs the agent directly
    with ``DaprCheckpointSaver`` (still gets state persistence, just no
    workflow-level retry).

    Args:
        model: LLM model string (e.g. ``"openai:gpt-4o-mini"``).
        system_prompt: System prompt for the agent.
        tools_factory: Callable returning a list of tools.  Called inside
            the activity so tools don't need to be serializable.
        store_name: Dapr State Store component name.
        max_attempts: Retry attempts for the workflow activity.
        retry_interval_sec: Initial retry interval in seconds.
        backoff_coefficient: Backoff multiplier for retries.
    """

    def __init__(
        self,
        model: str = "openai:gpt-4o-mini",
        system_prompt: str = "",
        tools_factory: Callable[[], list] | None = None,
        store_name: str = "agentstore",
        max_attempts: int = 3,
        retry_interval_sec: float = 2.0,
        backoff_coefficient: float = 2.0,
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.tools_factory = tools_factory or (lambda: [])
        self.store_name = store_name
        self.max_attempts = max_attempts
        self.retry_interval_sec = retry_interval_sec
        self.backoff_coefficient = backoff_coefficient

        # Try to set up Dapr Workflow
        self._has_workflow = False
        self._wfr = None
        self._wf_client = None
        try:
            from dapr.ext.workflow import (
                DaprWorkflowClient,
                WorkflowRuntime,
            )

            self._wfr = WorkflowRuntime()
            self._wf_client = DaprWorkflowClient()
            self._has_workflow = True
            self._register_workflow()
            logger.info("DaprWorkflowAgent: Dapr Workflow runtime ready")
        except ImportError:
            logger.info(
                "DaprWorkflowAgent: dapr-ext-workflow not installed — "
                "using simulation mode"
            )
        except Exception as exc:
            logger.info(
                "DaprWorkflowAgent: Dapr Workflow unavailable (%s) — "
                "using simulation mode",
                exc,
            )

    def _register_workflow(self) -> None:
        """Register the workflow and activity with the Dapr runtime."""
        from dapr.ext.workflow import (
            DaprWorkflowContext,
            RetryPolicy,
            WorkflowActivityContext,
        )

        wfr = self._wfr
        agent_ref = self  # capture for closure

        @wfr.workflow(name="agent_workflow")
        def agent_workflow(ctx: DaprWorkflowContext, wf_input: str):
            """Dapr Workflow: run the agent as a single retried activity."""
            retry = RetryPolicy(
                first_retry_interval=timedelta(
                    seconds=agent_ref.retry_interval_sec
                ),
                max_number_of_attempts=agent_ref.max_attempts,
                backoff_coefficient=agent_ref.backoff_coefficient,
            )
            result = yield ctx.call_activity(
                run_agent_activity,
                input=wf_input,
                retry_policy=retry,
            )
            return result

        @wfr.activity(name="run_agent_activity")
        def run_agent_activity(
            ctx: WorkflowActivityContext, activity_input: str
        ) -> str:
            """Activity: create agent, invoke, return response."""
            params = json.loads(activity_input)
            return agent_ref._invoke_agent(
                task=params["task"],
                thread_id=params["thread_id"],
            )

    def _invoke_agent(self, task: str, thread_id: str) -> str:
        """Create a DeepAgent with DaprCheckpointSaver and invoke it."""
        checkpointer = DaprCheckpointSaver(store_name=self.store_name)
        tools = self.tools_factory()

        agent = create_deep_agent(
            model=self.model,
            tools=tools,
            system_prompt=self.system_prompt,
            checkpointer=checkpointer,
        )

        config = {"configurable": {"thread_id": thread_id}}
        inp = {"messages": [HumanMessage(content=task)]}
        result = agent.invoke(inp, config)

        # Extract final response text
        messages = result.get("messages", [])
        if messages:
            last = messages[-1]
            content = getattr(last, "content", "")
            if isinstance(content, list):
                parts = [
                    item.get("text", str(item))
                    if isinstance(item, dict)
                    else str(item)
                    for item in content
                ]
                return "\n".join(parts).strip()
            return str(content)
        return ""

    def run(
        self,
        task: str,
        thread_id: str | None = None,
        instance_id: str | None = None,
    ) -> str:
        """Run the agent with durable execution.

        Args:
            task: The user's task / question.
            thread_id: Conversation thread ID (auto-generated if None).
            instance_id: Workflow instance ID (auto-generated if None).

        Returns:
            The agent's final text response.
        """
        if thread_id is None:
            thread_id = f"thread-{uuid.uuid4().hex[:8]}"
        if instance_id is None:
            instance_id = f"wf-{uuid.uuid4().hex[:12]}"

        if self._has_workflow:
            return self._run_with_workflow(task, thread_id, instance_id)
        else:
            return self._run_simulation(task, thread_id, instance_id)

    def _run_with_workflow(
        self, task: str, thread_id: str, instance_id: str
    ) -> str:
        """Run agent via Dapr Workflow (real durability)."""
        print(f"\n  {CYAN}[WORKFLOW]{RESET} Starting Dapr Workflow: {instance_id}")
        print(f"  {CYAN}[WORKFLOW]{RESET} Thread: {thread_id}")
        print(f"  {DIM}{'─' * 50}{RESET}")

        wf_input = json.dumps({
            "task": task,
            "thread_id": thread_id,
        })

        # Start workflow
        self._wfr.start()
        try:
            self._wf_client.schedule_new_workflow(
                workflow="agent_workflow",
                input=wf_input,
                instance_id=instance_id,
            )

            # Wait for completion
            result = self._wf_client.wait_for_workflow_completion(
                instance_id=instance_id,
                timeout_in_seconds=600,
            )

            status = result.runtime_status if result else "UNKNOWN"
            print(f"\n  {CYAN}[WORKFLOW]{RESET} Status: {GREEN}{status}{RESET}")
            print(f"  {CYAN}[WORKFLOW]{RESET} Instance: {instance_id}")

            if result and result.serialized_output:
                output = json.loads(result.serialized_output)
                return output if isinstance(output, str) else json.dumps(output)
            return ""
        finally:
            self._wfr.shutdown()

    def _run_simulation(
        self, task: str, thread_id: str, instance_id: str
    ) -> str:
        """Run agent directly with DaprCheckpointSaver (no workflow)."""
        print(f"\n  {YELLOW}[SIMULATION]{RESET} Running without Dapr Workflow")
        print(f"  {YELLOW}[SIMULATION]{RESET} Instance: {instance_id}")
        print(f"  {YELLOW}[SIMULATION]{RESET} Thread: {thread_id}")
        print(f"  {DIM}{'─' * 50}{RESET}")

        # Use run_with_trace if available, otherwise invoke directly
        try:
            from trace_utils import run_with_trace

            checkpointer = DaprCheckpointSaver(store_name=self.store_name)
            tools = self.tools_factory()
            agent = create_deep_agent(
                model=self.model,
                tools=tools,
                system_prompt=self.system_prompt,
                checkpointer=checkpointer,
            )
            result = run_with_trace(agent, task, thread_id=thread_id)
        except ImportError:
            result = self._invoke_agent(task, thread_id)

        print(f"\n  {GREEN}[DONE]{RESET} Instance: {instance_id}")
        return result


# ═══════════════════════════════════════════════════════════
# HELPERS: Inspect what's stored in checkpoints
# ═══════════════════════════════════════════════════════════


def inspect_checkpoints(checkpointer: DaprCheckpointSaver, thread_id: str) -> None:
    """Print what's inside each checkpoint stored in Dapr Redis."""
    config = {"configurable": {"thread_id": thread_id}}
    checkpoints = list(checkpointer.list(config, limit=20))

    print(f"\n  {CYAN}{'─' * 55}{RESET}")
    print(f"  {CYAN}[DAPR REDIS]{RESET} {len(checkpoints)} checkpoint(s) "
          f"for thread '{thread_id}'")
    print(f"  {CYAN}{'─' * 55}{RESET}")

    for i, cp in enumerate(checkpoints):
        cp_id = cp.config["configurable"]["checkpoint_id"][:16]
        metadata = cp.metadata or {}
        source = metadata.get("source", "?")
        step = metadata.get("step", "?")
        writes = metadata.get("writes", {})

        # Count messages in channel_values
        channel_vals = cp.checkpoint.get("channel_values", {})
        messages = channel_vals.get("messages", [])
        n_msgs = len(messages) if isinstance(messages, list) else 0

        # What node wrote this checkpoint
        write_keys = list(writes.keys()) if isinstance(writes, dict) else []
        node = write_keys[0] if write_keys else source

        print(f"  {DIM}  {i+1}. {cp_id}...{RESET}")
        print(f"  {DIM}     step={step}  node={node}  "
              f"messages={n_msgs}  writes={len(write_keys)}{RESET}")

        # Show the actual messages stored (last 2 only for brevity)
        if messages and i == 0:  # only for the latest checkpoint
            print(f"  {DIM}     ┌── Messages stored in this checkpoint:{RESET}")
            for msg in messages[-4:]:
                msg_type = getattr(msg, "type", type(msg).__name__)
                content = getattr(msg, "content", "")
                if isinstance(content, list):
                    content = " ".join(
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in content
                    )
                preview = str(content)[:80].replace("\n", " ")
                tool_calls = getattr(msg, "tool_calls", None)
                if tool_calls:
                    names = [tc.get("name", "?") for tc in tool_calls]
                    print(f"  {DIM}     │ {msg_type}: [calls: {', '.join(names)}]{RESET}")
                else:
                    print(f"  {DIM}     │ {msg_type}: {preview}{'...' if len(str(content)) > 80 else ''}{RESET}")
            print(f"  {DIM}     └──{RESET}")

    # Show Dapr key structure
    if checkpointer._simulate:
        keys = sorted(checkpointer._mem.keys())
    else:
        # Show what keys we know about from indices
        keys = []
        for cp in checkpoints:
            cpid = cp.config["configurable"]["checkpoint_id"]
            ns = cp.config["configurable"].get("checkpoint_ns", "")
            keys.append(f"cp:{thread_id}:{ns}:{cpid[:16]}...")
        keys.append(f"idx:{thread_id}:  (checkpoint index)")
        keys.append(f"writes:{thread_id}:...  (pending writes)")
        keys.append(f"blob:{thread_id}:...  (channel values)")

    print(f"\n  {CYAN}[DAPR REDIS]{RESET} Key structure in state store:")
    shown = 0
    for key in keys:
        if shown >= 8:
            print(f"  {DIM}     ... and {len(keys) - shown} more keys{RESET}")
            break
        print(f"  {DIM}     {key}{RESET}")
        shown += 1


# ═══════════════════════════════════════════════════════════
# SAP TOOLS: Simulated SAP systems for the demo
# ═══════════════════════════════════════════════════════════


@tool
def sap_check_vendor(vendor_id: str) -> str:
    """Check vendor status and details in SAP S/4HANA.

    Args:
        vendor_id: SAP vendor number (e.g. "V-10001")
    """
    vendors = {
        "V-10001": {
            "name": "Acme Industrial Supplies",
            "status": "ACTIVE",
            "payment_terms": "Net 30",
            "currency": "EUR",
            "country": "DE",
            "credit_rating": "A+",
            "ytd_spend": "€2.4M",
        },
        "V-10002": {
            "name": "Global Tech Components",
            "status": "ACTIVE",
            "payment_terms": "Net 45",
            "currency": "USD",
            "country": "US",
            "credit_rating": "A",
            "ytd_spend": "$890K",
        },
    }
    v = vendors.get(vendor_id)
    if v:
        return json.dumps(v, indent=2)
    return f"Error: Vendor {vendor_id} not found in SAP"


@tool
def sap_check_material(material_id: str) -> str:
    """Look up material/product details and stock in SAP MM.

    Args:
        material_id: SAP material number (e.g. "MAT-5001")
    """
    materials = {
        "MAT-5001": {
            "description": "Industrial Servo Motor 500W",
            "plant": "Plant 1000 (Munich)",
            "stock": 12,
            "unit": "EA",
            "price": "€1,250.00",
            "mrp_type": "PD (MRP)",
            "lead_time_days": 14,
            "last_po": "PO-4500012345",
        },
        "MAT-5002": {
            "description": "Hydraulic Valve Assembly HV-200",
            "plant": "Plant 1000 (Munich)",
            "stock": 3,
            "unit": "EA",
            "price": "€680.00",
            "mrp_type": "PD (MRP)",
            "lead_time_days": 21,
            "last_po": "PO-4500012200",
        },
        "MAT-5003": {
            "description": "PLC Controller Module X7",
            "plant": "Plant 2000 (Berlin)",
            "stock": 0,
            "unit": "EA",
            "price": "€3,400.00",
            "mrp_type": "PD (MRP)",
            "lead_time_days": 28,
            "last_po": "PO-4500011990",
        },
    }
    m = materials.get(material_id)
    if m:
        return json.dumps(m, indent=2)
    return f"Error: Material {material_id} not found in SAP"


@tool
def sap_create_purchase_order(
    vendor_id: str, material_id: str, quantity: int, notes: str = ""
) -> str:
    """Create a purchase order in SAP MM.

    Args:
        vendor_id: SAP vendor number
        material_id: SAP material number
        quantity: Order quantity
        notes: Optional notes for the PO
    """
    import random
    po_number = f"PO-450001{random.randint(3000, 9999)}"
    return json.dumps({
        "status": "CREATED",
        "po_number": po_number,
        "vendor": vendor_id,
        "material": material_id,
        "quantity": quantity,
        "notes": notes,
        "approval_status": "PENDING_APPROVAL",
        "message": f"Purchase order {po_number} created. Pending manager approval.",
    }, indent=2)


@tool
def sap_check_budget(cost_center: str, amount: float) -> str:
    """Check available budget for a cost center in SAP CO.

    Args:
        cost_center: SAP cost center (e.g. "CC-4100")
        amount: Amount to check against budget
    """
    budgets = {
        "CC-4100": {"name": "Manufacturing Ops", "budget": 500000, "spent": 320000, "currency": "EUR"},
        "CC-4200": {"name": "R&D Engineering", "budget": 750000, "spent": 680000, "currency": "EUR"},
    }
    b = budgets.get(cost_center)
    if not b:
        return f"Error: Cost center {cost_center} not found"
    available = b["budget"] - b["spent"]
    sufficient = "YES" if amount <= available else "NO — OVER BUDGET"
    return json.dumps({
        "cost_center": cost_center,
        "name": b["name"],
        "total_budget": f"€{b['budget']:,.0f}",
        "spent_ytd": f"€{b['spent']:,.0f}",
        "available": f"€{available:,.0f}",
        "requested": f"€{amount:,.0f}",
        "sufficient": sufficient,
    }, indent=2)


SAP_TOOLS = [sap_check_vendor, sap_check_material, sap_create_purchase_order, sap_check_budget]

SAP_SYSTEM_PROMPT = """You are an SAP Procurement Agent that helps process purchase requests.

You have access to these SAP systems:
- **SAP MM** (Materials Management): Check materials, stock levels, create POs
- **SAP FI/CO** (Finance/Controlling): Check budgets by cost center
- **SAP BP** (Business Partner): Check vendor status and details

## Your Workflow for Purchase Requests:
1. Check the vendor status (is vendor active?)
2. Check material details and current stock
3. Check budget availability for the cost center
4. If everything checks out, create the purchase order
5. Summarize: what was ordered, from whom, PO number, approval status

## Important:
- Always verify vendor is ACTIVE before ordering
- Always check budget BEFORE creating PO
- Flag any issues: low stock, over-budget, inactive vendor
- Be specific with SAP document numbers
"""


# ═══════════════════════════════════════════════════════════
# DEMO: SAP Purchase Order Processing with Crash Recovery
# ═══════════════════════════════════════════════════════════


def demo():
    """Demo: SAP procurement agent with Dapr crash recovery.

    Scenario: An SAP procurement agent processes a purchase request.
    Mid-conversation, the process "crashes". A new agent recovers
    the full conversation from Dapr Redis and continues processing.

    Shows:
    - What exactly is stored in each checkpoint
    - How the Dapr State Store keys are structured
    - Real SAP-style multi-step tool usage
    - Recovery with full conversation context
    """
    from trace_utils import run_with_trace

    THREAD = "sap-po-session-1"

    # Clean up any previous run
    checkpointer = DaprCheckpointSaver(store_name="agentstore")
    checkpointer.delete_thread(THREAD)

    # ═════════════════════════════════════════════════════
    # STEP 1: Process a purchase request
    # ═════════════════════════════════════════════════════

    print("=" * 65)
    print(" SAP DURABLE AGENT DEMO")
    print(" Scenario: Purchase order processing with crash recovery")
    print("=" * 65)

    print(f"\n{BOLD}STEP 1: Agent processes a purchase request{RESET}")
    print(f"{DIM}Agent will call SAP tools: check vendor → check material")
    print(f"→ check budget → create PO{RESET}")

    agent = create_deep_agent(
        model="openai:gpt-4o-mini",
        tools=SAP_TOOLS,
        system_prompt=SAP_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    run_with_trace(
        agent,
        "Process this purchase request:\n"
        "- Vendor: V-10001 (Acme Industrial Supplies)\n"
        "- Material: MAT-5002 (Hydraulic Valve Assembly)\n"
        "- Quantity: 10 units\n"
        "- Cost Center: CC-4100 (Manufacturing Ops)\n"
        "- Urgency: High — production line waiting",
        thread_id=THREAD,
    )

    # Show what's stored in Dapr Redis
    inspect_checkpoints(checkpointer, THREAD)

    # ═════════════════════════════════════════════════════
    # STEP 2: CRASH — destroy the agent
    # ═════════════════════════════════════════════════════

    print(f"\n{'=' * 65}")
    print(f" {RED}{'█' * 50}{RESET}")
    print(f" {RED} PROCESS CRASHED!{RESET}")
    print(f" {RED}{'█' * 50}{RESET}")
    print(f" Agent object destroyed. Python state gone.")
    print(f" BUT: All checkpoints are in Dapr Redis.")
    print(f" The conversation, tool results, PO number — all persisted.")
    print(f"{'=' * 65}")

    del agent  # everything in Python memory is gone

    # ═════════════════════════════════════════════════════
    # STEP 3: RECOVER — new agent, same thread_id
    # ═════════════════════════════════════════════════════

    print(f"\n{'=' * 65}")
    print(f" {GREEN}RECOVERY: Creating brand-new agent{RESET}")
    print(f" Same DaprCheckpointSaver + thread_id = '{THREAD}'")
    print(f" LangGraph loads full conversation from Dapr Redis")
    print(f"{'=' * 65}")

    # Brand new agent — no shared state with the old one
    agent2 = create_deep_agent(
        model="openai:gpt-4o-mini",
        tools=SAP_TOOLS,
        system_prompt=SAP_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    print(f"\n{BOLD}STEP 3a: Ask about the PO that was just created{RESET}")
    print(f"{DIM}(Agent must remember from Dapr Redis — it has no in-memory state){RESET}")

    run_with_trace(
        agent2,
        "What PO number was just created? Who is the vendor and what "
        "was the total cost? Is it still pending approval?",
        thread_id=THREAD,
    )

    print(f"\n{BOLD}STEP 3b: Follow-up — order another material from same vendor{RESET}")
    print(f"{DIM}(Agent should remember vendor V-10001 context from the crash){RESET}")

    run_with_trace(
        agent2,
        "Good. Now also order 5 units of MAT-5003 (PLC Controller Module) "
        "from the same vendor V-10001, same cost center CC-4100. "
        "Check if we have budget for it.",
        thread_id=THREAD,
    )

    # ═════════════════════════════════════════════════════
    # SUMMARY: What was stored and how
    # ═════════════════════════════════════════════════════

    inspect_checkpoints(checkpointer, THREAD)

    config = {"configurable": {"thread_id": THREAD}}
    total_cps = list(checkpointer.list(config, limit=50))

    print(f"\n{'=' * 65}")
    print(f" DEMO COMPLETE")
    print(f"{'=' * 65}")
    print(f"""
 {BOLD}What is stored in each checkpoint:{RESET}
   • {CYAN}messages{RESET}    — Full conversation (user + assistant + tool results)
   • {CYAN}channel_values{RESET} — LangGraph state (messages, tool call history)
   • {CYAN}metadata{RESET}   — Which node wrote it (model/tools), step number
   • {CYAN}writes{RESET}     — Pending writes from the last node execution
   • {CYAN}parent_id{RESET}  — Link to previous checkpoint (forms a chain)

 {BOLD}How it's stored in Dapr Redis:{RESET}
   • cp:{{thread}}:{{ns}}:{{id}}     — Checkpoint + metadata (serialized)
   • blob:{{thread}}:{{ns}}:{{ch}}:{{v}} — Channel values (messages, state)
   • writes:{{thread}}:{{ns}}:{{id}}  — Pending writes for a checkpoint
   • idx:{{thread}}:{{ns}}           — Sorted index of checkpoint IDs

 {BOLD}How recovery works:{RESET}
   1. New agent created with same checkpointer + thread_id
   2. LangGraph calls checkpointer.get_tuple(config)
   3. Checkpointer reads latest checkpoint from Dapr Redis
   4. Deserializes messages, channel values, pending writes
   5. Agent resumes with full conversation history

 {BOLD}Stats:{RESET}
   Total checkpoints: {len(total_cps)}
   Thread: '{THREAD}'
   Storage: Dapr State Store → Redis (localhost:6379)
""")


if __name__ == "__main__":
    demo()
