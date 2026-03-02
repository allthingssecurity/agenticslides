# MODULE 2: Core Building Blocks (45 minutes)
## Tools, Planning, and Context Management

---

## 2.1 — Tools & Backends (10 min)

### The Backend Architecture

Every DeepAgents agent interacts with a **backend** — an abstraction layer for file operations:

```
┌─────────────────────────────────────────────┐
│               YOUR AGENT                     │
│                                              │
│  Tools: ls, read_file, write_file,          │
│         edit_file, glob, grep, execute       │
│                                              │
│         ↕ (all go through)                   │
│                                              │
│  ┌──────────────────────────────────┐       │
│  │       BackendProtocol            │       │
│  │  ls_info() read() write() edit() │       │
│  │  grep_raw() glob_info() execute()│       │
│  └──────────────┬───────────────────┘       │
│                  │                           │
│    ┌─────────────┼─────────────┐            │
│    ↓             ↓             ↓            │
│  State      Filesystem    LocalShell        │
│  Backend     Backend       Backend          │
│ (in-memory) (local disk)  (disk+shell)      │
└─────────────────────────────────────────────┘
```

### Available Backends

| Backend | Storage | Shell? | Best For |
|---------|---------|--------|----------|
| `StateBackend` | In-memory (per thread) | No | Quick prototyping, testing |
| `FilesystemBackend` | Local disk | No | File-heavy workflows |
| `LocalShellBackend` | Local disk | Yes | Full development agent |
| `StoreBackend` | LangGraph store | No | Persistent cross-session data |
| `CompositeBackend` | Multiple (routed) | Via default | Production setups |

### Filesystem Tools Injected by `FilesystemMiddleware`

When you create a deep agent, it automatically gets these tools via `FilesystemMiddleware`:

```python
# These tools are automatically available to your agent:

ls(path="/")                          # List directory contents
read_file(file_path="/notes.md")      # Read a file (supports pagination)
write_file(file_path="/notes.md",     # Create or overwrite a file
           content="# My Notes")
edit_file(file_path="/notes.md",      # Exact string replacement
          old_string="old text",
          new_string="new text")
glob(pattern="**/*.py")               # Find files by pattern
grep(pattern="TODO", path="/src")     # Search file contents
execute(command="python main.py")     # Shell command (if backend supports it)
```

### Using Different Backends

```python
from deepagents import create_deep_agent, FilesystemMiddleware
from deepagents.backends import LocalShellBackend, FilesystemBackend

# Option 1: In-memory (default) — files disappear after the session
agent = create_deep_agent(model="openai:gpt-4o")

# Option 2: Local filesystem — files persist on disk
agent = create_deep_agent(
    model="openai:gpt-4o",
    backend=FilesystemBackend(root_dir="./workspace")
)

# Option 3: Full shell access — agent can run commands
agent = create_deep_agent(
    model="openai:gpt-4o",
    backend=LocalShellBackend(root_dir="./workspace")
)
```

### Hands-On: See the Filesystem in Action

```python
# filesystem_demo.py
from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage

agent = create_deep_agent(
    model="openai:gpt-4o",
    system_prompt="""You have access to a virtual filesystem.
    When asked to take notes, write them to files.
    When asked to recall, read from your files."""
)

# Agent writes to the filesystem
result = agent.invoke(
    {"messages": [HumanMessage(content=(
        "Take notes on the following:\n"
        "- Python was created by Guido van Rossum in 1991\n"
        "- JavaScript was created by Brendan Eich in 1995\n"
        "Save these as /research/languages.md"
    ))]},
    config={"configurable": {"thread_id": "fs-demo"}}
)

# Later, agent reads it back
result = agent.invoke(
    {"messages": [HumanMessage(content=(
        "Read my notes from /research/languages.md and tell me "
        "which language is older."
    ))]},
    config={"configurable": {"thread_id": "fs-demo"}}
)
```

---

## 2.2 — Planning with Todos (10 min)

### Why Planning Matters

Without planning, agents exhibit **random walk** behavior:
```
Task: "Analyze competitor pricing"
Shallow agent: search → search → search → forget → search → incomplete answer
Deep agent:    plan → search systematically → analyze → synthesize → answer
```

### The `write_todos` Tool

DeepAgents automatically includes a `write_todos` tool. The agent uses it to create structured task lists:

```python
# The agent internally calls:
write_todos([
    {"id": "1", "task": "Identify top 5 competitors", "status": "pending"},
    {"id": "2", "task": "Search pricing for each", "status": "pending"},
    {"id": "3", "task": "Create comparison table", "status": "pending"},
    {"id": "4", "task": "Write analysis summary", "status": "pending"},
])
```

### How Planning Works in Practice

```python
# planning_demo.py
from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage

agent = create_deep_agent(
    model="openai:gpt-4o",
    system_prompt="""You are a research analyst.

## CRITICAL RULES
1. For ANY multi-step task, ALWAYS start by creating a todo list using write_todos
2. Work through todos one at a time, marking each complete
3. Write research findings to files in /research/
4. Only provide your final answer AFTER all todos are complete

## Planning Strategy
- Break complex tasks into 3-7 discrete steps
- Each step should be independently achievable
- Steps should build on each other logically
"""
)

result = agent.invoke(
    {"messages": [HumanMessage(content=(
        "Research the pros and cons of Python vs Rust for building "
        "backend web services. Write a structured comparison."
    ))]},
    config={"configurable": {"thread_id": "planning-demo"}}
)
```

### What the Agent Does Internally

```
Step 1: write_todos([
    "1. Research Python backend frameworks and strengths",
    "2. Research Rust backend frameworks and strengths",
    "3. Compare performance characteristics",
    "4. Compare developer experience",
    "5. Write final comparison to /research/python_vs_rust.md"
])

Step 2: [Searches/researches Python backends]
         → writes notes to /research/python_notes.md

Step 3: [Searches/researches Rust backends]
         → writes notes to /research/rust_notes.md

Step 4: [Reads both note files, compares]
         → updates todo status

Step 5: [Synthesizes into final comparison]
         → writes /research/python_vs_rust.md
```

---

## 2.3 — Context Management (10 min)

### The Context Window Problem

Every LLM has a finite context window. As conversations grow:

```
Context window: [████████████████████░░░░░░░░] 70% full

After 20 more tool calls:
Context window: [████████████████████████████] 100% FULL — old data lost!
```

### SummarizationMiddleware

DeepAgents solves this with automatic **conversation summarization**:

```python
from deepagents.middleware import SummarizationMiddleware

# Configure when and how to summarize
summarization = SummarizationMiddleware(
    trigger=("fraction", 0.85),       # Trigger at 85% of context window
    retention=("fraction", 0.10),     # Keep newest 10%
)
```

### How Summarization Works

```
BEFORE summarization:
┌─────────────────────────────────────────────────┐
│ Msg 1: User asks about Python                   │
│ Msg 2: Agent searches... (long results)         │
│ Msg 3: Agent writes file                        │
│ Msg 4: User asks about Rust                     │
│ Msg 5: Agent searches... (long results)         │  ← 85% full!
│ Msg 6: Agent analyzes...                        │
└─────────────────────────────────────────────────┘

AFTER summarization:
┌─────────────────────────────────────────────────┐
│ [SUMMARY]: Previously researched Python and     │
│ Rust backends. Notes saved to /research/.       │
│ Python notes at /research/python_notes.md.      │
│ Rust notes at /research/rust_notes.md.          │
│                                                 │  ← Only 15% full!
│ Msg 6: Agent analyzes...                        │
│ (room for many more messages)                   │
└─────────────────────────────────────────────────┘
```

### The Key Insight: Files Survive Summarization

```
Context Window: gets summarized, old messages removed
     ↓
Filesystem: /research/python_notes.md ← STILL THERE
            /research/rust_notes.md   ← STILL THERE
            /research/comparison.md   ← STILL THERE

The agent can re-read its own notes after summarization!
```

This is why the **filesystem** is so critical — it acts as the agent's **long-term memory** during a single task.

### Practical Pattern: Write-Then-Summarize

Teach your agents to proactively offload:

```python
system_prompt = """
## Context Management Rules
1. After any research step, write findings to a file IMMEDIATELY
2. Never keep more than 3 search results in conversation at once
3. When synthesizing, read from files rather than relying on memory
4. If a tool returns more than 500 words, save it to a file and
   reference the file path instead
"""
```

---

## 2.4 — Lab 2: Research Agent (15 min)

### Goal
Build an agent that can search the web, take structured notes, and write a research report.

