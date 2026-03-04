# Challenge 8: AI Menu Assistant (300 pts)

## Overview

Build a CLI chatbot that uses an LLM to answer questions about a restaurant menu. The chatbot reads menu data from `menu.json` and answers natural language questions accurately.

## Your Task

Create a file called `chatbot.py` that exposes a function:

```python
def ask_menu_question(question: str) -> str:
    """
    Takes a natural language question about the menu and returns
    an accurate answer using an LLM.
    """
```

Your function should:
1. Load the menu data from `menu.json`
2. Use an LLM to answer the question based on the menu data
3. Return an accurate, natural language response

## Using the LLM Proxy

A Claude Haiku instance is available through the CTF server — no API key needed. Import the helper from the repo root:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ctf_helper import ask_llm

response = ask_llm(
    messages=[{"role": "user", "content": "What is the cheapest item?"}],
    system="You are a menu assistant. Here is the menu data: ..."
)
```

You can also use any other LLM you have access to (OpenAI, local models, Cursor, etc.).

## Testing

Run the test suite:

```bash
python test_chatbot.py
```

The test sends 10 questions about the menu and checks that your answers contain the correct information. You need to get at least **8 out of 10** correct — your solution is auto-submitted when you pass.

## Files

| File | Description |
|------|-------------|
| `menu.json` | The restaurant menu data (do not modify) |
| `test_chatbot.py` | Sends 10 questions, checks answers |

## Tips

- Read `menu.json` carefully to understand the data structure
- Make sure your LLM prompt includes the full menu data so the model can answer accurately
- Be precise — the tests check for specific values (prices, item names, calorie counts)
- Think about how to structure your system prompt to get accurate, factual answers
- Do not modify `menu.json` or `test_chatbot.py`
