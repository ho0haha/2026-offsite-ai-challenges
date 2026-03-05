#!/usr/bin/env python3
"""
===========================================================================
  RESTAURANT API SERVER - Internal Management System
  Version: 3.7.2-internal
  Last Updated: 2026-02-28

  WARNING: This server is for internal use only. Do not expose to public
  internet without proper gateway configuration. All endpoints require
  proper authentication unless otherwise noted.

  For questions contact: devops@restaurant-internal.local
===========================================================================
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
import sys
import time
import uuid
import base64
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import FastAPI, HTTPException, Request, Response, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# ===========================================================================
# LOGGING CONFIGURATION
# ===========================================================================

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    stream=sys.stdout,
)

logger = logging.getLogger("restaurant_api")
auth_logger = logging.getLogger("restaurant_api.auth")
order_logger = logging.getLogger("restaurant_api.orders")
payment_logger = logging.getLogger("restaurant_api.payments")
rate_limit_logger = logging.getLogger("restaurant_api.ratelimit")
menu_logger = logging.getLogger("restaurant_api.menu")
receipt_logger = logging.getLogger("restaurant_api.receipts")
verify_logger = logging.getLogger("restaurant_api.verify")


# ===========================================================================
# APPLICATION CONSTANTS
# ===========================================================================

APP_NAME = "Restaurant API Server"
APP_VERSION = "3.7.2-internal"
APP_DESCRIPTION = "Internal restaurant management API"

# The shared secret used for HMAC authentication
# In production this would come from a secrets manager
SHARED_SECRET = "restaurant-secret-2026"

# Token configuration
TOKEN_EXPIRY_MINUTES = 30
TOKEN_PREFIX = "rst_"
TOKEN_LENGTH = 48

# Rate limiting configuration
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 60

# Order configuration
MAX_ITEMS_PER_ORDER = 20
MIN_ITEMS_PER_ORDER = 1
MAX_QUANTITY_PER_ITEM = 10
ORDER_ID_PREFIX = "ORD-"

# Payment configuration
PAYMENT_METHODS = ["card", "cash", "gift_card"]
TAX_RATE = 0.0  # No tax for simplicity in this system
SERVICE_FEE = 0.0

# Receipt configuration
RECEIPT_ENCODING = "utf-8"
RECEIPT_VERSION = "v2"

# Verification
FLAG = "CTF{api_explorer_master_chef}"

# Internal system markers
SYSTEM_MARKER_ACTIVE = "ACTIVE"
SYSTEM_MARKER_INACTIVE = "INACTIVE"
SYSTEM_MARKER_MAINTENANCE = "MAINTENANCE"

# Current system status
CURRENT_SYSTEM_STATUS = SYSTEM_MARKER_ACTIVE


# ===========================================================================
# MENU DATA
# ===========================================================================

class MenuCategory(str, Enum):
    """Categories for menu items."""
    APPETIZER = "appetizer"
    MAIN_COURSE = "main_course"
    DESSERT = "dessert"
    BEVERAGE = "beverage"
    SIDE = "side"
    SPECIAL = "special"


# Full restaurant menu with detailed item information
# Each item has: id, name, description, price, category, available, allergens
RESTAURANT_MENU = {
    "items": [
        # === APPETIZERS ===
        {
            "id": "APP-001",
            "name": "Garden Salad",
            "description": "Fresh mixed greens with house vinaigrette dressing, cherry tomatoes, and croutons.",
            "price": 8.99,
            "category": MenuCategory.APPETIZER,
            "available": True,
            "allergens": ["gluten"],
            "preparation_time_minutes": 5,
            "calories": 220,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "APP-002",
            "name": "Truffle Wagyu Tartare",
            "description": "Premium A5 wagyu beef tartare with black truffle shavings, quail egg, and gold leaf. Our signature appetizer.",
            "price": 45.99,
            "category": MenuCategory.APPETIZER,
            "available": True,
            "allergens": ["egg"],
            "preparation_time_minutes": 15,
            "calories": 380,
            "is_vegetarian": False,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "APP-003",
            "name": "Soup of the Day",
            "description": "Chef's daily creation. Ask your server for today's selection.",
            "price": 7.50,
            "category": MenuCategory.APPETIZER,
            "available": True,
            "allergens": ["dairy"],
            "preparation_time_minutes": 3,
            "calories": 180,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 1,
        },
        {
            "id": "APP-004",
            "name": "Crispy Calamari",
            "description": "Lightly battered calamari rings served with marinara sauce and lemon wedges.",
            "price": 12.99,
            "category": MenuCategory.APPETIZER,
            "available": True,
            "allergens": ["gluten", "shellfish"],
            "preparation_time_minutes": 10,
            "calories": 450,
            "is_vegetarian": False,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "APP-005",
            "name": "Bruschetta Trio",
            "description": "Three varieties: classic tomato basil, mushroom truffle, and roasted pepper.",
            "price": 11.50,
            "category": MenuCategory.APPETIZER,
            "available": True,
            "allergens": ["gluten", "dairy"],
            "preparation_time_minutes": 8,
            "calories": 320,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },

        # === MAIN COURSES ===
        {
            "id": "MAIN-001",
            "name": "Grilled Salmon",
            "description": "Atlantic salmon fillet grilled to perfection, served with seasonal vegetables and lemon butter sauce.",
            "price": 24.99,
            "category": MenuCategory.MAIN_COURSE,
            "available": True,
            "allergens": ["fish", "dairy"],
            "preparation_time_minutes": 20,
            "calories": 520,
            "is_vegetarian": False,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "MAIN-002",
            "name": "Ribeye Steak",
            "description": "12oz USDA Prime ribeye, charbroiled to your preference. Served with garlic mashed potatoes.",
            "price": 38.99,
            "category": MenuCategory.MAIN_COURSE,
            "available": True,
            "allergens": ["dairy"],
            "preparation_time_minutes": 25,
            "calories": 780,
            "is_vegetarian": False,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "MAIN-003",
            "name": "Mushroom Risotto",
            "description": "Creamy arborio rice with wild mushroom medley, parmesan, and fresh herbs.",
            "price": 19.99,
            "category": MenuCategory.MAIN_COURSE,
            "available": True,
            "allergens": ["dairy"],
            "preparation_time_minutes": 22,
            "calories": 620,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "MAIN-004",
            "name": "Chicken Parmesan",
            "description": "Breaded chicken breast topped with marinara and melted mozzarella. Served with spaghetti.",
            "price": 18.99,
            "category": MenuCategory.MAIN_COURSE,
            "available": True,
            "allergens": ["gluten", "dairy", "egg"],
            "preparation_time_minutes": 20,
            "calories": 720,
            "is_vegetarian": False,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "MAIN-005",
            "name": "Lobster Tail",
            "description": "8oz cold water lobster tail, broiled with herb butter. Served with drawn butter and asparagus.",
            "price": 42.99,
            "category": MenuCategory.MAIN_COURSE,
            "available": True,
            "allergens": ["shellfish", "dairy"],
            "preparation_time_minutes": 18,
            "calories": 480,
            "is_vegetarian": False,
            "is_vegan": False,
            "spice_level": 0,
        },

        # === DESSERTS ===
        {
            "id": "DES-001",
            "name": "Tiramisu",
            "description": "Classic Italian dessert with espresso-soaked ladyfingers and mascarpone cream.",
            "price": 10.99,
            "category": MenuCategory.DESSERT,
            "available": True,
            "allergens": ["gluten", "dairy", "egg"],
            "preparation_time_minutes": 5,
            "calories": 450,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "DES-002",
            "name": "Chocolate Lava Cake",
            "description": "Warm chocolate cake with a molten center, served with vanilla ice cream.",
            "price": 12.99,
            "category": MenuCategory.DESSERT,
            "available": True,
            "allergens": ["gluten", "dairy", "egg"],
            "preparation_time_minutes": 15,
            "calories": 580,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "DES-003",
            "name": "Creme Brulee",
            "description": "Classic vanilla custard with a caramelized sugar top.",
            "price": 9.99,
            "category": MenuCategory.DESSERT,
            "available": True,
            "allergens": ["dairy", "egg"],
            "preparation_time_minutes": 5,
            "calories": 380,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },

        # === BEVERAGES ===
        {
            "id": "BEV-001",
            "name": "Sparkling Water",
            "description": "San Pellegrino sparkling mineral water, 500ml.",
            "price": 4.50,
            "category": MenuCategory.BEVERAGE,
            "available": True,
            "allergens": [],
            "preparation_time_minutes": 1,
            "calories": 0,
            "is_vegetarian": True,
            "is_vegan": True,
            "spice_level": 0,
        },
        {
            "id": "BEV-002",
            "name": "Fresh Lemonade",
            "description": "House-made lemonade with fresh lemons and a hint of mint.",
            "price": 5.99,
            "category": MenuCategory.BEVERAGE,
            "available": True,
            "allergens": [],
            "preparation_time_minutes": 3,
            "calories": 120,
            "is_vegetarian": True,
            "is_vegan": True,
            "spice_level": 0,
        },
        {
            "id": "BEV-003",
            "name": "Espresso",
            "description": "Double shot of our house blend espresso.",
            "price": 3.99,
            "category": MenuCategory.BEVERAGE,
            "available": True,
            "allergens": [],
            "preparation_time_minutes": 2,
            "calories": 5,
            "is_vegetarian": True,
            "is_vegan": True,
            "spice_level": 0,
        },
        {
            "id": "BEV-004",
            "name": "House Red Wine",
            "description": "Glass of our curated Cabernet Sauvignon selection.",
            "price": 12.00,
            "category": MenuCategory.BEVERAGE,
            "available": True,
            "allergens": ["sulfites"],
            "preparation_time_minutes": 1,
            "calories": 125,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },

        # === SIDES ===
        {
            "id": "SIDE-001",
            "name": "Garlic Bread",
            "description": "Toasted bread with garlic butter and herbs.",
            "price": 5.99,
            "category": MenuCategory.SIDE,
            "available": True,
            "allergens": ["gluten", "dairy"],
            "preparation_time_minutes": 5,
            "calories": 280,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "SIDE-002",
            "name": "Truffle Fries",
            "description": "Crispy fries tossed with truffle oil, parmesan, and fresh parsley.",
            "price": 8.99,
            "category": MenuCategory.SIDE,
            "available": True,
            "allergens": ["dairy"],
            "preparation_time_minutes": 8,
            "calories": 420,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },
        {
            "id": "SIDE-003",
            "name": "Steamed Vegetables",
            "description": "Seasonal vegetables lightly steamed with herb butter.",
            "price": 6.50,
            "category": MenuCategory.SIDE,
            "available": True,
            "allergens": ["dairy"],
            "preparation_time_minutes": 6,
            "calories": 120,
            "is_vegetarian": True,
            "is_vegan": False,
            "spice_level": 0,
        },
    ]
}


# ===========================================================================
# HELPER: MENU LOOKUP UTILITIES
# ===========================================================================

def _build_menu_index() -> Dict[str, dict]:
    """
    Build a dictionary index of menu items keyed by item ID.
    This allows O(1) lookup by item ID instead of scanning the list.
    Called once at startup and cached.
    """
    logger.debug("Building menu index from %d items", len(RESTAURANT_MENU["items"]))
    index = {}
    for item in RESTAURANT_MENU["items"]:
        item_id = item["id"]
        if item_id in index:
            logger.warning("Duplicate menu item ID found: %s", item_id)
        index[item_id] = item
    logger.debug("Menu index built successfully with %d entries", len(index))
    return index


def _get_items_by_category(category: MenuCategory) -> List[dict]:
    """
    Retrieve all menu items belonging to a specific category.
    Returns a list of menu item dictionaries.
    """
    menu_logger.debug("Fetching items for category: %s", category.value)
    result = []
    for item in RESTAURANT_MENU["items"]:
        if item["category"] == category:
            result.append(item)
    menu_logger.debug("Found %d items in category %s", len(result), category.value)
    return result


def _get_available_items() -> List[dict]:
    """
    Return only items that are currently marked as available.
    Filters out any items where available is False.
    """
    menu_logger.debug("Filtering available items from menu")
    available = [item for item in RESTAURANT_MENU["items"] if item.get("available", False)]
    menu_logger.debug("Found %d available items out of %d total", len(available), len(RESTAURANT_MENU["items"]))
    return available


def _calculate_item_price(item_id: str, quantity: int) -> Optional[float]:
    """
    Calculate the total price for a given item ID and quantity.
    Returns None if the item is not found.
    """
    menu_index = _build_menu_index()
    if item_id not in menu_index:
        menu_logger.warning("Item %s not found in menu index", item_id)
        return None
    item = menu_index[item_id]
    unit_price = item["price"]
    total = round(unit_price * quantity, 2)
    menu_logger.debug("Price for %dx %s: $%.2f", quantity, item_id, total)
    return total


def _validate_item_exists(item_id: str) -> bool:
    """Check if an item ID exists in the menu."""
    menu_index = _build_menu_index()
    exists = item_id in menu_index
    menu_logger.debug("Item %s exists: %s", item_id, exists)
    return exists


def _validate_item_available(item_id: str) -> bool:
    """Check if an item ID exists and is available for ordering."""
    menu_index = _build_menu_index()
    if item_id not in menu_index:
        return False
    return menu_index[item_id].get("available", False)


def _get_most_expensive_in_category(category: MenuCategory) -> Optional[dict]:
    """
    Find the most expensive item in a given category.
    Returns the item dictionary or None if no items exist in that category.
    """
    items = _get_items_by_category(category)
    if not items:
        return None
    most_expensive = max(items, key=lambda x: x["price"])
    menu_logger.debug(
        "Most expensive %s: %s at $%.2f",
        category.value,
        most_expensive["name"],
        most_expensive["price"],
    )
    return most_expensive


def _format_menu_for_response() -> dict:
    """
    Format the full menu for API response.
    Groups items by category and includes only relevant fields.
    """
    menu_logger.debug("Formatting menu for API response")
    formatted = {"categories": {}}

    for category in MenuCategory:
        items = _get_items_by_category(category)
        if items:
            formatted["categories"][category.value] = []
            for item in items:
                formatted_item = {
                    "id": item["id"],
                    "name": item["name"],
                    "description": item["description"],
                    "price": item["price"],
                    "available": item["available"],
                    "allergens": item["allergens"],
                }
                formatted["categories"][category.value].append(formatted_item)

    formatted["total_items"] = len(RESTAURANT_MENU["items"])
    formatted["last_updated"] = "2026-02-28T12:00:00Z"

    menu_logger.debug("Menu formatted with %d categories", len(formatted["categories"]))
    return formatted


def _search_menu_items(query: str) -> List[dict]:
    """
    Search menu items by name or description (case-insensitive).
    Returns matching items.
    """
    query_lower = query.lower()
    results = []
    for item in RESTAURANT_MENU["items"]:
        if query_lower in item["name"].lower() or query_lower in item["description"].lower():
            results.append(item)
    return results


def _get_menu_item_by_name(name: str) -> Optional[dict]:
    """
    Look up a menu item by its exact name (case-insensitive).
    Returns the item or None.
    """
    name_lower = name.lower()
    for item in RESTAURANT_MENU["items"]:
        if item["name"].lower() == name_lower:
            return item
    return None


# ===========================================================================
# HELPER: HMAC AUTHENTICATION UTILITIES
# ===========================================================================

def _compute_hmac_signature(
    secret: str,
    timestamp: str,
    method: str,
    path: str,
) -> str:
    """
    Compute HMAC-SHA256 signature for request authentication.

    The message is constructed as: timestamp + method + path
    The signature is returned as a hex digest.

    Args:
        secret: The shared secret key
        timestamp: Unix timestamp as string
        method: HTTP method (GET, POST, etc.)
        path: The request path (e.g., /api/auth/token)

    Returns:
        Hex-encoded HMAC-SHA256 signature
    """
    auth_logger.debug(
        "Computing HMAC signature for %s %s at timestamp %s",
        method, path, timestamp,
    )

    message = f"{timestamp}{method}{path}"

    signature = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    auth_logger.debug("Computed signature: %s...%s", signature[:8], signature[-8:])
    return signature


def _verify_hmac_signature(
    provided_signature: str,
    timestamp: str,
    method: str,
    path: str,
) -> bool:
    """
    Verify that a provided HMAC signature matches the expected signature.

    Uses constant-time comparison to prevent timing attacks.
    Also checks that the timestamp is within an acceptable window.

    Args:
        provided_signature: The signature from the request headers
        timestamp: The timestamp from the request headers
        method: The HTTP method
        path: The request path

    Returns:
        True if the signature is valid, False otherwise
    """
    auth_logger.debug("Verifying HMAC signature for %s %s", method, path)

    # Check timestamp freshness (within 5 minutes)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        time_diff = abs(current_time - request_time)

        if time_diff > 300:  # 5 minutes
            auth_logger.warning(
                "Timestamp too old: %d seconds difference", time_diff
            )
            return False
    except (ValueError, TypeError):
        auth_logger.warning("Invalid timestamp format: %s", timestamp)
        return False

    expected = _compute_hmac_signature(SHARED_SECRET, timestamp, method, path)

    is_valid = hmac.compare_digest(provided_signature, expected)
    auth_logger.debug("Signature verification result: %s", is_valid)
    return is_valid


def _generate_auth_scheme_description() -> dict:
    """
    Generate the description of the authentication scheme.
    This is returned by the /api/auth/discover endpoint.
    """
    return {
        "auth_type": "HMAC-SHA256",
        "description": "Sign requests using HMAC-SHA256. The message to sign is the concatenation of: timestamp + HTTP_METHOD + path. Include the signature in the X-Signature header and the timestamp in the X-Timestamp header.",
        "shared_secret": SHARED_SECRET,
        "headers_required": {
            "X-Signature": "HMAC-SHA256 hex digest of (timestamp + method + path)",
            "X-Timestamp": "Current Unix timestamp (integer as string)",
        },
        "example": {
            "method": "POST",
            "path": "/api/auth/token",
            "timestamp": "1709312400",
            "message_to_sign": "1709312400POST/api/auth/token",
            "note": "Use the shared_secret as the HMAC key",
        },
        "next_step": "POST /api/auth/token with valid X-Signature and X-Timestamp headers to obtain a Bearer token",
    }


# ===========================================================================
# HELPER: TOKEN MANAGEMENT
# ===========================================================================

# In-memory token store: token_string -> {session_id, created_at, expires_at}
_active_tokens: Dict[str, dict] = {}

# Token cleanup tracking
_last_token_cleanup = time.time()
_TOKEN_CLEANUP_INTERVAL = 300  # 5 minutes


def _generate_token() -> str:
    """
    Generate a new authentication token.
    Tokens are prefixed with TOKEN_PREFIX for easy identification.
    """
    raw_token = secrets.token_hex(TOKEN_LENGTH // 2)
    token = f"{TOKEN_PREFIX}{raw_token}"
    auth_logger.debug("Generated new token: %s...%s", token[:8], token[-4:])
    return token


def _create_session_token() -> dict:
    """
    Create a new session token and store it.
    Returns the token info dict with token string, session ID, and expiry.
    """
    _cleanup_expired_tokens()

    token = _generate_token()
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=TOKEN_EXPIRY_MINUTES)

    token_info = {
        "token": token,
        "session_id": session_id,
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "expires_in_seconds": TOKEN_EXPIRY_MINUTES * 60,
    }

    _active_tokens[token] = {
        "session_id": session_id,
        "created_at": now,
        "expires_at": expires_at,
    }

    auth_logger.info(
        "Created session token for session %s, expires at %s",
        session_id, expires_at.isoformat(),
    )

    return token_info


def _validate_token(token: str) -> Optional[dict]:
    """
    Validate a bearer token and return session info if valid.
    Returns None if the token is invalid or expired.
    """
    _cleanup_expired_tokens()

    if not token:
        auth_logger.debug("Empty token provided")
        return None

    # Strip 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token[7:]

    if token not in _active_tokens:
        auth_logger.debug("Token not found in active tokens")
        return None

    token_data = _active_tokens[token]
    now = datetime.now(timezone.utc)

    if now > token_data["expires_at"]:
        auth_logger.info("Token expired for session %s", token_data["session_id"])
        del _active_tokens[token]
        return None

    auth_logger.debug("Token valid for session %s", token_data["session_id"])
    return token_data


def _cleanup_expired_tokens():
    """
    Remove expired tokens from the active token store.
    Only runs if enough time has passed since last cleanup.
    """
    global _last_token_cleanup

    now_ts = time.time()
    if now_ts - _last_token_cleanup < _TOKEN_CLEANUP_INTERVAL:
        return

    _last_token_cleanup = now_ts
    now = datetime.now(timezone.utc)
    expired = [
        token for token, data in _active_tokens.items()
        if now > data["expires_at"]
    ]

    for token in expired:
        auth_logger.debug("Cleaning up expired token for session %s", _active_tokens[token]["session_id"])
        del _active_tokens[token]

    if expired:
        auth_logger.info("Cleaned up %d expired tokens", len(expired))


def _get_active_session_count() -> int:
    """Return the count of currently active sessions."""
    _cleanup_expired_tokens()
    return len(_active_tokens)


# ===========================================================================
# HELPER: RATE LIMITING
# ===========================================================================

# Rate limit tracking: IP -> list of timestamps
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)
_last_rate_limit_cleanup = time.time()
_RATE_LIMIT_CLEANUP_INTERVAL = 120


def _check_rate_limit(client_ip: str) -> Tuple[bool, int]:
    """
    Check if a client has exceeded the rate limit.

    Args:
        client_ip: The client's IP address

    Returns:
        Tuple of (is_allowed, remaining_requests)
    """
    _cleanup_rate_limit_store()

    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    # Remove old entries for this IP
    _rate_limit_store[client_ip] = [
        ts for ts in _rate_limit_store[client_ip]
        if ts > window_start
    ]

    current_count = len(_rate_limit_store[client_ip])
    remaining = max(0, RATE_LIMIT_MAX_REQUESTS - current_count)

    if current_count >= RATE_LIMIT_MAX_REQUESTS:
        rate_limit_logger.warning(
            "Rate limit exceeded for %s: %d requests in window",
            client_ip, current_count,
        )
        return False, 0

    # Record this request
    _rate_limit_store[client_ip].append(now)

    rate_limit_logger.debug(
        "Rate limit check for %s: %d/%d (remaining: %d)",
        client_ip, current_count + 1, RATE_LIMIT_MAX_REQUESTS, remaining - 1,
    )

    return True, remaining - 1


def _cleanup_rate_limit_store():
    """Periodically clean up old rate limit entries."""
    global _last_rate_limit_cleanup

    now = time.time()
    if now - _last_rate_limit_cleanup < _RATE_LIMIT_CLEANUP_INTERVAL:
        return

    _last_rate_limit_cleanup = now
    window_start = now - RATE_LIMIT_WINDOW_SECONDS

    empty_ips = []
    for ip, timestamps in _rate_limit_store.items():
        _rate_limit_store[ip] = [ts for ts in timestamps if ts > window_start]
        if not _rate_limit_store[ip]:
            empty_ips.append(ip)

    for ip in empty_ips:
        del _rate_limit_store[ip]

    if empty_ips:
        rate_limit_logger.debug("Cleaned up rate limit entries for %d IPs", len(empty_ips))


def _get_rate_limit_headers(remaining: int) -> dict:
    """Generate rate limit headers for responses."""
    return {
        "X-RateLimit-Limit": str(RATE_LIMIT_MAX_REQUESTS),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Window": f"{RATE_LIMIT_WINDOW_SECONDS}s",
    }


# ===========================================================================
# HELPER: ORDER MANAGEMENT
# ===========================================================================

class OrderStatus(str, Enum):
    """Possible statuses for an order."""
    CREATED = "created"
    PENDING_MODIFICATION = "pending_modification"
    MODIFIED = "modified"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# In-memory order store: order_id -> order data
_orders: Dict[str, dict] = {}

# Order sequence counter
_order_counter = 0


def _generate_order_id() -> str:
    """Generate a unique order ID."""
    global _order_counter
    _order_counter += 1
    order_id = f"{ORDER_ID_PREFIX}{_order_counter:06d}"
    order_logger.debug("Generated order ID: %s", order_id)
    return order_id


def _create_order(session_id: str, items: List[dict]) -> dict:
    """
    Create a new order.

    Args:
        session_id: The session ID of the authenticated user
        items: List of {"item_id": str, "quantity": int}

    Returns:
        The created order dict
    """
    order_id = _generate_order_id()
    menu_index = _build_menu_index()

    order_items = []
    subtotal = 0.0

    for item_request in items:
        item_id = item_request["item_id"]
        quantity = item_request["quantity"]

        menu_item = menu_index.get(item_id)
        if not menu_item:
            continue

        item_total = round(menu_item["price"] * quantity, 2)
        subtotal += item_total

        order_items.append({
            "item_id": item_id,
            "name": menu_item["name"],
            "unit_price": menu_item["price"],
            "quantity": quantity,
            "total": item_total,
        })

    subtotal = round(subtotal, 2)
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax + SERVICE_FEE, 2)

    order = {
        "order_id": order_id,
        "session_id": session_id,
        "status": OrderStatus.PENDING_MODIFICATION,
        "items": order_items,
        "subtotal": subtotal,
        "tax": tax,
        "service_fee": SERVICE_FEE,
        "total": total,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_at_ts": time.time(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "payment": None,
        "receipt": None,
        "modification_hint": _generate_modification_hint(),
    }

    _orders[order_id] = order

    order_logger.info(
        "Created order %s for session %s with %d items, total: $%.2f",
        order_id, session_id, len(order_items), total,
    )

    return order


def _generate_modification_hint() -> str:
    """Generate the hint for order modification step."""
    most_expensive_app = _get_most_expensive_in_category(MenuCategory.APPETIZER)
    if most_expensive_app:
        return (
            f"Your order needs the chef's special touch. "
            f"Item hint: it's the most expensive appetizer on the menu. "
            f"Think luxurious..."
        )
    return "Check the appetizer section of the menu for the chef's special."


def _get_order(order_id: str) -> Optional[dict]:
    """Retrieve an order by ID."""
    order = _orders.get(order_id)
    if order:
        order_logger.debug("Retrieved order %s (status: %s)", order_id, order["status"])
    else:
        order_logger.debug("Order %s not found", order_id)
    return order


def _modify_order(order_id: str, items_to_add: List[dict]) -> Optional[dict]:
    """
    Add items to an existing order.

    Only works if the order is in PENDING_MODIFICATION status.
    """
    order = _orders.get(order_id)
    if not order:
        return None

    if order["status"] != OrderStatus.PENDING_MODIFICATION:
        order_logger.warning(
            "Cannot modify order %s in status %s", order_id, order["status"]
        )
        return None

    menu_index = _build_menu_index()

    for item_request in items_to_add:
        item_id = item_request["item_id"]
        quantity = item_request.get("quantity", 1)

        menu_item = menu_index.get(item_id)
        if not menu_item:
            continue

        item_total = round(menu_item["price"] * quantity, 2)

        order["items"].append({
            "item_id": item_id,
            "name": menu_item["name"],
            "unit_price": menu_item["price"],
            "quantity": quantity,
            "total": item_total,
        })

    # Recalculate totals
    subtotal = sum(item["total"] for item in order["items"])
    subtotal = round(subtotal, 2)
    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax + SERVICE_FEE, 2)

    order["subtotal"] = subtotal
    order["tax"] = tax
    order["total"] = total
    order["status"] = OrderStatus.PENDING_PAYMENT
    order["updated_at"] = datetime.now(timezone.utc).isoformat()

    order_logger.info(
        "Modified order %s: added %d items, new total: $%.2f",
        order_id, len(items_to_add), total,
    )

    return order


def _process_payment(order_id: str, amount: float) -> Optional[dict]:
    """
    Process payment for an order.

    The amount must match the order total exactly.
    """
    order = _orders.get(order_id)
    if not order:
        payment_logger.warning("Payment attempted for non-existent order %s", order_id)
        return None

    if order["status"] != OrderStatus.PENDING_PAYMENT:
        payment_logger.warning(
            "Payment attempted for order %s in status %s",
            order_id, order["status"],
        )
        return None

    # Check amount matches
    expected = order["total"]
    if abs(amount - expected) > 0.01:
        payment_logger.warning(
            "Payment amount mismatch for order %s: expected $%.2f, got $%.2f",
            order_id, expected, amount,
        )
        return None

    payment_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"

    payment_info = {
        "payment_id": payment_id,
        "amount": amount,
        "method": "card",
        "status": "completed",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    order["payment"] = payment_info
    order["status"] = OrderStatus.PAID
    order["updated_at"] = datetime.now(timezone.utc).isoformat()

    payment_logger.info(
        "Payment %s processed for order %s: $%.2f",
        payment_id, order_id, amount,
    )

    return payment_info


def _generate_receipt(order_id: str) -> Optional[dict]:
    """
    Generate a receipt for a paid order.
    Includes a base64-encoded verification payload.
    """
    order = _orders.get(order_id)
    if not order:
        receipt_logger.warning("Receipt requested for non-existent order %s", order_id)
        return None

    if order["status"] != OrderStatus.PAID:
        receipt_logger.warning(
            "Receipt requested for order %s in status %s (must be PAID)",
            order_id, order["status"],
        )
        return None

    # Build verification data
    verification_payload = {
        "order_id": order_id,
        "total": order["total"],
        "payment_id": order["payment"]["payment_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verification_code": hashlib.sha256(
            f"{order_id}:{order['total']}:{SHARED_SECRET}".encode()
        ).hexdigest()[:16],
    }

    # Encode the verification payload
    encoded_verification = base64.b64encode(
        json.dumps(verification_payload).encode(RECEIPT_ENCODING)
    ).decode(RECEIPT_ENCODING)

    receipt = {
        "receipt_id": f"REC-{uuid.uuid4().hex[:12].upper()}",
        "order_id": order_id,
        "items": order["items"],
        "subtotal": order["subtotal"],
        "tax": order["tax"],
        "total": order["total"],
        "payment": order["payment"],
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "verification_data": encoded_verification,
        "hint": "The verification_data is base64 encoded. Decode it and POST the JSON to /api/verify to complete your journey.",
    }

    order["receipt"] = receipt

    receipt_logger.info("Generated receipt for order %s", order_id)

    return receipt


def _verify_receipt_data(verification_data: dict) -> Optional[str]:
    """
    Verify decoded receipt data and return the flag if valid.

    The verification_data should contain:
    - order_id
    - total
    - payment_id
    - verification_code
    """
    verify_logger.info("Verifying receipt data: %s", verification_data)

    order_id = verification_data.get("order_id")
    if not order_id:
        verify_logger.warning("Missing order_id in verification data")
        return None

    order = _orders.get(order_id)
    if not order:
        verify_logger.warning("Order %s not found during verification", order_id)
        return None

    if order["status"] != OrderStatus.PAID:
        verify_logger.warning("Order %s is not in PAID status", order_id)
        return None

    # Verify the verification code
    expected_code = hashlib.sha256(
        f"{order_id}:{order['total']}:{SHARED_SECRET}".encode()
    ).hexdigest()[:16]

    provided_code = verification_data.get("verification_code")
    if provided_code != expected_code:
        verify_logger.warning("Invalid verification code for order %s", order_id)
        return None

    # Check payment ID matches
    expected_payment_id = order.get("payment", {}).get("payment_id")
    provided_payment_id = verification_data.get("payment_id")
    if provided_payment_id != expected_payment_id:
        verify_logger.warning("Payment ID mismatch for order %s", order_id)
        return None

    verify_logger.info("Verification successful for order %s!", order_id)
    return FLAG


# ===========================================================================
# HELPER: RESPONSE FORMATTING
# ===========================================================================

def _error_response(
    status_code: int,
    message: str,
    hint: str,
    details: Optional[dict] = None,
) -> JSONResponse:
    """
    Create a standardized error response.
    All error responses include a hint field to guide the user.
    """
    body = {
        "error": True,
        "status_code": status_code,
        "message": message,
        "hint": hint,
    }
    if details:
        body["details"] = details

    logger.debug("Returning error %d: %s", status_code, message)
    return JSONResponse(status_code=status_code, content=body)


def _success_response(
    data: dict,
    status_code: int = 200,
    extra_headers: Optional[dict] = None,
) -> JSONResponse:
    """Create a standardized success response."""
    response = JSONResponse(status_code=status_code, content=data)
    if extra_headers:
        for key, value in extra_headers.items():
            response.headers[key] = value
    return response


def _format_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _format_order_summary(order: dict) -> dict:
    """Format an order for API response (summary view)."""
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "item_count": len(order["items"]),
        "total": order["total"],
        "created_at": order["created_at"],
        "updated_at": order["updated_at"],
    }


def _format_order_detail(order: dict) -> dict:
    """Format an order for API response (detailed view)."""
    return {
        "order_id": order["order_id"],
        "status": order["status"],
        "items": order["items"],
        "subtotal": order["subtotal"],
        "tax": order["tax"],
        "service_fee": order["service_fee"],
        "total": order["total"],
        "created_at": order["created_at"],
        "updated_at": order["updated_at"],
    }


# ===========================================================================
# HELPER: INPUT VALIDATION
# ===========================================================================

def _validate_order_items(items: list) -> Tuple[bool, str]:
    """
    Validate order items list.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not items:
        return False, "Items list cannot be empty"

    if len(items) > MAX_ITEMS_PER_ORDER:
        return False, f"Maximum {MAX_ITEMS_PER_ORDER} different items per order"

    if len(items) < MIN_ITEMS_PER_ORDER:
        return False, f"Minimum {MIN_ITEMS_PER_ORDER} item per order"

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return False, f"Item at index {i} must be an object"

        if "item_id" not in item:
            return False, f"Item at index {i} missing 'item_id'"

        if "quantity" not in item:
            return False, f"Item at index {i} missing 'quantity'"

        item_id = item["item_id"]
        quantity = item["quantity"]

        if not isinstance(quantity, int) or quantity < 1:
            return False, f"Invalid quantity for item {item_id}: must be a positive integer"

        if quantity > MAX_QUANTITY_PER_ITEM:
            return False, f"Maximum quantity per item is {MAX_QUANTITY_PER_ITEM}"

        if not _validate_item_exists(item_id):
            return False, f"Item {item_id} does not exist in the menu"

        if not _validate_item_available(item_id):
            return False, f"Item {item_id} is not currently available"

    return True, ""


