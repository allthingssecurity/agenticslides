"""
LAB 1: Your First Agent (Module 1)
=====================================
Build an agent with custom tools — calculator + clock.
Learn: @tool decorator, create_deep_agent(), tool calling, thread_id.

Run: python lab1_first_agent.py
"""
import math
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ─── STEP 1: Define Tools ──────────────────────────────

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.
    Supports: +, -, *, /, **, sqrt, sin, cos, log, pi, e

    Args:
        expression: A math expression, e.g. "2 + 3 * 4" or "sqrt(144)"
    """
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names.update({"abs": abs, "round": round})
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return f"Current date/time: {now.strftime('%Y-%m-%d %H:%M:%S (%A)')}"


# ─── STEP 2: Create the Agent ──────────────────────────

agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[calculator, get_current_time],
    system_prompt="""You are a helpful assistant with access to a calculator and clock.

## Rules
- For ANY math question, ALWAYS use the calculator tool — never calculate in your head
- Show your work: state what you're calculating and why
- Be concise but thorough
- When using the calculator, show the expression you're evaluating
"""
)


# ─── STEP 3: Helper Function ───────────────────────────

def ask(question: str, thread_id: str = "lab1"):
    """Send a message to the agent and print the response."""
    print(f"\n{'─'*50}")
    print(f"YOU: {question}")
    print(f"{'─'*50}")

    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread_id}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\nAGENT: {msg.content}")
            return


# ─── STEP 4: Run It ────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print(" LAB 1: Your First Agent")
    print("=" * 50)

    # Test 1: Basic tool use
    ask("What is the square root of 1764?")

    # Test 2: Multi-step calculation
    ask(
        "If I invest $10,000 at 7% annual compound interest, "
        "how much will I have after 10 years? Use A = P*(1+r)^t"
    )

    # Test 3: Time tool
    ask("What day of the week is it today?")

    # Test 4: Combining reasoning + tools
    ask(
        "I was born on March 15, 1995. "
        "How many days have I been alive? Use today's date."
    )

    print("\n" + "=" * 50)
    print(" LAB 1 COMPLETE!")
    print("=" * 50)
    print("""
    WHAT YOU LEARNED:
    ✓ @tool decorator — how to give agents capabilities
    ✓ create_deep_agent() — the factory function
    ✓ Tool calling — the LLM decides when/how to use tools
    ✓ Thread ID — conversation identity for stateful chats

    CHALLENGE: Add a 'unit_converter' tool that converts between
    units (kg↔lbs, km↔miles, etc.) and ask the agent to use it!

    NEXT: python lab2_research_agent.py
    """)
