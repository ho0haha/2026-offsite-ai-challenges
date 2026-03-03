"""
The Agent Maze - CTF Challenge Server
======================================
A randomized puzzle maze that an autonomous AI agent must navigate.
Each session generates a unique maze with 20 rooms, 10 collectible tokens,
and 10 distinct puzzle types. Sessions expire after 10 minutes or 100 API calls.

Run: python maze_server.py
"""

import hashlib
import heapq
import json
import random
import string
import struct
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FLAG = "CTF{maze_agent_autonomous_navigator}"

SESSION_TIMEOUT_SECONDS = 600  # 10 minutes
MAX_API_CALLS = 100
NUM_ROOMS = 20
NUM_TOKEN_ROOMS = 10
NUM_DEAD_ENDS = 5
NUM_TRAP_ROOMS = 3
NUM_AMBIGUITY_ROOMS = 2

# ---------------------------------------------------------------------------
# Puzzle Type Enumeration
# ---------------------------------------------------------------------------


class PuzzleType(str, Enum):
    MATH = "math"
    CIPHER = "cipher"
    LOGIC_GATE = "logic_gate"
    PATTERN = "pattern"
    GRAPH = "graph"
    API = "api"
    MEMORY = "memory"
    TRAP = "trap"
    AMBIGUITY = "ambiguity"
    BOSS = "boss"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class Room:
    id: str
    name: str
    description: str
    puzzle_type: PuzzleType
    puzzle_data: dict
    answer: Any
    exits: list  # list of room ids
    has_token: bool
    token_id: str | None = None
    is_dead_end: bool = False
    is_trap: bool = False
    is_ambiguity: bool = False
    trap_info: dict = field(default_factory=dict)
    ambiguity_info: dict = field(default_factory=dict)
    variables: dict = field(default_factory=dict)  # variables set when solving


@dataclass
class Session:
    session_id: str
    seed: int
    rooms: dict  # room_id -> Room
    room_order: list  # ordered list of room ids (the "intended" path)
    start_room: str
    current_room: str
    collected_tokens: list
    visited_rooms: list  # list of (room_id, timestamp) in order visited
    move_count: int
    api_call_count: int
    created_at: float
    solved_rooms: set = field(default_factory=set)
    room_variables: dict = field(default_factory=dict)  # room_id -> variables
    completed: bool = False


# ---------------------------------------------------------------------------
# Session Store (in-memory)
# ---------------------------------------------------------------------------

sessions: dict[str, Session] = {}

# ---------------------------------------------------------------------------
# Helper: Seeded Random
# ---------------------------------------------------------------------------


def seeded_random(seed: int) -> random.Random:
    """Return a deterministic Random instance for a given seed."""
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Puzzle Generators
# ---------------------------------------------------------------------------


def generate_math_puzzle(rng: random.Random, room_id: str, session_vars: dict) -> tuple[dict, Any, dict]:
    """
    Generate a math puzzle. May reference variables from previously visited rooms.
    Returns (puzzle_data, answer, variables_set).
    """
    # Pick a style
    style = rng.choice(["linear", "quadratic", "system", "variable_reference"])

    if style == "linear":
        a = rng.randint(2, 15)
        b = rng.randint(1, 50)
        x = rng.randint(1, 20)
        result = a * x + b
        puzzle = {
            "type": "math",
            "subtype": "linear_equation",
            "question": f"Solve for x: {a} * x + {b} = {result}",
            "hint": "Isolate x by subtracting b and dividing by a.",
        }
        variables = {"x_value": x}
        return puzzle, x, variables

    elif style == "quadratic":
        # Simple: (x - r1)(x - r2) = 0, ask for positive root
        r1 = rng.randint(1, 12)
        r2 = rng.randint(1, 12)
        while r2 == r1:
            r2 = rng.randint(1, 12)
        # Expanded: x^2 - (r1+r2)x + r1*r2 = 0
        b_coeff = -(r1 + r2)
        c_coeff = r1 * r2
        b_str = f"+ {-b_coeff}" if b_coeff < 0 else f"- {b_coeff}"
        puzzle = {
            "type": "math",
            "subtype": "quadratic_equation",
            "question": f"Solve: x^2 {b_str}x + {c_coeff} = 0. Provide the LARGER root.",
            "hint": "Factor or use the quadratic formula.",
        }
        answer = max(r1, r2)
        variables = {"larger_root": answer, "smaller_root": min(r1, r2)}
        return puzzle, answer, variables

    elif style == "system":
        # 2-variable system: ax + by = c, dx + ey = f
        x_val = rng.randint(1, 10)
        y_val = rng.randint(1, 10)
        a = rng.randint(1, 5)
        b = rng.randint(1, 5)
        d = rng.randint(1, 5)
        e = rng.randint(1, 5)
        while a * e == b * d:  # ensure non-degenerate
            e = rng.randint(1, 5)
        c = a * x_val + b * y_val
        f_val = d * x_val + e * y_val
        puzzle = {
            "type": "math",
            "subtype": "system_of_equations",
            "question": (
                f"Solve the system:\n"
                f"  {a}x + {b}y = {c}\n"
                f"  {d}x + {e}y = {f_val}\n"
                f"Provide the value of x + y."
            ),
            "hint": "Use substitution or elimination.",
        }
        answer = x_val + y_val
        variables = {"x": x_val, "y": y_val}
        return puzzle, answer, variables

    else:  # variable_reference
        # Reference a variable from a previous room if available
        if session_vars:
            ref_room_id = rng.choice(list(session_vars.keys()))
            ref_vars = session_vars[ref_room_id]
            if ref_vars:
                var_name = rng.choice(list(ref_vars.keys()))
                var_val = ref_vars[var_name]
                if isinstance(var_val, (int, float)):
                    multiplier = rng.randint(2, 7)
                    offset = rng.randint(1, 20)
                    answer = var_val * multiplier + offset
                    puzzle = {
                        "type": "math",
                        "subtype": "variable_reference",
                        "question": (
                            f"Recall the value '{var_name}' from room '{ref_room_id}'. "
                            f"Compute: {var_name} * {multiplier} + {offset}."
                        ),
                        "referenced_room": ref_room_id,
                        "referenced_variable": var_name,
                        "hint": f"You need the value of '{var_name}' from a previous room.",
                    }
                    variables = {"computed_value": answer}
                    return puzzle, answer, variables

        # Fallback to simple arithmetic
        a = rng.randint(10, 99)
        b = rng.randint(10, 99)
        answer = a + b
        puzzle = {
            "type": "math",
            "subtype": "addition",
            "question": f"Compute: {a} + {b}",
            "hint": "Simple addition.",
        }
        variables = {"sum_value": answer}
        return puzzle, answer, variables


