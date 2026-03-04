# Challenge 16: The Agent Maze

**Tier 5 | 1000 Points**

## Overview

Build an autonomous AI agent that navigates a randomized puzzle maze, solves 10 distinct puzzle types, and collects all tokens to retrieve the flag. Your agent must handle any maze layout -- the maze regenerates with new puzzles and structure on every attempt.

## The Challenge

A maze server generates a labyrinth of 20 rooms. Hidden across the maze are 10 collectible tokens, each guarded by a unique puzzle. Your agent must:

1. **Navigate** the maze by choosing exits and moving between rooms
2. **Solve** puzzles of 10 different types to unlock rooms and collect tokens
3. **Remember** information from earlier rooms (some puzzles reference past data)
4. **Detect traps** where the maze provides plausible but incorrect information
5. **Collect all 10 tokens** and submit them to claim the flag

## Rules

- You write your agent once and deploy it. **You cannot modify the agent mid-run.**
- Each session has a **10-minute time limit** and a **100 API call limit**.
- If your agent fails, a new session generates a **completely different maze** with new puzzles.
- The maze is deterministic within a session (same actions produce same results).

## Puzzle Types

Your agent will encounter these puzzle types in randomized order:

| # | Type | Description |
|---|------|-------------|
| 1 | **Math** | Solve equations -- may reference variables from earlier rooms |
| 2 | **Cipher** | Decode messages (Caesar, XOR, base64 variants) |
| 3 | **Logic Gate** | Determine missing output from a truth table |
| 4 | **Pattern** | Continue a number sequence |
| 5 | **Graph** | Find shortest path in a weighted graph |
| 6 | **API** | Fetch a secret from a sub-endpoint described in the room |
| 7 | **Memory** | Answer questions about rooms visited 3+ steps ago |
| 8 | **Trap** | Detect and correct intentionally wrong information |
| 9 | **Ambiguity** | Choose the correct exit using info from 2 previous rooms |
| 10 | **Boss** | Multi-step puzzle combining 3+ types |

## Maze Properties

- **20 rooms** per maze, interconnected with multiple paths
- **10 rooms** contain collectible tokens
- **5 dead ends** that branch off the main path
- **3 trap rooms** with deliberately misleading data
- **2 ambiguity rooms** with multiple valid-looking exits

## API Reference

### `GET /api/maze/start`
Start a new session. Returns session ID and the first room.

### `POST /api/maze/action`
Perform an action. Body:
```json
{
  "session_id": "...",
  "action": "solve|move|look",
  "data": {"answer": "..."} or {"exit": "room_id"}
}
```

### `GET /api/maze/status?session_id=...`
Get current position, collected tokens, move count, and remaining resources.

### `POST /api/maze/submit`
Submit when all 10 tokens are collected. Body:
```json
{"session_id": "..."}
```

### `GET /api/maze/map?session_id=...`
View connectivity of visited rooms only.

### `GET /api/maze/room_secret?room_id=...&session_id=...`
Fetch the secret for API-type puzzle rooms.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the maze server:
   ```bash
   python maze_server.py
   ```

3. Edit `agent_template.py` -- implement `solve_puzzle()` and navigation logic.

4. Run your agent:
   ```bash
   python agent_template.py
   ```

## Tips

- **Log everything.** Your agent should record every room visited, every puzzle encountered, and every answer attempted. You will need this data for Memory puzzles.
- **Use the LLM proxy.** `ctf_helper.ask_llm()` gives you Claude Haiku with no API key needed. Sending puzzle data to the LLM can help with complex reasoning. You can also use any LLM you have access to.
- **Handle failures gracefully.** If a puzzle answer is wrong, your agent should retry or move on, not crash.
- **Budget your API calls.** You have 100 calls for 20 rooms. That is roughly 5 calls per room (solve attempts + navigation).
- **Test incrementally.** Get your agent solving one puzzle type at a time before trying the full maze.

## Flag Format

```
CTF{...}
```