def _validate_payment_amount(amount) -> Tuple[bool, str]:
    """Validate that a payment amount is a valid number."""
    if amount is None:
        return False, "Payment amount is required"

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return False, "Payment amount must be a number"

    if amount <= 0:
        return False, "Payment amount must be positive"

    if amount > 10000:
        return False, "Payment amount exceeds maximum ($10,000)"

    return True, ""


def _validate_modification_items(items: list) -> Tuple[bool, str]:
    """Validate items to be added in an order modification."""
    if not items:
        return False, "Items to add cannot be empty"

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            return False, f"Item at index {i} must be an object"

        if "item_id" not in item:
            return False, f"Item at index {i} missing 'item_id'"

        item_id = item["item_id"]
        quantity = item.get("quantity", 1)

        if not isinstance(quantity, int) or quantity < 1:
            return False, f"Invalid quantity for item {item_id}"

        if not _validate_item_exists(item_id):
            return False, f"Item {item_id} does not exist"

        if not _validate_item_available(item_id):
            return False, f"Item {item_id} is not available"

    return True, ""


# ===========================================================================
# HELPER: INTERNAL SYSTEM UTILITIES
# ===========================================================================

def _log_request_info(request: Request):
    """Log basic information about an incoming request."""
    logger.debug(
        "Incoming request: %s %s from %s",
        request.method,
        request.url.path,
        request.client.host if request.client else "unknown",
    )


