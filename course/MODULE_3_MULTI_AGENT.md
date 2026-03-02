# MODULE 3: Multi-Agent Orchestration (45 minutes)
## Hands-On: Building Systems Where Agents Collaborate

> **This module is 90% code.** Every concept is taught through a working example.

---

## 3.1 — Your First Sub-Agent (10 min)

### The `task` Tool — How Agents Delegate

When you define sub-agents, the main agent gets a `task` tool it uses to delegate:

```python
# main agent calls:
task(description="Research Python web frameworks", subagent_type="researcher")
# → researcher sub-agent runs in isolated context
# → only the final answer comes back to main agent
```

### Live Code: Orchestrator + Researcher

```python
# lab3a_first_subagent.py
"""
GOAL: Build an orchestrator that delegates research to a sub-agent.
The sub-agent has web search; the orchestrator does NOT.
This forces delegation.
"""
import json
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

# --- Tool: only the researcher gets this ---
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

# --- Create the agent with a sub-agent ---
agent = create_deep_agent(
    model="openai:gpt-4o",
    # Main agent has NO tools — it must delegate
    tools=[],
    subagents=[
        {
            "name": "researcher",
            "description": "Use this agent to search the web and gather information on any topic. It has access to web search.",
            "system_prompt": (
                "You are a research agent. Use web_search to find information. "
                "Return a concise, well-organized summary of your findings. "
                "Always include source URLs when available."
            ),
            "tools": [web_search],
            "model": "openai:gpt-4o-mini",  # Cheaper model for sub-agent
        }
    ],
    system_prompt="""You are an orchestrator agent. You CANNOT search the web yourself.
You MUST delegate all research tasks to the "researcher" sub-agent using the task tool.

After receiving research results, synthesize them into a clear answer for the user."""
)

# --- Run it ---
result = agent.invoke(
    {"messages": [HumanMessage(content="What is LangGraph and how does it relate to LangChain?")]},
    config={"configurable": {"thread_id": "subagent-1"}}
)

for msg in reversed(result["messages"]):
    if msg.type == "ai" and msg.content:
        print(msg.content)
        break
```

### Run it:
```bash
python lab3a_first_subagent.py
```

### What happens under the hood:
```
1. User → Orchestrator: "What is LangGraph?"
2. Orchestrator calls: task(description="Search for what LangGraph is and
   its relationship to LangChain", subagent_type="researcher")
3. Researcher gets a FRESH context (isolated from orchestrator)
4. Researcher calls: web_search("LangGraph LangChain")
5. Researcher synthesizes search results
6. Researcher's FINAL message returns to Orchestrator
7. Orchestrator formats and delivers answer to user
```

---

## 3.2 — Parallel Sub-Agents (10 min)

### Live Code: Three Researchers in Parallel

