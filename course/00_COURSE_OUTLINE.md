# Agentic AI Masterclass — From Zero to Multi-Agent Systems
## 3-Hour Hands-On Course using DeepAgents + OpenAI APIs

---

## Course Philosophy
> "A plain LLM-in-a-tool-loop produces shallow agents that fail at long, multi-step tasks."
> — DeepAgents README

This course teaches you to build **deep agents** — systems that plan, delegate, manage context, and persist memory — using the open-source DeepAgents framework with OpenAI APIs. No LangSmith required.

---

## Prerequisites
- Python 3.11+
- An OpenAI API key
- Basic Python knowledge (functions, classes, async/await)
- A terminal and code editor

---

## Course Structure (3 Hours)

### MODULE 1: Foundations (45 min)
**Beginner — "What are agents and why do they fail?"**

| Section | Time | Topic |
|---------|------|-------|
| 1.1 | 10 min | **The Problem with Shallow Agents** — Why a raw LLM + tool loop isn't enough |
| 1.2 | 10 min | **The 4 Pillars of Deep Agents** — Planning, Sub-agents, Filesystem, Prompts |
| 1.3 | 10 min | **Environment Setup** — Install deepagents, configure OpenAI, first "hello world" agent |
| 1.4 | 15 min | **Lab 1: Your First Agent** — Build a simple tool-calling agent with `create_deep_agent()` |

### MODULE 2: Core Building Blocks (45 min)
**Intermediate — "How do agents think, remember, and act?"**

| Section | Time | Topic |
|---------|------|-------|
| 2.1 | 10 min | **Tools & Backends** — Filesystem tools, shell execution, backend architecture |
| 2.2 | 10 min | **Planning with Todos** — How `write_todos` enables task decomposition |
| 2.3 | 10 min | **Context Management** — SummarizationMiddleware, offloading to files |
| 2.4 | 15 min | **Lab 2: Research Agent** — Build an agent that searches the web, reads files, and writes reports |

### MODULE 3: Multi-Agent Orchestration (45 min)
**Advanced — "How do agents collaborate?"**

| Section | Time | Topic |
|---------|------|-------|
| 3.1 | 10 min | **Sub-Agent Architecture** — SubAgentMiddleware, context isolation, the `task` tool |
| 3.2 | 10 min | **Parallel Execution** — Running multiple sub-agents concurrently |
| 3.3 | 10 min | **Communication Patterns** — Sequential, parallel, filesystem-as-bus, memory sharing |
| 3.4 | 15 min | **Lab 3: Multi-Agent Q&A System** — Orchestrator + Researcher + Writer agents |

### MODULE 4: Capstone Projects (45 min)
**Expert — "Build production-grade multi-agent apps"**

| Section | Time | Topic |
|---------|------|-------|
| 4.1 | 25 min | **Project 1: Financial Deep Research System** — Multi-agent financial analysis |
| 4.2 | 15 min | **Project 2: Text-to-SQL Analytics Agent** — Natural language to database queries |
| 4.3 | 5 min | **Project 3 (Bonus Blueprint): Automated Content Pipeline** — Research → Write → Review |

---

## What You'll Build

### Lab 1: Hello Agent
A single agent that can use tools (calculator, web search) to answer questions.

### Lab 2: Research Agent
An agent that searches the web, reads documents, takes structured notes, and writes a summary report to the filesystem.

### Lab 3: Multi-Agent Q&A
An orchestrator that delegates to a "Researcher" sub-agent and a "Writer" sub-agent to answer complex questions with citations.

### Lab 4 (Capstone): Financial Deep Research
A production-grade system with:
- **Orchestrator Agent** — decomposes financial queries
- **Market Data Agent** — fetches stock data, financials, news
- **Analysis Agent** — performs quantitative analysis
- **Report Agent** — synthesizes findings into investor-grade reports
- Parallel execution, filesystem-based data sharing, structured output

### Lab 5 (Capstone): Text-to-SQL Analytics
An agent that:
- Explores database schemas automatically
- Converts natural language to SQL
- Executes queries safely
- Visualizes results and explains findings

### Bonus Blueprint: Content Pipeline
- Research Agent → Draft Agent → Review Agent → Final Output
- Shows skills middleware, memory persistence, quality control loops

---

## Key Takeaways
1. Deep agents = Planning + Sub-agents + Filesystem + Prompts
2. Context isolation prevents sub-agents from polluting each other
3. The filesystem is your async message bus between agents
4. Middleware is the extensibility layer — every capability is a middleware
5. OpenAI models work as first-class citizens via `"openai:gpt-4o"`
