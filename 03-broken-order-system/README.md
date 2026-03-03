# Challenge 3: The Broken Order System (200 pts)

## Scenario

You've inherited a FastAPI restaurant ordering API from a developer who left the company.
The test suite has **21 tests**, but **9 of them are failing** due to **5 bugs** in the code.
Your job is to find and fix all 5 bugs so every test passes.

## Getting Started

1. Open this folder in your AI coding assistant
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the test suite:
   ```bash
   pytest tests/test_orders.py -v
   ```
4. You should see **9 failing tests** (caused by 5 bugs). Use your AI tool's features to help you find and fix the bugs.

## API Endpoints

| Method | Path                   | Description                        |
|--------|------------------------|------------------------------------|
| POST   | `/orders`              | Create a new order                 |
| GET    | `/orders`              | List orders (paginated)            |
| GET    | `/orders/{id}`         | Get a specific order               |
| GET    | `/orders/{id}/summary` | Get order summary with totals/tax  |

## Rules

- The **tests are correct**. Do not modify any test files.
- All bugs are in the `app/` directory.
- There are exactly **5 bugs** spread across the source files.

## Submission

When all 21 tests pass, your solution is auto-submitted to the CTF server.

Good luck!
