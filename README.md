# Agentic AI Masterclass

A hands-on course where **your AI coding agent builds AI agents for you**. You paste a prompt, the agent writes the code, runs it, and verifies it works.

**4 modules | 9 labs | 3 hours | Zero manual coding required**

---

## What You Need

| Requirement | Details |
|-------------|---------|
| **An AI coding agent** | [Claude Code](https://claude.ai/code), [Codex](https://openai.com/codex), [Cursor](https://cursor.com), or similar |
| **An OpenAI API key** | Starts with `sk-` — get one at [platform.openai.com](https://platform.openai.com) |
| **Internet access** | Labs use OpenAI's web search via your API key |

> **Python, venv, and dependencies are installed automatically** by the agent in Module 1. You don't need to set anything up manually.

---

## How It Works (Step by Step)

### 1. Clone this repo

```bash
git clone https://github.com/allthingssecurity/agenticslides.git
cd agenticslides
```

### 2. Open your AI coding agent

Open **Claude Code**, **Codex**, **Cursor**, or whichever AI agent you use. Start a **new session** pointed at this repo folder.

### 3. Start with Module 1

Open the file `course/agent-docs/01-foundations.md` and copy the prompt from the top:

```
Read the file course/agent-docs/01-foundations.md and follow it step by step.

First complete the Environment Setup section, then build Lab 0 and Lab 1 from
scratch in the my-agents/ directory. Run each lab and verify it works before
moving on to the next one.

If you get stuck on any lab, you can consult the reference implementation in
course/labs/ but try building it yourself first.
```

**Paste it into your agent.** Then sit back and watch. The agent will:
- Install Python (if needed), create a virtual environment, install all dependencies
- Build Lab 0 (environment checker) and Lab 1 (calculator + clock agent) from scratch
- Run each lab and verify it works

### 4. Move to Module 2, 3, 4

When Module 1 is done, open a **new agent session** and repeat with the next module. Each module doc has its own prompt at the top.

| Module | File to Open | What Gets Built |
|--------|-------------|-----------------|
| **Module 1** | `course/agent-docs/01-foundations.md` | Setup verifier + calculator/clock agent |
| **Module 2** | `course/agent-docs/02-building-blocks.md` | Web search + research report agent |
| **Module 3** | `course/agent-docs/03-multi-agent.md` | Orchestrator, parallel agents, file pipeline |
| **Module 4** | `course/agent-docs/04-capstones.md` | Financial system, SQL agent, content pipeline |

> **Important:** Use a **fresh agent session** for each module. Don't continue in the same session.

---

## What You'll Build

By the end of the course, your `my-agents/` folder will contain 9 working AI agents:

| Lab | File | What It Does |
|-----|------|-------------|
| Lab 0 | `lab0_setup.py` | Environment checker + smoke test |
| Lab 1 | `lab1_first_agent.py` | Agent with calculator + clock tools |
| Lab 2 | `lab2_research_agent.py` | Web search agent that writes research reports |
| Lab 3a | `lab3a_first_subagent.py` | Orchestrator that delegates to a sub-agent |
| Lab 3b | `lab3b_parallel_agents.py` | 3 specialist agents running in parallel |
| Lab 3c | `lab3c_file_sharing.py` | Multi-agent pipeline communicating via files |
| Lab 4 | `lab4_financial_research.py` | 4-agent financial research system |
| Lab 5 | `lab5_text_to_sql.py` | Natural language to SQL query agent |
| Lab 6 | `lab6_content_pipeline.py` | 3-stage content creation pipeline |

---

## Course Concepts

| Module | Key Concepts |
|--------|-------------|
| **1. Foundations** | `create_deep_agent()`, `@tool` decorator, tool calling, `thread_id`, system prompts |
| **2. Building Blocks** | `write_todos` planning, web search tools, filesystem context management, write-then-summarize pattern |
| **3. Multi-Agent** | Sub-agent delegation with `task()`, parallel execution, filesystem-as-communication-bus |
| **4. Capstones** | Multi-phase orchestration, simulated data tools, SQLite integration, sequential pipelines |

---

## Repo Structure

```
agenticslides/
├── README.md                          ← You are here
├── course/
│   ├── agent-docs/                    ← STUDENT: Use these files
│   │   ├── 01-foundations.md          ← Module 1 (start here)
│   │   ├── 02-building-blocks.md      ← Module 2
│   │   ├── 03-multi-agent.md          ← Module 3
│   │   ├── 04-capstones.md            ← Module 4
│   │   ├── cheatsheet.md              ← Quick reference
│   │   └── AGENT_README.md            ← Instructor guide
│   ├── labs/                          ← Reference implementations (if you get stuck)
│   ├── website/                       ← Course website (human-readable version)
│   ├── MODULE_1_FOUNDATIONS.md        ← Concept deep-dives
│   ├── MODULE_2_BUILDING_BLOCKS.md
│   ├── MODULE_3_MULTI_AGENT.md
│   ├── MODULE_4_CAPSTONE_PROJECTS.md
│   ├── CHEATSHEET.md
│   └── 00_COURSE_OUTLINE.md
└── my-agents/                         ← Created by the agent (your work goes here)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Agent says "module not found" | Make sure the agent activated the venv: `source .venv/bin/activate` |
| API key error | Set it: `export OPENAI_API_KEY="sk-your-key-here"` |
| Agent gets confused | Start a **new session** — don't reuse old ones across modules |
| Lab fails to run | Check the reference implementation in `course/labs/` and compare |
| Python not found | Module 1 setup will install it, or install manually: `brew install python@3.13` (Mac) |

---

## Quick Start (TL;DR)

```bash
# 1. Clone
git clone https://github.com/allthingssecurity/agenticslides.git
cd agenticslides

# 2. Open your AI agent and paste:
# "Read the file course/agent-docs/01-foundations.md and follow it step by step."

# 3. Watch it build everything. Repeat for modules 2-4.
```
