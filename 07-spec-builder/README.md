# Challenge 7: Spec Builder + Build (500 pts)

## Overview

This is a two-phase challenge. First, you write a Product Requirements Document (PRD) based on a vague business brief. Then, you build the feature described in your own PRD.

## Phase 1: Write the PRD

Read `brief.md` — it contains a 3-sentence business brief from a stakeholder. Your job is to turn this into a proper PRD.

Create a file called `prd.md` that includes:

1. **User Stories** — At least 3 user stories in the format: "As a [role], I want [feature], so that [benefit]."
2. **Acceptance Criteria** — At least 5 specific, testable acceptance criteria.
3. **Edge Cases / Error Handling** — A section describing edge cases and how the system should handle errors.
4. **Technical Approach** — A section describing the technical approach, architecture, or implementation strategy.

## Phase 2: Build the Feature

Based on your PRD, implement a `waste_tracker.py` module.

The module should provide a `WasteTracker` class that can:
- Log food waste entries (date, item, quantity, unit, reason, brand)
- Query entries by date range and brand
- Calculate waste statistics (totals by category, daily averages, top wasted items)
- Determine waste trends (increasing, decreasing, or stable)
- Export data to CSV

## Submission

When you're ready, submit your solution for server-side validation:

```bash
python ctf_helper.py 7 prd.md
```

The server validates your PRD structure (user stories, acceptance criteria, edge cases, and technical approach sections). If everything passes, your score is recorded.

## Files

| File | Description |
|------|-------------|
| `brief.md` | The 3-sentence business brief |
| `requirements.txt` | Python dependencies |

## Rules

- You must create `prd.md` (your PRD) and `waste_tracker.py` (your implementation)
- The PRD must include all 4 required sections
- Do not modify `brief.md`
