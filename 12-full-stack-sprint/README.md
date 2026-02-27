# Challenge 12: Full Stack Sprint (500 pts)

## Tool: Claude Code

## Objective

Build a **store locator API** from scratch. You are given only data and tests — you must build everything else.

## What You're Given

- `data/stores.csv` — 500 store locations across the US (KFC, Taco Bell, Pizza Hut, Habit Burger)
- `test_e2e.py` — 15 end-to-end tests that your API must pass
- `requirements.txt` — Required packages

## What You Need To Build

A FastAPI application that serves as a store locator with these endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Homepage (returns 200) |
| GET | `/api/stores` | List all stores (supports filtering) |
| GET | `/api/stores/{id}` | Get a specific store |
| GET | `/api/stores/nearest` | Find nearest stores by lat/lng |
| GET | `/api/brands` | List unique brands |
| GET | `/api/cities` | List unique cities |

### Query Parameters for `/api/stores`

- `city` — Filter by city name
- `brand` — Filter by brand name
- `search` — Search by store name (case-insensitive partial match)
- `page` — Page number (default: 1)
- `limit` — Items per page (default: 50)

### Query Parameters for `/api/stores/nearest`

- `lat` — Latitude (required)
- `lng` — Longitude (required)
- `limit` — Number of results (default: 5)

## Project Structure

You need to create your FastAPI app so that it can be imported as either `app.main` or `main`. The test file will try both.

Suggested structure:
```
app/
  __init__.py
  main.py          # FastAPI app
```

## Running Tests

```bash
pip install -r requirements.txt
python -m pytest test_e2e.py -v
```

## Success Criteria

All 15 tests in `test_e2e.py` must pass.

## Submission

When all tests pass, your solution is auto-submitted to the CTF server.

## Tips

- Read `test_e2e.py` carefully to understand exactly what the API should return
- Load data from `data/stores.csv` at startup
- The nearest endpoint needs to calculate distances using the Haversine formula
- Each store in the nearest response needs a `distance_miles` field
- Make sure store objects include all required fields: id, name, brand, city, latitude, longitude
