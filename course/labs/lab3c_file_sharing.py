"""
LAB 3C: Filesystem as Communication Bus (Module 3)
=====================================================
Agents communicate through files:
  Data Collector writes → Analyst reads & processes → Orchestrator presents

Learn: File-based inter-agent communication, sequential pipeline.

Run: python lab3c_file_sharing.py
"""
import math
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ─── TOOL: Calculator for the analyst ──────────────────

@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression safely.

    Args:
        expression: Math expression like '2+3', 'sqrt(16)', 'round(3.14159, 2)'
    """
    allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed.update({"abs": abs, "round": round, "sum": sum, "max": max, "min": min})
    try:
        return str(eval(expression, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"Error: {e}"


# ─── SUB-AGENTS ────────────────────────────────────────

subagents = [
    {
        "name": "data_collector",
        "description": (
            "Collects and structures raw data. "
            "Writes all data to /data/ directory as markdown tables."
        ),
        "system_prompt": """You are a data collection specialist.

YOUR JOB:
1. When given a data task, create realistic, structured data
2. Write it as MARKDOWN TABLES to /data/[topic].md
3. Always include headers and units
4. Confirm what files you created

IMPORTANT: Write to files — other agents will read your output!

Example file format:
```
# Cloud Pricing Data
| Provider | Service | Specs | Monthly Cost |
|----------|---------|-------|-------------|
| AWS      | EC2     | 2 vCPU, 8GB | $67.00 |
```""",
        "tools": [],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "analyst",
        "description": (
            "Reads data from /data/, performs calculations and analysis, "
            "writes conclusions to /analysis/. Has a calculator tool."
        ),
        "system_prompt": """You are a data analyst with a calculator.

YOUR JOB:
1. Read data files from /data/ using read_file
2. Perform calculations using the calculate tool
3. Write your analysis to /analysis/results.md
4. Include: totals, averages, rankings, percentage differences
5. Provide clear conclusions backed by numbers

ALWAYS show your calculation steps!""",
        "tools": [calculate],
        "model": "openai:gpt-4o",
    },
]


# ─── ORCHESTRATOR ──────────────────────────────────────

agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=subagents,
    system_prompt="""You are a project manager orchestrating data analysis.

## WORKFLOW (SEQUENTIAL — each step depends on previous)
1. FIRST: data_collector gathers data → writes to /data/
2. THEN: analyst processes /data/ files → writes to /analysis/
3. FINALLY: You read /analysis/ and present findings to user

## HOW AGENTS COMMUNICATE:
  data_collector → writes /data/*.md
  analyst → reads /data/*.md → writes /analysis/*.md
  you → read /analysis/*.md → present to user

The FILESYSTEM is the communication channel between agents!
"""
)


# ─── RUN IT ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print(" LAB 3C: Filesystem as Communication Bus")
    print(" Collector → files → Analyst → files → Orchestrator")
    print("=" * 60)

    question = """
Compare cloud hosting costs for a standard web application:
- Providers: AWS, Google Cloud, Azure
- Services needed:
  - Compute: 2 vCPU, 8GB RAM
  - Storage: 100GB SSD
  - Database: PostgreSQL, 50GB
  - Bandwidth: 500GB/month
- Calculate total monthly cost for each
- Determine which is cheapest and by how much ($ and %)
    """

    print(f"\n QUERY: {question.strip()}")
    print(f"\n Running pipeline: collect → analyze → present...\n")

    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": "file-sharing-lab"}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\n{'─'*60}")
            print("FINAL ANALYSIS:")
            print(f"{'─'*60}")
            print(msg.content)
            break

    print(f"\n{'='*60}")
    print(" LAB 3C COMPLETE!")
    print("=" * 60)
    print("""
    DATA FLOW:
    data_collector wrote → /data/cloud_pricing.md
    analyst read /data/ → calculated → wrote /analysis/results.md
    orchestrator read /analysis/ → presented to you

    KEY INSIGHT:
    ✓ The filesystem IS the message bus between agents
    ✓ Each agent only knows about files, not other agents directly
    ✓ Pipeline: produce → consume → produce → consume
    ✓ Data persists — even after summarization, files remain

    NEXT: python lab4_financial_research.py (Capstone!)
    """)