```python
# lab3b_parallel_agents.py
"""
GOAL: Orchestrator launches 3 sub-agents in parallel to research
different aspects of a topic, then synthesizes results.
"""
import json
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

@tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query
    """
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10
        )
        data = resp.json()
        parts = []
        if data.get("Abstract"):
            parts.append(data["Abstract"])
        for t in data.get("RelatedTopics", [])[:5]:
            if isinstance(t, dict) and "Text" in t:
                parts.append(t["Text"])
        return "\n".join(parts) if parts else "No results found."
    except Exception as e:
        return f"Error: {e}"

# Define specialist sub-agents
subagents = [
    {
        "name": "tech_researcher",
        "description": "Researches technical aspects — architecture, implementation details, technology stack, APIs.",
        "system_prompt": (
            "You are a technical research specialist. "
            "Focus on architecture, implementation, APIs, and code-level details. "
            "Use web_search to find information. Be specific and technical."
        ),
        "tools": [web_search],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "market_researcher",
        "description": "Researches market aspects — adoption, competitors, pricing, community size, ecosystem.",
        "system_prompt": (
            "You are a market research specialist. "
            "Focus on adoption rates, community size, competitors, pricing, and ecosystem. "
            "Use web_search to find data. Include numbers when available."
        ),
        "tools": [web_search],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "pros_cons_analyst",
        "description": "Analyzes strengths and weaknesses, tradeoffs, and best/worst use cases.",
        "system_prompt": (
            "You are a critical analyst. "
            "Research and provide balanced pros/cons analysis. "
            "Use web_search. Be honest about both strengths and weaknesses."
        ),
        "tools": [web_search],
        "model": "openai:gpt-4o-mini",
    },
]

agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=subagents,
    system_prompt="""You are an orchestrator that produces comprehensive research reports.

## WORKFLOW
1. Plan your research by identifying 2-3 key aspects to investigate
2. Launch MULTIPLE sub-agents IN PARALLEL by calling the task tool
   multiple times in a single response
3. After all results return, synthesize into a structured report
4. Write the report to /output/report.md

## IMPORTANT
- Launch sub-agents in PARALLEL (multiple task calls at once) for speed
- Each sub-agent is a specialist — use the right one for each aspect
- Your final synthesis should combine all perspectives, not just repeat them
"""
)

# --- Run it ---
print("Starting parallel research (this may take 30-60 seconds)...\n")

result = agent.invoke(
    {"messages": [HumanMessage(content=(
        "Give me a comprehensive analysis of using Rust vs Go for "
        "building microservices in 2025."
    ))]},
    config={"configurable": {"thread_id": "parallel-1"}}
)

for msg in reversed(result["messages"]):
    if msg.type == "ai" and msg.content:
        print(msg.content)
        break
```

### Run it:
```bash
python lab3b_parallel_agents.py
```

### The parallel execution pattern:
```
                    ┌─────────────────────┐
                    │    ORCHESTRATOR      │
                    └──┬──────┬──────┬────┘
                       │      │      │
            (parallel) │      │      │
                       ↓      ↓      ↓
              ┌────────┐ ┌────────┐ ┌────────┐
              │ TECH   │ │MARKET  │ │PROS/   │
              │RESEARCH│ │RESEARCH│ │CONS    │
              └────┬───┘ └────┬───┘ └────┬───┘
                   │          │          │
                   ↓          ↓          ↓
              ┌────────────────────────────┐
              │  ORCHESTRATOR SYNTHESIZES   │
              │  → /output/report.md       │
              └────────────────────────────┘
```

---

## 3.3 — Filesystem as Communication Bus (10 min)

### Live Code: Agents Sharing Data via Files

```python
# lab3c_file_sharing.py
"""
GOAL: Researcher writes data to files, Analyst reads and processes it.
The filesystem is the communication channel between agents.
"""
import math
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression safely.

    Args:
        expression: Math expression like '2+3' or 'sqrt(16)'
    """
    allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed.update({"abs": abs, "round": round, "sum": sum, "max": max, "min": min})
    try:
        return str(eval(expression, {"__builtins__": {}}, allowed))
    except Exception as e:
        return f"Error: {e}"

subagents = [
    {
        "name": "data_collector",
        "description": "Collects and structures raw data. Write all data to files in /data/ directory.",
        "system_prompt": """You are a data collection agent.
When given a task:
1. Generate or collect the requested data
2. Write it as structured markdown or CSV to /data/ directory
3. ALWAYS write to files — this is how other agents will read your work
4. Confirm what files you created and their locations.""",
        "tools": [],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "analyst",
        "description": "Reads data from /data/ directory, performs calculations and analysis. Has a calculator tool.",
        "system_prompt": """You are a data analyst.
1. Read data files from /data/ directory using read_file
2. Perform calculations using the calculator tool
3. Write your analysis to /analysis/ directory
4. Provide clear conclusions with numbers.""",
        "tools": [calculate],
        "model": "openai:gpt-4o",
    },
]

agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=subagents,
    system_prompt="""You are a project manager orchestrating data analysis.

## WORKFLOW
1. First, delegate to data_collector to gather/structure the data
   → data_collector writes to /data/
2. Then, delegate to analyst to process the data
   → analyst reads from /data/ and writes to /analysis/
3. Read the analysis results from /analysis/ and present to user

## KEY: Agents communicate through the filesystem!
- data_collector → writes /data/*.md
- analyst → reads /data/*.md → writes /analysis/*.md
- you → read /analysis/*.md → present to user
"""
)

result = agent.invoke(
    {"messages": [HumanMessage(content="""
Create a comparison of cloud provider pricing for a standard web app:
- AWS, GCP, Azure
- Consider: compute (2 vCPU, 8GB RAM), storage (100GB SSD),
  database (PostgreSQL, 50GB), and bandwidth (500GB/month)
- Calculate total monthly cost for each
- Determine which is cheapest and by how much
    """)]},
    config={"configurable": {"thread_id": "filesys-bus"}}
)

for msg in reversed(result["messages"]):
    if msg.type == "ai" and msg.content:
        print(msg.content)
        break
```

