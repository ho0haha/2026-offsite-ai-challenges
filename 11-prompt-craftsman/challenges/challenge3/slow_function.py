"""
A function that works correctly but has poor performance.
It can be optimized from O(n^2) to O(n).
"""

from typing import List, Tuple, Optional


def find_pair_with_sum(numbers: List[int], target: int) -> Optional[Tuple[int, int]]:
    """
    Find two numbers in the list that add up to the target sum.
    Returns a tuple of (index1, index2) or None if no pair exists.

    Current implementation: O(n^2) — checks every pair with nested loops.
    """
    if not numbers or len(numbers) < 2:
        return None

    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] + numbers[j] == target:
                return (i, j)

    return None


def find_duplicates(items: List[str]) -> List[str]:
    """
    Find all duplicate items in a list.
    Returns a list of items that appear more than once.

    Current implementation: O(n^2) — for each item, scans the whole list.
    """
    duplicates = []

    for i in range(len(items)):
        if items[i] in duplicates:
            continue
        count = 0
        for j in range(len(items)):
            if items[i] == items[j]:
                count += 1
        if count > 1:
            duplicates.append(items[i])

    return duplicates
