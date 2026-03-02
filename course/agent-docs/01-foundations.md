# Module 1: Foundations — From Shallow to Deep Agents

## Student: Copy-Paste This Prompt Into a New Agent Session

> Open a **new session** in your AI coding agent (Codex, Claude Code, Cursor, etc.) and paste this:

```
Read the file course/agent-docs/01-foundations.md and follow it step by step.

First complete the Environment Setup section, then build Lab 0 and Lab 1 from
scratch in the my-agents/ directory. Run each lab and verify it works before
moving on to the next one.

If you get stuck on any lab, you can consult the reference implementation in
course/labs/ but try building it yourself first.
```

---

## Environment Setup

Complete every step below. The goal: a working Python 3.11+ venv with all dependencies, inside this repo.

### Step 1: Check if Python 3.11+ is installed

**Action:** `shell`
**OS[mac/linux]:**
```bash
python3 --version
```
**OS[windows]:**
```cmd
python --version
```

**Expected:** `Python 3.11.x` or higher (3.12, 3.13, etc. are fine).

**If Python is not installed or version is below 3.11:**

**OS[mac] (using Homebrew):**
```bash
# Install Homebrew if missing
which brew || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.13
```

**OS[linux] (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install -y python3.13 python3.13-venv python3-pip
```

**OS[windows]:**
```cmd
# Download and install from https://www.python.org/downloads/
# During install: CHECK "Add python.exe to PATH" and "Install pip"
# After install, restart your terminal and verify with: python --version
```

After installing, re-verify with `python3 --version` (mac/linux) or `python --version` (windows).

### Step 2: Create the working directory

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
mkdir -p my-agents
```

### Step 3: Create and activate a virtual environment

**Action:** `shell`
**OS[mac/linux]:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
**OS[windows]:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**Verify venv is active:**
```bash
which python    # mac/linux: should show .venv/bin/python
where python    # windows: should show .venv\Scripts\python.exe
```

### Step 4: Upgrade pip and install dependencies

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
pip install --upgrade pip
pip install "deepagents>=0.4.3" "langchain-openai>=1.1.8" "openai>=1.66.0"
```

### Step 5: Set the OpenAI API key

**Action:** `shell`
**OS[mac/linux]:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```
**OS[windows]:**
```cmd
set OPENAI_API_KEY=sk-your-key-here
```

**Note:** Replace `sk-your-key-here` with the actual key. The key must start with `sk-`.

### Step 6: Verify everything works

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python -c "import sys; assert sys.version_info >= (3,11), f'Need 3.11+, got {sys.version}'; print(f'Python {sys.version} OK')"
python -c "from deepagents import create_deep_agent; print('deepagents OK')"
python -c "import langchain_openai; print('langchain-openai OK')"
python -c "import openai; print('openai OK')"
python -c "import os; key=os.getenv('OPENAI_API_KEY',''); assert key.startswith('sk-'), 'OPENAI_API_KEY not set'; print('API key OK')"
```
**Expected:** Five lines of "OK" output. If any line fails, fix that issue before proceeding.

---

## Concepts

### The Shallow Agent Problem

A "shallow agent" is a raw LLM in a tool loop: observe → think → act → repeat. This fails at complex tasks because:

- **No planning** — the agent guesses the next step instead of making a plan
- **Context overflow** — the conversation fills up and the agent forgets earlier work
- **No delegation** — one agent tries to do everything, overloading its context
- **Lost work** — when context is truncated, research and progress disappear

### The 4 Pillars of Deep Agents

| Pillar | Mechanism | Why It Matters |
|--------|-----------|----------------|
| **Planning** | `write_todos` tool | Agent decomposes tasks before acting |
| **Sub-Agents** | `task()` tool | Delegate to specialists with isolated contexts |
| **Filesystem** | `read_file` / `write_file` / `edit_file` | Offload context to files; files survive summarization |
| **System Prompts** | Structured instructions | Guide agent behavior with explicit workflows and rules |

### Core API: `create_deep_agent()`

```python
from deepagents import create_deep_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

agent = create_deep_agent(
    model="openai:gpt-4o",          # LLM backend
    tools=[tool1, tool2],            # Custom @tool functions
    subagents=[{...}],               # Sub-agent definitions (optional)
    system_prompt="You are..."       # Agent's instructions
)

# Invoke the agent
result = agent.invoke(
    {"messages": [HumanMessage(content="Your question")]},
    config={"configurable": {"thread_id": "unique-id"}}
)
response = result["messages"][-1].content
```

---

## Lab 0: Build a Setup Verification Script

### Goal
Create a script that checks Python version, installed packages, API key, and runs a smoke test agent.

### Step 1: Create the file

**Action:** `create-file`
**File:** `my-agents/lab0_setup.py`
**Content:**
```python
"""
LAB 0: Environment Setup & Verification
=========================================
Run this first to verify everything is installed correctly.
"""
import os
import sys


def check_setup():
    print("=" * 50)
    print(" DeepAgents Course — Setup Checker")
    print("=" * 50)

    errors = []

    # Check Python version
    v = sys.version_info
    print(f"\n[1] Python version: {v.major}.{v.minor}.{v.micro}", end=" ")
    if v >= (3, 11):
        print("✓")
    else:
        print("✗ (need 3.11+)")
        errors.append("Python 3.11+ required")

    # Check deepagents
    print("[2] deepagents package:", end=" ")
    try:
        import deepagents
        print("✓")
    except ImportError:
        print("✗")
        errors.append("Run: pip install deepagents")

    # Check langchain-openai
    print("[3] langchain-openai package:", end=" ")
    try:
        import langchain_openai
        print("✓")
    except ImportError:
        print("✗")
        errors.append("Run: pip install langchain-openai>=1.1.8")

    # Check OpenAI API key
    print("[4] OPENAI_API_KEY:", end=" ")
    key = os.getenv("OPENAI_API_KEY", "")
    if key.startswith("sk-"):
        print(f"✓ (starts with sk-...{key[-4:]})")
    else:
        print("✗ (not set or invalid)")
        errors.append("Run: export OPENAI_API_KEY='sk-your-key-here'")

    # Check openai
    print("[5] openai package:", end=" ")
    try:
        import openai
        print("✓")
    except ImportError:
        print("✗")
        errors.append("Run: pip install openai>=1.66.0")

    print("\n" + "=" * 50)
    if errors:
        print(" ISSUES FOUND:")
        for e in errors:
            print(f"   → {e}")
        print("=" * 50)
        return False
    else:
        print(" ALL CHECKS PASSED — Ready to go!")
        print("=" * 50)
        return True


def test_agent():
    """Quick smoke test — create an agent and get a response."""
    print("\n[6] Testing agent creation...")
    from deepagents import create_deep_agent
    from langchain_core.messages import HumanMessage

    agent = create_deep_agent(
        model="openai:gpt-4o-mini",
        system_prompt="You are a test agent. Respond with exactly: SETUP OK"
    )

    result = agent.invoke(
        {"messages": [HumanMessage(content="Confirm setup")]},
        config={"configurable": {"thread_id": "setup-test"}}
    )

    response = result["messages"][-1].content
    print(f"    Agent response: {response}")

    if "OK" in response.upper() or "SETUP" in response.upper():
        print("    ✓ Agent is working!\n")
        return True
    else:
        print("    ✓ Agent responded (content may vary, but it's working)\n")
        return True


if __name__ == "__main__":
    if check_setup():
        test_agent()
        print("You're ready for the course! Start with lab1_first_agent.py")
    else:
        print("\nFix the issues above, then run this script again.")
```

### Step 2: Run it

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python my-agents/lab0_setup.py
```

### Step 3: Verify

**Expected output:**
```
==================================================
 DeepAgents Course — Setup Checker
==================================================

[1] Python version: 3.1x.x ✓
[2] deepagents package: ✓
[3] langchain-openai package: ✓
[4] OPENAI_API_KEY: ✓ (starts with sk-...XXXX)
[5] openai package: ✓

==================================================
 ALL CHECKS PASSED — Ready to go!
==================================================

[6] Testing agent creation...
    Agent response: SETUP OK
    ✓ Agent is working!

You're ready for the course! Start with lab1_first_agent.py
```

**Success criteria:** All 5 checks show `✓`, and the smoke test agent responds.

### What You Built
- A diagnostic script that validates the entire environment
- Your first `create_deep_agent()` call — using `gpt-4o-mini` for a cheap smoke test
- The `invoke()` pattern: pass `messages` + `thread_id`, get back `messages`

---

## Lab 1: Build a Calculator + Clock Agent

### Goal
Create an agent with two custom tools (`calculator` and `get_current_time`), then ask it questions that require tool use.

### Step 1: Create the file with imports

**Action:** `create-file`
**File:** `my-agents/lab1_first_agent.py`
**Content:**
```python
"""
LAB 1: Your First Agent
=========================
An agent with calculator + clock tools.
"""
import math
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent
```

### Step 2: Add the calculator tool

**Action:** `append-to-file`
**File:** `my-agents/lab1_first_agent.py`
**Content:**
```python


# ─── TOOL 1: Calculator ──────────────────────────────────

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression.
    Supports: +, -, *, /, **, sqrt, sin, cos, log, pi, e

    Args:
        expression: A math expression, e.g. "2 + 3 * 4" or "sqrt(144)"
    """
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names.update({"abs": abs, "round": round})
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"Result: {result}"
    except Exception as e:
        return f"Error evaluating '{expression}': {e}"
```

**Why this works:**
- `@tool` decorator from `langchain_core.tools` registers a function as a tool the LLM can call
- The **docstring** is what the LLM reads to decide when to use the tool — make it descriptive
- The **Args section** tells the LLM what parameters to pass
- `eval()` is restricted to `math` functions only (no `__builtins__`) for safety

### Step 3: Add the clock tool

**Action:** `append-to-file`
**File:** `my-agents/lab1_first_agent.py`
**Content:**
```python


# ─── TOOL 2: Clock ───────────────────────────────────────

@tool
def get_current_time() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return f"Current date/time: {now.strftime('%Y-%m-%d %H:%M:%S (%A)')}"
```

### Step 4: Create the agent

**Action:** `append-to-file`
**File:** `my-agents/lab1_first_agent.py`
**Content:**
```python


# ─── CREATE THE AGENT ────────────────────────────────────

agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[calculator, get_current_time],
    system_prompt="""You are a helpful assistant with access to a calculator and clock.

## Rules
- For ANY math question, ALWAYS use the calculator tool — never calculate in your head
- Show your work: state what you're calculating and why
- Be concise but thorough
- When using the calculator, show the expression you're evaluating
"""
)
```

**Key decisions:**
- `model="openai:gpt-4o"` — the full-power model for the main agent
- `tools=[calculator, get_current_time]` — both tools are available
- The system prompt **explicitly says** "ALWAYS use the calculator" — without this, the LLM might try to do math itself

### Step 5: Add the helper function and test queries

**Action:** `append-to-file`
**File:** `my-agents/lab1_first_agent.py`
**Content:**
```python


# ─── HELPER FUNCTION ─────────────────────────────────────

def ask(question: str, thread_id: str = "lab1"):
    """Send a message to the agent and print the response."""
    print(f"\n{'─'*50}")
    print(f"YOU: {question}")
    print(f"{'─'*50}")

    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread_id}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\nAGENT: {msg.content}")
            return


# ─── RUN THE TESTS ────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print(" LAB 1: Your First Agent")
    print("=" * 50)

    # Test 1: Basic tool use
    ask("What is the square root of 1764?")

    # Test 2: Multi-step calculation
    ask(
        "If I invest $10,000 at 7% annual compound interest, "
        "how much will I have after 10 years? Use A = P*(1+r)^t"
    )

    # Test 3: Time tool
    ask("What day of the week is it today?")

    # Test 4: Combining reasoning + tools
    ask(
        "I was born on March 15, 1995. "
        "How many days have I been alive? Use today's date."
    )

    print("\n" + "=" * 50)
    print(" LAB 1 COMPLETE!")
    print("=" * 50)
```

### Step 6: Run it

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python my-agents/lab1_first_agent.py
```

### Step 7: Verify

**Expected output pattern:**
```
==================================================
 LAB 1: Your First Agent
==================================================

──────────────────────────────────────────────────
YOU: What is the square root of 1764?
──────────────────────────────────────────────────

AGENT: [Uses calculator, returns 42.0]

──────────────────────────────────────────────────
YOU: If I invest $10,000 at 7% annual compound interest...
──────────────────────────────────────────────────

AGENT: [Uses calculator with 10000*(1.07)**10, returns ~$19,671.51]

──────────────────────────────────────────────────
YOU: What day of the week is it today?
──────────────────────────────────────────────────

AGENT: [Uses get_current_time, returns current day]

──────────────────────────────────────────────────
YOU: I was born on March 15, 1995. How many days have I been alive?
──────────────────────────────────────────────────

AGENT: [Uses get_current_time + calculator, returns day count]

==================================================
 LAB 1 COMPLETE!
==================================================
```

**Success criteria:**
- All 4 queries return agent responses (no errors)
- The agent uses the `calculator` tool for math (not calculating in its head)
- The agent uses `get_current_time` for time queries
- Compound interest answer is approximately $19,671.51

### What You Built
- **Two custom tools** using `@tool` — the LLM reads the docstrings to decide when to call them
- **An agent** via `create_deep_agent()` with tools and a system prompt
- **The invoke pattern** — `messages` in, `messages` out, scoped by `thread_id`
- **Behavioral shaping** — the system prompt forces calculator use (without it, the LLM guesses)

### What You Learned
| Concept | How It Works |
|---------|-------------|
| `@tool` decorator | Turns a Python function into an LLM-callable tool; the docstring is the tool description |
| `create_deep_agent()` | Factory function: model + tools + system_prompt → agent |
| Tool calling | The LLM decides **when** and **how** to call tools based on the user's question |
| `thread_id` | Scopes the conversation — different IDs = separate conversations |
| System prompt | Shapes behavior — "ALWAYS use calculator" prevents the LLM from guessing |