### Data flow:
```
data_collector writes:
  /data/aws_pricing.md
  /data/gcp_pricing.md
  /data/azure_pricing.md

analyst reads those files, calculates:
  /analysis/cost_comparison.md   ← with totals and winner

orchestrator reads:
  /analysis/cost_comparison.md   ← presents to user
```

---

## 3.4 — Lab 3: Complete Multi-Agent Q&A System (15 min)

### Goal
Build a production-quality Q&A system: Orchestrator + Researcher + Writer

```python
# lab3_multi_agent_qa.py
"""
COMPLETE MULTI-AGENT Q&A SYSTEM
================================
- Orchestrator: Plans and coordinates
- Researcher: Searches web, takes notes
- Writer: Reads notes, writes polished answers
"""
import json
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

# ─── TOOLS ───────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for current information.

    Args:
        query: The search query
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
            results.append(f"## {data.get('Heading', 'Result')}\n{data['Abstract']}\nSource: {data.get('AbstractURL', 'N/A')}")
        for t in data.get("RelatedTopics", [])[:5]:
            if isinstance(t, dict) and "Text" in t:
                results.append(f"- {t['Text']}\n  URL: {t.get('FirstURL', 'N/A')}")
        return "\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {e}"

# ─── SUB-AGENTS ──────────────────────────────────────

researcher_agent = {
    "name": "researcher",
    "description": (
        "A web researcher. Delegates search tasks to this agent. "
        "It searches the web, gathers information, and saves "
        "structured notes to /research/ directory."
    ),
    "system_prompt": """You are an expert web researcher.

## YOUR JOB
1. Receive a research task from the orchestrator
2. Search the web 2-3 times with different query angles
3. Write structured notes to /research/[topic].md
4. Include ALL source URLs in your notes
5. Return a brief summary of what you found and where you saved it

## NOTE FORMAT
```markdown
# [Topic]
## Key Facts
- fact 1 (source: URL)
- fact 2 (source: URL)
## Details
...
## Sources
- [Source 1](URL)
```

ALWAYS write to files. Never just return text without saving notes.""",
    "tools": [web_search],
    "model": "openai:gpt-4o-mini",
}

writer_agent = {
    "name": "writer",
    "description": (
        "A professional writer. Reads research notes from /research/ "
        "and writes polished, well-structured responses. Does NOT "
        "search the web — only works from existing research notes."
    ),
    "system_prompt": """You are an expert writer and communicator.

## YOUR JOB
1. Read research notes from /research/ directory
2. Synthesize them into a clear, well-structured response
3. Write the final output to /output/answer.md
4. Return the polished answer to the orchestrator

## WRITING RULES
- Use clear headings and structure
- Lead with the most important information
- Include a "Sources" section at the bottom
- Keep language accessible but precise
- If research notes are thin on a topic, say so honestly

DO NOT make up information. Only use what's in the research notes.""",
    "tools": [],  # Writer has no search — only filesystem (automatic)
    "model": "openai:gpt-4o",
}

# ─── ORCHESTRATOR ────────────────────────────────────

orchestrator = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=[researcher_agent, writer_agent],
    system_prompt="""You are an intelligent Q&A orchestrator.

## WORKFLOW (follow this EXACTLY)

### Step 1: Analyze the question
- Is it simple (single search) or complex (multi-faceted)?
- Identify 1-3 research aspects needed

### Step 2: Research phase
- Send each research aspect to the "researcher" sub-agent
- For complex questions, launch multiple researcher tasks IN PARALLEL
- Each researcher task should be specific: "Research [specific aspect]"

### Step 3: Writing phase
- After ALL research is complete, send one task to the "writer"
- Tell the writer what files to read and what structure to use
- Writer task: "Read notes from /research/ and write a [format] about [topic]"

### Step 4: Deliver
- Read /output/answer.md
- Present the answer to the user
- Mention that detailed notes are in /research/

## PARALLEL RESEARCH
For multi-part questions, launch researchers in parallel:
- task("Research aspect 1", subagent_type="researcher")
- task("Research aspect 2", subagent_type="researcher")
(both in same response = parallel execution)

## QUALITY CHECK
Before delivering, quickly verify the answer addresses all parts of the question.
"""
)

# ─── RUN THE SYSTEM ──────────────────────────────────

def ask(question: str, thread: str = "qa"):
    """Ask the multi-agent system a question."""
    print(f"\n{'='*60}")
    print(f"QUESTION: {question}")
    print(f"{'='*60}\n")

    result = orchestrator.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\nANSWER:\n{msg.content}")
            break

# ─── TEST QUESTIONS ──────────────────────────────────

if __name__ == "__main__":
    # Simple question
    ask(
        "What is WebAssembly and why is it important for web development?",
        thread="q1"
    )

    # Complex multi-faceted question
    ask(
        "Compare GraphQL vs REST APIs. Cover: performance differences, "
        "when to use each, learning curve, and tooling ecosystem.",
        thread="q2"
    )
```

