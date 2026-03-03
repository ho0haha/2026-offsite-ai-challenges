# Challenge 15: The Undocumented API

**Tier 4 | 500 points**

## Setup

```bash
pip install -r requirements.txt
python server.py
```

## Challenge

A restaurant API server is running on `http://localhost:8000`.

The only documented endpoint is `GET /health`.

Discover the rest. Complete the full workflow. Submit your solution as a working Python script (`explorer.py`).

## Rules

- Do not read `server.py` — treat the server as a black box
- Follow the hints in API responses
- There are 10 steps to complete
- Rate limit: 60 requests per minute

## Submission

Your completed `explorer.py` should, when run, execute the full API flow from start to finish and print the flag.
