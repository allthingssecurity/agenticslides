"""
LAB 6 — BONUS: Automated Content Pipeline (Module 4)
======================================================
Multi-agent content creation with quality control:
  Researcher → Writer → Editor/Reviewer → Final Output

Learn: Sequential pipeline, quality control loop, agent specialization.

Run: python lab6_content_pipeline.py
"""
import json
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ─── TOOL ──────────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query
    """
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10
        )
        data = resp.json()
        parts = []
        if data.get("Abstract"):
            parts.append(data["Abstract"])
        for t in data.get("RelatedTopics", [])[:5]:
            if isinstance(t, dict) and "Text" in t:
                parts.append(f"- {t['Text']}")
        return "\n".join(parts) if parts else "No results found."
    except Exception as e:
        return f"Error: {e}"


# ─── PIPELINE AGENTS ──────────────────────────────────

content_pipeline = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=[
        # Stage 1: Research
        {
            "name": "topic_researcher",
            "description": (
                "Deep topic researcher. Searches web, gathers facts, stats, "
                "and expert opinions. Writes notes to /research/."
            ),
            "system_prompt": """You are an expert topic researcher.

JOB:
1. Search 3-5 times with different query angles
2. Write structured research notes to /research/notes.md
3. Include: key facts, statistics, expert quotes, trends
4. List ALL source URLs
5. Note any conflicting information

NOTE FORMAT:
# Research: [Topic]
## Key Facts & Stats
- fact (source URL)
## Expert Opinions
- quote/opinion (source)
## Current Trends
- trend
## Counterarguments / Controversies
- point
## Sources
- [Source](URL)
""",
            "tools": [web_search],
            "model": "openai:gpt-4o-mini",
        },

        # Stage 2: Write
        {
            "name": "content_writer",
            "description": (
                "Professional writer. Reads /research/ notes and writes "
                "polished articles to /drafts/. Does NOT search."
            ),
            "system_prompt": """You are a professional content writer.

JOB:
1. Read research notes from /research/notes.md
2. Write a polished article to /drafts/article.md
3. Structure: engaging intro → clear sections → examples → conclusion

ARTICLE FORMAT:
---
title: [SEO-friendly title]
meta_description: [155 chars for SEO]
word_count_target: 1000
---

# [Title]

[Engaging opening hook — a surprising stat or question]

## [Section 1 — the core concept]
[Explain with examples]

## [Section 2 — deeper dive]
[Data, comparisons, expert insights]

## [Section 3 — practical implications]
[What this means for the reader]

## Key Takeaways
- [takeaway 1]
- [takeaway 2]
- [takeaway 3]

## Sources
- [Source](URL)

RULES:
- Write 800-1200 words
- Use short paragraphs (2-3 sentences)
- Include at least one data point per section
- Conversational but authoritative tone
- NO fluff or filler — every sentence adds value
""",
            "tools": [],
            "model": "openai:gpt-4o",
        },

        # Stage 3: Review & Polish
        {
            "name": "editor_reviewer",
            "description": (
                "Senior editor. Reviews /drafts/ for quality, accuracy, "
                "and engagement. Writes feedback + final version."
            ),
            "system_prompt": """You are a senior content editor.

JOB:
1. Read the draft from /drafts/article.md
2. Read original research from /research/notes.md (to fact-check)
3. Write detailed feedback to /review/feedback.md
4. Write the IMPROVED final version to /final/article.md

REVIEW CHECKLIST:
□ Accuracy — claims match research notes?
□ Structure — logical flow, clear headings?
□ Engagement — strong hook, interesting examples?
□ Clarity — jargon explained, sentences concise?
□ Completeness — all key points from research covered?
□ SEO — title, meta description, headers good?
□ Grammar — clean, professional writing?

FEEDBACK FORMAT (/review/feedback.md):
# Editorial Review
## Overall Rating: [A/B/C/D]
## Strengths
- ...
## Issues Found
- [issue]: [fix applied]
## Changes Made
- [change 1]
- [change 2]

THEN write the polished final version to /final/article.md
""",
            "tools": [],
            "model": "openai:gpt-4o",
        },
    ],

    system_prompt="""You orchestrate a content creation pipeline.

## PIPELINE (SEQUENTIAL — each step depends on the previous)

### Step 1: Research
- task to topic_researcher: "Research [topic] for an article targeting [audience]"
- Researcher writes to /research/notes.md

### Step 2: Write Draft
- task to content_writer: "Read /research/notes.md and write an article about [topic] for [audience]"
- Writer reads /research/ → writes to /drafts/article.md

### Step 3: Edit & Finalize
- task to editor_reviewer: "Review /drafts/article.md against /research/notes.md. Write feedback to /review/ and final version to /final/"
- Editor reads /drafts/ + /research/ → writes /review/feedback.md + /final/article.md

### Step 4: Deliver
- Read /final/article.md
- Read /review/feedback.md
- Present BOTH to the user: the final article + editor's notes

## IMPORTANT
- Steps MUST run sequentially (each needs previous step's files)
- Be specific in task descriptions about file paths
- Include target audience in writer's task
"""
)


# ─── RUN IT ─────────────────────────────────────────────

def create_content(topic: str, audience: str = "tech professionals"):
    """Run the full content pipeline."""
    print(f"\n{'='*60}")
    print(f" CONTENT PIPELINE")
    print(f" Topic: {topic}")
    print(f" Audience: {audience}")
    print(f" Pipeline: Research → Write → Edit → Deliver")
    print(f"{'='*60}\n")
    print("Running 3-stage pipeline (1-2 minutes)...\n")

    result = content_pipeline.invoke(
        {"messages": [HumanMessage(content=(
            f"Create a high-quality article.\n"
            f"Topic: {topic}\n"
            f"Target audience: {audience}\n"
            f"Run the full pipeline: research → write → review & edit"
        ))]},
        config={"configurable": {"thread_id": "content-pipeline"}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\n{'─'*60}")
            print(msg.content)
            break


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║  BONUS: Automated Content Pipeline                       ║
║  Researcher → Writer → Editor → Final Article            ║
╚══════════════════════════════════════════════════════════╝
    """)

    create_content(
        topic="How AI Agents Are Changing Software Development in 2025",
        audience="software developers and engineering managers"
    )

    # More examples to try:
    # create_content(
    #     topic="The Rise of Rust in Backend Development",
    #     audience="backend engineers considering Rust"
    # )
    # create_content(
    #     topic="Remote Work Best Practices for Engineering Teams",
    #     audience="engineering managers and team leads"
    # )

    print(f"\n{'='*60}")
    print(" CONTENT PIPELINE COMPLETE!")
    print("=" * 60)
    print("""
    PIPELINE EXECUTED:
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │  RESEARCHER  │───→│   WRITER     │───→│   EDITOR     │
    │  web_search  │    │  reads notes │    │  fact-checks  │
    │  → /research/│    │  → /drafts/  │    │  → /review/   │
    └──────────────┘    └──────────────┘    │  → /final/    │
                                            └──────────────┘

    FILES CREATED:
    /research/notes.md    ← raw research with sources
    /drafts/article.md    ← first draft
    /review/feedback.md   ← editorial feedback
    /final/article.md     ← polished final article

    KEY PATTERNS:
    ✓ Sequential pipeline (each stage needs previous output)
    ✓ Quality control (editor reviews against research)
    ✓ File-based handoff between stages
    ✓ Separation of concerns (research ≠ writing ≠ editing)

    CONGRATULATIONS — Course complete! 🎓
    """)
