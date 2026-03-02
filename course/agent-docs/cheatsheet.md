# DeepAgents + OpenAI — Agent Quick Reference

> Consult this file anytime during the course for common patterns, tool signatures, and configuration.

---

## Setup (Copy-Paste Ready)

**OS[mac/linux]:**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install deepagents "langchain-openai>=1.1.8" "openai>=1.66.0"
export OPENAI_API_KEY="sk-your-key-here"
```

**OS[windows]:**
```cmd
python -m venv .venv && .venv\Scripts\activate
pip install deepagents "langchain-openai>=1.1.8" "openai>=1.66.0"
set OPENAI_API_KEY=sk-your-key-here
```

---

## Pattern 1: Simple Agent with Custom Tools

```python
from deepagents import create_deep_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

@tool
def my_tool(query: str) -> str:
    """Tool description — the LLM reads this to decide when to call it."""
    return "result"

agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[my_tool],
    system_prompt="You are a helpful assistant."
)

result = agent.invoke(
    {"messages": [HumanMessage(content="Hello")]},
    config={"configurable": {"thread_id": "thread-1"}}
)
print(result["messages"][-1].content)
```

**Used in:** Lab 1 (calculator + clock), Lab 2 (web search), Lab 5 (SQL agent)

---

## Pattern 2: Sub-Agent Delegation

```python
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[],  # No tools = orchestrator MUST delegate
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

**Used in:** Lab 3a (orchestrator + researcher)

---

## Pattern 3: Parallel Sub-Agents

```python
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[],
    subagents=[agent_a, agent_b, agent_c],
    system_prompt="""
    Launch ALL sub-agents IN PARALLEL by calling multiple
    task() tools in a SINGLE response.
    """
)
```

**Used in:** Lab 3b (tech + market + pros/cons researchers), Lab 4 Phase 1 (market data + news)

---

## Pattern 4: File-Based Sequential Pipeline

```python
subagents = [
    {
        "name": "collector",
        "description": "Writes data to /data/",
        "system_prompt": "Write findings to /data/output.md",
        "tools": [],
        "model": "openai:gpt-4o-mini",
    },
    {
        "name": "analyst",
        "description": "Reads /data/, writes /analysis/",
        "system_prompt": "Read /data/output.md, analyze, write /analysis/",
        "tools": [calculate],
        "model": "openai:gpt-4o",
    },
]
# Orchestrator runs: collector first → analyst second → present
```

**Used in:** Lab 3c (collector → analyst), Lab 6 (researcher → writer → editor)

---

## Pattern 5: Multi-Phase System (Parallel + Sequential)

```python
agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[],
    subagents=[data_agent, news_agent, analyst_agent, writer_agent],
    system_prompt="""
    Phase 1 (PARALLEL): data_agent + news_agent
    Phase 2 (SEQUENTIAL): analyst reads Phase 1 output
    Phase 3 (SEQUENTIAL): writer reads all data → final report
    """
)
```

**Used in:** Lab 4 (financial research system)

---

## Sub-Agent Definition Template

```python
{
    "name": "agent_name",             # Required — unique identifier
    "description": "What it does",     # Required — orchestrator reads this to route tasks
    "system_prompt": "Instructions",   # Required — detailed workflow for the sub-agent
    "tools": [tool1, tool2],           # Optional — custom tools (empty list = filesystem only)
    "model": "openai:gpt-4o-mini",    # Optional — defaults to orchestrator's model
}
```

---

## Available Models

| Model | Best For | Relative Cost | Rate Limits |
|-------|----------|---------------|-------------|
| `openai:gpt-4o-mini` | **Default for all agents** — great balance of quality, cost, and rate limits | $ | High (perfect for student keys) |
| `openai:gpt-4o` | Complex reasoning, writing (upgrade when you have paid-tier API keys) | $$ | Lower (may hit 30k TPM on free tier) |
| `openai:gpt-4-turbo` | Long context tasks | $$ | Lower |

**Recommendation:** Use `gpt-4o-mini` for ALL agents during the course. It has much higher rate limits and lower cost, which is critical for student/free-tier API keys. Upgrade to `gpt-4o` only if you have a paid-tier key and need higher quality output.

---

## Built-in Tools (Automatic via FilesystemMiddleware)

Every agent gets these tools for free — no need to define them:

| Tool | Signature | Purpose |
|------|-----------|---------|
| `ls(path)` | `ls("/research/")` | List directory contents |
| `read_file(path)` | `read_file("/data/notes.md")` | Read a file |
| `write_file(path, content)` | `write_file("/output/report.md", "# Report\n...")` | Create/overwrite a file |
| `edit_file(path, old, new)` | `edit_file("/draft.md", "old", "new")` | Find & replace in a file |
| `glob(pattern)` | `glob("*.md")` | Find files by pattern |
| `grep(pattern)` | `grep("revenue")` | Search file contents |
| `write_todos(items)` | `write_todos(["Step 1", "Step 2"])` | Create a task plan |
| `execute(command)` | `execute("wc -l report.md")` | Run a shell command |