def _get_client_ip(request: Request) -> str:
    """Extract the client IP from the request."""
    if request.client:
        return request.client.host
    return "127.0.0.1"


def _sanitize_input(value: str, max_length: int = 500) -> str:
    """Basic input sanitization."""
    if not isinstance(value, str):
        return str(value)[:max_length]
    return value.strip()[:max_length]


def _generate_request_id() -> str:
    """Generate a unique request ID for tracking."""
    return f"req_{uuid.uuid4().hex[:16]}"


def _check_system_status() -> bool:
    """Check if the system is in an active state."""
    return CURRENT_SYSTEM_STATUS == SYSTEM_MARKER_ACTIVE


def _get_server_info() -> dict:
    """Get basic server information."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": CURRENT_SYSTEM_STATUS,
        "uptime_note": "Server started at process launch",
    }


def _calculate_order_hash(order: dict) -> str:
    """Calculate a hash of an order for integrity checking."""
    order_string = json.dumps(
        {
            "order_id": order["order_id"],
            "items": order["items"],
            "total": order["total"],
        },
        sort_keys=True,
    )
    return hashlib.md5(order_string.encode()).hexdigest()


def _is_valid_order_id_format(order_id: str) -> bool:
    """Check if a string looks like a valid order ID."""
    if not order_id:
        return False
    return order_id.startswith(ORDER_ID_PREFIX) and len(order_id) > len(ORDER_ID_PREFIX)


# ===========================================================================
# PYDANTIC MODELS
# ===========================================================================

class OrderItemRequest(BaseModel):
    """Request model for a single order item."""
    item_id: str = Field(..., description="Menu item ID")
    quantity: int = Field(..., ge=1, le=MAX_QUANTITY_PER_ITEM, description="Quantity to order")


class CreateOrderRequest(BaseModel):
    """Request model for creating an order."""
    items: List[OrderItemRequest] = Field(
        ..., min_length=1, max_length=MAX_ITEMS_PER_ORDER,
        description="List of items to order"
    )


class ModifyOrderRequest(BaseModel):
    """Request model for modifying an order."""
    items_to_add: List[OrderItemRequest] = Field(
        ..., min_length=1,
        description="List of items to add to the order"
    )


class PaymentRequest(BaseModel):
    """Request model for payment."""
    amount: float = Field(..., gt=0, description="Payment amount")
    method: Optional[str] = Field("card", description="Payment method")


class VerifyRequest(BaseModel):
    """Request model for verification."""
    verification_data: dict = Field(..., description="Decoded verification data from receipt")


# ===========================================================================
# FASTAPI APPLICATION SETUP
# ===========================================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url=None,  # Disable auto docs
    redoc_url=None,  # Disable redoc
    openapi_url=None,  # Disable OpenAPI schema
)


# ===========================================================================
# MIDDLEWARE: RATE LIMITING & REQUEST LOGGING
# ===========================================================================

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to enforce rate limiting on all requests.
    Also logs request information and adds tracking headers.
    """
    request_id = _generate_request_id()
    client_ip = _get_client_ip(request)

    _log_request_info(request)

    # Check rate limit
    is_allowed, remaining = _check_rate_limit(client_ip)

    if not is_allowed:
        rate_limit_logger.warning(
            "Rate limit exceeded for %s on %s %s",
            client_ip, request.method, request.url.path,
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": True,
                "status_code": 429,
                "message": "Rate limit exceeded",
                "hint": f"You are limited to {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW_SECONDS} seconds. "
                        f"Slow down and think about each request. Quality over quantity! "
                        f"Tip: Plan your exploration strategy before making rapid requests.",
                "retry_after_seconds": RATE_LIMIT_WINDOW_SECONDS,
            },
            headers={
                "Retry-After": str(RATE_LIMIT_WINDOW_SECONDS),
                "X-RateLimit-Limit": str(RATE_LIMIT_MAX_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-Request-ID": request_id,
            },
        )

    # Process the request
    response = await call_next(request)

    # Add rate limit headers to all responses
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-Request-ID"] = request_id

    return response


