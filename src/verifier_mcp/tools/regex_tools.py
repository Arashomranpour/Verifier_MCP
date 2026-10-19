"""Regex verification.

An LLM proposes a regex; this runs it against labelled cases so the pattern is proven to
match what it should and reject what it shouldn't, with capture groups surfaced.
"""

from __future__ import annotations

import re
from typing import Any


def test_regex(pattern: str, cases: list[dict[str, Any]], flags: str = "") -> dict[str, Any]:
    """Test a regex against labelled cases.

    Each case: {"text": str, "should_match": bool}. `flags` is any subset of "imsx".
    Returns {all_passed, results:[{text, expected, matched, groups, passed}]}.
    """
    flag_val = 0
    for ch in flags.lower():
        flag_val |= {"i": re.I, "m": re.M, "s": re.S, "x": re.X}.get(ch, 0)

    try:
        rx = re.compile(pattern, flag_val)
    except re.error as exc:
        return {"all_passed": False, "error": f"invalid regex: {exc}"}

    results = []
    all_passed = True
    for case in cases:
        text = case.get("text", "")
        expected = bool(case.get("should_match", True))
        m = rx.search(text)
        matched = m is not None
        passed = matched == expected
        all_passed = all_passed and passed
        results.append({
            "text": text,
            "expected": expected,
            "matched": matched,
            "groups": list(m.groups()) if m else [],
            "passed": passed,
        })
    return {"all_passed": all_passed, "results": results}