### Run it:
```bash
python lab3_multi_agent_qa.py
```

### Expected Execution Flow (Complex Question):
```
Orchestrator: "Complex question with 3 aspects. Launching parallel research."
  │
  ├─→ Researcher 1: "Research GraphQL vs REST performance"
  │   └→ web_search("GraphQL REST performance comparison")
  │   └→ write_file("/research/performance.md")
  │
  ├─→ Researcher 2: "Research when to use GraphQL vs REST"
  │   └→ web_search("when use GraphQL vs REST")
  │   └→ write_file("/research/use_cases.md")
  │
  └─→ Researcher 3: "Research GraphQL REST tooling ecosystem"
      └→ web_search("GraphQL REST developer tools")
      └→ write_file("/research/tooling.md")

  (all three complete)

Orchestrator → Writer: "Read /research/*.md, write comparison article"
  Writer:
    └→ read_file("/research/performance.md")
    └→ read_file("/research/use_cases.md")
    └→ read_file("/research/tooling.md")
    └→ write_file("/output/answer.md")

Orchestrator: reads /output/answer.md → presents to user
```

---

## Key Patterns Learned

| Pattern | Code | When to Use |
|---------|------|-------------|
| Single delegation | `task(desc, subagent_type="x")` | Simple subtask |
| Parallel delegation | Multiple `task()` calls in one response | Independent research aspects |
| File-based communication | Agent A writes → Agent B reads | Data pipeline between agents |
| Specialist agents | Different tools per sub-agent | Separation of concerns |
| Orchestrator has no tools | Forces delegation | Clean architecture |

---

**Next:** Module 4 — Capstone projects including Financial Deep Research and Text-to-SQL.
