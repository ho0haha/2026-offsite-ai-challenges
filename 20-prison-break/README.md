# Challenge 20: A Prison of My Own Design

**Tier 7 — Legendary (2000 pts)**

*The final challenge. No local files. No test suite. Just you, your AI, and a text-based prison.*

## Overview

This is a live, server-hosted text adventure game. You must navigate a prison, solve puzzles, interact with NPCs, and escape — all within 120 turns.

The game runs entirely on the CTF server. You interact with it through API calls.

## Getting Started

### 1. Activate the Modem

Before the prison endpoints become visible, you must discover and activate the modem on the CTF dashboard. Look for it.

### 2. Start a Session

```bash
curl -X POST "$CTF_SERVER/api/prison/start" \
  -H "Authorization: Bearer $CTF_TOKEN" \
  -H "Content-Type: application/json"
```

Returns a `sessionId` and the opening narrative.

### 3. Send Commands

```bash
curl -X POST "$CTF_SERVER/api/prison/command" \
  -H "Authorization: Bearer $CTF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId": "<your-session-id>", "command": "look"}'
```

### 4. Check Status

```bash
curl "$CTF_SERVER/api/prison/status" \
  -H "Authorization: Bearer $CTF_TOKEN"
```

## Game Rules

- **120 turns** until lights-out. After that, it's over.
- **3-second cooldown** between commands.
- **Inventory limit** of 6 items.
- Some commands are **free** (don't consume a turn): `help`, `inventory`, `look`, `examine`, `read`, `listen`, `smell`
- All other commands cost **1 turn**.
- Guards patrol on a schedule. Get caught where you shouldn't be and face consequences.
- There are multiple NPCs. How you treat them matters.
- There are multiple paths, but only one way out.

## Commands

| Command | Example | Cost |
|---------|---------|------|
| GO | `go north`, `n`, `go up` | 1 turn |
| LOOK | `look` | free |
| EXAMINE | `examine bed`, `examine wall closely` | free |
| SEARCH | `search room`, `search desk` | 1 turn |
| TAKE | `take key`, `grab note` | 1 turn |
| DROP | `drop blanket` | 1 turn |
| USE | `use key on door` | 1 turn |
| COMBINE | `combine wire and tape` | 1 turn |
| READ | `read note` | free |
| TALK | `talk to sal` | 1 turn |
| ASK | `ask marcus about tunnel` | 1 turn |
| GIVE | `give cigarettes to sal` | 1 turn |
| LISTEN | `listen` | free |
| INVENTORY | `inventory`, `i` | free |
| HELP | `help` | free |

Additional verbs: `knock`, `confess`, `flatter`, `whisper`, `threaten`, `turn`, `open`, `smell`

## Hints

1. Talk to everyone. Trust is earned.
2. Not everything is where you'd expect it.
3. Some puzzles require items from different parts of the prison.
4. If you're stuck, `examine` everything `closely`.
5. The clock is always ticking.
6. Restarting is allowed: `POST /api/prison/start?restart=true`

## Submission

The flag is automatically submitted when you escape. You'll see it in the final response.

## Requirements

No local dependencies. This challenge is played entirely via the CTF server API.

You will need:
- Your `CTF_SERVER` URL and `CTF_TOKEN` (from `.env`)
- An HTTP client (`curl`, Python `requests`, or your AI assistant)
- Patience, strategy, and 120 well-chosen moves
