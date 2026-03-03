# Challenge 4: Production Incident (200 pts)

## Scenario

It's 2 AM and PagerDuty just woke you up. The production API server is returning 503 errors
and the health check is failing. The connection pool is being exhausted, but the code looks
correct at first glance — every handler has proper try/finally cleanup.

You need to diagnose the root cause from the **logs and code together**, then fix the issue.

## Getting Started

1. Open this folder in your AI coding assistant
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. **Start with the logs** — they contain critical clues about what's happening:
   ```bash
   # Read the production logs first
   cat logs/error.log
   ```
4. Then examine the application code in `app/` to find the root cause
5. Try running the health check to confirm the issue: `python healthcheck.py`
6. Find the root cause and fix the bug

## What You Have

| File                | Description                                     |
|---------------------|-------------------------------------------------|
| `app/server.py`     | Request router and handlers (~250 lines)        |
| `app/database.py`   | Database connection pool with acquire/release    |
| `app/config.py`     | Configuration settings                           |
| `logs/error.log`    | Production logs from the incident (~350 lines)  |
| `healthcheck.py`    | Health check script (currently failing)          |
| `recover.sh`        | Validates your fix and prints the flag           |

## Hints

- Which endpoint correlates with pool drain in the logs?
- What happens right before the active connection count increases without decreasing?
- Are there any warnings that appear alongside connection leaks?
- The code *looks* correct — every function has both `get_connection` and `release_connection`. Look deeper.

## Validating Your Fix

After you've fixed the bug, run the recovery script:

```bash
bash recover.sh
```

## Rules

- The bug is in the `app/` directory
- Do not modify `healthcheck.py` or `recover.sh`
- The logs are read-only clues; don't modify them

## Submission

Successfully fix the root cause and run `recover.sh` — your solution is auto-submitted to the CTF server.

Good luck, on-call engineer!
