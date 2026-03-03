# Challenge 9: Smart Feedback Sorter (250 pts)

## Overview

Build a script that uses the Claude API to automatically categorize customer feedback into predefined categories and determine sentiment.

## Your Task

Create a script called `sorter.py` (or whatever you prefer) that:

1. Reads customer feedback from `feedback.csv`
2. Uses the Claude API to classify each feedback entry
3. Writes results to `output.csv`

### Input: `feedback.csv`

Contains 50 customer feedback entries with columns:
- `id` — unique identifier
- `feedback_text` — the customer's feedback

### Output: `output.csv`

Your script must produce a file called `output.csv` with columns:
- `id` — matching the feedback id
- `category` — one of: `service`, `food_quality`, `wait_time`, `cleanliness`, `other`
- `sentiment` — one of: `positive`, `negative`

## Categories

| Category | Description |
|----------|-------------|
| `service` | About staff behavior, attentiveness, friendliness, helpfulness |
| `food_quality` | About taste, temperature, freshness, portion size, presentation |
| `wait_time` | About how long it took to be served, seated, or receive food |
| `cleanliness` | About restaurant cleanliness, hygiene, tidiness |
| `other` | Anything that doesn't fit the above (parking, app, ambiance, etc.) |

## Validation

After generating `output.csv`, run:

```bash
python validate.py
```

This compares your output against a ground truth file. Both the category AND sentiment must match for each entry to count as correct. You need **85% accuracy** (at least 43 out of 50 correct) — your solution is auto-submitted when you pass.

## Files

| File | Description |
|------|-------------|
| `feedback.csv` | 50 customer feedback entries to classify |
| `ground_truth.json` | Correct classifications (used by validator) |
| `validate.py` | Checks your output.csv against ground truth |
| `requirements.txt` | Python dependencies |

## Tips

- Read through `feedback.csv` to understand the range of feedback
- Some entries are intentionally ambiguous — use your best judgment when crafting prompts
- You can process entries individually or in batches
- Make sure your output uses the exact category and sentiment strings listed above
- Your `ANTHROPIC_API_KEY` environment variable must be set
- Do not modify `feedback.csv`, `ground_truth.json`, or `validate.py`
