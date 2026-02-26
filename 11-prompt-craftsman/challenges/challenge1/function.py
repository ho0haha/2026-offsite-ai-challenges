"""
A complex data processing function that needs comprehensive documentation.
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime


def process_transaction_batch(
    transactions: List[Dict[str, any]],
    currency_rates: Dict[str, float],
    base_currency: str = "USD",
    filters: Optional[Dict[str, any]] = None,
    include_metadata: bool = False,
    max_retries: int = 3,
) -> Tuple[List[Dict], Dict[str, any]]:
    results = []
    stats = {"processed": 0, "skipped": 0, "errors": 0, "total_value": 0.0}

    if not transactions:
        raise ValueError("Transaction list cannot be empty")

    if base_currency not in currency_rates and base_currency != "USD":
        raise KeyError(f"Base currency '{base_currency}' not found in rates")

    for txn in transactions:
        if not isinstance(txn, dict) or "amount" not in txn:
            stats["errors"] += 1
            continue

        if filters:
            skip = False
            if "min_amount" in filters and txn["amount"] < filters["min_amount"]:
                skip = True
            if "max_amount" in filters and txn["amount"] > filters["max_amount"]:
                skip = True
            if "status" in filters and txn.get("status") != filters["status"]:
                skip = True
            if "date_after" in filters:
                txn_date = datetime.fromisoformat(txn.get("date", "2000-01-01"))
                if txn_date < filters["date_after"]:
                    skip = True
            if skip:
                stats["skipped"] += 1
                continue

        source_currency = txn.get("currency", "USD")
        amount = txn["amount"]

        if source_currency != base_currency:
            if source_currency not in currency_rates:
                stats["errors"] += 1
                continue
            rate = currency_rates[source_currency]
            if base_currency != "USD":
                base_rate = currency_rates[base_currency]
                amount = (amount / rate) * base_rate
            else:
                amount = amount / rate

        result = {
            "id": txn.get("id", f"txn_{stats['processed']}"),
            "original_amount": txn["amount"],
            "converted_amount": round(amount, 2),
            "currency": base_currency,
            "status": txn.get("status", "completed"),
        }

        if include_metadata:
            result["metadata"] = {
                "source_currency": source_currency,
                "conversion_rate": currency_rates.get(source_currency, 1.0),
                "processed_at": datetime.now().isoformat(),
                "retry_count": 0,
            }

        results.append(result)
        stats["processed"] += 1
        stats["total_value"] += amount

    stats["total_value"] = round(stats["total_value"], 2)
    return results, stats
