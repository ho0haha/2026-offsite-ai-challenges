# Challenge 2: Bug Squash

**Points:** 50 | **Tool:** Claude Code | **Difficulty:** Easy

## Objective

Use your AI coding tool to find and fix 3 bugs in a Python script.

## Instructions

1. Open `buggy_script.py` — it's a restaurant order processing script with **3 planted bugs**
2. Feed the file to Claude Code and ask it to identify all bugs
3. Apply the fixes
4. Run the script:
   ```bash
   python buggy_script.py
   ```
5. When the script runs correctly, it prints your **flag**
6. Submit the flag on the CTF leaderboard

## Bug Types

There are exactly 3 bugs:
- An **off-by-one error**
- A **wrong operator**
- A **missing return statement**

## Tips

- Try asking: "Find all bugs in this file and explain each one"
- The script processes a sample restaurant order and should print a summary
- If the output doesn't look right, check the error messages carefully

## Files

- `buggy_script.py` — Fix the 3 bugs in this file
