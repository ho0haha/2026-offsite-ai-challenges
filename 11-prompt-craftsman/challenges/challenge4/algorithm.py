"""
A recursive algorithm for analysis.
"""

from typing import List, Optional


def merge_sort(arr: List[int]) -> List[int]:
    """
    Sort an array using the merge sort algorithm.
    This is a recursive divide-and-conquer sorting algorithm.
    """
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid])
    right_half = merge_sort(arr[mid:])

    return _merge(left_half, right_half)


def _merge(left: List[int], right: List[int]) -> List[int]:
    """Merge two sorted arrays into one sorted array."""
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


def binary_search(arr: List[int], target: int) -> Optional[int]:
    """
    Search for a target value in a sorted array using binary search.
    Returns the index of the target, or None if not found.
    """
    return _binary_search_recursive(arr, target, 0, len(arr) - 1)


def _binary_search_recursive(
    arr: List[int], target: int, low: int, high: int
) -> Optional[int]:
    """Recursive helper for binary search."""
    if low > high:
        return None

    mid = (low + high) // 2

    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return _binary_search_recursive(arr, target, mid + 1, high)
    else:
        return _binary_search_recursive(arr, target, low, mid - 1)