# ===========================================================================
# DEPENDENCY: AUTH TOKEN VALIDATION
# ===========================================================================

async def require_auth(request: Request) -> dict:
    """
    FastAPI dependency that validates the Authorization header.
    Returns session info if valid, raises HTTPException otherwise.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail={
                "error": True,
                "message": "Missing Authorization header",
                "hint": "Include an 'Authorization: Bearer <token>' header. "
                        "Get a token by first discovering the auth scheme at POST /api/auth/discover, "
                        "then requesting a token at POST /api/auth/token with proper HMAC signature.",
            },
        )

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={
                "error": True,
                "message": "Invalid Authorization format",
                "hint": "Use 'Bearer <token>' format. Example: 'Authorization: Bearer rst_abc123...'",
            },
        )

    token = auth_header[7:]
    session_info = _validate_token(token)

    if not session_info:
        raise HTTPException(
            status_code=401,
            detail={
                "error": True,
                "message": "Invalid or expired token",
                "hint": "Your token may have expired (tokens last 30 minutes). "
                        "Request a new token at POST /api/auth/token with valid HMAC signature.",
            },
        )

    return session_info


# ===========================================================================
# ROUTE: HEALTH CHECK (THE ENTRY POINT)
# ===========================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint - the only documented endpoint.
    This is the starting point for API exploration.
    """
    logger.info("Health check requested")

    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "timestamp": _format_timestamp(),
        "hint": "Try POST /api/auth/discover",
    }


