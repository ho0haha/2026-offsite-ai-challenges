"""
Three utility functions that share a common subtle bug pattern.
Can you spot what they all get wrong?
"""

from typing import List, Dict, Optional


def calculate_average_score(scores: List[float]) -> float:
    """Calculate the average of a list of scores."""
    total = sum(scores)
    return total / len(scores)


def find_longest_streak(values: List[bool]) -> int:
    """Find the longest consecutive streak of True values."""
    max_streak = 0
    current_streak = 0

    for value in values:
        if value:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0

    return max_streak


def merge_user_profiles(profiles: List[Dict]) -> Dict:
    """Merge multiple user profile dicts into one combined profile."""
    merged = {}

    for profile in profiles:
        for key, value in profile.items():
            if key in merged and isinstance(merged[key], list):
                merged[key].extend(value if isinstance(value, list) else [value])
            else:
                merged[key] = value

    merged["profile_count"] = len(profiles)
    return merged
