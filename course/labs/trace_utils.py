"""
Trace Utilities for Agentic AI Course Labs
============================================
Provides real-time formatted traces of agent tool calls, sub-agent
delegations, and file writes — so students can see what the agent
actually does instead of just "exit code 0".

Three main exports:
  - run_with_trace(agent, question, thread_id) — streams events with colored output
  - interactive_mode(agent, lab_name)           — REPL loop after demo queries
  - resilient_web_search(query)                 — web search with retry/backoff

Usage in any lab:
    from trace_utils import run_with_trace, interactive_mode, resilient_web_search
"""

import time
from langchain_core.messages import HumanMessage

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

# ─── Tool-name → display label mapping ──────────────────

TOOL_LABELS = {
    "web_search": ("SEARCH", CYAN),
    "search_financial_news": ("SEARCH", CYAN),
    "calculator": ("CALC", GREEN),
    "calculate": ("CALC", GREEN),
    "calculate_financial_metrics": ("CALC", GREEN),
    "get_current_time": ("CLOCK", GREEN),
    "get_stock_data": ("DATA", CYAN),
    "explore_schema": ("SCHEMA", CYAN),
    "run_sql_query": ("SQL", CYAN),
    "write_file": ("WRITE", MAGENTA),
    "edit_file": ("EDIT", MAGENTA),
    "read_file": ("READ", BLUE),
    "write_todos": ("PLAN", YELLOW),
    "ls": ("LS", DIM),
    "glob": ("GLOB", DIM),
    "grep": ("GREP", DIM),
    "execute": ("EXEC", RED),
    "task": ("DELEGATE", YELLOW),
}


def _label_for_tool(name: str) -> tuple[str, str]:
    """Return (label, color) for a tool name."""
    if name in TOOL_LABELS:
        return TOOL_LABELS[name]
    return ("TOOL", BLUE)


def _truncate(text: str, max_len: int = 120) -> str:
    """Truncate text for display."""
    text = text.replace("\n", " ").strip()
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _format_args(args: dict) -> str:
    """Format tool call arguments for display."""
    if not args:
        return ""
    parts = []
    for k, v in args.items():
        sv = str(v)
        if len(sv) > 80:
            sv = sv[:77] + "..."
        parts.append(f'{k}="{sv}"' if isinstance(v, str) else f"{k}={sv}")
    return ", ".join(parts)


# ─── Resilient web search with retry ────────────────────

def resilient_web_search(query: str, max_retries: int = 3) -> str:
    """Search the web with automatic retry on rate limits.

    Uses OpenAI's Responses API with web_search_preview.
    Retries with exponential backoff on 429 (rate limit) errors.

    Args:
        query: The search query
        max_retries: Max number of retries (default 3)
    """
    from openai import OpenAI
    client = OpenAI()
    for attempt in range(max_retries + 1):
        try:
            response = client.responses.create(
                model="gpt-4o-mini",
                tools=[{"type": "web_search_preview"}],
                input=query
            )
            return response.output_text
        except Exception as e:
            error_str = str(e)
            # Retry on rate limit (429) with exponential backoff
            if "429" in error_str or "rate_limit" in error_str.lower() or "rate limit" in error_str.lower():
                if attempt < max_retries:
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    print(f"  {YELLOW}[RATE LIMIT]{RESET} Waiting {wait}s before retry ({attempt+1}/{max_retries})...")
                    time.sleep(wait)
                    continue
            return f"Search error: {e}"
    return f"Search failed after {max_retries} retries (rate limited)"


# ─── Core streaming function ────────────────────────────

