# Module 2: Core Building Blocks — Tools, Planning, and Context Management

## Student: Copy-Paste This Prompt Into a New Agent Session

> Open a **new session** in your AI coding agent and paste this:

```
Read the file course/agent-docs/02-building-blocks.md and follow it step by step.

First complete the Environment Setup section (skip if already done), then build
Lab 2 from scratch in the my-agents/ directory.

IMPORTANT: Build the files only — do NOT run the labs. After building, tell
the student: "Lab is ready. Run: python my-agents/lab2_research_agent.py"
The student will run it in their own terminal to see traces and interactive mode.

If you get stuck, consult the reference at course/labs/lab2_research_agent.py
but try building it yourself first.
```

---

## Environment Setup

This is a new agent session, so the environment must be ready. Follow every step — the checks will skip anything already done.

### Step 1: Ensure Python 3.11+ is available

**Action:** `shell`
**OS[mac/linux]:**
```bash
python3 --version
```
**OS[windows]:**
```cmd
python --version
```
**Expected:** `Python 3.11.x` or higher. If not installed, follow the Python installation steps in `course/agent-docs/01-foundations.md` → Environment Setup → Step 1.

### Step 2: Create working directory, venv, install deps, set API key

**Action:** `shell`
**OS[mac/linux]:**
```bash
mkdir -p my-agents
# Create venv if it doesn't exist, then activate
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "deepagents>=0.4.3" "langchain-openai>=1.1.8" "openai>=1.66.0"
export OPENAI_API_KEY="sk-your-key-here"
```
**OS[windows]:**
```cmd
mkdir my-agents 2>nul
if not exist .venv python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install "deepagents>=0.4.3" "langchain-openai>=1.1.8" "openai>=1.66.0"
set OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Verify

**Action:** `shell`
```bash
python -c "import sys; assert sys.version_info >= (3,11); print(f'Python {sys.version} OK')"
python -c "from deepagents import create_deep_agent; print('deepagents OK')"
python -c "import openai; print('openai OK')"
python -c "import os; assert os.getenv('OPENAI_API_KEY','').startswith('sk-'); print('API key OK')"
```
**Expected:** Four lines of "OK".

### Prerequisites
- Module 1 completed (Lab 0 + Lab 1 built and ran successfully)
- Internet access (this lab uses OpenAI's web search)

---

## Concepts

### Built-in Filesystem Tools

Every agent created with `create_deep_agent()` automatically gets these tools via `FilesystemMiddleware` — you don't need to define them:

| Tool | What It Does |
|------|-------------|
| `ls(path)` | List directory contents |
| `read_file(path)` | Read a file |
| `write_file(path, content)` | Create or overwrite a file |
| `edit_file(path, old, new)` | Find & replace in a file |
| `glob(pattern)` | Find files by pattern |
| `grep(pattern)` | Search file contents |
| `execute(command)` | Run a shell command |
| `write_todos(items)` | Create a task plan |

These exist **in addition to** any custom tools you pass via `tools=[]`.

### Planning with `write_todos`

Without planning, an agent randomly walks through a task — searching, forgetting, re-searching. With `write_todos`, the agent creates a structured plan first:

```
write_todos([
    "Search for Python backend frameworks",
    "Search for JavaScript backend frameworks",
    "Compare performance benchmarks",
    "Write notes to /research/",
    "Synthesize report to /output/report.md"
])
```

**Instruct agents to plan first** in the system prompt: `"ALWAYS start by using write_todos to break the task into steps."`

### Context Management: The Write-Then-Summarize Pattern

Problem: long research conversations fill the context window. The framework uses `SummarizationMiddleware` to compress old messages.

**Key insight: files survive summarization.** If the agent writes notes to `/research/notes.md`, those notes persist even after the conversation is compressed. The pattern:

1. Agent searches for information
2. Agent **immediately** writes findings to a file
3. Context gets summarized (old messages compressed)
4. Agent reads the file to recall what it found
5. No information is lost

This is why every research agent must be told: **"Write notes to files IMMEDIATELY after each search."**

---

## Lab 2: Build a Research Agent

### Goal
Create an agent that:
1. Plans its research with `write_todos`
2. Searches the web via an OpenAI web search tool you build
3. Takes structured notes to `/research/` files
4. Synthesizes a final report to `/output/report.md`

### Step 1: Create the file with imports

**Action:** `create-file`
**File:** `my-agents/lab2_research_agent.py`
**Content:**
```python
"""
LAB 2: Research Agent
======================
Searches the web, takes notes to files, writes a research report.
"""
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent
from trace_utils import run_with_trace, interactive_mode, resilient_web_search
```

### Step 2: Build the web search tool

**Action:** `append-to-file`
**File:** `my-agents/lab2_research_agent.py`
**Content:**
```python


# ─── TOOL: Web Search ──────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for current information on any topic.

    Args:
        query: The search query
    """
    return resilient_web_search(query)
```

**How this works:**
- Uses `resilient_web_search()` from `trace_utils` — handles rate limits automatically
- Retries with exponential backoff (1s, 2s, 4s) on 429 errors — no manual intervention needed
- Uses `gpt-4o-mini` internally for cost-effective web search
- Returns an error string instead of crashing on permanent failures

### Step 3: Build the research agent with a detailed system prompt

**Action:** `append-to-file`
**File:** `my-agents/lab2_research_agent.py`
**Content:**
```python


# ─── AGENT: Research Agent ─────────────────────────────

research_agent = create_deep_agent(
    model="openai:gpt-4o-mini",
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
```

**Why this system prompt matters:**
- **Numbered workflow** — the agent follows steps in order instead of randomly acting
- **File organization** — tells the agent exactly where to write files
- **Quality rules** — "write immediately" prevents information loss during summarization
- **Report format** — structured template ensures consistent output

### Step 4: Add the runner and main block

**Action:** `append-to-file`
**File:** `my-agents/lab2_research_agent.py`
**Content:**
```python


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

    interactive_mode(research_agent, "Lab 2: Research Agent")
```

### Step 5: Tell the student to run it

**Action:** Tell the student:

> Lab 2 is ready. Run it in your terminal:
> ```bash
> python my-agents/lab2_research_agent.py
> ```
> You'll see colored traces showing `[SEARCH]`, `[PLAN]`, `[WRITE]`, and `[FILE WRITTEN]` events
> in real time as the agent researches, takes notes, and writes its report.
> After the demo query, you'll get an interactive prompt to try your own research topics.

**Do NOT run it yourself.** The student runs labs in their own terminal.

### What You Built
- **A web search tool** using OpenAI's Responses API with web search
- **A research agent** with a detailed system prompt defining a 5-step workflow
- **The planning pattern** — `write_todos` decomposes the task before execution
- **The write-immediately pattern** — notes go to files right after each search

### What You Learned
| Concept | How It Works |
|---------|-------------|
| Built-in filesystem tools | Every agent gets `read_file`, `write_file`, etc. automatically |
| `write_todos` | Agent creates a task plan before starting — prevents random-walk behavior |
| Context offloading | Research written to files survives context summarization |
| System prompt workflow | Numbered steps + file paths + quality rules = reliable agent behavior |
| OpenAI Web Search | `client.responses.create()` with `web_search_preview` tool — uses your existing API key for live web results |
