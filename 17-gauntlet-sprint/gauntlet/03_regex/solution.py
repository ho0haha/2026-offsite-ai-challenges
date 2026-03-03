"""
Restaurant Hours Regex Challenge - Solution Stub

Implement parse_hours(text) that extracts restaurant hour entries from a string.
"""

import re
from typing import List, NamedTuple, Optional


class HoursEntry(NamedTuple):
    days: str           # e.g., "Mon-Fri" or "Sun"
    open_time: Optional[str]   # e.g., "11am" or "11:30am", None if closed
    close_time: Optional[str]  # e.g., "10pm" or "10:30pm", None if closed
    is_closed: bool     # True if "Closed"


def parse_hours(text: str) -> List[HoursEntry]:
    """
    Parse restaurant hours string and return a list of HoursEntry.

    Examples:
        "Mon-Fri 11am-10pm, Sat 10am-11pm, Sun Closed"
        -> [
            HoursEntry("Mon-Fri", "11am", "10pm", False),
            HoursEntry("Sat", "10am", "11pm", False),
            HoursEntry("Sun", None, None, True),
        ]

    TODO: Implement this using a regex pattern.
    """
    return []
