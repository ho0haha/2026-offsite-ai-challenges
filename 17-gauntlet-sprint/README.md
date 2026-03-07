# Challenge 17: The Gauntlet Sprint

**Tier 6 — 1000 Points**

## Overview

The Gauntlet Sprint is a rapid-fire collection of 10 independent mini-challenges spanning different software engineering domains. Each challenge tests a distinct skill: async programming, SQL optimization, regex, sorting, rate limiting, log parsing, memory management, caching, database migration, and stream processing.

You must **complete at least 9 out of 10** challenges to earn the flag.

## Structure

```
gauntlet/
├── 01_async/       — Fix a race condition in async Python
├── 02_sql/         — Optimize a slow SQL query
├── 03_regex/       — Write a regex for restaurant hours
├── 04_sort/        — Implement a multi-criteria custom sort
├── 05_ratelimit/   — Build a sliding-window rate limiter
├── 06_logparse/    — Parse POS system logs into a report
├── 07_memleak/     — Fix memory leaks in a long-running server
├── 08_cache/       — Implement an LRU cache with TTL
├── 09_migration/   — Write a database schema migration
└── 10_stream/      — Build a streaming JSON aggregator
```

## Rules

1. Each mini-challenge has its own `README.md` with specific instructions.
2. Edit only the designated files (usually `solution.py` or the buggy file).
3. Do NOT modify any `test_*.py` files.
4. Each challenge should be solvable in 10-15 minutes individually.
5. You need **9 out of 10** passing to earn the flag.

## Running

From this directory, run the master test runner:

```bash
python run_gauntlet.py
```

This will execute each mini-challenge's tests and report pass/fail. When 9 or more pass, the flag is printed.

You can also run individual challenges:

```bash
cd gauntlet/01_async && python -m pytest test_async.py -v
```

## Flag

Complete 9/10 challenges to reveal the flag.
