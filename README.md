# AI Coding CTF - Challenge Pack

Yum! Brands Engineering Leadership Offsite - AI Coding Challenge

## Getting Started

1. Clone this repo:
   ```bash
   git clone <repo-url>
   cd 2026-offsite-ai-challenges
   ```

2. Make sure you have **Python 3.11+** installed:
   ```bash
   python --version
   ```

3. Run the one-time setup to register on the leaderboard:
   ```bash
   python setup.py
   ```
   This registers your name on the server and caches your session so challenge tests can auto-submit.

4. Each challenge is in its own directory. Navigate to a challenge and read the `README.md`:
   ```bash
   cd 01-hello-ai
   cat README.md
   ```

5. Install challenge dependencies:
   ```bash
   pip install -r requirements.txt
   ```

6. Solve the challenge, get the flag, and submit it on the leaderboard!

## Challenges

| # | Challenge | Points | Tool | Difficulty |
|---|-----------|--------|------|------------|
| 1 | [Hello AI](./01-hello-ai) | 50 | Cursor | Easy |
| 2 | [Bug Squash](./02-bug-squash) | 50 | Claude Code | Easy |
| 3 | [The Broken Order System](./03-broken-order-system) | 200 | Cursor | Medium |
| 4 | [Production Incident](./04-production-incident) | 200 | Claude Code | Medium |
| 5 | [Spaghetti Untangler](./05-spaghetti-untangler) | 250 | Cursor | Hard |
| 6 | [Test Factory](./06-test-factory) | 200 | Claude Code | Medium |
| 7 | [Spec Builder + Build](./07-spec-builder) | 500 | Claude Code | Hard |
| 8 | [AI Menu Assistant](./08-ai-menu-assistant) | 300 | Cursor | Medium |
| 9 | [Smart Feedback Sorter](./09-smart-feedback-sorter) | 250 | Claude Code | Medium |
| 10 | [Context is King](./10-context-is-king) | 350 | Cursor | Hard |
| 11 | [Prompt Craftsman](./11-prompt-craftsman) | 200 | Cursor | Medium |
| 12 | [Full Stack Sprint](./12-full-stack-sprint) | 500 | Claude Code | Hard |

## Tool Assignments

- **Cursor challenges:** 1, 3, 5, 8, 10, 11
- **Claude Code challenges:** 2, 4, 6, 7, 9, 12

## Recommended Order

1. **Start with the warm-ups** (Challenges 1 & 2) to get comfortable
2. **Pick challenges that interest you** from the main categories
3. **Higher points = harder** but more rewarding
4. **Nobody finishes everything** - focus on quality over quantity

## Prerequisites

- Python 3.11+
- pip
- [Cursor](https://cursor.sh) (for Cursor challenges)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (for Claude Code challenges)
- For challenges 8 & 9: `ANTHROPIC_API_KEY` environment variable (provided by facilitator)