def generate_cipher_puzzle(rng: random.Random, room_id: str, _session_vars: dict) -> tuple[dict, Any, dict]:
    """Generate a cipher decoding puzzle (Caesar, XOR, base64)."""
    import base64

    subtype = rng.choice(["caesar", "xor", "base64", "reverse_caesar"])

    # Generate a random word/phrase as the plaintext
    words = [
        "token", "secret", "alpha", "bravo", "charlie", "delta", "echo",
        "foxtrot", "gamma", "hotel", "india", "juliet", "kilo", "lima",
        "maze", "navigate", "oracle", "puzzle", "quest", "riddle",
        "sphinx", "cipher", "vector", "zenith", "beacon", "cryptic",
    ]
    plain = rng.choice(words)

    if subtype == "caesar":
        shift = rng.randint(1, 25)
        encoded = ""
        for ch in plain:
            if ch.isalpha():
                base = ord("a") if ch.islower() else ord("A")
                encoded += chr((ord(ch) - base + shift) % 26 + base)
            else:
                encoded += ch
        puzzle = {
            "type": "cipher",
            "subtype": "caesar",
            "question": f"Decode this Caesar cipher (shift={shift}): '{encoded}'",
            "encoded": encoded,
            "shift": shift,
            "hint": "Shift each letter back by the given amount.",
        }
        variables = {"decoded_word": plain}
        return puzzle, plain, variables

    elif subtype == "reverse_caesar":
        shift = rng.randint(1, 25)
        encoded = ""
        for ch in plain:
            if ch.isalpha():
                base = ord("a") if ch.islower() else ord("A")
                encoded += chr((ord(ch) - base - shift) % 26 + base)
            else:
                encoded += ch
        puzzle = {
            "type": "cipher",
            "subtype": "reverse_caesar",
            "question": (
                f"This text was Caesar-shifted backwards by {shift}: '{encoded}'. "
                f"What is the original plaintext?"
            ),
            "encoded": encoded,
            "shift": shift,
            "hint": "Shift each letter forward by the given amount.",
        }
        variables = {"decoded_word": plain}
        return puzzle, plain, variables

    elif subtype == "xor":
        key = rng.randint(1, 255)
        encoded_bytes = bytes([b ^ key for b in plain.encode()])
        encoded_hex = encoded_bytes.hex()
        puzzle = {
            "type": "cipher",
            "subtype": "xor",
            "question": (
                f"XOR-decode this hex string with key {key} (decimal): '{encoded_hex}'"
            ),
            "encoded_hex": encoded_hex,
            "key": key,
            "hint": "XOR each byte of the hex-decoded data with the key byte.",
        }
        variables = {"decoded_word": plain}
        return puzzle, plain, variables

    else:  # base64
        encoded = base64.b64encode(plain.encode()).decode()
        puzzle = {
            "type": "cipher",
            "subtype": "base64",
            "question": f"Base64-decode this string: '{encoded}'",
            "encoded": encoded,
            "hint": "Standard base64 decoding.",
        }
        variables = {"decoded_word": plain}
        return puzzle, plain, variables


def generate_logic_gate_puzzle(rng: random.Random, room_id: str, _session_vars: dict) -> tuple[dict, Any, dict]:
    """Generate a logic gate / boolean truth table puzzle."""
    # Pick gate types
    gate_types = ["AND", "OR", "XOR", "NAND", "NOR"]
    gate = rng.choice(gate_types)

    # Generate a truth table with one missing entry
    inputs_list = [(0, 0), (0, 1), (1, 0), (1, 1)]

    def evaluate_gate(g, a, b):
        if g == "AND":
            return int(a and b)
        elif g == "OR":
            return int(a or b)
        elif g == "XOR":
            return int(a ^ b)
        elif g == "NAND":
            return int(not (a and b))
        elif g == "NOR":
            return int(not (a or b))
        return 0

    truth_table = []
    for a_val, b_val in inputs_list:
        truth_table.append({
            "A": a_val,
            "B": b_val,
            "output": evaluate_gate(gate, a_val, b_val),
        })

    # Hide one entry
    hidden_idx = rng.randint(0, 3)
    answer = truth_table[hidden_idx]["output"]
    display_table = []
    for i, row in enumerate(truth_table):
        if i == hidden_idx:
            display_table.append({"A": row["A"], "B": row["B"], "output": "?"})
        else:
            display_table.append(row)

    puzzle = {
        "type": "logic_gate",
        "subtype": gate,
        "question": (
            f"Given this truth table for an unknown gate, determine the missing output.\n"
            f"Truth table: {json.dumps(display_table)}\n"
            f"What is the missing output value (0 or 1)?"
        ),
        "truth_table": display_table,
        "hint": f"Identify the logic gate from the known outputs, then compute the missing one.",
    }
    variables = {"gate_type": gate, "missing_output": answer}
    return puzzle, answer, variables


