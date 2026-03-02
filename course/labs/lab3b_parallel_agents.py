"""
LAB 3B: Parallel Sub-Agents (Module 3)
=========================================
Orchestrator launches 3 specialist sub-agents IN PARALLEL,
then synthesizes their results.

Learn: Parallel execution, specialist agents, synthesis pattern.

Run: python lab3b_parallel_agents.py
"""
from openai import OpenAI
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
        client = OpenAI()
        response = client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=query
        )
        return response.output_text
    except Exception as e:
        return f"Error: {e}"


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
    print("""
    WHAT HAPPENED:
    Orchestrator launched 3 sub-agents SIMULTANEOUSLY:
      ├→ tech_researcher  (architecture, APIs)
      ├→ market_researcher (adoption, ecosystem)
      └→ pros_cons_analyst (strengths, weaknesses)
    All three ran in parallel, then results were synthesized.

    KEY INSIGHTS:
    ✓ Parallel execution — multiple task() calls in one response
    ✓ Specialist agents — each focuses on their domain
    ✓ Synthesis — orchestrator combines all perspectives
    ✓ File sharing — agents write to /research/, orchestrator reads

    NEXT: python lab3c_file_sharing.py
    """)
