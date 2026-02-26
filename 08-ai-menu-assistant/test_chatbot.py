#!/usr/bin/env python3
"""
Test suite for the AI Menu Assistant chatbot.

Sends 10 questions to the chatbot and checks that the answers
contain correct information from the menu. Requires 8/10 to pass.

Participants must create chatbot.py with:
    def ask_menu_question(question: str) -> str
"""

import sys
import time

# ---------------------------------------------------------------------------
# Test definitions
# Each test has: question, list of acceptable substrings (at least one must
# appear), and a human-readable description of what's expected.
# ---------------------------------------------------------------------------

TESTS = [
    {
        "question": "What's the price of the Classic Burger?",
        "must_contain_any": ["9.99"],
        "description": "Must mention the price $9.99",
    },
    {
        "question": "What items are vegetarian?",
        "must_contain_all_of_n": {
            "items": [
                "Veggie Burger",
                "French Fries",
                "Onion Rings",
                "Caesar Salad",
                "Coleslaw",
                "Mac & Cheese",
                "Sweet Potato Fries",
                "Garden Side Salad",
                "Loaded Nachos",
                "Vegan Coconut Ice Cream",
            ],
            "min_matches": 2,
        },
        "description": "Must name at least 2 vegetarian items",
    },
    {
        "question": "Does the Spicy Chicken Sandwich contain dairy?",
        "must_contain_any": ["yes", "dairy", "does contain"],
        "description": "Must confirm dairy is an allergen (dairy is listed)",
    },
    {
        "question": "What's the cheapest item on the menu?",
        "must_contain_any": ["Sparkling Water"],
        "description": "Must identify Sparkling Water ($1.99) as cheapest",
    },
    {
        "question": "What items contain nuts?",
        "must_contain_any": ["Peanut Butter Cookie"],
        "description": "Must mention the Peanut Butter Cookie (only item with nuts allergen)",
    },
    {
        "question": "How many calories in the Caesar Salad?",
        "must_contain_any": ["340"],
        "description": "Must state 340 calories",
    },
    {
        "question": "What sides are available?",
        "must_contain_all_of_n": {
            "items": [
                "French Fries",
                "Onion Rings",
                "Caesar Salad",
                "Coleslaw",
                "Mac & Cheese",
                "Sweet Potato Fries",
                "Garden Side Salad",
                "Loaded Nachos",
            ],
            "min_matches": 3,
        },
        "description": "Must name at least 3 side items",
    },
    {
        "question": "Is there anything under $5?",
        "must_contain_all_of_n": {
            "items": [
                "French Fries",
                "Onion Rings",
                "Coleslaw",
                "Mac & Cheese",
                "Sweet Potato Fries",
                "Garden Side Salad",
                "Soft Drink",
                "Fresh Lemonade",
                "Iced Tea",
                "Sparkling Water",
                "Peanut Butter Cookie",
                "Vegan Coconut Ice Cream",
                "Churros",
            ],
            "min_matches": 2,
        },
        "description": "Must name at least 2 items under $5",
    },
    {
        "question": "What's the most expensive item on the menu?",
        "must_contain_any": ["BBQ Bacon Burger"],
        "description": "Must identify BBQ Bacon Burger ($12.49) as most expensive",
    },
    {
        "question": "What desserts do you have?",
        "must_contain_all_of_n": {
            "items": [
                "Chocolate Brownie Sundae",
                "Apple Pie",
                "Cheesecake",
                "Peanut Butter Cookie",
                "Vegan Coconut Ice Cream",
                "Churros",
            ],
            "min_matches": 2,
        },
        "description": "Must name at least 2 desserts",
    },
]


def check_must_contain_any(response: str, substrings: list[str]) -> bool:
    """Return True if response contains at least one of the substrings (case-insensitive)."""
    response_lower = response.lower()
    return any(s.lower() in response_lower for s in substrings)


def check_must_contain_all_of_n(response: str, config: dict) -> bool:
    """Return True if response contains at least `min_matches` of the listed items."""
    response_lower = response.lower()
    items = config["items"]
    min_matches = config["min_matches"]
    match_count = sum(1 for item in items if item.lower() in response_lower)
    return match_count >= min_matches


def run_tests():
    """Run all tests against the chatbot."""
    # Import the participant's chatbot
    try:
        from chatbot import ask_menu_question
    except ImportError as e:
        print(f"ERROR: Could not import ask_menu_question from chatbot.py: {e}")
        print("Make sure chatbot.py exists and defines: def ask_menu_question(question: str) -> str")
        sys.exit(1)

    print("=" * 65)
    print("  AI Menu Assistant — Test Suite (10 questions)")
    print("=" * 65)
    print()

    passed = 0
    total = len(TESTS)

    for i, test in enumerate(TESTS, 1):
        question = test["question"]
        description = test["description"]

        print(f"  Q{i}: {question}")
        print(f"       Expected: {description}")

        try:
            response = ask_menu_question(question)
            response_str = str(response)
        except Exception as e:
            print(f"       FAIL (exception): {e}")
            print()
            continue

        # Truncate displayed response for readability
        display_response = response_str[:200] + ("..." if len(response_str) > 200 else "")
        print(f"       Response: {display_response}")

        # Check correctness
        ok = False
        if "must_contain_any" in test:
            ok = check_must_contain_any(response_str, test["must_contain_any"])
        if "must_contain_all_of_n" in test:
            ok = check_must_contain_all_of_n(response_str, test["must_contain_all_of_n"])

        if ok:
            print("       PASS")
            passed += 1
        else:
            print("       FAIL")

        print()

        # Small delay between API calls to avoid rate limiting
        if i < total:
            time.sleep(0.5)

    print("=" * 65)
    print(f"  Results: {passed}/{total} passed")
    print("=" * 65)
    print()

    if passed >= 8:
        print("  FLAG{ai_menu_assistant_8_of_10}")
        print()
    else:
        print(f"  Not enough correct answers. Need at least 8/10, got {passed}/10.")
        print("  Review your chatbot logic and try again.")
        print()


if __name__ == "__main__":
    run_tests()