def run_with_trace(agent, question: str, thread_id: str = "traced", max_retries: int = 2) -> str:
    """Stream agent execution with real-time formatted traces.

    Automatically retries on rate limit errors with backoff.

    Args:
        agent: A compiled LangGraph agent from create_deep_agent()
        question: The user's question / prompt
        thread_id: Conversation thread ID for stateful chat
        max_retries: Number of retries on rate limit (default 2)

    Returns:
        The agent's final text response
    """
    print(f"\n{DIM}{'─' * 50}{RESET}")
    print(f"{BOLD}YOU:{RESET} {question}")
    print(f"{DIM}{'─' * 50}{RESET}\n")

    final_response = ""
    pending_tool_calls: dict[str, str] = {}

    config = {"configurable": {"thread_id": thread_id}}
    inp = {"messages": [HumanMessage(content=question)]}

    for attempt in range(max_retries + 1):
        try:
            for event in agent.stream(inp, config, stream_mode="updates"):
                if "__interrupt__" in event:
                    continue

                if "model" in event:
                    messages = event["model"].get("messages", [])
                    for msg in messages:
                        tool_calls = getattr(msg, "tool_calls", None) or []
                        if tool_calls:
                            for tc in tool_calls:
                                name = tc.get("name", "unknown")
                                args = tc.get("args", {})
                                tc_id = tc.get("id", "")
                                pending_tool_calls[tc_id] = name
                                label, color = _label_for_tool(name)

                                if name == "task":
                                    desc = args.get("description", "")
                                    sub_type = args.get("subagent_type", "")
                                    print(f"  {color}[{label}]{RESET} task(\"{_truncate(desc, 60)}\", subagent_type=\"{sub_type}\")")
                                elif name == "write_file":
                                    path = args.get("path", args.get("file_path", ""))
                                    print(f"  {color}[{label}]{RESET} write_file(\"{path}\")")
                                elif name == "write_todos":
                                    items = args.get("items", args.get("todos", []))
                                    if isinstance(items, list):
                                        print(f"  {color}[{label}]{RESET} write_todos({items})")
                                    else:
                                        print(f"  {color}[{label}]{RESET} write_todos(...)")
                                else:
                                    arg_str = _format_args(args)
                                    print(f"  {color}[{label}]{RESET} {name}({arg_str})")
                        else:
                            content = getattr(msg, "content", "")
                            if content:
                                final_response = content

                elif "tools" in event:
                    messages = event["tools"].get("messages", [])
                    for msg in messages:
                        tc_id = getattr(msg, "tool_call_id", "")
                        tool_name = pending_tool_calls.get(tc_id, "")
                        content = getattr(msg, "content", "")
                        label, color = _label_for_tool(tool_name)

                        if tool_name == "task":
                            print(f"  {GREEN}[SUB-AGENT DONE]{RESET} {_truncate(content, 100)}")
                        elif tool_name in ("write_file", "edit_file"):
                            print(f"  {GREEN}[FILE WRITTEN]{RESET} {_truncate(content, 100)}")
                        elif tool_name in ("ls", "glob", "grep"):
                            print(f"  {DIM}[RESULT] {_truncate(content, 80)}{RESET}")
                        else:
                            print(f"  {GREEN}[RESULT]{RESET} {_truncate(content, 100)}")

            # If we got here without exception, break out of retry loop
            break

        except Exception as e:
            error_str = str(e)
            if ("429" in error_str or "rate_limit" in error_str.lower() or "rate limit" in error_str.lower()) and attempt < max_retries:
                wait = 3 * (attempt + 1)  # 3s, 6s
                print(f"\n  {YELLOW}[RATE LIMIT]{RESET} Waiting {wait}s before retry ({attempt+1}/{max_retries})...")
                time.sleep(wait)
                continue
            else:
                print(f"\n  {RED}[ERROR]{RESET} {error_str}")
                return ""

    # Print the final response
    if final_response:
        print(f"\n{'─' * 50}")
        print(f"{BOLD}AGENT RESPONSE:{RESET}")
        print(f"{'─' * 50}")
        print(final_response)

    return final_response


# ─── Interactive REPL ────────────────────────────────────

def interactive_mode(agent, lab_name: str, thread_id: str | None = None):
    """Start an interactive REPL so students can try their own queries.

    Args:
        agent: A compiled LangGraph agent from create_deep_agent()
        lab_name: Display name for the prompt banner
        thread_id: Optional thread_id (defaults to lab_name + "-interactive")
    """
    tid = thread_id or f"{lab_name}-interactive"

    print(f"\n{'═' * 50}")
    print(f"  {BOLD}YOUR TURN — Try it yourself!{RESET}")
    print(f"{'═' * 50}")
    print(f"  Lab: {lab_name}")
    print(f"  Type a question (or 'quit' to exit)")
    print(f"{'═' * 50}")

    while True:
        try:
            user_input = input(f"\n{BOLD}>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        run_with_trace(agent, user_input, thread_id=tid)