### Step 1: Create a Web Search Tool

```python
# lab2_research_agent.py
import json
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

@tool
def web_search(query: str, num_results: int = 5) -> str:
    """Search the web for information.

    Args:
        query: The search query
        num_results: Number of results to return (default 5)
    """
    # Using a free search API (DuckDuckGo Instant Answer)
    # In production, use Tavily, Serper, or similar
    try:
        response = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10
        )
        data = response.json()

        results = []
        # Abstract (main answer)
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "Main Result"),
                "snippet": data["Abstract"],
                "source": data.get("AbstractURL", "")
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "title": topic.get("Text", "")[:80],
                    "snippet": topic.get("Text", ""),
                    "source": topic.get("FirstURL", "")
                })

        if not results:
            return f"No results found for: {query}"

        return json.dumps(results, indent=2)

    except Exception as e:
        return f"Search error: {e}"
```

### Step 2: Build the Research Agent

```python
research_agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[web_search],
    system_prompt="""You are a research agent that produces well-organized research reports.

## Workflow (ALWAYS follow this order)
1. **Plan**: Use write_todos to break the research into steps
2. **Research**: Search for information on each aspect
3. **Take Notes**: Write findings to /research/ as structured markdown files
4. **Synthesize**: Read your notes and write a final report to /output/report.md
5. **Deliver**: Present a summary to the user with the report location

## File Organization
/research/
├── topic_1.md      # Notes for each research topic
├── topic_2.md
└── sources.md      # All URLs and citations
/output/
└── report.md       # Final polished report

## Research Quality Rules
- Search at least 2-3 times per topic from different angles
- Always note your sources (URLs)
- Distinguish facts from opinions
- If information conflicts, note the discrepancy
- Write notes IMMEDIATELY after each search — don't hold them in memory

## Report Format
# [Title]
## Executive Summary (2-3 sentences)
## Key Findings
### [Topic 1]
...
### [Topic N]
## Comparison Table (if applicable)
## Sources
"""
)
```

### Step 3: Run the Research

```python
result = research_agent.invoke(
    {"messages": [HumanMessage(content="""
        Research the current state of AI agent frameworks in 2025.
        Compare at least 3 major frameworks (LangChain/DeepAgents,
        CrewAI, and AutoGen). Focus on:
        1. Architecture approach
        2. Ease of use
        3. Multi-agent support
        4. Community and ecosystem
    """)]},
    config={"configurable": {"thread_id": "research-lab2"}}
)

# Print the final response
for msg in reversed(result["messages"]):
    if msg.type == "ai" and msg.content:
        print(msg.content)
        break
```

### Step 4: Verify the Agent's Work

```python
# The agent should have created files — let's check
verify_agent = create_deep_agent(model="openai:gpt-4o")

result = verify_agent.invoke(
    {"messages": [HumanMessage(content="List all files in / and read the report")]},
    config={"configurable": {"thread_id": "research-lab2"}}  # Same thread!
)
```

### What You Should See

The agent will:
1. Create a todo list with research steps
2. Search for each framework
3. Write notes to `/research/langchain_notes.md`, `/research/crewai_notes.md`, etc.
4. Create `/research/sources.md` with citations
5. Read its own notes and synthesize `/output/report.md`
6. Present a summary

### Understanding the Data Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  web_search  │     │  write_file  │     │  read_file   │
│  "CrewAI"    │────→│  /research/  │────→│  all notes   │
│              │     │  crewai.md   │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                           ┌──────▼───────┐
                                           │  write_file  │
                                           │  /output/    │
                                           │  report.md   │
                                           └──────────────┘
```

### Challenge Exercise

Enhance the agent with a `fetch_url` tool that can read the full content of web pages. Then ask it to do deeper research by actually reading source material.

---

## Key Concepts Recap

| Concept | What You Learned |
|---------|-----------------|
| Backends | Pluggable storage layer — in-memory, disk, or remote sandbox |
| Filesystem tools | `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep` |
| `write_todos` | Built-in planning tool for task decomposition |
| Summarization | Auto-compresses conversation when context fills up |
| Context offloading | Write to files → read later → survives summarization |
| Research pattern | Search → Notes → Synthesize → Report |

---

**Next:** Module 3 introduces multi-agent orchestration — how to build systems where agents collaborate.
