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

3. Copy the environment template and fill in your values:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set `CTF_SERVER`, `CTF_JOIN_CODE`, and `ANTHROPIC_API_KEY` (provided by facilitator).

4. Run the one-time setup to register on the leaderboard:
   ```bash
   python setup.py
   ```
   This registers your name on the server and caches your session so challenge tests can auto-submit.

5. Each challenge is in its own directory. Navigate to a challenge and read the `README.md`:
   ```bash
   cd 01-hello-ai
   cat README.md
   ```

6. Install challenge dependencies:
   ```bash
   pip install -r requirements.txt
   ```

7. Solve the challenge, get the flag, and submit it on the leaderboard!

## Challenges

| # | Challenge | Points | Difficulty |
|---|-----------|--------|------------|
| 1 | [Hello AI](./01-hello-ai) | 50 | Easy |
| 2 | [Bug Squash](./02-bug-squash) | 50 | Easy |
| 3 | [The Broken Order System](./03-broken-order-system) | 200 | Medium |
| 4 | [Production Incident](./04-production-incident) | 200 | Medium |
| 5 | [Spaghetti Untangler](./05-spaghetti-untangler) | 250 | Hard |
| 6 | [Test Factory](./06-test-factory) | 200 | Medium |
| 7 | [Spec Builder + Build](./07-spec-builder) | 500 | Hard |
| 8 | [AI Menu Assistant](./08-ai-menu-assistant) | 300 | Medium |
| 9 | [Smart Feedback Sorter](./09-smart-feedback-sorter) | 250 | Medium |
| 10 | [Context is King](./10-context-is-king) | 350 | Hard |
| 11 | [Prompt Craftsman](./11-prompt-craftsman) | 200 | Medium |
| 12 | [Full Stack Sprint](./12-full-stack-sprint) | 500 | Hard |

## Tier Progression

Challenges unlock progressively as you prove your skills:

| Tier | Challenges | Unlock Rule |
|------|-----------|-------------|
| 1 | 1-2 (Warm-Up) | Available immediately |
| 2 | 3-6 (Debugging, Refactoring) | Complete both Tier 1 challenges |
| 3 | 7-12 (Advanced) | Complete 2+ Tier 2 challenges |

## Recommended Order

1. **Start with the warm-ups** (Challenges 1 & 2) to get comfortable
2. **Pick challenges that interest you** from the main categories
3. **Higher points = harder** but more rewarding
4. **Nobody finishes everything** - focus on quality over quantity

## Prerequisites

- Python 3.11+
- pip
- An AI coding assistant ([Cursor](https://cursor.sh), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), GitHub Copilot, etc.)
- For challenges 8 & 9: `ANTHROPIC_API_KEY` environment variable (provided by facilitator)