def generate_pattern_puzzle(rng: random.Random, room_id: str, _session_vars: dict) -> tuple[dict, Any, dict]:
    """Generate a sequence continuation puzzle."""
    pattern_type = rng.choice([
        "arithmetic", "geometric", "fibonacci_like", "triangular",
        "powers", "alternating",
    ])

    if pattern_type == "arithmetic":
        start = rng.randint(1, 20)
        diff = rng.randint(2, 10)
        seq = [start + i * diff for i in range(6)]
        answer = seq[-1]
        shown = seq[:-1]

    elif pattern_type == "geometric":
        start = rng.randint(1, 5)
        ratio = rng.randint(2, 4)
        seq = [start * (ratio ** i) for i in range(6)]
        answer = seq[-1]
        shown = seq[:-1]

    elif pattern_type == "fibonacci_like":
        a = rng.randint(1, 5)
        b = rng.randint(1, 5)
        seq = [a, b]
        for _ in range(5):
            seq.append(seq[-1] + seq[-2])
        answer = seq[6]
        shown = seq[:6]

    elif pattern_type == "triangular":
        # Triangular numbers: n*(n+1)/2
        offset = rng.randint(0, 5)
        seq = [(n + offset) * (n + offset + 1) // 2 for n in range(1, 8)]
        answer = seq[-1]
        shown = seq[:-1]

    elif pattern_type == "powers":
        base = rng.randint(2, 4)
        seq = [base ** i for i in range(1, 8)]
        answer = seq[-1]
        shown = seq[:-1]

    else:  # alternating
        a_diff = rng.randint(1, 5)
        b_diff = rng.randint(1, 5)
        a_start = rng.randint(1, 10)
        b_start = rng.randint(1, 10)
        seq = []
        for i in range(8):
            if i % 2 == 0:
                seq.append(a_start + (i // 2) * a_diff)
            else:
                seq.append(b_start + (i // 2) * b_diff)
        answer = seq[-1]
        shown = seq[:-1]

    puzzle = {
        "type": "pattern",
        "subtype": pattern_type,
        "question": f"Continue the sequence: {shown}. What is the next number?",
        "sequence": shown,
        "hint": f"Look for a {pattern_type} pattern.",
    }
    variables = {"next_in_sequence": answer}
    return puzzle, answer, variables


def generate_graph_puzzle(rng: random.Random, room_id: str, _session_vars: dict) -> tuple[dict, Any, dict]:
    """Generate a shortest path in weighted graph puzzle."""
    # Create a small graph with 5-7 nodes
    num_nodes = rng.randint(5, 7)
    node_names = [chr(ord("A") + i) for i in range(num_nodes)]

    # Generate edges (ensure connected)
    edges = []
    # First create a spanning path
    shuffled = list(node_names)
    rng.shuffle(shuffled)
    for i in range(len(shuffled) - 1):
        w = rng.randint(1, 15)
        edges.append((shuffled[i], shuffled[i + 1], w))

    # Add some extra edges
    num_extra = rng.randint(2, 5)
    for _ in range(num_extra):
        a = rng.choice(node_names)
        b = rng.choice(node_names)
        if a != b:
            w = rng.randint(1, 15)
            edges.append((a, b, w))

    # Pick source and destination
    source = rng.choice(node_names)
    dest = rng.choice(node_names)
    while dest == source:
        dest = rng.choice(node_names)

    # Compute shortest path using Dijkstra
    adjacency: dict[str, list[tuple[str, int]]] = {n: [] for n in node_names}
    for a, b, w in edges:
        adjacency[a].append((b, w))
        adjacency[b].append((a, w))

    dist: dict[str, float] = {n: float("inf") for n in node_names}
    dist[source] = 0
    pq = [(0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in adjacency[u]:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))

    answer = int(dist[dest]) if dist[dest] != float("inf") else -1

    edge_list = [{"from": a, "to": b, "weight": w} for a, b, w in edges]

    puzzle = {
        "type": "graph",
        "subtype": "shortest_path",
        "question": (
            f"Find the shortest path distance from '{source}' to '{dest}' "
            f"in this undirected weighted graph.\n"
            f"Edges: {json.dumps(edge_list)}\n"
            f"Provide the total distance (integer). If unreachable, answer -1."
        ),
        "edges": edge_list,
        "source": source,
        "destination": dest,
        "nodes": node_names,
        "hint": "Use Dijkstra's algorithm on the undirected graph.",
    }
    variables = {"shortest_distance": answer}
    return puzzle, answer, variables


def generate_api_puzzle(rng: random.Random, room_id: str, _session_vars: dict) -> tuple[dict, Any, dict]:
    """
    Generate an API sub-request puzzle. The agent must call a specific
    endpoint described in the room to get a value, then submit it.
    """
    # We'll generate a secret code and embed it at an endpoint
    secret_code = "".join(rng.choices(string.ascii_uppercase + string.digits, k=8))

    puzzle = {
        "type": "api",
        "subtype": "fetch_secret",
        "question": (
            f"This room requires you to fetch a secret from an API endpoint.\n"
            f"Make a GET request to: /api/maze/room_secret?room_id={room_id}\n"
            f"The response will contain a 'secret_code' field. Submit that code as your answer."
        ),
        "endpoint": f"/api/maze/room_secret?room_id={room_id}",
        "hint": "Fetch the endpoint described and return the secret_code value.",
    }
    variables = {"secret_code": secret_code}
    return puzzle, secret_code, variables


def generate_memory_puzzle(
    rng: random.Random,
    room_id: str,
    _session_vars: dict,
    visited_rooms: list[str] | None = None,
    all_rooms: dict | None = None,
) -> tuple[dict, Any, dict]:
    """
    Generate a memory puzzle that references a room visited 3+ rooms ago.
    If not enough history, fall back to a simpler memory question.
    """
    if visited_rooms and all_rooms and len(visited_rooms) >= 3:
        # Reference a room visited at least 3 steps ago
        target_idx = rng.randint(0, max(0, len(visited_rooms) - 3))
        target_room_id = visited_rooms[target_idx]
        target_room = all_rooms.get(target_room_id)

        if target_room:
            question_type = rng.choice(["name", "puzzle_type", "token"])
            if question_type == "name":
                answer = target_room.name
                puzzle = {
                    "type": "memory",
                    "subtype": "recall_room_name",
                    "question": (
                        f"Recall the room you visited as your #{target_idx + 1} room. "
                        f"What was its name?"
                    ),
                    "target_visit_number": target_idx + 1,
                    "hint": "Check your visit history / logs.",
                }
            elif question_type == "puzzle_type":
                answer = target_room.puzzle_type.value
                puzzle = {
                    "type": "memory",
                    "subtype": "recall_puzzle_type",
                    "question": (
                        f"What type of puzzle was in the room you visited as your "
                        f"#{target_idx + 1} room?"
                    ),
                    "target_visit_number": target_idx + 1,
                    "hint": "Recall the puzzle type (e.g. math, cipher, pattern, etc.).",
                }
            else:
                had_token = target_room.has_token
                answer = "yes" if had_token else "no"
                puzzle = {
                    "type": "memory",
                    "subtype": "recall_token",
                    "question": (
                        f"Did the room you visited as your #{target_idx + 1} room "
                        f"contain a token? Answer 'yes' or 'no'."
                    ),
                    "target_visit_number": target_idx + 1,
                    "hint": "Check whether that room had a collectible token.",
                }
            variables = {"memory_answer": answer}
            return puzzle, answer, variables

    # Fallback: simple memory question
    secret_number = rng.randint(100, 999)
    answer = str(secret_number)
    puzzle = {
        "type": "memory",
        "subtype": "remember_number",
        "question": (
            f"Remember this number: {secret_number}. "
            f"You will need it later. For now, submit it back as your answer."
        ),
        "number_to_remember": secret_number,
        "hint": "Just return the number shown.",
    }
    variables = {"remembered_number": secret_number}
    return puzzle, answer, variables


def generate_trap_puzzle(rng: random.Random, room_id: str, _session_vars: dict) -> tuple[dict, Any, dict]:
    """
    Generate a trap room. The room provides plausible but wrong data.
    The agent must detect the inconsistency.
    """
    trap_style = rng.choice(["wrong_sum", "off_by_one", "contradictory_clue"])

    if trap_style == "wrong_sum":
        numbers = [rng.randint(10, 50) for _ in range(5)]
        correct_sum = sum(numbers)
        wrong_sum = correct_sum + rng.choice([-3, -2, -1, 1, 2, 3])
        puzzle = {
            "type": "trap",
            "subtype": "wrong_sum",
            "question": (
                f"The room inscription says the sum of {numbers} is {wrong_sum}. "
                f"Is this correct? If not, provide the CORRECT sum."
            ),
            "claimed_numbers": numbers,
            "claimed_sum": wrong_sum,
            "hint": "Verify the arithmetic yourself. Don't trust the room's claim.",
        }
        answer = correct_sum
        variables = {"correct_sum": correct_sum, "was_trap": True}
        return puzzle, answer, variables

    elif trap_style == "off_by_one":
        sequence = list(range(rng.randint(1, 5), rng.randint(20, 30), rng.randint(2, 4)))
        if len(sequence) < 4:
            sequence = [2, 5, 8, 11, 14, 17, 20]
        wrong_next = sequence[-1] + (sequence[1] - sequence[0]) + rng.choice([-1, 1])
        correct_next = sequence[-1] + (sequence[1] - sequence[0])
        puzzle = {
            "type": "trap",
            "subtype": "off_by_one",
            "question": (
                f"A sign says the next number in the sequence {sequence} is {wrong_next}. "
                f"Verify this. If incorrect, provide the CORRECT next number."
            ),
            "sequence": sequence,
            "claimed_next": wrong_next,
            "hint": "Calculate the common difference and find the real next term.",
        }
        answer = correct_next
        variables = {"correct_next": correct_next, "was_trap": True}
        return puzzle, answer, variables

    else:  # contradictory_clue
        # Two statements, one is false
        val_a = rng.randint(1, 20)
        val_b = rng.randint(1, 20)
        real_product = val_a * val_b
        fake_product = real_product + rng.choice([-5, -3, -2, 2, 3, 5])

        statements = [
            f"Statement 1: A = {val_a}, B = {val_b}.",
            f"Statement 2: A * B = {fake_product}.",
        ]
        puzzle = {
            "type": "trap",
            "subtype": "contradictory_clue",
            "question": (
                f"Two inscriptions on the wall:\n"
                f"  {statements[0]}\n"
                f"  {statements[1]}\n"
                f"One statement is wrong. What is the TRUE value of A * B?"
            ),
            "statements": statements,
            "hint": "Calculate A * B from Statement 1 and compare with Statement 2.",
        }
        answer = real_product
        variables = {"true_product": real_product, "was_trap": True}
        return puzzle, answer, variables


def generate_ambiguity_puzzle(
    rng: random.Random,
    room_id: str,
    session_vars: dict,
    exits: list[str] | None = None,
) -> tuple[dict, Any, dict]:
    """
    Generate an ambiguity room. Two exits look valid. The correct one
    requires combining information from 2 previous rooms.
    """
    if not exits or len(exits) < 2:
        exits = ["exit_left", "exit_right"]

    exit_a, exit_b = exits[0], exits[1]

    # Try to reference two previous rooms
    available_rooms = list(session_vars.keys())
    if len(available_rooms) >= 2:
        ref_rooms = rng.sample(available_rooms, 2)
        vars_1 = session_vars[ref_rooms[0]]
        vars_2 = session_vars[ref_rooms[1]]

        # Find numeric variables from each
        num_val_1 = None
        num_val_2 = None
        for v in vars_1.values():
            if isinstance(v, (int, float)):
                num_val_1 = v
                break
        for v in vars_2.values():
            if isinstance(v, (int, float)):
                num_val_2 = v
                break

        if num_val_1 is not None and num_val_2 is not None:
            combined = num_val_1 + num_val_2
            if combined % 2 == 0:
                correct_exit = exit_a
                wrong_exit = exit_b
            else:
                correct_exit = exit_b
                wrong_exit = exit_a

            puzzle = {
                "type": "ambiguity",
                "subtype": "combine_previous",
                "question": (
                    f"Two exits: '{exit_a}' and '{exit_b}'.\n"
                    f"Clue: Recall a numeric value from room '{ref_rooms[0]}' "
                    f"and a numeric value from room '{ref_rooms[1]}'. "
                    f"Add them together. If the sum is even, take '{exit_a}'. "
                    f"If odd, take '{exit_b}'.\n"
                    f"Which exit do you take?"
                ),
                "exits": [exit_a, exit_b],
                "referenced_rooms": ref_rooms,
                "hint": "You need numeric values from two specific previous rooms.",
            }
            answer = correct_exit
            variables = {"chosen_exit": correct_exit}
            return puzzle, answer, variables

    # Fallback: simpler ambiguity
    secret = rng.randint(1, 100)
    if secret % 2 == 0:
        correct_exit = exit_a
    else:
        correct_exit = exit_b

    puzzle = {
        "type": "ambiguity",
        "subtype": "parity_check",
        "question": (
            f"Two exits: '{exit_a}' and '{exit_b}'.\n"
            f"A number is hidden in this room: {secret}.\n"
            f"If the number is even, take '{exit_a}'. If odd, take '{exit_b}'.\n"
            f"Which exit do you take?"
        ),
        "exits": [exit_a, exit_b],
        "hidden_number": secret,
        "hint": "Check if the number is even or odd.",
    }
    answer = correct_exit
    variables = {"chosen_exit": correct_exit}
    return puzzle, answer, variables


def generate_boss_puzzle(rng: random.Random, room_id: str, session_vars: dict) -> tuple[dict, Any, dict]:
    """
    Generate a boss room puzzle that combines 3+ types:
    1. Decode a cipher to get a number
    2. Use that number in a math equation
    3. The result determines which pattern to continue
    """
    import base64

    # Step 1: Cipher - decode to get a number
    hidden_number = rng.randint(2, 9)
    hidden_str = str(hidden_number)
    cipher_method = rng.choice(["base64", "caesar"])

    if cipher_method == "base64":
        encoded = base64.b64encode(hidden_str.encode()).decode()
        cipher_instruction = f"Base64-decode '{encoded}' to get a number N."
    else:
        shift = rng.randint(1, 10)
        # Caesar on digit: shift the digit
        shifted_digit = (hidden_number + shift) % 10
        cipher_instruction = (
            f"A digit was Caesar-shifted by +{shift} (mod 10) to become {shifted_digit}. "
            f"Find the original digit N."
        )

    # Step 2: Math - compute with N
    multiplier = rng.randint(2, 5)
    addend = rng.randint(1, 10)
    math_result = hidden_number * multiplier + addend
    math_instruction = f"Compute M = N * {multiplier} + {addend}."

    # Step 3: Pattern - use M to identify next term
    start = math_result
    diff = rng.randint(2, 7)
    sequence = [start + i * diff for i in range(5)]
    final_answer = sequence[-1] + diff
    pattern_instruction = (
        f"Starting from M, generate an arithmetic sequence with common difference {diff} "
        f"for 5 terms. What is the 6th term?"
    )

    puzzle = {
        "type": "boss",
        "subtype": "multi_step",
        "question": (
            f"BOSS ROOM - Multi-step challenge:\n\n"
            f"Step 1 (Cipher): {cipher_instruction}\n\n"
            f"Step 2 (Math): {math_instruction}\n\n"
            f"Step 3 (Pattern): {pattern_instruction}\n\n"
            f"Submit the final answer (the 6th term)."
        ),
        "steps": ["cipher", "math", "pattern"],
        "hint": (
            f"Solve each step in order. "
            f"Cipher gives N, Math gives M = N*{multiplier}+{addend}, "
            f"Pattern: M, M+{diff}, M+2*{diff}, ... find 6th term."
        ),
    }
    variables = {"N": hidden_number, "M": math_result, "final_answer": final_answer}
    return puzzle, final_answer, variables


# ---------------------------------------------------------------------------
# Puzzle Generator Dispatch
# ---------------------------------------------------------------------------

PUZZLE_GENERATORS = {
    PuzzleType.MATH: generate_math_puzzle,
    PuzzleType.CIPHER: generate_cipher_puzzle,
    PuzzleType.LOGIC_GATE: generate_logic_gate_puzzle,
    PuzzleType.PATTERN: generate_pattern_puzzle,
    PuzzleType.GRAPH: generate_graph_puzzle,
    PuzzleType.API: generate_api_puzzle,
    PuzzleType.TRAP: generate_trap_puzzle,
    PuzzleType.BOSS: generate_boss_puzzle,
}


# ---------------------------------------------------------------------------
# Room Name Generator
# ---------------------------------------------------------------------------


def generate_room_name(rng: random.Random, puzzle_type: PuzzleType, index: int) -> str:
    """Generate a thematic room name."""
    prefixes = {
        PuzzleType.MATH: ["The Arithmetic Chamber", "Hall of Equations", "Number Sanctum",
                          "The Calculus Crypt", "Division Den"],
        PuzzleType.CIPHER: ["The Cipher Vault", "Encryption Alcove", "Code Room",
                            "The Cryptex Chamber", "Decoder's Den"],
        PuzzleType.LOGIC_GATE: ["The Logic Laboratory", "Boolean Basement", "Gate Room",
                                 "Truth Table Tower", "Circuit Crypt"],
        PuzzleType.PATTERN: ["The Sequence Hall", "Pattern Parlor", "Series Sanctum",
                              "The Fibonacci Foyer", "Iteration Inn"],
        PuzzleType.GRAPH: ["The Graph Garden", "Network Nexus", "Path Plaza",
                            "The Dijkstra Den", "Edge Gallery"],
        PuzzleType.API: ["The API Alcove", "Endpoint Emporium", "Request Room",
                          "The REST Retreat", "Fetch Foyer"],
        PuzzleType.MEMORY: ["The Memory Manor", "Recall Room", "Echo Chamber",
                             "The Mnemonic Maze", "Remembrance Hall"],
        PuzzleType.TRAP: ["The Deception Den", "Trick Tunnel", "Illusion Inn",
                           "The False Floor", "Mirage Chamber"],
        PuzzleType.AMBIGUITY: ["The Fork", "Crossroads Chamber", "The Dilemma Door",
                                "Bifurcation Bay", "Choice Corridor"],
        PuzzleType.BOSS: ["The Boss Chamber", "Final Trial Room", "The Gauntlet",
                           "Grandmaster's Gallery", "The Crucible"],
    }
    options = prefixes.get(puzzle_type, ["Mystery Room"])
    return rng.choice(options)


# ---------------------------------------------------------------------------
# Room Description Generator
# ---------------------------------------------------------------------------


def generate_room_description(rng: random.Random, room: Room) -> str:
    """Generate atmospheric flavor text for a room."""
    atmospheres = [
        "Dim torchlight flickers across ancient stone walls.",
        "A low hum emanates from glowing crystals embedded in the ceiling.",
        "The air is cool and dry. Strange symbols are etched into the floor.",
        "Water drips rhythmically from somewhere above. Moss covers the walls.",
        "A warm breeze carries the scent of old parchment and machine oil.",
        "Phosphorescent fungi cast an eerie green glow throughout the chamber.",
        "Mechanical gears turn slowly behind glass panels in the walls.",
        "The room is perfectly circular, with a domed ceiling of polished obsidian.",
        "Bookshelves line every wall, filled with leather-bound volumes.",
        "A large hourglass stands in the center, sand flowing upward.",
    ]

    token_text = ""
    if room.has_token:
        token_text = (
            f"\n\nA glowing token [{room.token_id}] floats above a pedestal. "
            f"Solve the puzzle to collect it."
        )

    trap_text = ""
    if room.is_trap:
        trap_text = "\n\n[WARNING: Something about this room feels... off.]"

    dead_end_text = ""
    if room.is_dead_end:
        dead_end_text = "\n\n[This appears to be a dead end. Solve the puzzle to unlock the way back.]"

    exit_text = f"\n\nExits: {', '.join(room.exits)}"

    return (
        f"{rng.choice(atmospheres)}{token_text}{trap_text}{dead_end_text}"
        f"\n\n--- PUZZLE ---\n{room.puzzle_data.get('question', 'No puzzle here.')}"
        f"{exit_text}"
    )


# ---------------------------------------------------------------------------
# Maze Generator
# ---------------------------------------------------------------------------


def generate_maze(seed: int) -> dict[str, Room]:
    """
    Generate a complete maze with NUM_ROOMS rooms.
    Returns a dict of room_id -> Room.
    """
    rng = seeded_random(seed)

    # Determine puzzle type assignments
    # We need: 3 trap rooms, 2 ambiguity rooms, and distribute the rest
    puzzle_types: list[PuzzleType] = []

    # Mandatory assignments
    puzzle_types.extend([PuzzleType.TRAP] * NUM_TRAP_ROOMS)
    puzzle_types.extend([PuzzleType.AMBIGUITY] * NUM_AMBIGUITY_ROOMS)

    # Fill remaining with other types (ensure at least one of each)
    other_types = [
        PuzzleType.MATH, PuzzleType.CIPHER, PuzzleType.LOGIC_GATE,
        PuzzleType.PATTERN, PuzzleType.GRAPH, PuzzleType.API,
        PuzzleType.MEMORY, PuzzleType.BOSS,
    ]
    # Ensure at least one of each
    puzzle_types.extend(other_types)

    # Fill remaining slots randomly from other types
    remaining = NUM_ROOMS - len(puzzle_types)
    for _ in range(remaining):
        puzzle_types.append(rng.choice(other_types))

    rng.shuffle(puzzle_types)

    # Assign tokens to 10 rooms
    token_indices = set(rng.sample(range(NUM_ROOMS), NUM_TOKEN_ROOMS))

    # Assign dead ends to 5 rooms (not the start room, index 0)
    non_start_indices = list(range(1, NUM_ROOMS))
    dead_end_indices = set(rng.sample(non_start_indices, NUM_DEAD_ENDS))

    # Generate room IDs
    room_ids = [f"room_{i:03d}" for i in range(NUM_ROOMS)]

    # Build connectivity: create a main path, then add branches for dead ends
    # Main path: room_0 -> room_1 -> ... -> room_(N-1)
    # Dead ends branch off the main path but lead nowhere else
    main_path_indices = [i for i in range(NUM_ROOMS) if i not in dead_end_indices]

    # Connectivity map
    connectivity: dict[int, list[int]] = {i: [] for i in range(NUM_ROOMS)}

    # Connect main path rooms sequentially
    for idx in range(len(main_path_indices) - 1):
        a = main_path_indices[idx]
        b = main_path_indices[idx + 1]
        connectivity[a].append(b)
        connectivity[b].append(a)

    # Connect dead ends to random main-path rooms
    for de_idx in dead_end_indices:
        # Attach to a random main-path room
        attach_to = rng.choice(main_path_indices)
        connectivity[attach_to].append(de_idx)
        connectivity[de_idx].append(attach_to)

    # Add a few extra cross-connections for non-linearity (but not too many)
    num_extra_connections = rng.randint(2, 4)
    for _ in range(num_extra_connections):
        a = rng.choice(main_path_indices)
        b = rng.choice(main_path_indices)
        if a != b and b not in connectivity[a]:
            connectivity[a].append(b)
            connectivity[b].append(a)

    # Generate rooms
    rooms: dict[str, Room] = {}
    session_vars: dict[str, dict] = {}  # placeholder for variable references

    for i in range(NUM_ROOMS):
        room_id = room_ids[i]
        puzzle_type = puzzle_types[i]
        has_token = i in token_indices
        is_dead_end = i in dead_end_indices
        is_trap = puzzle_type == PuzzleType.TRAP
        is_ambiguity = puzzle_type == PuzzleType.AMBIGUITY

        # Get exit room IDs
        exit_ids = [room_ids[j] for j in connectivity[i]]

        # Generate puzzle
        if puzzle_type == PuzzleType.MEMORY:
            puzzle_data, answer, variables = generate_memory_puzzle(
                rng, room_id, session_vars,
                visited_rooms=None,  # will be dynamic at runtime
                all_rooms=None,
            )
        elif puzzle_type == PuzzleType.AMBIGUITY:
            puzzle_data, answer, variables = generate_ambiguity_puzzle(
                rng, room_id, session_vars, exits=exit_ids[:2] if len(exit_ids) >= 2 else exit_ids,
            )
        elif puzzle_type in PUZZLE_GENERATORS:
            puzzle_data, answer, variables = PUZZLE_GENERATORS[puzzle_type](
                rng, room_id, session_vars,
            )
        else:
            # Fallback
            puzzle_data = {"type": "unknown", "question": "This room has no puzzle."}
            answer = None
            variables = {}

        token_id = f"TOKEN_{rng.randint(1000, 9999)}" if has_token else None

        name = generate_room_name(rng, puzzle_type, i)

        room = Room(
            id=room_id,
            name=name,
            description="",  # generated later with full context
            puzzle_type=puzzle_type,
            puzzle_data=puzzle_data,
            answer=answer,
            exits=exit_ids,
            has_token=has_token,
            token_id=token_id,
            is_dead_end=is_dead_end,
            is_trap=is_trap,
            is_ambiguity=is_ambiguity,
            variables=variables,
        )

        rooms[room_id] = room
        session_vars[room_id] = variables

    # Generate descriptions (needs full room context)
    desc_rng = seeded_random(seed + 1)
    for room_id, room in rooms.items():
        room.description = generate_room_description(desc_rng, room)

    return rooms


# ---------------------------------------------------------------------------
# Session Management
# ---------------------------------------------------------------------------


def create_session() -> Session:
    """Create a new maze session."""
    session_id = str(uuid.uuid4())
    seed = int.from_bytes(uuid.uuid4().bytes[:4], "big")

    rooms = generate_maze(seed)
    room_ids = list(rooms.keys())
    start_room = room_ids[0]

    session = Session(
        session_id=session_id,
        seed=seed,
        rooms=rooms,
        room_order=room_ids,
        start_room=start_room,
        current_room=start_room,
        collected_tokens=[],
        visited_rooms=[(start_room, time.time())],
        move_count=0,
        api_call_count=0,
        created_at=time.time(),
        solved_rooms=set(),
        room_variables={},
    )
    sessions[session_id] = session
    return session


def validate_session(session_id: str) -> tuple[Session | None, str | None]:
    """Validate a session. Returns (session, error_message)."""
    if not session_id:
        return None, "Missing session_id"

    session = sessions.get(session_id)
    if not session:
        return None, "Invalid session_id. Session not found."

    # Check timeout
    elapsed = time.time() - session.created_at
    if elapsed > SESSION_TIMEOUT_SECONDS:
        return None, f"Session expired. Time limit of {SESSION_TIMEOUT_SECONDS}s exceeded."

    # Check API call limit
    if session.api_call_count >= MAX_API_CALLS:
        return None, f"Session expired. API call limit of {MAX_API_CALLS} exceeded."

    session.api_call_count += 1
    return session, None


def room_to_dict(room: Room, include_answer: bool = False) -> dict:
    """Serialize a room to a dictionary for API responses."""
    result = {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "puzzle": room.puzzle_data,
        "exits": room.exits,
        "has_token": room.has_token,
        "token_id": room.token_id,
        "is_dead_end": room.is_dead_end,
    }
    if include_answer:
        result["answer"] = room.answer
    return result


# ---------------------------------------------------------------------------
# Dynamic Puzzle Regeneration for Memory/Ambiguity
# ---------------------------------------------------------------------------


def regenerate_dynamic_puzzle(session: Session, room: Room) -> None:
    """
    For memory and ambiguity rooms, regenerate the puzzle using current
    session state (visited rooms, collected variables).
    """
    rng = seeded_random(session.seed + hash(room.id))

    if room.puzzle_type == PuzzleType.MEMORY:
        visited_ids = [r_id for r_id, _ in session.visited_rooms]
        puzzle_data, answer, variables = generate_memory_puzzle(
            rng, room.id, session.room_variables,
            visited_rooms=visited_ids,
            all_rooms=session.rooms,
        )
        room.puzzle_data = puzzle_data
        room.answer = answer
        room.variables = variables
        # Re-generate description
        desc_rng = seeded_random(session.seed + 1 + hash(room.id))
        room.description = generate_room_description(desc_rng, room)

    elif room.puzzle_type == PuzzleType.AMBIGUITY:
        puzzle_data, answer, variables = generate_ambiguity_puzzle(
            rng, room.id, session.room_variables,
            exits=room.exits[:2] if len(room.exits) >= 2 else room.exits,
        )
        room.puzzle_data = puzzle_data
        room.answer = answer
        room.variables = variables
        desc_rng = seeded_random(session.seed + 1 + hash(room.id))
        room.description = generate_room_description(desc_rng, room)


# ---------------------------------------------------------------------------
# Answer Validation
# ---------------------------------------------------------------------------


def validate_answer(room: Room, submitted_answer: Any) -> bool:
    """Check if a submitted answer matches the room's expected answer."""
    expected = room.answer
    submitted = submitted_answer

    # Normalize types for comparison
    if isinstance(expected, int):
        try:
            submitted = int(float(str(submitted)))
        except (ValueError, TypeError):
            return False
        return submitted == expected

    if isinstance(expected, float):
        try:
            submitted = float(str(submitted))
        except (ValueError, TypeError):
            return False
        return abs(submitted - expected) < 0.01

    if isinstance(expected, str):
        submitted_str = str(submitted).strip().lower()
        expected_str = expected.strip().lower()
        return submitted_str == expected_str

    return str(submitted) == str(expected)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------


@app.route("/api/maze/start", methods=["GET"])
def maze_start():
    """Start a new maze session. Returns session_id and the first room."""
    session = create_session()
    start_room = session.rooms[session.start_room]

    return jsonify({
        "session_id": session.session_id,
        "message": (
            "Welcome to The Agent Maze! Navigate through 20 rooms, "
            "solve puzzles, and collect all 10 tokens. "
            f"You have {SESSION_TIMEOUT_SECONDS // 60} minutes and "
            f"{MAX_API_CALLS} API calls."
        ),
        "room": room_to_dict(start_room),
        "rules": {
            "total_rooms": NUM_ROOMS,
            "tokens_required": NUM_TOKEN_ROOMS,
            "time_limit_seconds": SESSION_TIMEOUT_SECONDS,
            "api_call_limit": MAX_API_CALLS,
            "actions": {
                "solve": "Submit an answer to the current room's puzzle",
                "move": "Move to an adjacent room via an exit",
                "look": "Re-examine the current room",
            },
        },
    })


@app.route("/api/maze/action", methods=["POST"])
def maze_action():
    """
    Perform an action in the maze.

    Actions:
    - solve: Submit an answer. Body: {session_id, action: "solve", data: {answer: <value>}}
    - move: Move to an exit. Body: {session_id, action: "move", data: {exit: "<room_id>"}}
    - look: Re-examine current room. Body: {session_id, action: "look"}
    """
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON body"}), 400

    session_id = body.get("session_id")
    session, error = validate_session(session_id)
    if error:
        return jsonify({"error": error}), 400

    action = body.get("action", "").lower()
    data = body.get("data", {})
    current_room = session.rooms[session.current_room]

    if action == "look":
        # Regenerate dynamic puzzles on look
        regenerate_dynamic_puzzle(session, current_room)
        return jsonify({
            "action": "look",
            "room": room_to_dict(current_room),
            "status": {
                "tokens_collected": len(session.collected_tokens),
                "tokens_required": NUM_TOKEN_ROOMS,
                "move_count": session.move_count,
                "api_calls_remaining": MAX_API_CALLS - session.api_call_count,
                "time_remaining_seconds": max(
                    0,
                    SESSION_TIMEOUT_SECONDS - (time.time() - session.created_at),
                ),
            },
        })

    elif action == "solve":
        if not data or "answer" not in data:
            return jsonify({"error": "Missing 'data.answer' field"}), 400

        submitted = data["answer"]

        # Regenerate dynamic puzzles before validation
        regenerate_dynamic_puzzle(session, current_room)

        if validate_answer(current_room, submitted):
            # Correct answer
            session.solved_rooms.add(current_room.id)
            session.room_variables[current_room.id] = current_room.variables

            result = {
                "action": "solve",
                "correct": True,
                "message": "Correct! The puzzle is solved.",
            }

            # Collect token if present
            if current_room.has_token and current_room.token_id not in session.collected_tokens:
                session.collected_tokens.append(current_room.token_id)
                result["token_collected"] = current_room.token_id
                result["message"] += f" You collected token: {current_room.token_id}!"

            result["tokens_collected"] = len(session.collected_tokens)
            result["tokens_required"] = NUM_TOKEN_ROOMS
            result["room"] = room_to_dict(current_room)

            if len(session.collected_tokens) >= NUM_TOKEN_ROOMS:
                result["message"] += (
                    " You have collected all tokens! "
                    "Use POST /api/maze/submit to claim your flag."
                )

            return jsonify(result)
        else:
            return jsonify({
                "action": "solve",
                "correct": False,
                "message": "Incorrect answer. Try again.",
                "room": room_to_dict(current_room),
            })

    elif action == "move":
        if not data or "exit" not in data:
            return jsonify({"error": "Missing 'data.exit' field"}), 400

        target_room_id = data["exit"]

        # Must solve current room's puzzle before moving (unless already solved)
        if current_room.id not in session.solved_rooms:
            return jsonify({
                "error": "You must solve the current room's puzzle before moving.",
                "room": room_to_dict(current_room),
            }), 400

        # Validate exit
        if target_room_id not in current_room.exits:
            return jsonify({
                "error": f"Invalid exit '{target_room_id}'. Available exits: {current_room.exits}",
            }), 400

        # Move to target room
        session.current_room = target_room_id
        session.move_count += 1
        session.visited_rooms.append((target_room_id, time.time()))

        new_room = session.rooms[target_room_id]

        # Regenerate dynamic puzzles for the new room
        regenerate_dynamic_puzzle(session, new_room)

        return jsonify({
            "action": "move",
            "message": f"You moved to {new_room.name}.",
            "room": room_to_dict(new_room),
            "status": {
                "tokens_collected": len(session.collected_tokens),
                "tokens_required": NUM_TOKEN_ROOMS,
                "move_count": session.move_count,
                "api_calls_remaining": MAX_API_CALLS - session.api_call_count,
            },
        })

    else:
        return jsonify({
            "error": f"Unknown action '{action}'. Valid actions: solve, move, look",
        }), 400


@app.route("/api/maze/status", methods=["GET"])
def maze_status():
    """Get the current status of a maze session."""
    session_id = request.args.get("session_id")
    session, error = validate_session(session_id)
    if error:
        return jsonify({"error": error}), 400

    current_room = session.rooms[session.current_room]
    elapsed = time.time() - session.created_at

    return jsonify({
        "session_id": session.session_id,
        "current_room": {
            "id": current_room.id,
            "name": current_room.name,
            "solved": current_room.id in session.solved_rooms,
        },
        "tokens_collected": session.collected_tokens,
        "tokens_count": len(session.collected_tokens),
        "tokens_required": NUM_TOKEN_ROOMS,
        "move_count": session.move_count,
        "api_call_count": session.api_call_count,
        "api_calls_remaining": MAX_API_CALLS - session.api_call_count,
        "time_elapsed_seconds": round(elapsed, 1),
        "time_remaining_seconds": round(max(0, SESSION_TIMEOUT_SECONDS - elapsed), 1),
        "visited_rooms": [
            {"room_id": r_id, "timestamp": ts}
            for r_id, ts in session.visited_rooms
        ],
        "solved_rooms": list(session.solved_rooms),
        "completed": session.completed,
    })


@app.route("/api/maze/submit", methods=["POST"])
def maze_submit():
    """Submit collected tokens to claim the flag."""
    body = request.get_json(force=True, silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON body"}), 400

    session_id = body.get("session_id")
    session, error = validate_session(session_id)
    if error:
        return jsonify({"error": error}), 400

    if len(session.collected_tokens) < NUM_TOKEN_ROOMS:
        return jsonify({
            "error": (
                f"Not enough tokens. You have {len(session.collected_tokens)}/{NUM_TOKEN_ROOMS}. "
                f"Collect all tokens before submitting."
            ),
            "tokens_collected": session.collected_tokens,
            "tokens_required": NUM_TOKEN_ROOMS,
        }), 400

    # Success!
    session.completed = True
    elapsed = time.time() - session.created_at

    return jsonify({
        "success": True,
        "flag": FLAG,
        "message": "Congratulations! Your agent has navigated the maze!",
        "stats": {
            "time_taken_seconds": round(elapsed, 1),
            "move_count": session.move_count,
            "api_calls_used": session.api_call_count,
            "tokens_collected": len(session.collected_tokens),
        },
    })


@app.route("/api/maze/room_secret", methods=["GET"])
def room_secret():
    """
    Endpoint for API-type puzzle rooms. Returns a secret code
    that the agent must retrieve and submit as the puzzle answer.
    """
    room_id = request.args.get("room_id")
    session_id = request.args.get("session_id")

    if not room_id:
        return jsonify({"error": "Missing room_id parameter"}), 400

    # If session_id provided, validate it
    if session_id:
        session, error = validate_session(session_id)
        if error:
            return jsonify({"error": error}), 400

        room = session.rooms.get(room_id)
        if not room:
            return jsonify({"error": f"Room '{room_id}' not found in session"}), 404

        if room.puzzle_type != PuzzleType.API:
            return jsonify({"error": "This room does not have an API puzzle"}), 400

        return jsonify({
            "room_id": room_id,
            "secret_code": room.variables.get("secret_code", "UNKNOWN"),
            "message": "Submit this secret_code as your puzzle answer.",
        })

    # Without session_id, check all active sessions for this room
    for sid, session in sessions.items():
        room = session.rooms.get(room_id)
        if room and room.puzzle_type == PuzzleType.API:
            return jsonify({
                "room_id": room_id,
                "secret_code": room.variables.get("secret_code", "UNKNOWN"),
                "message": "Submit this secret_code as your puzzle answer.",
            })

    return jsonify({"error": "Room not found"}), 404


@app.route("/api/maze/map", methods=["GET"])
def maze_map():
    """
    Return a partial map of rooms the agent has visited.
    Only reveals connectivity of visited rooms.
    """
    session_id = request.args.get("session_id")
    session, error = validate_session(session_id)
    if error:
        return jsonify({"error": error}), 400

    visited_ids = {r_id for r_id, _ in session.visited_rooms}
    map_data = {}

    for r_id in visited_ids:
        room = session.rooms[r_id]
        map_data[r_id] = {
            "name": room.name,
            "exits": room.exits,
            "solved": r_id in session.solved_rooms,
            "has_token": room.has_token,
            "token_collected": room.token_id in session.collected_tokens if room.token_id else False,
        }

    return jsonify({
        "session_id": session.session_id,
        "visited_count": len(visited_ids),
        "total_rooms": NUM_ROOMS,
        "map": map_data,
        "current_room": session.current_room,
    })


# ---------------------------------------------------------------------------
# Health / Info Endpoints
# ---------------------------------------------------------------------------


@app.route("/", methods=["GET"])
def index():
    """Root endpoint with challenge info."""
    return jsonify({
        "challenge": "The Agent Maze",
        "description": (
            "Build an autonomous AI agent that navigates a randomized puzzle maze. "
            "Collect all 10 tokens to claim the flag."
        ),
        "endpoints": {
            "GET /api/maze/start": "Start a new maze session",
            "POST /api/maze/action": "Perform an action (solve, move, look)",
            "GET /api/maze/status": "Get session status",
            "POST /api/maze/submit": "Submit tokens to claim flag",
            "GET /api/maze/map": "View map of visited rooms",
            "GET /api/maze/room_secret": "Fetch secret for API puzzle rooms",
        },
        "rules": {
            "total_rooms": NUM_ROOMS,
            "tokens_to_collect": NUM_TOKEN_ROOMS,
            "time_limit": f"{SESSION_TIMEOUT_SECONDS // 60} minutes",
            "api_call_limit": MAX_API_CALLS,
        },
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check."""
    return jsonify({
        "status": "ok",
        "active_sessions": len(sessions),
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  The Agent Maze - CTF Challenge Server")
    print("=" * 60)
    print(f"  Rooms per maze:    {NUM_ROOMS}")
    print(f"  Tokens to collect: {NUM_TOKEN_ROOMS}")
    print(f"  Time limit:        {SESSION_TIMEOUT_SECONDS // 60} minutes")
    print(f"  API call limit:    {MAX_API_CALLS}")
    print("=" * 60)
    print("  Starting server on http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
