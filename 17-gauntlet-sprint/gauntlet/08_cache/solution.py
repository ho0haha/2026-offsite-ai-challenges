"""
LRU Cache with TTL - Solution Stub

Implement LRUCache with O(1) get/put/delete operations and TTL expiration.
Do NOT use functools.lru_cache or cachetools.
"""

from typing import Any, Optional


class LRUCache:
    def __init__(self, capacity: int, max_age: float):
        """
        Initialize the LRU cache.

        Args:
            capacity: Maximum number of items in the cache.
            max_age: Time-to-live for each entry in seconds.
        """
        self.capacity = capacity
        self.max_age = max_age
        # TODO: Initialize your data structures (hint: OrderedDict or doubly-linked list + dict)

    def get(self, key: str, timestamp: float) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Returns None if the key doesn't exist or has expired.
        Accessing a key moves it to the most-recently-used position
        but does NOT reset its TTL.

        TODO: Implement this.
        """
        return None

    def put(self, key: str, value: Any, timestamp: float) -> None:
        """
        Insert or update a key-value pair.

        If updating an existing key, reset its TTL.
        If at capacity, evict the least recently used non-expired item.

        TODO: Implement this.
        """
        pass

    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Returns True if the key existed (even if expired), False otherwise.

        TODO: Implement this.
        """
        return False
