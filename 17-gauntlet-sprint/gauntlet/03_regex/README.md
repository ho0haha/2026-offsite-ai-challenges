# Challenge 03: Restaurant Hours Regex

## Problem

Write a single regex pattern that matches restaurant hours strings and captures the relevant components.

## Format

Restaurant hours follow this pattern:

```
Mon-Fri 11am-10pm
Sat 10am-11pm
Sun Closed
Mon-Thu 11:30am-9:30pm, Fri-Sat 11:30am-10:30pm, Sun 12pm-8pm
```

Valid day names: Mon, Tue, Wed, Thu, Fri, Sat, Sun
Times: 12-hour format with am/pm, optional :MM minutes
"Closed" is valid instead of a time range.

## Task

Edit `solution.py` to implement `parse_hours(text)` which uses a regex to find all hour entries in a string. Each match should capture:
- `days`: the day or day range (e.g., "Mon-Fri", "Sat")
- `open_time`: opening time or None if Closed (e.g., "11am", "11:30am")
- `close_time`: closing time or None if Closed (e.g., "10pm", "10:30pm")
- `is_closed`: boolean, True if the entry says "Closed"

## Files

- `solution.py` — Your solution. Edit this file.
- `test_regex.py` — Tests. Do NOT modify.

## Run

```bash
python -m pytest test_regex.py -v
```
