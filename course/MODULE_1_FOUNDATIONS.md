# MODULE 1: Foundations (45 minutes)
## From Shallow to Deep Agents

---

## 1.1 — The Problem with Shallow Agents (10 min)

### What is an "Agent"?

An **agent** is an LLM that can:
1. **Observe** — Read inputs, tool results, environment state
2. **Think** — Reason about what to do next
3. **Act** — Call tools, write code, make API calls
4. **Loop** — Repeat until the task is done

```
┌─────────────────────────────────┐
│         AGENT LOOP              │
│                                 │
│   User Query                    │
│       ↓                         │
│   LLM thinks → picks a tool    │
│       ↓                         │
│   Tool executes → returns result│
│       ↓                         │
│   LLM thinks again...          │
│       ↓                         │
│   (repeat until done)           │
│       ↓                         │
│   Final Answer                  │
└─────────────────────────────────┘
```

### The "Shallow Agent" Problem

A **shallow agent** is just an LLM in a tool loop with no additional structure. Here's why they fail at real-world tasks:

| Problem | What Happens | Example |
|---------|-------------|---------|
| **No Planning** | Agent jumps straight into action without thinking | Asked to "build a REST API", starts writing random endpoints |
| **Context Overflow** | Too much information crammed into one conversation | 50 tool calls later, the LLM forgets the original goal |
| **No Delegation** | One agent tries to do everything | Research + code + test + deploy all in one context |
| **Lost Work** | Results disappear when context is truncated | 10,000 words of research vanish after summarization |

### Real Example: Why ChatGPT Struggles with Complex Tasks

```
User: "Research the top 5 AI frameworks, compare their features,
       write a 2000-word report, and create a comparison table."

Shallow Agent Behavior:
  Step 1: Search "top AI frameworks" ✓
  Step 2: Search "LangChain features" ✓
  Step 3: Search "CrewAI features" ✓
  Step 4: ... context window filling up ...
  Step 5: Starts forgetting earlier search results
  Step 6: Writes incomplete report missing key data
  Step 7: Table is inconsistent with the report text
```

### The Solution: Deep Agents

Deep Agents solve this with **4 pillars**:

```
┌──────────────────────────────────────────────────┐
│                  DEEP AGENT                       │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │ PLANNING │  │SUB-AGENTS│  │  FILESYSTEM   │   │
│  │write_todos│ │  task()  │  │read/write/edit│   │
│  │decompose │  │ delegate │  │  offload ctx  │   │
│  └──────────┘  └──────────┘  └──────────────┘   │
│                                                   │
│  ┌──────────────────────────────────────────┐    │
│  │         DETAILED SYSTEM PROMPTS           │    │
│  │    Guide behavior, set boundaries         │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

---

## 1.2 — The 4 Pillars of Deep Agents (10 min)

### Pillar 1: Planning (write_todos)

Agents break complex tasks into discrete steps **before** acting:

```python
# The agent automatically creates a todo list
todos = [
    "1. Search for top 5 AI frameworks",
    "2. For each framework, research key features",
    "3. Create comparison matrix",
    "4. Write executive summary",
    "5. Generate final report with table"
]
```

**Why this matters:** Without planning, agents take random walks through solution space. With planning, they follow a structured path.

### Pillar 2: Sub-Agents (task delegation)

Instead of one agent doing everything, the **orchestrator** delegates to **specialists**:

```
┌─────────────┐
│ ORCHESTRATOR │
└──────┬──────┘
       │
       ├──→ [Researcher Agent] → searches web, takes notes
       ├──→ [Analyst Agent]    → processes data, finds patterns
       └──→ [Writer Agent]     → synthesizes into final report
```

**Key insight:** Each sub-agent gets its own **isolated context window**. The researcher's 50 search results don't pollute the writer's clean context.

### Pillar 3: Filesystem (context offloading)

Instead of keeping everything in the conversation, agents write to files:

```
/workspace/
├── research/
│   ├── langchain_notes.md      ← Researcher wrote this
│   ├── crewai_notes.md         ← Researcher wrote this
│   └── comparison_data.json    ← Analyst wrote this
└── output/
    └── final_report.md         ← Writer reads notes, writes report
```

**Why this matters:** Files persist beyond the context window. When conversation history is summarized, the work product survives.

### Pillar 4: Detailed System Prompts

The system prompt is the agent's **operating manual**:

```markdown
You are a financial research analyst agent.

## Your Role
- You research financial data and produce investor-grade reports
- You ALWAYS plan before acting using write_todos
- You delegate complex sub-tasks to specialized sub-agents

## Rules
- Never make up financial data — always cite sources
- Write research notes to /research/ before synthesizing
- Maximum 3 search queries per sub-topic
```

---

## 1.3 — Environment Setup (10 min)

### Step 1: Create Project Directory

```bash
mkdir agentic-ai-course && cd agentic-ai-course
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 2: Install DeepAgents

