"""
Reference solution for the Fuzz Gauntlet challenge.
This implementation passes all Hypothesis property-based tests.

Flag: CTF{fuzz_tested_and_bulletproof}
"""

import math
import re
from datetime import datetime, timedelta

import pytz

from models import (
    AuditEntry,
    BillResult,
    ParsedOrder,
    ParseError,
    ReconciledInventory,
    Reservation,
    ScheduleResult,
)


# ---------------------------------------------------------------------------
# 1. calculate_bill
# ---------------------------------------------------------------------------

# Coupon format: "PCT:<value>" for percentage, "FIXED:<value>" for dollar amount
_COUPON_RE = re.compile(r"^(PCT|FIXED):(\d+(?:\.\d+)?)$")


def calculate_bill(
    items: list[dict],
    coupons: list[str],
    tax_rate: float,
) -> BillResult:
    """Calculate a restaurant bill with coupons and tax.

    Args:
        items: list of dicts with keys "name" (str), "price" (float), "quantity" (int).
        coupons: list of coupon strings, e.g. "PCT:10" or "FIXED:5.00".
        tax_rate: tax rate as a decimal (e.g. 0.08 for 8%). Must be in [0, 1].

    Returns:
        BillResult with subtotal, discount_total, tax, total, and line_items.

    Raises:
        ValueError: if any price/quantity is negative, tax_rate is out of range,
                    or any numeric value is NaN/Inf.
    """
    # Validate tax_rate
    if not isinstance(tax_rate, (int, float)):
        raise ValueError("tax_rate must be a number")
    if math.isnan(tax_rate) or math.isinf(tax_rate):
        raise ValueError("tax_rate must be finite")
    if tax_rate < 0 or tax_rate > 1:
        raise ValueError("tax_rate must be between 0 and 1")

    line_items: list[dict] = []
    subtotal = 0.0

    for item in items:
        name = str(item.get("name", ""))
        price = item.get("price", 0)
        quantity = item.get("quantity", 0)

        if not isinstance(price, (int, float)):
            raise ValueError(f"price must be a number, got {type(price)}")
        if not isinstance(quantity, (int, float)):
            raise ValueError(f"quantity must be a number, got {type(quantity)}")

        if math.isnan(price) or math.isinf(price):
            raise ValueError("price must be finite")
        if math.isnan(quantity) or math.isinf(quantity):
            raise ValueError("quantity must be finite")

        quantity = int(quantity)
        if price < 0:
            raise ValueError("price must not be negative")
        if quantity < 0:
            raise ValueError("quantity must not be negative")

        line_total = round(price * quantity, 2)
        line_items.append({
            "name": name,
            "price": price,
            "quantity": quantity,
            "line_total": line_total,
        })
        subtotal += line_total

    subtotal = round(subtotal, 2)

    # Apply coupons sequentially
    discount_total = 0.0
    discounted = subtotal

    for coupon in coupons:
        m = _COUPON_RE.match(coupon)
        if m is None:
            continue  # skip invalid coupons silently

        kind, raw_val = m.group(1), float(m.group(2))
        if math.isnan(raw_val) or math.isinf(raw_val):
            continue

        if kind == "PCT":
            pct = min(raw_val, 100.0)  # cap at 100%
            amt = round(discounted * pct / 100.0, 2)
        else:  # FIXED
            amt = round(min(raw_val, discounted), 2)  # never go below 0

        discount_total += amt
        discounted = round(discounted - amt, 2)
        discounted = max(discounted, 0.0)

    discount_total = round(discount_total, 2)

    # Tax is applied after discounts
    tax = round(discounted * tax_rate, 2)
    total = round(discounted + tax, 2)

    return BillResult(
        subtotal=subtotal,
        discount_total=discount_total,
        tax=tax,
        total=total,
        line_items=line_items,
    )


# ---------------------------------------------------------------------------
# 2. schedule_reservation
# ---------------------------------------------------------------------------


