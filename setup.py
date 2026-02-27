"""
One-time CTF setup — registers you on the leaderboard and caches your session
so that pytest validation never prompts for your name.

Run this once before starting any challenges:
    python setup.py
"""

import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError

SESSION_FILE = os.path.expanduser("~/.ctf_session")


def main():
    # --- Load .env ---------------------------------------------------------
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        print("ERROR: .env file not found at repo root.")
        print("Ask an organizer for the .env file.")
        sys.exit(1)

    env = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip('"').strip("'")

    server = env.get("CTF_SERVER", "").rstrip("/")
    join_code = env.get("CTF_JOIN_CODE", "YUMCTF")

    if not server:
        print("ERROR: CTF_SERVER not set in .env")
        sys.exit(1)

    # --- Check for existing session ----------------------------------------
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE) as f:
                session = json.load(f)
            if session.get("participantId") and session.get("name"):
                print()
                print("=" * 50)
                print(f"  Already set up as: {session['name']}")
                print("  Session cached at: " + SESSION_FILE)
                print("  You're good to go — start solving challenges!")
                print("=" * 50)
                print()
                return
        except (json.JSONDecodeError, KeyError):
            pass  # corrupted file, re-register

    # --- Verify server connectivity ----------------------------------------
    print()
    print(f"Checking CTF server at {server} ...")
    try:
        req = Request(server, method="GET")
        with urlopen(req, timeout=10):
            pass
        print("Server is reachable!")
    except (URLError, OSError) as e:
        print(f"ERROR: Cannot reach CTF server at {server}")
        print(f"  {e}")
        print()
        print("Make sure the server is running and your .env is correct.")
        sys.exit(1)

    # --- Register via ctf_helper -------------------------------------------
    # Import ctf_helper from the same directory as this script
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ctf_helper

    print()
    pid, eid = ctf_helper.get_participant_id()

    # Confirm success
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            session = json.load(f)
        print()
        print("=" * 50)
        print(f"  Setup complete!")
        print(f"  Name:    {session.get('name', '?')}")
        print(f"  Session: {SESSION_FILE}")
        print()
        print("  You're registered on the leaderboard.")
        print("  Now go solve some challenges!")
        print("=" * 50)
        print()
    else:
        print("  Registered, but session file was not cached.")
        print("  Challenges will still work — you may be prompted again.")


if __name__ == "__main__":
    main()
