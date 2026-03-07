"""
LAB 3A: Your First Sub-Agent
==============================
Orchestrator delegates research to a sub-agent.
The orchestrator has NO tools - it MUST delegate.
"""
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent
from trace_utils import run_with_trace, interactive_mode, resilient_web_search


# TOOL: Only the researcher gets this
@tool
def web_search(query: str) -> str:
    """Search the web and return results.

    Args:
        query: Search query string
    """
    return resilient_web_search(query)


# AGENT: Orchestrator + Researcher Sub-Agent
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    # Orchestrator has NO tools - it MUST delegate
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
            "model": "openai:gpt-4o-mini",
        }
    ],
    system_prompt="""You are an orchestrator agent.

You CANNOT search the web yourself - you have no search tools.
You MUST delegate ALL research tasks to the "researcher" sub-agent
using the task tool.

## YOUR WORKFLOW
1. Analyze the user's question
2. Delegate research: task(description="...", subagent_type="researcher")
3. Receive the researcher's findings
4. Synthesize and present a clear answer to the user

Be specific in your task descriptions so the researcher knows
exactly what to search for.""",
)


# RUN IT
def ask(question: str, thread: str = "subagent-demo"):
    print(f"\n{'=' * 60}")
    print(f" QUERY: {question}")
    print(f"{'=' * 60}\n")

    run_with_trace(agent, question, thread_id=thread)


if __name__ == "__main__":
    print("=" * 60)
    print(" LAB 3A: Your First Sub-Agent")
    print(" Orchestrator -> delegates -> Researcher -> answers")
    print("=" * 60)

    ask("What is LangGraph and how does it relate to LangChain?")

    print(f"\n{'=' * 60}")
    print(" LAB 3A COMPLETE!")
    print("=" * 60)

    interactive_mode(agent, "Lab 3a: Sub-Agent Delegation")
