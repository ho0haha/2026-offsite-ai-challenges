"""
Tests for the restaurant hours regex challenge.
Do NOT modify this file.
"""

import pytest
from solution import parse_hours, HoursEntry


# --- Valid strings (25 cases) ---

VALID_CASES = [
    (
        "Mon-Fri 11am-10pm",
        [HoursEntry("Mon-Fri", "11am", "10pm", False)],
    ),
    (
        "Sat 10am-11pm",
        [HoursEntry("Sat", "10am", "11pm", False)],
    ),
    (
        "Sun Closed",
        [HoursEntry("Sun", None, None, True)],
    ),
    (
        "Mon-Fri 11am-10pm, Sat 10am-11pm, Sun Closed",
        [
            HoursEntry("Mon-Fri", "11am", "10pm", False),
            HoursEntry("Sat", "10am", "11pm", False),
            HoursEntry("Sun", None, None, True),
        ],
    ),
    (
        "Mon-Thu 11:30am-9:30pm, Fri-Sat 11:30am-10:30pm, Sun 12pm-8pm",
        [
            HoursEntry("Mon-Thu", "11:30am", "9:30pm", False),
            HoursEntry("Fri-Sat", "11:30am", "10:30pm", False),
            HoursEntry("Sun", "12pm", "8pm", False),
        ],
    ),
    (
        "Mon 6am-2pm",
        [HoursEntry("Mon", "6am", "2pm", False)],
    ),
    (
        "Tue-Wed 5:30pm-11:30pm",
        [HoursEntry("Tue-Wed", "5:30pm", "11:30pm", False)],
    ),
    (
        "Thu 7am-3pm, Fri 7am-12am",
        [
            HoursEntry("Thu", "7am", "3pm", False),
            HoursEntry("Fri", "7am", "12am", False),
        ],
    ),
    (
        "Mon-Sun 11am-11pm",
        [HoursEntry("Mon-Sun", "11am", "11pm", False)],
    ),
    (
        "Sat-Sun 9am-4pm",
        [HoursEntry("Sat-Sun", "9am", "4pm", False)],
    ),
    (
        "Mon Closed, Tue-Sun 11am-9pm",
        [
            HoursEntry("Mon", None, None, True),
            HoursEntry("Tue-Sun", "11am", "9pm", False),
        ],
    ),
    (
        "Mon-Wed 11am-9pm, Thu-Fri 11am-10pm, Sat 10am-10pm, Sun 10am-9pm",
        [
            HoursEntry("Mon-Wed", "11am", "9pm", False),
            HoursEntry("Thu-Fri", "11am", "10pm", False),
            HoursEntry("Sat", "10am", "10pm", False),
            HoursEntry("Sun", "10am", "9pm", False),
        ],
    ),
    (
        "Fri-Sat 5pm-12am",
        [HoursEntry("Fri-Sat", "5pm", "12am", False)],
    ),
    (
        "Mon-Fri 6:30am-2:30pm",
        [HoursEntry("Mon-Fri", "6:30am", "2:30pm", False)],
    ),
    (
        "Wed 4pm-10pm",
        [HoursEntry("Wed", "4pm", "10pm", False)],
    ),
    (
        "Mon-Sat 11am-10pm, Sun Closed",
        [
            HoursEntry("Mon-Sat", "11am", "10pm", False),
            HoursEntry("Sun", None, None, True),
        ],
    ),
    (
        "Tue 11:30am-2:30pm",
        [HoursEntry("Tue", "11:30am", "2:30pm", False)],
    ),
    (
        "Mon-Fri 7am-7pm, Sat 8am-5pm, Sun Closed",
        [
            HoursEntry("Mon-Fri", "7am", "7pm", False),
            HoursEntry("Sat", "8am", "5pm", False),
            HoursEntry("Sun", None, None, True),
        ],
    ),
    (
        "Thu-Sun 5pm-11pm",
        [HoursEntry("Thu-Sun", "5pm", "11pm", False)],
    ),
    (
        "Mon-Fri 11am-3pm, Mon-Fri 5pm-10pm",
        [
            HoursEntry("Mon-Fri", "11am", "3pm", False),
            HoursEntry("Mon-Fri", "5pm", "10pm", False),
        ],
    ),
    (
        "Sat 11:30am-11:30pm",
        [HoursEntry("Sat", "11:30am", "11:30pm", False)],
    ),
    (
        "Mon-Wed Closed, Thu-Sun 4pm-10pm",
        [
            HoursEntry("Mon-Wed", None, None, True),
            HoursEntry("Thu-Sun", "4pm", "10pm", False),
        ],
    ),
    (
        "Fri 11am-12am, Sat 11am-12am",
        [
            HoursEntry("Fri", "11am", "12am", False),
            HoursEntry("Sat", "11am", "12am", False),
        ],
    ),
    (
        "Sun 10am-3pm",
        [HoursEntry("Sun", "10am", "3pm", False)],
    ),
    (
        "Mon-Thu 11am-9:30pm, Fri 11am-10:30pm, Sat 10:30am-10:30pm, Sun 10:30am-9:30pm",
        [
            HoursEntry("Mon-Thu", "11am", "9:30pm", False),
            HoursEntry("Fri", "11am", "10:30pm", False),
            HoursEntry("Sat", "10:30am", "10:30pm", False),
            HoursEntry("Sun", "10:30am", "9:30pm", False),
        ],
    ),
]


