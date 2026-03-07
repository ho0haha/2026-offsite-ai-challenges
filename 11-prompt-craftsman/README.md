# Challenge 11: Prompt Craftsman (200 pts)

## Objective

Complete 5 prompt engineering mini-challenges. For each challenge, you must craft the right prompts to your AI assistant and save the output to the `outputs/` directory.

## Challenges

| # | Task | Input | Output File |
|---|------|-------|-------------|
| 1 | Generate comprehensive docstring | `challenges/challenge1/function.py` | `outputs/output1.md` |
| 2 | Identify common bug pattern | `challenges/challenge2/functions.py` | `outputs/output2.md` |
| 3 | Suggest optimization with before/after | `challenges/challenge3/slow_function.py` | `outputs/output3.md` |
| 4 | Explain time complexity in plain English | `challenges/challenge4/algorithm.py` | `outputs/output4.md` |
| 5 | Write migration plan | `challenges/challenge5/old_schema.py` & `new_schema.py` | `outputs/output5.md` |

## How to Complete

1. Read each challenge's `task.md` for specific requirements
2. Use your AI coding assistant to generate the required output
3. Save each output to the corresponding file in `outputs/`

## Submission

When all 5 outputs are ready, submit them for server-side validation:

```bash
python ctf_helper.py 11 outputs/output1.md outputs/output2.md outputs/output3.md outputs/output4.md outputs/output5.md
```

The server validates that each output contains the required elements. All 5 must pass.

## Tips

- Read the task.md files carefully — they specify exactly what must be in each output
- The validator checks for specific required elements in each output
- Quality matters — make sure your outputs are thorough and complete