# ===========================================================================
# ROUTE: AUTH DISCOVERY
# ===========================================================================

@app.post("/api/auth/discover")
async def auth_discover():
    """
    Discover the authentication scheme used by this API.
    Returns detailed instructions on how to authenticate.
    """
    auth_logger.info("Auth scheme discovery requested")

    scheme = _generate_auth_scheme_description()

    return {
        "success": True,
        "auth_scheme": scheme,
        "hint": "Use the shared_secret to compute HMAC-SHA256 signatures. "
                "Next step: POST /api/auth/token with X-Signature and X-Timestamp headers.",
    }


# ===========================================================================
# ROUTE: TOKEN REQUEST
# ===========================================================================

@app.post("/api/auth/token")
async def request_token(request: Request):
    """
    Request an authentication token.
    Requires valid HMAC signature in X-Signature header and
    timestamp in X-Timestamp header.
    """
    auth_logger.info("Token request received")

    # Get required headers
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")

    if not signature:
        return _error_response(
            401,
            "Missing X-Signature header",
            "Compute HMAC-SHA256 of (timestamp + 'POST' + '/api/auth/token') using the shared_secret, "
            "and include it as the X-Signature header. Also include X-Timestamp with current Unix timestamp.",
        )

    if not timestamp:
        return _error_response(
            401,
            "Missing X-Timestamp header",
            "Include the current Unix timestamp as the X-Timestamp header value. "
            "Example: X-Timestamp: 1709312400",
        )

    # Verify the signature
    is_valid = _verify_hmac_signature(
        signature, timestamp, "POST", "/api/auth/token"
    )

    if not is_valid:
        return _error_response(
            401,
            "Invalid HMAC signature",
            "Double-check your signature computation. The message to sign is: "
            "timestamp + 'POST' + '/api/auth/token' (concatenated, no separators). "
            "Use HMAC-SHA256 with the shared_secret as key. "
            "Make sure your timestamp is current (within 5 minutes).",
            details={
                "expected_message_format": "<timestamp>POST/api/auth/token",
                "algorithm": "HMAC-SHA256",
                "output_format": "hex digest",
            },
        )

    # Generate token
    token_info = _create_session_token()

    auth_logger.info("Token issued for session %s", token_info["session_id"])

    return {
        "success": True,
        "token": token_info["token"],
        "token_type": "Bearer",
        "session_id": token_info["session_id"],
        "expires_at": token_info["expires_at"],
        "expires_in_seconds": token_info["expires_in_seconds"],
        "hint": "Use this token in the Authorization header: 'Bearer <token>'. "
                "Next step: GET /api/menu to see what's available.",
    }


# ===========================================================================
# ROUTE: MENU
# ===========================================================================

@app.get("/api/menu")
async def get_menu(session: dict = Depends(require_auth)):
    """
    Get the full restaurant menu.
    Requires authentication.
    """
    menu_logger.info("Menu requested by session %s", session["session_id"])

    menu_data = _format_menu_for_response()

    response = JSONResponse(content={
        "success": True,
        "menu": menu_data,
        "hint": "Choose items and place an order with POST /api/order. "
                "Send a JSON body with an 'items' array containing objects with 'item_id' and 'quantity'.",
    })
    response.headers["X-Menu-Version"] = "1.0"
    return response


# ===========================================================================
# ROUTE: CATALOG (dead-end)
# ===========================================================================

@app.get("/api/v1/catalog")
async def get_catalog(request: Request):
    """Return a plausible but fake menu catalog."""
    fake_items = []
    for i, item in enumerate(RESTAURANT_MENU["items"]):
        fake_items.append({
            "catalog_id": f"CAT-{9000 + i}",
            "name": item["name"],
            "price": item["price"],
            "category": item["category"],
        })
    return JSONResponse({"catalog": fake_items, "version": "2.1"})


# ===========================================================================
# ROUTE: CREATE ORDER
# ===========================================================================

@app.post("/api/order")
async def create_order(
    request: Request,
    session: dict = Depends(require_auth),
):
    """
    Place a new order.
    Requires authentication and a JSON body with items.
    """
    order_logger.info("Order creation requested by session %s", session["session_id"])

    try:
        body = await request.json()
    except Exception:
        return _error_response(
            400,
            "Invalid JSON body",
            "Send a JSON body with an 'items' array. Example: "
            '{"items": [{"item_id": "MAIN-001", "quantity": 1}]}',
        )

    items = body.get("items")
    if not items:
        return _error_response(
            400,
            "Missing 'items' in request body",
            "Include an 'items' array with at least one item. Each item needs 'item_id' and 'quantity'. "
            "Check GET /api/menu for available item IDs.",
        )

    # Detect catalog IDs (from dead-end /api/v1/catalog) and accept silently
    has_catalog_ids = any(
        isinstance(item, dict) and str(item.get("item_id", "")).startswith("CAT-")
        for item in items
    )
    if has_catalog_ids:
        order_logger.info("Order with catalog IDs detected - returning fake pending status")
        return JSONResponse(content={
            "status": "pending",
            "message": "Order is being processed",
        })

    # Validate items
    is_valid, error_msg = _validate_order_items(items)
    if not is_valid:
        return _error_response(
            400,
            f"Invalid order items: {error_msg}",
            "Check your item IDs against the menu (GET /api/menu). "
            "Each item needs a valid 'item_id' and a positive integer 'quantity'.",
        )

    # Create the order
    order = _create_order(session["session_id"], items)

    return {
        "success": True,
        "order": _format_order_detail(order),
        "hint": f"Order created! Check your order status at GET /api/order/{order['order_id']}/status",
    }


# ===========================================================================
# ROUTE: ORDER STATUS
# ===========================================================================

