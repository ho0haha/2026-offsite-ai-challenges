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

| # | Challenge | Tier | Points | Difficulty |
|---|-----------|------|--------|------------|
| 1 | [Hello AI](./01-hello-ai) | 1 | 50 | Warm-Up |
| 2 | [Bug Squash](./02-bug-squash) | 1 | 50 | Warm-Up |
| 3 | [The Broken Order System](./03-broken-order-system) | 1 | 200 | Warm-Up |
| 4 | [Production Incident](./04-production-incident) | 1 | 200 | Warm-Up |
| 5 | [Spaghetti Untangler](./05-spaghetti-untangler) | 2 | 250 | Easy |
| 6 | [Test Factory](./06-test-factory) | 2 | 200 | Easy |
| 7 | [Spec Builder + Build](./07-spec-builder) | 2 | 500 | Easy |
| 8 | [AI Menu Assistant](./08-ai-menu-assistant) | 3 | 300 | Medium |
| 9 | [Smart Feedback Sorter](./09-smart-feedback-sorter) | 3 | 250 | Medium |
| 10 | [Context is King](./10-context-is-king) | 3 | 350 | Medium |
| 11 | [Prompt Craftsman](./11-prompt-craftsman) | 4 | 200 | Hard |
| 12 | [Full Stack Sprint](./12-full-stack-sprint) | 4 | 500 | Hard |
| 13 | [The Onion Bug](./13-onion-bug) | 4 | 600 | Hard |
| 14 | [The Fuzz Gauntlet](./14-fuzz-gauntlet) | 5 | 600 | Expert |
| 15 | [The Undocumented API](./15-undocumented-api) | 5 | 500 | Expert |
| 16 | [The Agent Maze](./16-agent-maze) | 5 | 1000 | Expert |
| 17 | [The Gauntlet Sprint](./17-gauntlet-sprint) | 6 | 1000 | Master |
| 18 | TBD | 6 | TBD | Master |
| 19 | [Roy G Biv](./19-roy-g-biv) | 6 | 1000 | Master |
| 20 | [A Prison of My Own Design](./20-prison-break) | 7 | 2000 | Legendary |

## Tier Progression

Challenges unlock progressively as you prove your skills:

| Tier | Name | Challenges | Unlock Rule |
|------|------|-----------|-------------|
| 1 | Warm-Up | 1–4 | Available immediately |
| 2 | Easy | 5–7 | Complete 2+ Tier 1 challenges |
| 3 | Medium | 8–10 | Complete 2+ Tier 2 challenges |
| 4 | Hard | 11–13 | Complete 2+ Tier 3 challenges |
| 5 | Expert | 14–16 | Complete 2+ Tier 4 challenges |
| 6 | Master | 17–19 | Complete 2+ Tier 5 challenges |
| 7 | Legendary | 20 | Complete all Tier 6 challenges |

## Recommended Order

1. **Start with the warm-ups** (Tier 1) to get comfortable
2. **Pick challenges that interest you** within each unlocked tier
3. **Higher tiers = harder** but more rewarding
4. **Nobody finishes everything** — focus on quality over quantity
5. **Tier 7 is the endgame** — only one team can claim it first

## Prerequisites

- Python 3.11+
- pip
- An AI coding assistant ([Cursor](https://cursor.sh), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), GitHub Copilot, etc.)
- For challenges 8 & 9: `ANTHROPIC_API_KEY` environment variable (provided by facilitator)
