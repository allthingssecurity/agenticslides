# Module 5: Extensions — Long-Term Memory and Skills

## Student: Copy-Paste This Prompt Into a New Agent Session

> Open a **new session** in your AI coding agent and paste this:

```
Read the file course/agent-docs/05-memory-skills.md and follow it step by step.

First complete the Environment Setup section (skip if already done), then build
Lab 7 and Lab 8 from scratch in the my-agents/ directory.

IMPORTANT: Build the files only — do NOT run the labs. After building each lab,
tell the student: "Lab is ready. Run: python my-agents/labX.py"
The student will run it in their own terminal to verify behavior.

If you get stuck, consult the references at course/labs/lab7_long_term_memory.py
and course/labs/lab8_skills_agent.py.
```

---

## Environment Setup

### Step 1: Verify Python 3.11+

```bash
python3 --version
```

### Step 2: Activate venv + dependencies

```bash
mkdir -p my-agents
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "deepagents>=0.4.3" "langchain-openai>=1.1.8" "openai>=1.66.0"
export OPENAI_API_KEY="sk-your-key-here"
```

### Step 3: Verify

```bash
python -c "import sys; assert sys.version_info >= (3,11); print(f'Python {sys.version} OK')"
python -c "from deepagents import create_deep_agent; print('deepagents OK')"
python -c "import openai; print('openai OK')"
python -c "import os; assert os.getenv('OPENAI_API_KEY','').startswith('sk-'); print('API key OK')"
```

---

## Lab 7: Long-Term Memory Across Sessions

### Goal
Show memory persistence across different thread IDs by routing `/memories/` to a store backend.

### Build file
Create `my-agents/lab7_long_term_memory.py` with the same implementation pattern as the reference:
- `CompositeBackend` routing `/memories/` to `StoreBackend`
- `FilesystemBackend` as default for normal files
- one agent that updates `/memories/user-profile.md`
- two demo calls using different thread IDs (`session-a`, `session-b`)
- interactive mode at the end

Reference: `course/labs/lab7_long_term_memory.py`

### Tell the student
`Lab is ready. Run: python my-agents/lab7_long_term_memory.py`

---

## Lab 8: Skills-Driven Agent

### Goal
Show how custom `SKILL.md` files are created and loaded via `skills=[...]` in a separate use case.

### Build files
Create these files:
- `my-agents/skills/lab8/release-notes/SKILL.md`
- `my-agents/skills/lab8/risk-assessment/SKILL.md`
- `my-agents/skills/lab8/executive-brief/SKILL.md`
- `my-agents/lab8_skills_agent.py`

Agent requirements:
- `FilesystemBackend(root_dir=BASE_DIR)`
- `skills=["/skills/lab8/"]`
- system prompt instructs agent to read relevant skill file(s) and apply them
- demo query about release readiness
- interactive mode at the end

References:
- `course/labs/lab8_skills_agent.py`
- `course/labs/skills/lab8/`

### Tell the student
`Lab is ready. Run: python my-agents/lab8_skills_agent.py`

---

## What You Learn

- **Memory lab:** cross-thread memory behavior and backend routing (`/memories/` vs normal filesystem)
- **Skills lab:** reusable capability packs with `SKILL.md` + progressive disclosure
- **Separation of concerns:** capstones remain unchanged; memory and skills are isolated in dedicated labs