```bash
pip install deepagents "langchain-openai>=1.1.8"
```

> **Note:** We install `langchain-openai` explicitly since we're using OpenAI models.
> The core `deepagents` package defaults to Anthropic but fully supports OpenAI.

### Step 3: Configure OpenAI API Key

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Or create a `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

### Step 4: Verify Installation

```python
# test_setup.py
from deepagents import create_deep_agent
from langchain_core.messages import HumanMessage

# Create the simplest possible agent
agent = create_deep_agent(
    model="openai:gpt-4o",
    system_prompt="You are a helpful assistant. Keep responses brief."
)

# Run it
result = agent.invoke(
    {"messages": [HumanMessage(content="Say hello and confirm you're working!")]},
    config={"configurable": {"thread_id": "test-1"}}
)

# Print the last message
print(result["messages"][-1].content)
```

```bash
python test_setup.py
# Expected: "Hello! I'm working and ready to help. What can I do for you?"
```

### Understanding `create_deep_agent()`

```python
def create_deep_agent(
    model="openai:gpt-4o",          # The LLM to use
    tools=[],                         # Custom tools the agent can call
    system_prompt=None,               # Your instructions for the agent
    subagents=[],                     # Specialist agents to delegate to
    middleware=[],                     # Extensibility hooks
    backend=None,                     # Where files are stored
    memory=[],                        # Paths to AGENTS.md memory files
    skills=[],                        # Paths to skill directories
    interrupt_on=[],                  # Tools that need human approval
)
```

**Key behavior with OpenAI:**
- When you pass `"openai:gpt-4o"`, it automatically enables the OpenAI Responses API
- Authentication uses the `OPENAI_API_KEY` environment variable
- All OpenAI models with tool-calling support work: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, etc.

---

## 1.4 — Lab 1: Your First Agent (15 min)

### Goal
Build an agent with custom tools that can answer math questions and tell the current time.

### Step 1: Define Tools

```python
# lab1_first_agent.py
import math
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression. Supports basic math and functions like sqrt, sin, cos, log.

    Args:
        expression: A mathematical expression to evaluate, e.g. "2 + 3 * 4" or "sqrt(144)"
    """
    # Allow only safe math operations
    allowed_names = {
        k: v for k, v in math.__dict__.items() if not k.startswith("__")
    }
    allowed_names.update({"abs": abs, "round": round})

    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return f"Current date/time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
```

### Step 2: Create the Agent

```python
agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[calculator, get_current_time],
    system_prompt="""You are a helpful assistant with access to a calculator and clock.

## Rules
- For any math question, ALWAYS use the calculator tool — never calculate in your head
- Show your work: state what you're calculating and why
- Be concise but thorough
"""
)
```

### Step 3: Test It

```python
def ask(question: str, thread_id: str = "lab1"):
    """Helper to send a message and print the response."""
    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread_id}}
    )
    # Get the last AI message
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"Agent: {msg.content}")
            break

# Test basic tool use
ask("What is the square root of 1764?")

# Test multi-step reasoning
ask("If I invest $10,000 at 7% annual compound interest, "
    "how much will I have after 10 years? Use the formula A = P(1+r)^t")

# Test time tool
ask("What time is it right now?")

# Test combining tools
ask("How many days until the end of this year? Use the current date.")
```

### Expected Output
```
Agent: The square root of 1764 is 42.

Agent: Using the compound interest formula A = P(1+r)^t:
- P = $10,000, r = 0.07, t = 10
- A = 10000 × (1.07)^10 = $19,671.51
After 10 years, you'd have approximately $19,671.51.

Agent: The current date and time is 2025-01-15 14:32:07.

Agent: Today is January 15, 2025. The year ends on December 31, 2025.
That's 350 days from now.
```

### What Just Happened?

```
┌──────────────────────────────────────────┐
│  1. User asks: "sqrt of 1764?"           │
│  2. LLM decides to use calculator tool   │
│  3. Tool call: calculator("sqrt(1764)")  │
│  4. Tool returns: "Result: 42.0"         │
│  5. LLM formats answer: "sqrt is 42"    │
└──────────────────────────────────────────┘
```

### Challenge Exercise
Add a third tool `web_search` that simulates searching (or uses a real API) and ask the agent a question that requires both search and calculation.

---

## Key Concepts Recap

| Concept | What You Learned |
|---------|-----------------|
| Shallow vs Deep | Raw LLM + tools fails; need planning + delegation + filesystem |
| 4 Pillars | Planning, Sub-agents, Filesystem, System Prompts |
| `create_deep_agent()` | The factory function that builds agents |
| `@tool` decorator | How to give agents capabilities |
| Tool calling | LLM decides when/how to use tools |
| Thread ID | Conversation identity for stateful interactions |

---

**Next:** Module 2 dives into the middleware system — how agents plan, manage context, and interact with files.
