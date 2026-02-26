# Challenge 4: Production Incident (200 pts)

## Tool: Claude Code

## Scenario

It's 2 AM and PagerDuty just woke you up. The production API server is returning 500 errors
and the health check is failing. You need to diagnose the root cause from the logs and code,
then fix the issue.

## Getting Started

1. Open this folder in your terminal with **Claude Code**
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Investigate the situation:
   - Read the error logs in `logs/error.log`
   - Examine the application code in `app/`
   - Try running the health check: `python healthcheck.py`
4. Find the root cause and fix the bug

## What You Have

| File                | Description                              |
|---------------------|------------------------------------------|
| `app/server.py`     | Main application server                  |
| `app/database.py`   | Database connection pool                 |
| `app/config.py`     | Configuration settings                   |
| `logs/error.log`    | ~500 lines of production logs            |
| `healthcheck.py`    | Health check script (currently failing)  |
| `recover.sh`        | Validates your fix and prints the flag   |

## Validating Your Fix

After you've fixed the bug, run the recovery script:

```bash
bash recover.sh
```

## Rules

- The bug is in the `app/` directory
- Do not modify `healthcheck.py` or `recover.sh`
- The logs are read-only clues; don't modify them

## Flag

Successfully fix the root cause and run `recover.sh` to receive:

```
FLAG{production_incident_r00t_caus3}
```

Good luck, on-call engineer!