@app.get("/api/order/{order_id}/status")
async def get_order_status(order_id: str):
    """
    Get the current status of an order.
    Includes hints about what to do next based on the status.
    """
    order_logger.info("Status requested for order %s", order_id)

    if not _is_valid_order_id_format(order_id):
        return _error_response(
            400,
            "Invalid order ID format",
            f"Order IDs look like '{ORDER_ID_PREFIX}000001'. Check the order_id from your create order response.",
        )

    order = _get_order(order_id)
    if not order:
        return _error_response(
            404,
            f"Order {order_id} not found",
            "Make sure you're using the correct order_id from the create order response.",
        )

    # Build status-specific hints
    status_hints = {
        OrderStatus.PENDING_MODIFICATION: (
            f"Your order needs the chef's special. {order.get('modification_hint', '')} "
            f"Use POST /api/order/{order_id}/modify to add the required item. "
            f"Send a JSON body with 'items_to_add' array."
        ),
        OrderStatus.MODIFIED: (
            f"Your order has been modified. Proceed to payment with POST /api/order/{order_id}/pay"
        ),
        OrderStatus.PENDING_PAYMENT: (
            f"Ready for payment! POST /api/order/{order_id}/pay with "
            f'{{"amount": {order["total"]}}} to pay the exact total.'
        ),
        OrderStatus.PAID: (
            f"Payment received! Get your receipt at GET /api/order/{order_id}/receipt"
        ),
    }

    hint = status_hints.get(
        order["status"],
        "Check back later for updates on your order.",
    )

    return {
        "success": True,
        "order_id": order_id,
        "status": order["status"],
        "total": order["total"],
        "item_count": len(order["items"]),
        "hint": hint,
    }


# ===========================================================================
# ROUTE: MODIFY ORDER
# ===========================================================================

@app.post("/api/order/{order_id}/modify")
async def modify_order(order_id: str, request: Request):
    """
    Modify an existing order by adding items.
    Only works for orders in 'pending_modification' status.
    """
    order_logger.info("Modification requested for order %s", order_id)

    order = _get_order(order_id)
    if not order:
        return _error_response(
            404,
            f"Order {order_id} not found",
            "Check your order_id.",
        )

    if order["status"] != OrderStatus.PENDING_MODIFICATION:
        return _error_response(
            409,
            f"Order {order_id} cannot be modified (status: {order['status']})",
            f"Only orders with status 'pending_modification' can be modified. "
            f"Current status is '{order['status']}'.",
        )

    # Check if order is ready for modification (5-second processing delay)
    created_at = order.get("created_at_ts", 0)
    if time.time() - created_at < 5:
        remaining = 5 - (time.time() - created_at)
        return JSONResponse(
            status_code=425,
            content={"error": "Too Early", "ready_in_seconds": round(remaining, 1),
                     "message": "Order is still being prepared for modification"}
        )

    try:
        body = await request.json()
    except Exception:
        return _error_response(
            400,
            "Invalid JSON body",
            'Send a JSON body with "items_to_add" array. '
            'Example: {"items_to_add": [{"item_id": "APP-002", "quantity": 1}]}',
        )

    items_to_add = body.get("items_to_add")
    if not items_to_add:
        return _error_response(
            400,
            "Missing 'items_to_add' in request body",
            "Include an 'items_to_add' array with items to add to your order. "
            "Remember: you need to add the chef's special - the most expensive appetizer!",
        )

    # Validate modification items
    is_valid, error_msg = _validate_modification_items(items_to_add)
    if not is_valid:
        return _error_response(
            400,
            f"Invalid modification items: {error_msg}",
            "Check the menu (GET /api/menu) for valid item IDs.",
        )

    # Check if the most expensive appetizer is being added
    most_expensive_app = _get_most_expensive_in_category(MenuCategory.APPETIZER)
    required_item_id = most_expensive_app["id"] if most_expensive_app else None

    has_required_item = any(
        item.get("item_id") == required_item_id
        for item in items_to_add
    )

    if not has_required_item:
        return _error_response(
            400,
            "Missing the chef's special item",
            f"The chef insists on adding the most expensive appetizer to your order. "
            f"Check the appetizer section of the menu for the priciest option. "
            f"Hint: Look for something luxurious and premium...",
        )

    # Apply modification
    updated_order = _modify_order(order_id, items_to_add)
    if not updated_order:
        return _error_response(
            500,
            "Failed to modify order",
            "Something went wrong. Try again.",
        )

    return {
        "success": True,
        "order": _format_order_detail(updated_order),
        "hint": f"Order modified! Now pay with POST /api/order/{order_id}/pay. "
                f"Send the exact total: {updated_order['total']}",
    }


# ===========================================================================
# ROUTE: PAYMENT
# ===========================================================================

@app.post("/api/order/{order_id}/pay")
async def pay_order(order_id: str, request: Request):
    """
    Process payment for an order.
    The amount must match the order total exactly.
    """
    payment_logger.info("Payment requested for order %s", order_id)

    order = _get_order(order_id)
    if not order:
        return _error_response(
            404,
            f"Order {order_id} not found",
            "Check your order_id.",
        )

    if order["status"] != OrderStatus.PENDING_PAYMENT:
        return _error_response(
            409,
            f"Order {order_id} is not ready for payment (status: {order['status']})",
            f"Order must be in 'pending_payment' status. Current status: '{order['status']}'. "
            f"Did you modify your order first? Check GET /api/order/{order_id}/status for details.",
        )

    try:
        body = await request.json()
    except Exception:
        return _error_response(
            400,
            "Invalid JSON body",
            f'Send a JSON body with the payment amount: {{"amount": {order["total"]}}}',
        )

    amount = body.get("amount")

    is_valid, error_msg = _validate_payment_amount(amount)
    if not is_valid:
        return _error_response(
            400,
            f"Invalid payment: {error_msg}",
            f"Send the exact order total as 'amount'. Your order total is ${order['total']:.2f}",
        )

    amount = float(amount)

    # Check exact match
    if abs(amount - order["total"]) > 0.01:
        return _error_response(
            400,
            f"Payment amount ${amount:.2f} does not match order total ${order['total']:.2f}",
            f"You must pay the exact order total. The correct amount is ${order['total']:.2f}",
        )

    # Process payment
    payment_info = _process_payment(order_id, amount)
    if not payment_info:
        return _error_response(
            500,
            "Payment processing failed",
            "Something went wrong. Try again.",
        )

    etag = hashlib.md5(f"{order_id}:{SHARED_SECRET}".encode()).hexdigest()
    response = JSONResponse(content={
        "success": True,
        "payment": payment_info,
        "order_id": order_id,
        "hint": f"Payment successful! Get your receipt at GET /api/order/{order_id}/receipt",
    })
    response.headers["ETag"] = f'"{etag}"'
    return response


# ===========================================================================
# ROUTE: RECEIPT
# ===========================================================================

