"""
LAB 7: Long-Term Memory Across Sessions
=======================================
Demonstrates cross-session memory using /memories/ routed to StoreBackend.

Session A writes durable preferences.
Session B (different thread_id) recalls and applies them.
"""
import os

from deepagents import create_deep_agent
from deepagents.backends.composite import CompositeBackend
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.store import StoreBackend
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore

from trace_utils import interactive_mode, run_with_trace

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINTER = MemorySaver()
STORE = InMemoryStore()


def make_backend(runtime):
    """Route /memories/ to long-term store; keep normal files on local disk."""
    return CompositeBackend(
        default=FilesystemBackend(root_dir=BASE_DIR),
        routes={"/memories/": StoreBackend(runtime)},
    )


memory_agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[],
    backend=make_backend,
    store=STORE,
    checkpointer=CHECKPOINTER,
    system_prompt="""You are a personal assistant with long-term memory.

## MEMORY BEHAVIOR
- At the start of each task, read /memories/user-profile.md.
- If missing, create /memories/user-profile.md with sections:
  - Identity
  - Preferences
  - Work Style
  - Important Context
- When user shares durable preferences or profile details, update memory IMMEDIATELY.
- When asked what you remember, read memory and answer from it.

## SAFETY
- Never store secrets (API keys, passwords, tokens, private credentials).

## RESPONSE STYLE
- Be concise and practical.
- If confidence is low, ask one clarifying question.
""",
)


def ask_session(thread_id: str, question: str):
    print(f"\n{'=' * 68}")
    print(f" THREAD: {thread_id}")
    print(f" QUERY: {question}")
    print(f"{'=' * 68}\n")
    run_with_trace(memory_agent, question, thread_id=thread_id)


if __name__ == "__main__":
    print("=" * 68)
    print(" LAB 7: Long-Term Memory Across Sessions")
    print(" Session A writes memory, Session B recalls it")
    print("=" * 68)

    ask_session(
        "session-a",
        "My name is Alex. I prefer concise bullet summaries and action items first. "
        "Please remember this for future sessions.",
    )

    ask_session(
        "session-b",
        "What do you remember about my preferences, and how will you format future answers?",
    )

    print(f"\n{'=' * 68}")
    print(" LAB 7 COMPLETE!")
    print("=" * 68)

    interactive_mode(memory_agent, "Lab 7: Long-Term Memory", thread_id="session-c")