@pytest.mark.parametrize("text,expected", VALID_CASES, ids=[f"valid_{i}" for i in range(25)])
def test_valid_hours(text, expected):
    result = parse_hours(text)
    assert len(result) == len(expected), (
        f"Expected {len(expected)} entries, got {len(result)} for: {text}"
    )
    for i, (r, e) in enumerate(zip(result, expected)):
        assert r.days == e.days, f"Entry {i}: days mismatch for: {text}"
        assert r.open_time == e.open_time, f"Entry {i}: open_time mismatch for: {text}"
        assert r.close_time == e.close_time, f"Entry {i}: close_time mismatch for: {text}"
        assert r.is_closed == e.is_closed, f"Entry {i}: is_closed mismatch for: {text}"


# --- Invalid strings (25 cases) ---

INVALID_CASES = [
    "",                                 # empty
    "Open 24 hours",                    # no day format
    "Monday-Friday 11am-10pm",          # full day names
    "Mon-Fri 11-10",                    # missing am/pm
    "Mon-Fri 11:00-22:00",             # 24h format
    "25pm-3am",                         # no day
    "Mon-Fri",                          # no time
    "M-F 11am-10pm",                    # single letter days
    "Mon-Fri 13pm-10pm",               # 13pm invalid
    "Mon-Fri 11am to 10pm",            # "to" instead of dash
    "Lun-Vie 11am-10pm",               # Spanish days
    "Mon/Fri 11am-10pm",               # slash instead of dash for days
    "Mon-Fri 11AM-10PM",               # uppercase AM/PM
    "Open daily",                       # no specific times
    "by appointment only",             # no hours
    "11am-10pm Mon-Fri",               # reversed order
    "Mon-Fri: 11am-10pm",             # colon separator
    "CLOSED",                           # all caps, no day
    "Mon-Fri 11am - 10pm",             # spaces around time dash
    "Mon-Fri 11a.m.-10p.m.",           # periods in am/pm
    "Available Mon-Fri 11am-10pm",     # prefix text
    "Mon-Fri 11am-10pm (kitchen closes 9pm)",  # parenthetical
    "24/7",                             # 24/7 format
    "9-5",                              # bare numbers
    "Mon-Xyz 11am-10pm",               # invalid day name
]


@pytest.mark.parametrize("text", INVALID_CASES, ids=[f"invalid_{i}" for i in range(25)])
def test_invalid_hours(text):
    result = parse_hours(text)
    assert len(result) == 0, f"Expected no matches for invalid input: {text!r}, got {result}"
