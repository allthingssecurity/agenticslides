"""
LAB 2: Research Agent (Module 2)
==================================
Build an agent that searches the web, takes notes to files,
and writes a structured research report.

Learn: Filesystem tools, planning with todos, context offloading.

Run: python lab2_research_agent.py
"""
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent
from trace_utils import run_with_trace, interactive_mode, resilient_web_search


# ─── TOOL: Web Search ──────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for current information on any topic.

    Args:
        query: The search query
    """
    return resilient_web_search(query)


# ─── AGENT: Research Agent ─────────────────────────────

research_agent = create_deep_agent(
    model="openai:gpt-4o-mini",  # Use mini to avoid rate limits on free-tier keys
    tools=[web_search],
    system_prompt="""You are a research agent that produces well-organized reports.

## WORKFLOW (ALWAYS follow this order)
1. **Plan**: Use write_todos to break the research into 3-5 steps
2. **Research**: Search for information on each aspect (2-3 searches per topic)
3. **Take Notes**: Write findings to /research/ as structured markdown files
4. **Synthesize**: Read your notes and write a final report to /output/report.md
5. **Deliver**: Present a summary to the user with key findings

## File Organization
/research/
├── topic_1.md       # Notes on each research topic
├── topic_2.md
└── sources.md       # All URLs and citations collected
/output/
└── report.md        # Final polished report

## Research Quality Rules
- Search at least 2-3 times per topic from different angles
- Write notes IMMEDIATELY after each search — don't hold them in memory
- Always include source URLs
- Distinguish facts from opinions
- If information conflicts, note the discrepancy

## Report Format (for /output/report.md)
# [Title]
## Executive Summary
(2-3 sentences)
## Key Findings
### [Topic 1]
...
### [Topic N]
## Comparison Table (if applicable)
| Aspect | Option A | Option B |
|--------|----------|----------|
## Sources
- [Name](URL)
"""
)


# ─── RUN IT ─────────────────────────────────────────────

def research(question: str, thread: str = "lab2"):
    """Run a research query."""
    print(f"\n{'='*60}")
    print(f" RESEARCH QUERY: {question}")
    print(f"{'='*60}\n")

    run_with_trace(research_agent, question, thread_id=thread)


if __name__ == "__main__":
    print("=" * 60)
    print(" LAB 2: Research Agent")
    print(" The agent will: search → take notes → write report")
    print("=" * 60)

    research(
        "Compare Python vs JavaScript for backend development in 2025. "
        "Cover: performance, ecosystem, developer experience, and job market."
    )

    print(f"\n{'='*60}")
    print(" LAB 2 COMPLETE!")
    print("=" * 60)
    print("""
    WHAT YOU LEARNED:
    ✓ Filesystem tools — agent writes notes to /research/ files
    ✓ Planning — agent uses write_todos before starting
    ✓ Context offloading — research saved to files, not just memory
    ✓ Structured output — organized report in /output/report.md

    KEY INSIGHT:
    The agent wrote to files, so even if the conversation is
    summarized, the research notes persist and can be re-read!

    CHALLENGE: Add a fetch_url tool that reads full web pages,
    and ask the agent to do deeper research on a technical topic.

    NEXT: python lab3a_first_subagent.py
    """)

    interactive_mode(research_agent, "Lab 2: Research Agent")
