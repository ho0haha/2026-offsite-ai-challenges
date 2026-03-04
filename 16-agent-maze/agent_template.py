"""
The Agent Maze - Agent Template
================================
Starter template for building an autonomous maze-navigating agent.
Your agent must navigate a randomized maze, solve diverse puzzles,
and collect all 10 tokens to retrieve the flag.

Usage:
    1. Start the maze server: python maze_server.py
    2. Implement solve_puzzle() and navigation logic below
    3. Run: python agent_template.py

Environment:
    - ctf_helper.ask_llm() provides Claude Haiku via the CTF server (no API key needed)
    - MAZE_SERVER_URL defaults to http://localhost:5000
"""

import json
import logging
import os
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAZE_SERVER_URL = os.environ.get("MAZE_SERVER_URL", "http://localhost:5000")
# LLM access: use ctf_helper.ask_llm() for Claude Haiku via the CTF server
import sys as _sys
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ctf_helper import ask_llm

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("agent_run.log"),
    ],
)
logger = logging.getLogger("maze_agent")

# ---------------------------------------------------------------------------
# HTTP Client
# ---------------------------------------------------------------------------


class MazeClient:
    """HTTP client for interacting with the Maze Server API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session_id = None

    def start(self) -> dict:
        """Start a new maze session."""
        resp = requests.get(f"{self.base_url}/api/maze/start")
        resp.raise_for_status()
        data = resp.json()
        self.session_id = data["session_id"]
        logger.info("Session started: %s", self.session_id)
        return data

    def action(self, action: str, data: dict | None = None) -> dict:
        """Perform an action in the maze (solve, move, look)."""
        payload = {
            "session_id": self.session_id,
            "action": action,
        }
        if data:
            payload["data"] = data
        resp = requests.post(f"{self.base_url}/api/maze/action", json=payload)
        resp.raise_for_status()
        return resp.json()

    def solve(self, answer) -> dict:
        """Submit an answer to the current room's puzzle."""
        return self.action("solve", {"answer": answer})

    def move(self, exit_id: str) -> dict:
        """Move to an adjacent room."""
        return self.action("move", {"exit": exit_id})

    def look(self) -> dict:
        """Re-examine the current room."""
        return self.action("look")

    def status(self) -> dict:
        """Get the current session status."""
        resp = requests.get(
            f"{self.base_url}/api/maze/status",
            params={"session_id": self.session_id},
        )
        resp.raise_for_status()
        return resp.json()

    def get_map(self) -> dict:
        """Get the map of visited rooms."""
        resp = requests.get(
            f"{self.base_url}/api/maze/map",
            params={"session_id": self.session_id},
        )
        resp.raise_for_status()
        return resp.json()

    def submit(self) -> dict:
        """Submit collected tokens to claim the flag."""
        resp = requests.post(
            f"{self.base_url}/api/maze/submit",
            json={"session_id": self.session_id},
        )
        resp.raise_for_status()
        return resp.json()

    def fetch_room_secret(self, room_id: str) -> dict:
        """Fetch the secret for an API puzzle room."""
        resp = requests.get(
            f"{self.base_url}/api/maze/room_secret",
            params={"room_id": room_id, "session_id": self.session_id},
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Puzzle Solver
# ---------------------------------------------------------------------------


def solve_puzzle(room: dict, agent_state: dict) -> any:
    """
    Solve the puzzle in the current room.

    Args:
        room: The room data from the API, including:
            - room["puzzle"]["type"]: Puzzle type (math, cipher, logic_gate, etc.)
            - room["puzzle"]["subtype"]: Specific variant
            - room["puzzle"]["question"]: The puzzle prompt
            - room["puzzle"] may contain additional fields depending on type
        agent_state: Your agent's state dict for tracking visited rooms,
                     collected variables, etc.

    Returns:
        The answer to submit, or None if unable to solve.

    Puzzle types you need to handle:
        - math: Solve equations (linear, quadratic, systems, variable references)
        - cipher: Decode messages (Caesar, XOR, base64)
        - logic_gate: Determine missing truth table output
        - pattern: Continue a number sequence
        - graph: Find shortest path in weighted graph
        - api: Fetch a secret from a sub-endpoint
        - memory: Answer questions about previously visited rooms
        - trap: Detect and correct false information
        - ambiguity: Choose correct exit using info from previous rooms
        - boss: Multi-step puzzle combining multiple types

    TIP: You can use ask_llm() for reasoning about complex puzzles.
    Consider sending the puzzle data to the LLM and parsing the response.
    """
    puzzle = room.get("puzzle", {})
    puzzle_type = puzzle.get("type", "unknown")

    logger.info("Puzzle type: %s (subtype: %s)", puzzle_type, puzzle.get("subtype"))
    logger.info("Question: %s", puzzle.get("question", "N/A"))

    # TODO: Implement puzzle-solving logic for each type
    # Example structure:
    #
    # if puzzle_type == "math":
    #     return solve_math(puzzle, agent_state)
    # elif puzzle_type == "cipher":
    #     return solve_cipher(puzzle, agent_state)
    # elif puzzle_type == "logic_gate":
    #     return solve_logic_gate(puzzle, agent_state)
    # elif puzzle_type == "pattern":
    #     return solve_pattern(puzzle, agent_state)
    # elif puzzle_type == "graph":
    #     return solve_graph(puzzle, agent_state)
    # elif puzzle_type == "api":
    #     return solve_api(puzzle, agent_state)
    # elif puzzle_type == "memory":
    #     return solve_memory(puzzle, agent_state)
    # elif puzzle_type == "trap":
    #     return solve_trap(puzzle, agent_state)
    # elif puzzle_type == "ambiguity":
    #     return solve_ambiguity(puzzle, agent_state)
    # elif puzzle_type == "boss":
    #     return solve_boss(puzzle, agent_state)

    return None


# ---------------------------------------------------------------------------
# Navigation Strategy
# ---------------------------------------------------------------------------


def choose_next_room(room: dict, agent_state: dict) -> str | None:
    """
    Decide which exit to take from the current room.

    Args:
        room: Current room data with exits list.
        agent_state: Agent's internal state tracking visited rooms, etc.

    Returns:
        The room_id of the exit to take, or None if nowhere to go.
    """
    exits = room.get("exits", [])
    visited = agent_state.get("visited_rooms", set())

    # Prefer unvisited rooms
    unvisited = [e for e in exits if e not in visited]
    if unvisited:
        return unvisited[0]

    # If all exits visited, backtrack (pick any)
    if exits:
        return exits[0]

    return None


# ---------------------------------------------------------------------------
# Main Agent Loop
# ---------------------------------------------------------------------------


def run_agent():
    """Main agent execution loop."""
    client = MazeClient(MAZE_SERVER_URL)

    # Agent state for tracking progress across rooms
    agent_state = {
        "visited_rooms": set(),
        "room_history": [],       # list of (room_id, room_data) tuples
        "room_variables": {},     # room_id -> variables learned from solving
        "tokens_collected": [],
        "solved_rooms": set(),
    }

    # --- Start the maze ---
    logger.info("Starting maze session...")
    start_data = client.start()
    logger.info("Message: %s", start_data.get("message"))

    current_room = start_data["room"]
    agent_state["visited_rooms"].add(current_room["id"])
    agent_state["room_history"].append((current_room["id"], current_room))

    max_iterations = 200  # safety limit
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        room_id = current_room["id"]
        logger.info("--- Iteration %d | Room: %s ---", iteration, room_id)

        # Check if already solved
        if room_id not in agent_state["solved_rooms"]:
            # Attempt to solve the puzzle
            answer = solve_puzzle(current_room, agent_state)

            if answer is not None:
                logger.info("Submitting answer: %s", answer)
                result = client.solve(answer)
                logger.info("Result: %s", result.get("message"))

                if result.get("correct"):
                    agent_state["solved_rooms"].add(room_id)

                    if result.get("token_collected"):
                        agent_state["tokens_collected"].append(
                            result["token_collected"]
                        )
                        logger.info(
                            "Token collected! (%d/%d)",
                            len(agent_state["tokens_collected"]),
                            result.get("tokens_required", 10),
                        )

                    # Check if we have all tokens
                    if result.get("tokens_collected", 0) >= result.get(
                        "tokens_required", 10
                    ):
                        logger.info("All tokens collected! Submitting...")
                        submit_result = client.submit()
                        if submit_result.get("success"):
                            logger.info("FLAG: %s", submit_result.get("flag"))
                            logger.info("Stats: %s", submit_result.get("stats"))
                            return submit_result
                        else:
                            logger.warning(
                                "Submit failed: %s", submit_result.get("error")
                            )
                else:
                    logger.warning("Wrong answer for room %s", room_id)
                    # TODO: Implement retry logic or ask Claude for help
            else:
                logger.warning("Could not solve puzzle in room %s", room_id)
                # TODO: Implement fallback strategy

        # Navigate to next room
        if room_id in agent_state["solved_rooms"]:
            next_room_id = choose_next_room(current_room, agent_state)
            if next_room_id:
                logger.info("Moving to: %s", next_room_id)
                move_result = client.move(next_room_id)
                current_room = move_result["room"]
                agent_state["visited_rooms"].add(current_room["id"])
                agent_state["room_history"].append(
                    (current_room["id"], current_room)
                )
            else:
                logger.warning("No exits available. Stuck!")
                break
        else:
            # Can't move without solving. Check status and maybe retry.
            status = client.status()
            logger.info("Status: %s", json.dumps(status, indent=2))
            if status.get("api_calls_remaining", 0) <= 0:
                logger.error("Out of API calls!")
                break
            # For now, break to avoid infinite loop on unsolved rooms
            logger.error("Unable to solve room %s. Stopping.", room_id)
            break

    logger.warning("Agent loop ended without completing the maze.")
    final_status = client.status()
    logger.info("Final status: %s", json.dumps(final_status, indent=2))
    return final_status


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("=== The Agent Maze - Autonomous Agent ===")
    logger.info("Server: %s", MAZE_SERVER_URL)
    logger.info("LLM proxy available via ctf_helper.ask_llm()")

    result = run_agent()
    print("\n=== Final Result ===")
    print(json.dumps(result, indent=2))