@app.get("/api/order/{order_id}/receipt")
async def get_receipt(order_id: str, request: Request):
    """
    Get the receipt for a paid order.
    The receipt contains base64-encoded verification data.
    """
    receipt_logger.info("Receipt requested for order %s", order_id)

    order = _get_order(order_id)
    if not order:
        return _error_response(
            404,
            f"Order {order_id} not found",
            "Check your order_id.",
        )

    if order["status"] != OrderStatus.PAID:
        return _error_response(
            409,
            f"Receipt not available (order status: {order['status']})",
            f"You need to pay for your order first. "
            f"Check GET /api/order/{order_id}/status for the current state.",
        )

    # Verify ETag via If-None-Match header
    expected_etag = hashlib.md5(f"{order_id}:{SHARED_SECRET}".encode()).hexdigest()
    client_etag = request.headers.get("If-None-Match", "").strip('"')
    if client_etag != expected_etag:
        # Return a zeroed-out receipt that LOOKS valid but has wrong amounts
        receipt_logger.info("ETag mismatch for order %s - returning zeroed receipt", order_id)
        return {
            "success": True,
            "receipt": {
                "receipt_id": f"REC-{uuid.uuid4().hex[:12].upper()}",
                "order_id": order_id,
                "items": [
                    {**item, "unit_price": 0.00, "total": 0.00}
                    for item in order["items"]
                ],
                "subtotal": 0.00,
                "tax": 0.00,
                "total": 0.00,
                "payment": {
                    "payment_id": order["payment"]["payment_id"],
                    "amount": 0.00,
                    "method": "card",
                    "status": "completed",
                    "processed_at": order["payment"]["processed_at"],
                },
                "issued_at": datetime.now(timezone.utc).isoformat(),
                "verification_data": base64.b64encode(
                    json.dumps({
                        "order_id": order_id,
                        "total": 0.00,
                        "payment_id": order["payment"]["payment_id"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "verification_code": hashlib.sha256(
                            f"{order_id}:0.00:{SHARED_SECRET}".encode()
                        ).hexdigest()[:16],
                    }).encode()
                ).decode(),
                "hint": "The verification_data is base64 encoded. Decode it and POST the JSON to /api/verify to complete your journey.",
            },
        }

    # Generate receipt if not already generated
    if not order.get("receipt"):
        receipt = _generate_receipt(order_id)
        if not receipt:
            return _error_response(
                500,
                "Failed to generate receipt",
                "Something went wrong. Try again.",
            )
    else:
        receipt = order["receipt"]

    return {
        "success": True,
        "receipt": receipt,
    }


# ===========================================================================
# ROUTE: VERIFY
# ===========================================================================

@app.post("/api/verify")
async def verify(request: Request):
    """
    Verify decoded receipt data and receive the flag.
    Submit the decoded verification_data from the receipt.
    """
    verify_logger.info("Verification request received")

    try:
        body = await request.json()
    except Exception:
        return _error_response(
            400,
            "Invalid JSON body",
            "Send a JSON body with the decoded verification_data from your receipt. "
            "The verification_data in the receipt is base64 encoded - decode it first!",
        )

    verification_data = body.get("verification_data")
    if not verification_data:
        return _error_response(
            400,
            "Missing 'verification_data' in request body",
            "Include the 'verification_data' field with the decoded JSON from your receipt. "
            "Remember: the receipt's verification_data is base64 encoded. "
            "Decode it, parse the JSON, and submit it here.",
        )

    if isinstance(verification_data, str):
        # Maybe they sent the base64 string directly - try to decode
        try:
            decoded = base64.b64decode(verification_data)
            verification_data = json.loads(decoded)
            verify_logger.info("Auto-decoded base64 verification data")
        except Exception:
            return _error_response(
                400,
                "Invalid verification_data format",
                "The verification_data should be a JSON object. "
                "If you're sending the raw base64 string, decode it first to get the JSON object, "
                "then submit that object.",
            )

    if not isinstance(verification_data, dict):
        return _error_response(
            400,
            "verification_data must be a JSON object",
            "Decode the base64 verification_data from the receipt to get a JSON object, "
            "then submit that object.",
        )

    # Verify
    flag = _verify_receipt_data(verification_data)

    if not flag:
        return _error_response(
            400,
            "Verification failed",
            "The verification data is invalid. Make sure you're submitting the exact "
            "decoded data from your receipt without modifications. "
            "Required fields: order_id, total, payment_id, verification_code.",
            details={
                "required_fields": ["order_id", "total", "payment_id", "verification_code"],
            },
        )

    verify_logger.info("FLAG CAPTURED! Verification successful.")

    return {
        "success": True,
        "message": "Congratulations! You have successfully explored the API and completed the full order flow!",
        "flag": flag,
    }


# ===========================================================================
# DECOY ROUTES
# These return 404 with hints to redirect explorers to correct paths
# ===========================================================================

@app.get("/api")
async def decoy_api_root():
    """Decoy: API root."""
    return _error_response(
        404,
        "No resource at /api",
        "The API has several endpoints. Start with GET /health to discover the first step.",
    )


@app.get("/api/auth")
async def decoy_auth_root():
    """Decoy: Auth root."""
    return _error_response(
        404,
        "No resource at /api/auth",
        "Try POST /api/auth/discover to learn about the authentication scheme.",
    )


@app.get("/api/auth/discover")
async def decoy_auth_discover_get():
    """Decoy: GET instead of POST for auth discover."""
    return _error_response(
        405,
        "Method not allowed: use POST",
        "POST /api/auth/discover, not GET.",
    )


@app.get("/api/auth/token")
async def decoy_auth_token_get():
    """Decoy: GET instead of POST for token."""
    return _error_response(
        405,
        "Method not allowed: use POST",
        "POST /api/auth/token with X-Signature and X-Timestamp headers.",
    )


@app.get("/api/auth/login")
@app.post("/api/auth/login")
async def decoy_auth_login():
    """Decoy: Common login endpoint."""
    return _error_response(
        404,
        "No login endpoint exists",
        "This API uses HMAC-based authentication, not username/password. "
        "Start with POST /api/auth/discover to learn the auth scheme.",
    )


@app.get("/api/auth/register")
@app.post("/api/auth/register")
async def decoy_auth_register():
    """Decoy: Common register endpoint."""
    return _error_response(
        404,
        "No registration endpoint exists",
        "Authentication is HMAC-based. Start with POST /api/auth/discover.",
    )


@app.get("/api/auth/signup")
@app.post("/api/auth/signup")
async def decoy_auth_signup():
    """Decoy: signup alias."""
    return _error_response(
        404,
        "No signup endpoint exists",
        "Use POST /api/auth/discover to learn how to authenticate.",
    )


@app.get("/api/users")
@app.post("/api/users")
async def decoy_users():
    """Decoy: Users endpoint."""
    return _error_response(
        404,
        "No users endpoint",
        "This is a restaurant ordering API, not a user management system. "
        "Try GET /health to start.",
    )


@app.get("/api/admin")
@app.post("/api/admin")
async def decoy_admin():
    """Decoy: Admin endpoint."""
    return _error_response(
        404,
        "No admin panel here",
        "Nice try! Start with GET /health and follow the hints.",
    )


@app.get("/api/docs")
async def decoy_docs():
    """Decoy: Docs endpoint."""
    return _error_response(
        404,
        "Documentation is not available",
        "This API is undocumented by design. Explore it! Start with GET /health.",
    )


@app.get("/api/swagger")
async def decoy_swagger():
    """Decoy: Swagger endpoint."""
    return _error_response(
        404,
        "No Swagger UI available",
        "No auto-generated docs here. Discover endpoints by following hints, starting with GET /health.",
    )


@app.get("/api/openapi")
@app.get("/api/openapi.json")
async def decoy_openapi():
    """Decoy: OpenAPI spec endpoint."""
    return _error_response(
        404,
        "No OpenAPI specification available",
        "The API must be explored manually. Start with GET /health.",
    )


@app.get("/api/v1")
@app.get("/api/v2")
@app.get("/api/v3")
async def decoy_versioned_api():
    """Decoy: Versioned API root."""
    return _error_response(
        404,
        "No versioned API endpoints",
        "Endpoints are directly under /api/. Start with GET /health.",
    )


@app.get("/api/orders")
async def decoy_orders_list():
    """Decoy: Orders list endpoint."""
    return _error_response(
        404,
        "Cannot list all orders",
        "To interact with orders, first create one with POST /api/order (singular). "
        "You need to be authenticated first - see GET /health for the starting point.",
    )


@app.get("/api/items")
async def decoy_items():
    """Decoy: Items endpoint."""
    return _error_response(
        404,
        "No /api/items endpoint",
        "Looking for the menu? Try GET /api/menu (requires authentication).",
    )


@app.get("/api/food")
@app.get("/api/foods")
async def decoy_food():
    """Decoy: Food endpoint."""
    return _error_response(
        404,
        "No /api/food endpoint",
        "The menu is at GET /api/menu (requires authentication).",
    )


@app.get("/api/restaurant")
async def decoy_restaurant():
    """Decoy: Restaurant info endpoint."""
    return _error_response(
        404,
        "No restaurant info endpoint",
        "This is the restaurant's internal API. Start exploring at GET /health.",
    )


@app.get("/api/status")
async def decoy_status():
    """Decoy: Status endpoint."""
    return _error_response(
        404,
        "System status is at /health, not /api/status",
        "Use GET /health for system status.",
    )


@app.get("/api/ping")
async def decoy_ping():
    """Decoy: Ping endpoint."""
    return _error_response(
        404,
        "No ping endpoint",
        "Use GET /health instead.",
    )


@app.get("/api/config")
@app.get("/api/settings")
async def decoy_config():
    """Decoy: Config endpoint."""
    return _error_response(
        404,
        "No configuration endpoint available",
        "This is a restaurant ordering API. Start with GET /health.",
    )


@app.get("/api/search")
async def decoy_search():
    """Decoy: Search endpoint."""
    return _error_response(
        404,
        "No search endpoint",
        "Browse the menu at GET /api/menu (requires auth).",
    )


@app.get("/api/cart")
@app.post("/api/cart")
async def decoy_cart():
    """Decoy: Cart endpoint."""
    return _error_response(
        404,
        "No cart system - orders are placed directly",
        "Place orders directly with POST /api/order (requires auth). "
        "No cart needed!",
    )


@app.get("/api/checkout")
@app.post("/api/checkout")
async def decoy_checkout():
    """Decoy: Checkout endpoint."""
    return _error_response(
        404,
        "No checkout endpoint",
        "Payment is done per-order with POST /api/order/{order_id}/pay.",
    )


@app.get("/api/payment")
@app.post("/api/payment")
@app.get("/api/payments")
async def decoy_payment():
    """Decoy: Payment endpoint."""
    return _error_response(
        404,
        "No standalone payment endpoint",
        "Payments are linked to orders. Use POST /api/order/{order_id}/pay.",
    )


@app.get("/api/receipt")
@app.get("/api/receipts")
async def decoy_receipts():
    """Decoy: Receipts endpoint."""
    return _error_response(
        404,
        "Receipts are per-order",
        "Get a receipt at GET /api/order/{order_id}/receipt after paying.",
    )


@app.get("/api/flag")
@app.post("/api/flag")
async def decoy_flag():
    """Decoy: Direct flag request."""
    return _error_response(
        404,
        "No shortcut to the flag!",
        "You'll need to complete the full order flow. Start at GET /health and follow every hint.",
    )


@app.get("/api/secret")
@app.get("/api/secrets")
async def decoy_secret():
    """Decoy: Secrets endpoint."""
    return _error_response(
        404,
        "No secrets here (well, not at this endpoint)",
        "The real secrets are discovered by following the API flow. Start at GET /health.",
    )


@app.get("/api/debug")
async def decoy_debug():
    """Decoy: Debug endpoint."""
    return _error_response(
        404,
        "No debug endpoint in production",
        "This is a production server. Explore the API starting from GET /health.",
    )


@app.get("/api/test")
async def decoy_test():
    """Decoy: Test endpoint."""
    return _error_response(
        404,
        "No test endpoint",
        "Start your exploration at GET /health.",
    )


@app.get("/api/info")
async def decoy_info():
    """Decoy: Info endpoint."""
    return _error_response(
        404,
        "Server info is at /health",
        "Use GET /health for server information and the first exploration hint.",
    )


@app.get("/robots.txt")
async def decoy_robots():
    """Decoy: robots.txt."""
    return Response(
        content="User-agent: *\nDisallow: /api/auth/discover\nDisallow: /api/verify\n",
        media_type="text/plain",
    )


@app.get("/sitemap.xml")
async def decoy_sitemap():
    """Decoy: sitemap."""
    return _error_response(
        404,
        "No sitemap",
        "This is an API server, not a website. Start at GET /health.",
    )


@app.get("/")
async def root():
    """Root endpoint redirects to health."""
    return {
        "message": "Restaurant API Server",
        "hint": "Try GET /health",
    }


@app.get("/favicon.ico")
async def favicon():
    """No favicon."""
    return Response(status_code=204)


# ===========================================================================
# DECOY ROUTES: COMMON API PATTERNS
# ===========================================================================

@app.get("/api/categories")
async def decoy_categories():
    """Decoy: Categories endpoint."""
    return _error_response(
        404,
        "No standalone categories endpoint",
        "Menu categories are included in the GET /api/menu response.",
    )


@app.get("/api/specials")
async def decoy_specials():
    """Decoy: Specials endpoint."""
    return _error_response(
        404,
        "No specials endpoint",
        "Special items are part of the regular menu. GET /api/menu (requires auth).",
    )


@app.get("/api/reservations")
@app.post("/api/reservations")
async def decoy_reservations():
    """Decoy: Reservations endpoint."""
    return _error_response(
        404,
        "No reservations system",
        "This API handles ordering only. Start with GET /health.",
    )


@app.get("/api/reviews")
@app.post("/api/reviews")
async def decoy_reviews():
    """Decoy: Reviews endpoint."""
    return _error_response(
        404,
        "No reviews endpoint",
        "Focus on placing an order! Start at GET /health.",
    )


@app.get("/api/delivery")
@app.post("/api/delivery")
async def decoy_delivery():
    """Decoy: Delivery endpoint."""
    return _error_response(
        404,
        "No delivery tracking here",
        "This API handles the ordering flow. Start at GET /health.",
    )


@app.get("/api/tips")
@app.post("/api/tips")
async def decoy_tips():
    """Decoy: Tips endpoint."""
    return _error_response(
        404,
        "No tipping endpoint",
        "Here's a free tip: follow the hints starting from GET /health!",
    )


# ===========================================================================
# INTERNAL: DIAGNOSTIC AND MONITORING HELPERS
# ===========================================================================

def _get_system_diagnostics() -> dict:
    """
    Gather system diagnostic information.
    Internal use only - not exposed via API.
    """
    return {
        "active_sessions": _get_active_session_count(),
        "total_orders": len(_orders),
        "pending_orders": sum(
            1 for o in _orders.values()
            if o["status"] in (OrderStatus.CREATED, OrderStatus.PENDING_MODIFICATION)
        ),
        "paid_orders": sum(
            1 for o in _orders.values()
            if o["status"] == OrderStatus.PAID
        ),
        "rate_limit_tracked_ips": len(_rate_limit_store),
        "system_status": CURRENT_SYSTEM_STATUS,
        "app_version": APP_VERSION,
    }


def _log_diagnostic_summary():
    """Log a summary of system diagnostics."""
    diag = _get_system_diagnostics()
    logger.info(
        "System diagnostics: sessions=%d, orders=%d, pending=%d, paid=%d",
        diag["active_sessions"],
        diag["total_orders"],
        diag["pending_orders"],
        diag["paid_orders"],
    )


def _calculate_revenue() -> float:
    """Calculate total revenue from paid orders."""
    total = 0.0
    for order in _orders.values():
        if order["status"] == OrderStatus.PAID and order.get("payment"):
            total += order["payment"]["amount"]
    return round(total, 2)


def _get_popular_items() -> List[dict]:
    """Get a summary of most ordered items across all orders."""
    item_counts: Dict[str, int] = defaultdict(int)
    for order in _orders.values():
        for item in order["items"]:
            item_counts[item["item_id"]] += item["quantity"]

    sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
    menu_index = _build_menu_index()

    return [
        {
            "item_id": item_id,
            "name": menu_index.get(item_id, {}).get("name", "Unknown"),
            "total_ordered": count,
        }
        for item_id, count in sorted_items[:10]
    ]


def _validate_menu_integrity() -> bool:
    """
    Validate that the menu data is consistent and complete.
    Checks for duplicate IDs, missing fields, invalid prices, etc.
    """
    seen_ids = set()
    for item in RESTAURANT_MENU["items"]:
        # Check for duplicate IDs
        if item["id"] in seen_ids:
            logger.error("Duplicate menu item ID: %s", item["id"])
            return False
        seen_ids.add(item["id"])

        # Check required fields
        required_fields = ["id", "name", "description", "price", "category", "available"]
        for field in required_fields:
            if field not in item:
                logger.error("Menu item %s missing field: %s", item.get("id", "?"), field)
                return False

        # Check price is valid
        if not isinstance(item["price"], (int, float)) or item["price"] < 0:
            logger.error("Invalid price for menu item %s: %s", item["id"], item["price"])
            return False

    logger.info("Menu integrity check passed: %d items validated", len(seen_ids))
    return True


def _generate_daily_report() -> dict:
    """
    Generate a daily summary report.
    Internal use only.
    """
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total_orders": len(_orders),
        "total_revenue": _calculate_revenue(),
        "popular_items": _get_popular_items(),
        "system_status": CURRENT_SYSTEM_STATUS,
        "diagnostics": _get_system_diagnostics(),
    }


