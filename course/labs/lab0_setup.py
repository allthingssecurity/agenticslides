"""
LAB 0: Environment Setup & Verification
=========================================
Run this first to verify everything is installed correctly.

Setup:
  pip install deepagents "langchain-openai>=1.1.8"
  export OPENAI_API_KEY="sk-your-key-here"
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

    # Check openai (used by our search tools)
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
        model="openai:gpt-4o-mini",  # Use mini for cheaper setup test
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
