# DeepAgents + OpenAI — Quick Reference Cheat Sheet

## Setup (30 seconds)
```bash
pip install deepagents "langchain-openai>=1.1.8" httpx
export OPENAI_API_KEY="sk-..."
```

---

## Pattern 1: Simple Agent with Tools
```python
from deepagents import create_deep_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

@tool
def my_tool(query: str) -> str:
    """Tool description."""
    return "result"

agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[my_tool],
    system_prompt="You are a helpful assistant."
)

result = agent.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config={"configurable": {"thread_id": "thread-1"}}
)
print(result["messages"][-1].content)
```

---

## Pattern 2: Sub-Agent Delegation
```python
agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],  # No tools = must delegate
    subagents=[{
        "name": "researcher",
        "description": "Searches the web for information.",
        "system_prompt": "You search and summarize.",
        "tools": [web_search],
        "model": "openai:gpt-4o-mini",
    }],
    system_prompt="Delegate all research to the researcher."
)
```

---

## Pattern 3: Parallel Sub-Agents
```python
agent = create_deep_agent(
    model="openai:gpt-4o",
    subagents=[agent_a, agent_b, agent_c],
    system_prompt="""
    Launch ALL sub-agents IN PARALLEL by calling multiple
    task() tools in a SINGLE response."""
)
```

---

## Pattern 4: File-Based Pipeline
```python
subagents = [
    {"name": "collector", "description": "Writes data to /data/",
     "system_prompt": "Write findings to /data/output.md", ...},
    {"name": "analyst", "description": "Reads /data/, writes /analysis/",
     "system_prompt": "Read /data/output.md, analyze, write /analysis/", ...},
]
# Collector writes → Analyst reads → Orchestrator presents
```

---

## Pattern 5: Full Multi-Phase System
```python
agent = create_deep_agent(
    model="openai:gpt-4o",
    subagents=[data_agent, news_agent, analyst_agent, writer_agent],
    system_prompt="""
    Phase 1 (PARALLEL): data_agent + news_agent
    Phase 2 (SEQUENTIAL): analyst reads Phase 1 output
    Phase 3 (SEQUENTIAL): writer reads all data → final report
    """
)
```

---

## SubAgent Definition
```python
{
    "name": "agent_name",             # Required
    "description": "What it does",     # Required — orchestrator reads this
    "system_prompt": "Instructions",   # Required
    "tools": [tool1, tool2],           # Optional
    "model": "openai:gpt-4o-mini",    # Optional (cheaper for sub-tasks)
}
```

---

## Available Models (OpenAI)
| Model | Best For | Cost |
|-------|----------|------|
| `openai:gpt-4o` | Orchestrator, complex reasoning | $$ |
| `openai:gpt-4o-mini` | Sub-agents, simple tasks | $ |
| `openai:gpt-4-turbo` | Long context tasks | $$ |

---

## Built-in Tools (automatic via FilesystemMiddleware)
```
ls(path)           — list directory
read_file(path)    — read a file
write_file(path, content)  — create/overwrite file
edit_file(path, old, new)  — find & replace in file
glob(pattern)      — find files by pattern
grep(pattern)      — search file contents
write_todos(items) — create task plan (automatic)
```

---

## File Organization Convention
```
/research/     ← raw research notes
/data/         ← structured data
/analysis/     ← processed analysis
/drafts/       ← work in progress
/output/       ← final deliverables
/report/       ← reports
```
