"""
Test script to verify Phase 2.2.2 Context Assembly and Prompt Engineering.
"""

from prompt_builder import build_context, get_system_prompt, build_user_prompt

def test_prompt_builder():
    # 1. Test System Prompt
    print("=== SYSTEM PROMPT ===")
    print(get_system_prompt())
    print("\n")

    # 2. Test Context Assembly with chunks
    mock_chunks = [
        {
            "text": "The HDFC Mid-Cap Fund has an expense ratio of 1.2%.",
            "metadata": {"source_url": "https://groww.in/funds/1", "last_updated": "2026-05-09"}
        },
        {
            "text": "Exit load is 1% if redeemed within 365 days.",
            "metadata": {"source_url": "https://groww.in/funds/1", "last_updated": "2026-05-09"}
        }
    ]

    context = build_context(mock_chunks)
    print("=== ASSEMBLED CONTEXT ===")
    print(context)
    print("\n")

    # 3. Test User Prompt Injection
    query = "What is the expense ratio?"
    user_prompt = build_user_prompt(context, query)
    print("=== FINAL USER PROMPT ===")
    print(user_prompt)
    print("\n")

    # 4. Test Empty Context Handling
    empty_context = build_context([])
    empty_user_prompt = build_user_prompt(empty_context, query)
    print("=== EMPTY CONTEXT USER PROMPT ===")
    print(empty_user_prompt)

if __name__ == "__main__":
    test_prompt_builder()
