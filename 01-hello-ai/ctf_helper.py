"""
CTF Helper — Auto-submit utility for the AI Coding CTF.

Uses only Python stdlib (no pip installs needed).
Reads CTF_SERVER and CTF_JOIN_CODE from .env file at repo root.
Caches participant session in ~/.ctf_session.

Usage from validation scripts:
    import ctf_helper
    ctf_helper.submit(challenge_number, ["file1.py", "file2.py"])

Usage from shell (for bash validation scripts):
    python ctf_helper.py <challenge_number> <file1> [file2] ...
"""

import json
import os
import sys
import hashlib
import uuid
import time
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

SESSION_FILE = os.path.expanduser("~/.ctf_session")
_config_cache = {}


def _find_env_file():
    """Walk up from this file's directory to find .env"""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        env_path = os.path.join(d, ".env")
        if os.path.exists(env_path):
            return env_path
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return None


def _load_env():
    """Load CTF_SERVER and CTF_JOIN_CODE from .env file."""
    if _config_cache:
        return _config_cache

    env_path = _find_env_file()
    if not env_path:
        print("ERROR: Could not find .env file. Expected at repository root.")
        print("It should contain:")
        print("  CTF_SERVER=http://<server-ip>:3000")
        print("  CTF_JOIN_CODE=YUMCTF")
        sys.exit(1)

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                _config_cache[key.strip()] = value.strip().strip('"').strip("'")

    if "CTF_SERVER" not in _config_cache:
        print("ERROR: CTF_SERVER not found in .env file")
        sys.exit(1)

    return _config_cache


def _api_post_json(url, data):
    """POST JSON to a URL and return the parsed response."""
    body = json.dumps(data).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_participant_id():
    """
    Get the participant ID, using cached session or prompting for name.
    Returns (participant_id, event_id) tuple.
    """
    # Check cache
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE) as f:
                session = json.load(f)
            if "participantId" in session and "eventId" in session:
                return session["participantId"], session["eventId"]
        except (json.JSONDecodeError, KeyError):
            pass

    env = _load_env()
    server = env["CTF_SERVER"].rstrip("/")
    join_code = env.get("CTF_JOIN_CODE", "YUMCTF")

    print()
    print("=" * 50)
    print("  No CTF session found.")
    print("  Enter your name (as shown on the website):")
    print("=" * 50)
    name = input("  Name: ").strip()

    if not name:
        print("ERROR: Name cannot be empty")
        sys.exit(1)

    print(f"  Looking you up...")

    try:
        result = _api_post_json(f"{server}/api/join", {
            "name": name,
            "joinCode": join_code,
        })
    except (URLError, HTTPError) as e:
        print(f"ERROR: Could not connect to CTF server at {server}")
        print(f"  {e}")
        sys.exit(1)

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)

    participant_id = result.get("participantId") or result.get("participant", {}).get("id")
    event_id = result.get("eventId") or result.get("event", {}).get("id")

    if not participant_id or not event_id:
        print(f"ERROR: Unexpected response from server: {result}")
        sys.exit(1)

    # Cache session
    session = {"participantId": participant_id, "eventId": event_id, "name": name}
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(session, f)
    except OSError:
        pass  # Non-fatal if we can't cache

    print(f"  Found! Session saved. Welcome, {name}!")
    print()
    return participant_id, event_id


def _build_multipart(fields, files):
    """
    Build a multipart/form-data body using only stdlib.
    fields: dict of name -> value (strings)
    files: dict of form_field_name -> (filename, content_bytes)
    Returns (content_type, body_bytes)
    """
    boundary = f"----CTFBoundary{uuid.uuid4().hex}"
    parts = []

    for name, value in fields.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n'
            f"\r\n"
            f"{value}\r\n"
        )

    for form_name, (filename, content) in files.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{form_name}"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n"
            f"\r\n"
        )
        parts.append(content)
        parts.append(b"\r\n" if isinstance(content, bytes) else "\r\n")

    parts.append(f"--{boundary}--\r\n")

    # Convert all parts to bytes
    body = b""
    for part in parts:
        if isinstance(part, str):
            body += part.encode("utf-8")
        else:
            body += part

    content_type = f"multipart/form-data; boundary={boundary}"
    return content_type, body


def submit(challenge_number, file_paths):
    """
    Submit a challenge solution to the CTF server.

    Args:
        challenge_number: int (1-12)
        file_paths: list of file paths relative to the challenge directory
    """
    participant_id, event_id = get_participant_id()
    env = _load_env()
    server = env["CTF_SERVER"].rstrip("/")

    # Read all solution files
    files_data = {}
    for fpath in file_paths:
        if not os.path.exists(fpath):
            print(f"ERROR: File not found: {fpath}")
            print("  Make sure you're running from the challenge directory.")
            return False

        with open(fpath, "rb") as f:
            content = f.read()
        # Form field name is "file:{relative_path}"
        form_name = f"file:{fpath}"
        files_data[form_name] = (os.path.basename(fpath), content)

    fields = {
        "participantId": participant_id,
        "challengeNumber": str(challenge_number),
    }

    content_type, body = _build_multipart(fields, files_data)

    try:
        req = Request(f"{server}/api/validate", data=body, method="POST")
        req.add_header("Content-Type", content_type)
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError) as e:
        print()
        print("=" * 50)
        print("  Could not reach the CTF server.")
        print(f"  Error: {e}")
        print()
        print("  Your solution passed local validation!")
        print("  Please try again when the server is available,")
        print("  or ask an organizer for help.")
        print("=" * 50)
        return False

    if result.get("valid"):
        points = result.get("pointsAwarded", 0)
        already = result.get("alreadySolved", False)
        print()
        print("=" * 50)
        if already:
            print("  Already solved! Nice work.")
        else:
            print(f"  CHALLENGE {challenge_number} COMPLETE! +{points} points!")
        print(f"  Check the leaderboard at {server}/leaderboard")
        print("=" * 50)
        print()

        # Print fallback token just in case
        token = result.get("token")
        if token and not already:
            print(f"  Backup token (if needed): {token}")
            print()

        return True
    else:
        message = result.get("message", "Validation failed")
        details = result.get("details", [])
        print()
        print("=" * 50)
        print(f"  Validation failed: {message}")
        if details:
            for d in details:
                print(f"    - {d}")
        print("=" * 50)
        print()
        return False


# CLI mode: python ctf_helper.py <challenge_number> <file1> [file2] ...
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ctf_helper.py <challenge_number> <file1> [file2] ...")
        sys.exit(1)

    ch_num = int(sys.argv[1])
    files = sys.argv[2:]
    success = submit(ch_num, files)
    sys.exit(0 if success else 1)
