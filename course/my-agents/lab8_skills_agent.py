"""
LAB 8: Skills Creation + Skill-Driven Agent
============================================
Shows how to create custom skills and load them into an agent.

Skills source in this lab:
- /skills/lab8/release-notes/SKILL.md
- /skills/lab8/risk-assessment/SKILL.md
- /skills/lab8/executive-brief/SKILL.md
"""
import os

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from trace_utils import interactive_mode, run_with_trace

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


skills_agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=[],
    backend=FilesystemBackend(root_dir=BASE_DIR),
    skills=["/skills/lab8/"],
    system_prompt="""You are a release-planning assistant.

## SKILLS WORKFLOW
1. Identify whether the request matches one or more loaded skills.
2. Read the relevant SKILL.md file(s) before producing your answer.
3. Follow the skill instructions exactly.
4. Start your output with: Skills Used: <skill-names>

## OUTPUT REQUIREMENTS
- Provide a clear structure with headings.
- Include assumptions and open risks.
- End with a concrete next-step checklist.
""",
)


def ask(question: str, thread_id: str = "lab8-skills"):
    print(f"\n{'=' * 68}")
    print(f" QUERY: {question}")
    print(f"{'=' * 68}\n")
    run_with_trace(skills_agent, question, thread_id=thread_id)


if __name__ == "__main__":
    print("=" * 68)
    print(" LAB 8: Skills-Driven Agent")
    print(" Custom skills loaded from /skills/lab8/")
    print("=" * 68)

    ask(
        "Prepare a release readiness brief for version 2.8.\n"
        "Changes: switched auth token handling, added async job retries, "
        "migrated payment webhook parser, fixed dashboard caching bug.\n"
        "Audience: VP Engineering and Product leadership."
    )

    print(f"\n{'=' * 68}")
    print(" LAB 8 COMPLETE!")
    print("=" * 68)

    interactive_mode(skills_agent, "Lab 8: Skills Agent", thread_id="lab8-live")
