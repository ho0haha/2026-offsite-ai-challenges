#!/usr/bin/env python3
"""PRD Validator — checks that a PRD markdown file meets minimum structural requirements."""

import re
import sys


def read_file(path: str) -> str:
    """Read and return the contents of a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Could not read file: {e}")
        sys.exit(1)


def check_user_stories(content: str) -> tuple[bool, str]:
    """Check for at least 3 user stories in 'As a... I want... So that...' format."""
    # Match user stories — flexible with punctuation and casing
    pattern = r"[Aa]s\s+a[n]?\s+.{3,80}[,;]?\s*[Ii]\s+want\s+.{3,200}[,;]?\s*[Ss]o\s+that\s+.{3,200}"
    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
    count = len(matches)
    if count >= 3:
        return True, f"Found {count} user stories (minimum 3)"
    else:
        return False, f"Found only {count} user stories (minimum 3 required). Each must follow: 'As a [role], I want [feature], so that [benefit].'"


def check_acceptance_criteria(content: str) -> tuple[bool, str]:
    """Check for an acceptance criteria section with at least 5 criteria."""
    # Find the acceptance criteria section
    ac_pattern = r"(?:#{1,4}\s*)?[Aa]cceptance\s+[Cc]riteria"
    ac_match = re.search(ac_pattern, content)
    if not ac_match:
        return False, "No 'Acceptance Criteria' section found. Add a heading containing 'Acceptance Criteria'."

    # Extract text from the acceptance criteria section to the next heading or end
    start = ac_match.end()
    next_heading = re.search(r"\n#{1,4}\s+", content[start:])
    if next_heading:
        section_text = content[start : start + next_heading.start()]
    else:
        section_text = content[start:]

    # Count criteria — look for bullet points, numbered items, or lines starting with -/*/digits
    criteria_lines = re.findall(
        r"^\s*(?:[-*+]|\d+[.)]\s)", section_text, re.MULTILINE
    )
    count = len(criteria_lines)

    if count >= 5:
        return True, f"Found {count} acceptance criteria (minimum 5)"
    else:
        return False, f"Found only {count} acceptance criteria (minimum 5 required). Use bullet points or numbered lists."


def check_edge_cases(content: str) -> tuple[bool, str]:
    """Check for an edge cases / error handling section."""
    patterns = [
        r"(?:#{1,4}\s*)?[Ee]dge\s+[Cc]ases",
        r"(?:#{1,4}\s*)?[Ee]rror\s+[Hh]andling",
        r"(?:#{1,4}\s*)?[Ee]dge\s+[Cc]ases\s*[/&]\s*[Ee]rror\s+[Hh]andling",
        r"(?:#{1,4}\s*)?[Ee]rror\s+[Hh]andling\s*[/&]\s*[Ee]dge\s+[Cc]ases",
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            # Check there's actual content after the heading
            start = match.end()
            next_heading = re.search(r"\n#{1,4}\s+", content[start:])
            if next_heading:
                section_text = content[start : start + next_heading.start()].strip()
            else:
                section_text = content[start:].strip()

            if len(section_text) > 30:
                return True, "Edge cases / error handling section found with content"
            else:
                return False, "Edge cases / error handling section found but has too little content (need substantive descriptions)."

    return False, "No 'Edge Cases' or 'Error Handling' section found. Add a heading containing 'Edge Cases' or 'Error Handling'."


def check_technical_approach(content: str) -> tuple[bool, str]:
    """Check for a technical approach section."""
    patterns = [
        r"(?:#{1,4}\s*)?[Tt]echnical\s+[Aa]pproach",
        r"(?:#{1,4}\s*)?[Tt]echnical\s+[Dd]esign",
        r"(?:#{1,4}\s*)?[Aa]rchitecture",
        r"(?:#{1,4}\s*)?[Ii]mplementation\s+[Ss]trategy",
        r"(?:#{1,4}\s*)?[Tt]echnical\s+[Ss]pecification",
    ]

    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            start = match.end()
            next_heading = re.search(r"\n#{1,4}\s+", content[start:])
            if next_heading:
                section_text = content[start : start + next_heading.start()].strip()
            else:
                section_text = content[start:].strip()

            if len(section_text) > 50:
                return True, "Technical approach section found with content"
            else:
                return False, "Technical approach section found but has too little content (need substantive description of approach)."

    return False, "No 'Technical Approach' section found. Add a heading containing 'Technical Approach', 'Technical Design', 'Architecture', or 'Implementation Strategy'."


def main():
    if len(sys.argv) < 2:
        print("Usage: python prd_validator.py <path_to_prd.md>")
        sys.exit(1)

    filepath = sys.argv[1]
    content = read_file(filepath)

    print("=" * 60)
    print("PRD VALIDATION RESULTS")
    print("=" * 60)
    print()

    checks = [
        ("User Stories (>=3)", check_user_stories),
        ("Acceptance Criteria (>=5)", check_acceptance_criteria),
        ("Edge Cases / Error Handling", check_edge_cases),
        ("Technical Approach", check_technical_approach),
    ]

    all_passed = True
    for name, check_fn in checks:
        passed, message = check_fn(content)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        print(f"         {message}")
        print()
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("RESULT: ALL CHECKS PASSED")
        sys.exit(0)
    else:
        print("RESULT: SOME CHECKS FAILED — please revise your PRD")
        sys.exit(1)


if __name__ == "__main__":
    main()