def schedule_reservation(
    existing: list[Reservation],
    new: Reservation,
) -> ScheduleResult:
    """Schedule a new reservation, detecting conflicts with existing ones.

    Args:
        existing: list of current reservations (assumed valid).
        new: the reservation to add.

    Returns:
        ScheduleResult containing the full list of reservations and any conflicts.

    Raises:
        ValueError: if the new reservation has invalid fields (non-positive
                    duration, party_size < 1, invalid timezone, or falls in a
                    DST spring-forward gap).
    """
    # Validate timezone
    try:
        tz = pytz.timezone(new.timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Unknown timezone: {new.timezone}")

    # Validate party size
    if new.party_size < 1:
        raise ValueError("party_size must be at least 1")

    # Validate name is non-empty
    if not new.name or not new.name.strip():
        raise ValueError("name must be non-empty")

    # Localize start and end to the reservation's timezone
    try:
        loc_start = tz.localize(new.start, is_dst=None)
        loc_end = tz.localize(new.end, is_dst=None)
    except pytz.exceptions.AmbiguousTimeError:
        # Fall-back: pick is_dst=True (treat as the earlier wall-clock occurrence)
        loc_start = tz.localize(new.start, is_dst=True)
        loc_end = tz.localize(new.end, is_dst=True)
    except pytz.exceptions.NonExistentTimeError:
        raise ValueError("Reservation falls in a DST spring-forward gap")

    # Validate positive duration using UTC
    utc_start = loc_start.astimezone(pytz.utc)
    utc_end = loc_end.astimezone(pytz.utc)
    if utc_end <= utc_start:
        raise ValueError("Reservation must have positive duration (end > start)")

    # Detect conflicts
    conflicts: list[tuple[Reservation, Reservation]] = []
    for ex in existing:
        try:
            ex_tz = pytz.timezone(ex.timezone)
        except pytz.exceptions.UnknownTimeZoneError:
            continue

        try:
            ex_start = ex_tz.localize(ex.start, is_dst=None)
        except (pytz.exceptions.AmbiguousTimeError, pytz.exceptions.NonExistentTimeError):
            ex_start = ex_tz.localize(ex.start, is_dst=True)
        try:
            ex_end = ex_tz.localize(ex.end, is_dst=None)
        except (pytz.exceptions.AmbiguousTimeError, pytz.exceptions.NonExistentTimeError):
            ex_end = ex_tz.localize(ex.end, is_dst=True)

        ex_utc_start = ex_start.astimezone(pytz.utc)
        ex_utc_end = ex_end.astimezone(pytz.utc)

        # Overlap check: two intervals overlap iff start_a < end_b AND start_b < end_a
        if utc_start < ex_utc_end and ex_utc_start < utc_end:
            conflicts.append((ex, new))

    all_reservations = existing + [new]
    return ScheduleResult(reservations=all_reservations, conflicts=conflicts)


# ---------------------------------------------------------------------------
# 3. parse_order
# ---------------------------------------------------------------------------

# Known menu items and common abbreviations
_ABBREVIATIONS: dict[str, str] = {
    "burg": "burger",
    "chsbrgr": "cheeseburger",
    "fries": "fries",
    "ff": "french fries",
    "coke": "coke",
    "pepsi": "pepsi",
    "h2o": "water",
    "oj": "orange juice",
    "blt": "blt sandwich",
    "coff": "coffee",
    "esp": "espresso",
    "chx": "chicken",
    "sal": "salad",
    "sndwch": "sandwich",
    "wrp": "wrap",
}

_MODIFIERS_SET = frozenset({
    "no onion", "no onions", "extra cheese", "no cheese",
    "well done", "medium rare", "rare", "medium",
    "no ice", "extra ice", "no salt", "extra salt",
    "gluten free", "dairy free", "no mayo", "extra mayo",
    "spicy", "mild", "hot", "no pickles", "extra pickles",
    "no tomato", "no lettuce", "add bacon", "no bacon",
    "decaf", "iced", "large", "small", "medium size",
    "to go", "for here", "no sauce", "extra sauce",
})

# Pattern: optional quantity + item name
_ITEM_RE = re.compile(
    r"(\d+)\s*[xX*]?\s+(.+?)(?:\s*,|\s*$)|(.+?)(?:\s*,|\s*$)"
)


def parse_order(text: str) -> "ParsedOrder | ParseError":
    """Parse a free-form text order into structured data.

    This function must NEVER raise an exception. If the input cannot be
    meaningfully parsed, return a ParseError instead.

    Args:
        text: raw order text (may be unicode, empty, adversarial, etc.)

    Returns:
        ParsedOrder on success, ParseError on failure.
    """
    try:
        return _do_parse_order(text)
    except Exception as exc:
        return ParseError(message=str(exc), position=0)


def _do_parse_order(text: str) -> "ParsedOrder | ParseError":
    if not isinstance(text, str):
        return ParseError(message="Input must be a string", position=0)

    raw_text = text
    # Normalize unicode whitespace
    text = " ".join(text.split())
    text = text.strip()

    if not text:
        return ParseError(message="Empty order", position=0)

    # Strip dangerous/injection-like characters but keep the input parseable
    # Remove anything that looks like SQL injection or script tags
    sanitized = text
    sanitized = re.sub(r"<[^>]*>", "", sanitized)  # strip HTML tags
    sanitized = re.sub(r"[;'\"\\\-]{2,}", "", sanitized)  # strip SQL-injection patterns

    sanitized = sanitized.strip()
    if not sanitized:
        return ParseError(message="Order contains only invalid characters", position=0)

    items: list[str] = []
    quantities: list[int] = []
    modifiers: list[str] = []

    # Split on commas and newlines
    parts = re.split(r"[,\n]+", sanitized)

    for part in parts:
        part = part.strip().lower()
        if not part:
            continue

        # Check if this is a modifier
        if part in _MODIFIERS_SET:
            modifiers.append(part)
            continue

        # Check for modifier embedded in item: "2x burger no onion"
        found_mod = None
        for mod in sorted(_MODIFIERS_SET, key=len, reverse=True):
            if part.endswith(" " + mod):
                found_mod = mod
                part = part[: -(len(mod) + 1)].strip()
                break

        if found_mod:
            modifiers.append(found_mod)

        # Try to parse quantity
        m = re.match(r"^(\d+)\s*[xX*]?\s+(.+)$", part)
        if m:
            qty = int(m.group(1))
            item_name = m.group(2).strip()
        else:
            qty = 1
            item_name = part.strip()

        if not item_name:
            continue

        # Expand abbreviations
        item_name = _ABBREVIATIONS.get(item_name, item_name)

        if qty < 1:
            qty = 1

        items.append(item_name)
        quantities.append(qty)

    if not items:
        return ParseError(message="No valid items found in order", position=0)

    return ParsedOrder(
        items=items,
        quantities=quantities,
        modifiers=modifiers,
        raw_text=raw_text,
    )


# ---------------------------------------------------------------------------
# 4. reconcile_inventory
# ---------------------------------------------------------------------------


def reconcile_inventory(
    source_a: dict,
    source_b: dict,
    source_c: dict,
) -> ReconciledInventory:
    """Reconcile inventory counts from three independent sources.

    Resolution strategy:
      - If all three sources agree, use that value.
      - If two sources agree, use the majority value (flagged as conflict).
      - If all three disagree, use the median value (flagged as conflict).
      - Items missing from a source are treated as quantity 0 for that source.
      - Final quantities are clamped to >= 0.

    Args:
        source_a: dict mapping item name (str) to quantity (int).
        source_b: dict mapping item name (str) to quantity (int).
        source_c: dict mapping item name (str) to quantity (int).

    Returns:
        ReconciledInventory with merged items, audit trail, and conflicts list.

    Raises:
        ValueError: if any quantity is not a finite number.
    """
    # Gather all item keys
    all_keys: set[str] = set()
    for src in (source_a, source_b, source_c):
        for k, v in src.items():
            if not isinstance(k, str):
                raise ValueError(f"Item key must be a string, got {type(k)}")
            if not isinstance(v, (int, float)):
                raise ValueError(f"Quantity must be a number, got {type(v)}")
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                raise ValueError("Quantity must be finite")
            all_keys.add(k)

    items: dict[str, int] = {}
    audit_trail: list[AuditEntry] = []
    conflicts: list[str] = []

    for key in sorted(all_keys):
        va = int(source_a.get(key, 0))
        vb = int(source_b.get(key, 0))
        vc = int(source_c.get(key, 0))

        sources = {"source_a": va, "source_b": vb, "source_c": vc}

        if va == vb == vc:
            resolved = va
            method = "unanimous"
        elif va == vb:
            resolved = va
            method = "majority(a,b)"
            conflicts.append(key)
        elif va == vc:
            resolved = va
            method = "majority(a,c)"
            conflicts.append(key)
        elif vb == vc:
            resolved = vb
            method = "majority(b,c)"
            conflicts.append(key)
        else:
            resolved = sorted([va, vb, vc])[1]  # median
            method = "median"
            conflicts.append(key)

        resolved = max(resolved, 0)  # clamp to non-negative
        items[key] = resolved
        audit_trail.append(AuditEntry(
            item=key,
            sources=sources,
            resolved_quantity=resolved,
            resolution_method=method,
        ))

    return ReconciledInventory(
        items=items,
        audit_trail=audit_trail,
        conflicts=conflicts,
    )