---

## File Organization Convention

```
/research/     ← raw research notes, search results
/data/         ← structured data (tables, JSON)
/analysis/     ← processed analysis, calculations
/drafts/       ← work-in-progress content
/output/       ← final deliverables (reports, articles)
/report/       ← formatted reports (used in Lab 4)
/review/       ← editorial feedback (used in Lab 6)
/final/        ← polished final versions (used in Lab 6)
```

---

## Agent Invocation Template

```python
result = agent.invoke(
    {"messages": [HumanMessage(content="Your query here")]},
    config={"configurable": {"thread_id": "unique-thread-id"}}
)

# Get the agent's final response
response = result["messages"][-1].content
```

**thread_id:** Must be unique per conversation. Different thread IDs = separate conversations.

---

## Pattern 6: Trace Utilities (Used in All Labs)

```python
from trace_utils import run_with_trace, interactive_mode, resilient_web_search

# Instead of agent.invoke(), use run_with_trace() for visible traces:
run_with_trace(agent, "Your question here", thread_id="thread-1")
# Shows colored output: [SEARCH], [CALC], [WRITE], [DELEGATE], [SUB-AGENT DONE], etc.
# Automatically retries on rate limit (429) errors with backoff.

# Add at end of __main__ for student experimentation:
interactive_mode(agent, "Lab Name")
# Starts a REPL loop: "YOUR TURN — Try it yourself!"
```

**trace_utils.py** is a shared module all labs import. It uses `agent.stream(stream_mode="updates")` instead of `agent.invoke()` to show real-time formatted traces.

**Used in:** All labs (lab1 through lab6)

---

## Pattern 7: Resilient Web Search (Used in Labs with Web Search)

```python
from trace_utils import resilient_web_search

@tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query
    """
    return resilient_web_search(query)
```

**How it works:**
- Uses OpenAI's Responses API with `web_search_preview` tool
- Automatically retries on 429 (rate limit) errors with exponential backoff (1s, 2s, 4s)
- Uses `gpt-4o-mini` internally for cost-effective web search
- Returns an error string instead of crashing on permanent failures

**Why this matters:** Free-tier and student API keys have low rate limits (30k TPM). Without retry logic, labs crash on the first rate limit hit. With `resilient_web_search`, labs handle rate limits gracefully.

**Used in:** Lab 2, Lab 3a, Lab 3b, Lab 4, Lab 6

---

## Lab Execution Quick Reference

After building each lab in `my-agents/`, run it:

| Lab | Command | Time | Key Output |
|-----|---------|------|------------|
| Lab 0 | `python my-agents/lab0_setup.py` | 10s | "ALL CHECKS PASSED" |
| Lab 1 | `python my-agents/lab1_first_agent.py` | 30s | 4 answered questions |
| Lab 2 | `python my-agents/lab2_research_agent.py` | 60s | Research report |
| Lab 3a | `python my-agents/lab3a_first_subagent.py` | 30s | Delegated answer |
| Lab 3b | `python my-agents/lab3b_parallel_agents.py` | 90s | Synthesized report |
| Lab 3c | `python my-agents/lab3c_file_sharing.py` | 60s | Cost analysis |
| Lab 4 | `python my-agents/lab4_financial_research.py` | 120s | Investment report |
| Lab 5 | `python my-agents/lab5_text_to_sql.py` | 90s | SQL results + explanations |
| Lab 6 | `python my-agents/lab6_content_pipeline.py` | 120s | Article + editorial review |

Reference implementations (if stuck): `course/labs/lab*.py`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'deepagents'` | `pip install deepagents>=0.4.3` |
| `ModuleNotFoundError: No module named 'langchain_openai'` | `pip install "langchain-openai>=1.1.8"` |
| `ModuleNotFoundError: No module named 'openai'` | `pip install "openai>=1.66.0"` |
| `OPENAI_API_KEY not set` | `export OPENAI_API_KEY="sk-..."` (mac/linux) or `set OPENAI_API_KEY=sk-...` (windows) |
| `openai.AuthenticationError` | API key is invalid or expired — check at platform.openai.com |
| `openai.RateLimitError` | Labs auto-retry with backoff via `resilient_web_search()` and `run_with_trace()`. If it persists: wait 60s, or switch all models to `gpt-4o-mini` (higher rate limits) |
| Timeout on web search | OpenAI web search may be slow — `resilient_web_search()` retries automatically with exponential backoff |
| Lab 5 database error | Delete `my-agents/sample_analytics.db` and re-run — the script recreates it |
