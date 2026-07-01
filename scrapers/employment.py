"""Employment-type (full-time / part-time) extraction from posting text.

Used two ways:
  * scrape time — Applitrack posting blocks / CPS titles;
  * backfill    — stored title+description of existing rows (run_all).

Returns 'full_time' | 'part_time' | None. None = not stated / ambiguous —
the FT/PT filter treats it as unknown, never as a match.
"""

from __future__ import annotations

import re

FULL_TIME = "full_time"
PART_TIME = "part_time"

# (?<![\d.]) guards keep "0.5" from matching inside "10.5" and "1.0" from
# matching inside "21.0"; FTE fractions appear as "0.5 FTE", ".5 FTE", "FTE 0.6".
_PART_PATTERNS = [
    r"\bpart[\s-]?time\b",
    r"\bhalf[\s-]?time\b",
    r"(?<![\d.])(?:0?\.\d+)\s*FTE",
    r"\bFTE\s*(?:of\s*)?[:=]?\s*(?:0?\.\d+)(?![\d.])",
]
_FULL_PATTERNS = [
    r"\bfull[\s-]?time\b",
    r"(?<![\d.])1\.0+\s*FTE",
    r"\bFTE\s*(?:of\s*)?[:=]?\s*1(?:\.0+)?(?![\d.])",
]

_PART = [re.compile(p, re.IGNORECASE) for p in _PART_PATTERNS]
_FULL = [re.compile(p, re.IGNORECASE) for p in _FULL_PATTERNS]


def extract_employment_type(*texts: str | None) -> str | None:
    """FT/PT signal across any number of text fragments (title, block, description).

    Both signals present (e.g. "1.0 FTE or part-time considered") -> None:
    better to show the posting under both filters' "unknown" than to hide it
    behind the wrong one.
    """
    blob = " ".join(t for t in texts if t)
    if not blob:
        return None
    part = any(p.search(blob) for p in _PART)
    full = any(p.search(blob) for p in _FULL)
    if part and not full:
        return PART_TIME
    if full and not part:
        return FULL_TIME
    return None
