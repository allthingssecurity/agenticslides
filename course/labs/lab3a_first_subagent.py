"""
LAB 3A: Your First Sub-Agent (Module 3)
==========================================
Build an orchestrator that delegates research to a sub-agent.
The sub-agent has web search; the orchestrator does NOT — forcing delegation.

Learn: SubAgent definition, task() tool, context isolation.

Run: python lab3a_first_subagent.py
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
    print("""
    WHAT HAPPENED:
    1. Orchestrator received your question
    2. Since it has NO search tools, it called:
       task(description="...", subagent_type="researcher")
    3. Researcher got a FRESH, ISOLATED context
    4. Researcher searched the web and synthesized findings
    5. Only the researcher's FINAL answer came back
    6. Orchestrator formatted and delivered it to you

    KEY INSIGHTS:
    ✓ Sub-agents get isolated context (no cross-contamination)
    ✓ Only the final message returns (prevents context bloat)
    ✓ Different models per agent (gpt-4o orchestrator, gpt-4o-mini researcher)

    NEXT: python lab3b_parallel_agents.py
    """)
