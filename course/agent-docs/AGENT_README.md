# Agentic AI Masterclass — Instructor Guide

> **For the instructor:** This README explains how students use these docs with their AI coding agent. Each module is a standalone file with a copy-paste prompt at the top.

---

## How Students Use This (Build-Only Model)

Each module doc has a **copy-paste prompt** at the very top. The student:

1. Opens a **new agent session** (Codex, Claude Code, Cursor, etc.)
2. Copies the prompt block from the module doc
3. Pastes it into the agent
4. The agent **builds all files** (including `trace_utils.py` in Module 1) but does **NOT run** them
5. Student runs each lab in their **own terminal**: `python my-agents/labX.py`
6. Student sees **real-time traces** (tool calls, sub-agent delegations, file writes) and gets an **interactive prompt** to try their own queries

**Why build-only?** Running labs inside the agent session showed "exit code 0" and a wall of text. With build-only, students see colored traces and can experiment interactively.

---

## Course Overview

**5 modules, 11 labs, progressive difficulty:**

| Module | Doc File | What Gets Built | Copy-Paste Prompt? |
|--------|----------|-----------------|--------------------|
| 1. Foundations | `01-foundations.md` | Setup verifier + calculator/clock agent | Yes |
| 2. Building Blocks | `02-building-blocks.md` | Web search + filesystem research agent | Yes |
| 3. Multi-Agent | `03-multi-agent.md` | Orchestrator, parallel agents, file pipeline | Yes |
| 4. Capstones | `04-capstones.md` | Financial system, SQL agent, content pipeline | Yes |
| 5. Memory + Skills | `05-memory-skills.md` | Long-term memory demo + custom skills demo | Yes |

**Plus:** `cheatsheet.md` — quick reference (agent can consult anytime)

---

## Module Order

Students should do modules in order:

1. `01-foundations.md` — setup + first agent (start here)
2. `02-building-blocks.md` — tools, planning, context
3. `03-multi-agent.md` — sub-agents, parallel, pipelines
4. `04-capstones.md` — production-grade apps
5. `05-memory-skills.md` — dedicated memory/skills labs

---

## Prerequisites (Student Must Have)

- **Python 3.11+** installed
- **An OpenAI API key** (starts with `sk-`)
- **Internet access** (labs use OpenAI web search)
- **An AI coding agent** (Codex, Claude Code, Cursor, etc.)

---

## What Each Module Doc Contains

Every module doc follows this structure:

1. **Copy-paste prompt** (top of file) — student pastes this into a fresh agent session
2. **Self-contained setup** — each module handles its own env setup (venv, deps, API key)
3. **Concepts section** — teaches the "why" so the agent understands context
4. **Build-from-scratch labs** — step-by-step `create-file` / `append-to-file` instructions with exact code
5. **Run + Verify** — exact commands and expected output patterns
6. **What You Learned** — summary table at the end of each lab

---

## Reference Implementations

If the agent gets stuck, reference implementations exist at:

| Lab | Reference File |
|-----|---------------|
| Lab 0 | `course/labs/lab0_setup.py` |
| Lab 1 | `course/labs/lab1_first_agent.py` |
| Lab 2 | `course/labs/lab2_research_agent.py` |
| Lab 3a | `course/labs/lab3a_first_subagent.py` |
| Lab 3b | `course/labs/lab3b_parallel_agents.py` |
| Lab 3c | `course/labs/lab3c_file_sharing.py` |
| Lab 4 | `course/labs/lab4_financial_research.py` |
| Lab 5 | `course/labs/lab5_text_to_sql.py` |
| Lab 6 | `course/labs/lab6_content_pipeline.py` |
| Lab 7 | `course/labs/lab7_long_term_memory.py` |
| Lab 8 | `course/labs/lab8_skills_agent.py` |
