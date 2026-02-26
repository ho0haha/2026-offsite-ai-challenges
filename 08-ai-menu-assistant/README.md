# Challenge 8: AI Menu Assistant (300 pts)

**Tool:** Cursor

## Overview

Build a CLI chatbot that uses the Claude API to answer questions about a restaurant menu. The chatbot reads menu data from `menu.json` and answers natural language questions accurately.

## Your Task

Create a file called `chatbot.py` that exposes a function:

```python
def ask_menu_question(question: str) -> str:
    """
    Takes a natural language question about the menu and returns
    an accurate answer using the Claude API.
    """
```

Your function should:
1. Load the menu data from `menu.json`
2. Use the Anthropic Claude API to answer the question based on the menu data
3. Return an accurate, natural language response

## Requirements

- Use the `anthropic` Python package to call the Claude API
- Your `ANTHROPIC_API_KEY` environment variable must be set
- The function must return accurate information that matches the menu data
- Install dependencies: `pip install -r requirements.txt`

## Testing

Run the test suite:

```bash
python test_chatbot.py
```

The test sends 10 questions about the menu and checks that your answers contain the correct information. You need to get at least **8 out of 10** correct to earn the flag.

## Files

| File | Description |
|------|-------------|
| `menu.json` | The restaurant menu data (do not modify) |
| `test_chatbot.py` | Sends 10 questions, checks answers |
| `requirements.txt` | Python dependencies |

## Tips

- Read `menu.json` carefully to understand the data structure
- Make sure your Claude prompt includes the full menu data so the model can answer accurately
- Be precise — the tests check for specific values (prices, item names, calorie counts)
- Think about how to structure your system prompt to get accurate, factual answers
- Do not modify `menu.json` or `test_chatbot.py`