def _format_currency(amount: float) -> str:
    """Format a number as currency."""
    return f"${amount:,.2f}"


def _format_percentage(value: float) -> str:
    """Format a number as percentage."""
    return f"{value:.1f}%"


def _clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns default on division by zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def _truncate_string(s: str, max_length: int = 100) -> str:
    """Truncate a string to max_length characters."""
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def _merge_dicts(base: dict, override: dict) -> dict:
    """Merge two dictionaries, with override taking precedence."""
    result = base.copy()
    result.update(override)
    return result


def _deep_copy_order(order: dict) -> dict:
    """Create a deep copy of an order dictionary."""
    return json.loads(json.dumps(order))


def _calculate_order_item_count(order: dict) -> int:
    """Calculate the total number of items in an order (sum of quantities)."""
    return sum(item.get("quantity", 0) for item in order.get("items", []))


def _estimate_preparation_time(order: dict) -> int:
    """
    Estimate total preparation time for an order in minutes.
    Uses the max preparation time across all items.
    """
    menu_index = _build_menu_index()
    max_time = 0
    for item in order.get("items", []):
        menu_item = menu_index.get(item.get("item_id", ""))
        if menu_item:
            prep_time = menu_item.get("preparation_time_minutes", 10)
            max_time = max(max_time, prep_time)
    return max_time


def _generate_order_confirmation_text(order: dict) -> str:
    """Generate a human-readable order confirmation."""
    lines = [f"Order Confirmation: {order['order_id']}"]
    lines.append("-" * 40)
    for item in order["items"]:
        lines.append(f"  {item['quantity']}x {item['name']} - ${item['total']:.2f}")
    lines.append("-" * 40)
    lines.append(f"  Subtotal: ${order['subtotal']:.2f}")
    if order["tax"] > 0:
        lines.append(f"  Tax: ${order['tax']:.2f}")
    if order["service_fee"] > 0:
        lines.append(f"  Service Fee: ${order['service_fee']:.2f}")
    lines.append(f"  TOTAL: ${order['total']:.2f}")
    return "\n".join(lines)


def _obfuscate_token(token: str) -> str:
    """Obfuscate a token for logging purposes."""
    if len(token) <= 8:
        return "****"
    return f"{token[:4]}...{token[-4:]}"


def _parse_bearer_token(auth_header: str) -> Optional[str]:
    """Parse a Bearer token from an Authorization header."""
    if not auth_header:
        return None
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:].strip()


# ===========================================================================
# INTERNAL: CONFIGURATION HELPERS
# ===========================================================================

def _get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value from environment or defaults."""
    env_key = f"RESTAURANT_API_{key.upper()}"
    return os.environ.get(env_key, default)


def _is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return _get_config_value("DEBUG", "false").lower() == "true"


def _get_allowed_origins() -> List[str]:
    """Get list of allowed CORS origins."""
    origins = _get_config_value("CORS_ORIGINS", "*")
    if origins == "*":
        return ["*"]
    return [o.strip() for o in origins.split(",")]


def _get_max_request_size() -> int:
    """Get maximum request body size in bytes."""
    return int(_get_config_value("MAX_REQUEST_SIZE", "1048576"))


# ===========================================================================
# INTERNAL: DATA SERIALIZATION HELPERS
# ===========================================================================

def _serialize_datetime(dt: datetime) -> str:
    """Serialize a datetime to ISO format string."""
    return dt.isoformat()


def _serialize_enum(value: Enum) -> str:
    """Serialize an enum to its value."""
    return value.value


def _serialize_order_for_storage(order: dict) -> str:
    """Serialize an order dict to JSON string for storage."""
    def _default_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    return json.dumps(order, default=_default_serializer, indent=2)


def _deserialize_order_from_storage(data: str) -> dict:
    """Deserialize an order from JSON string."""
    return json.loads(data)


# ===========================================================================
# STARTUP EVENT
# ===========================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    Validates menu data and logs server information.
    """
    logger.info("=" * 60)
    logger.info("Starting %s v%s", APP_NAME, APP_VERSION)
    logger.info("=" * 60)

    # Validate menu
    if _validate_menu_integrity():
        logger.info("Menu integrity check: PASSED")
    else:
        logger.error("Menu integrity check: FAILED")
        sys.exit(1)

    # Log configuration
    logger.info("Rate limit: %d requests per %d seconds", RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
    logger.info("Token expiry: %d minutes", TOKEN_EXPIRY_MINUTES)
    logger.info("System status: %s", CURRENT_SYSTEM_STATUS)
    logger.info("=" * 60)
    logger.info("Server ready. Only /health is documented. Good luck exploring!")
    logger.info("=" * 60)


# ===========================================================================
# MAIN ENTRY POINT
# ===========================================================================

if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    logger.info("Starting server on %s:%d", host, port)

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )
