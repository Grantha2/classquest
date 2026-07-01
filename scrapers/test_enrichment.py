"""Tests for posting enrichment (closing date, FT/PT) and the digest guard.

Run:  scrapers/.venv/Scripts/python.exe -m pytest scrapers/ -q
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))  # import flat modules under pytest

import pytest  # noqa: E402

from applitrack_scraper import _extract_fields  # noqa: E402
from digest import digest_due, render_digest_html, render_subject  # noqa: E402
from employment import extract_employment_type  # noqa: E402


# ── employment type ──────────────────────────────────────────────

EMPLOYMENT_CASES = [
    ("Part-Time Reading Teacher", "part_time"),
    ("Grade 3 Teacher - Full Time", "full_time"),
    ("Full-time Elementary Teacher", "full_time"),
    ("Teacher, part time (mornings)", "part_time"),
    ("Half-time Interventionist", "part_time"),
    ("0.5 FTE Grade 2 Teacher", "part_time"),
    (".5 FTE Bilingual Teacher", "part_time"),
    ("FTE: 0.6 — Grade 4", "part_time"),
    ("1.0 FTE Elementary Classroom Teacher", "full_time"),
    ("FTE 1.0 Grade 5 Teacher", "full_time"),
    # no signal
    ("2nd Grade Teacher", None),
    ("Elementary Teacher 2026-2027", None),
    ("", None),
    (None, None),
    # ambiguous: both signals -> unknown, never guess
    ("Full-time or part-time considered", None),
    # decimals inside larger numbers must not read as FTE fractions
    ("Room 10.5 FTE information session", None),  # "10.5 FTE" is not 0.5
]


@pytest.mark.parametrize("text,expected", EMPLOYMENT_CASES)
def test_extract_employment_type(text, expected):
    assert extract_employment_type(text) == expected


def test_extract_employment_type_multiple_fragments():
    assert extract_employment_type("Grade 1 Teacher", "This is a full-time position.") == "full_time"
    assert extract_employment_type(None, None) is None


# ── Applitrack block fields ──────────────────────────────────────

BLOCK = (
    "Grade 3 Teacher JobID: 4321 Position Type: Elementary School Teaching/Grade 3 "
    "Date Posted: 6/20/2026 Location: Lincoln Elementary School "
    "Closing Date: 07/15/2026 This is a full-time position beginning August 2026."
)


def test_extract_fields_closing_date_and_employment():
    fields = _extract_fields(BLOCK)
    assert fields["posting_date"] == "2026-06-20"
    assert fields["closing_date"] == "2026-07-15"
    assert fields["location"] == "Lincoln Elementary School"
    assert fields["employment_type"] == "full_time"


def test_extract_fields_until_filled_has_no_closing_date():
    fields = _extract_fields(
        "Teacher JobID: 1 Date Posted: 6/1/2026 Location: Central School "
        "Closing Date: Until Filled"
    )
    assert fields["closing_date"] is None
    assert fields["posting_date"] == "2026-06-01"


def test_extract_fields_without_optional_fields():
    fields = _extract_fields("Grade 2 Teacher JobID: 2")
    assert fields["closing_date"] is None
    assert fields["employment_type"] is None


# ── digest ───────────────────────────────────────────────────────

NOW = datetime(2026, 7, 1, 13, 0, tzinfo=timezone.utc)


def test_digest_due_never_sent():
    assert digest_due(None, NOW) is True


def test_digest_due_yesterday():
    assert digest_due((NOW - timedelta(hours=22)).isoformat(), NOW) is True


def test_digest_not_due_same_day():
    assert digest_due((NOW - timedelta(hours=5)).isoformat(), NOW) is False


def test_digest_due_handles_z_suffix_and_garbage():
    assert digest_due("2026-06-30T07:00:00Z", NOW) is True
    assert digest_due("not-a-timestamp", NOW) is True  # treat as never-sent


SAMPLE_POSTINGS = [
    {
        "title": "3rd Grade Teacher <script>",
        "district_name": "Naperville Unit 203",
        "location": "Maplebrook Elementary",
        "external_url": "https://example.com/job?id=1&x=2",
        "relevance_score": 9,
        "relevance_reason": "Matches your 1-6 general-classroom focus.",
        "closing_date": "2026-07-10",
        "employment_type": "full_time",
    },
]


def test_render_digest_html_escapes_and_links():
    out = render_digest_html(SAMPLE_POSTINGS, "https://classquest.example")
    assert "&lt;script&gt;" in out and "<script>" not in out
    assert "https://example.com/job?id=1&amp;x=2" in out
    assert "Full-time" in out and "closes 2026-07-10" in out
    assert "https://classquest.example/dashboard" in out


def test_render_digest_html_without_app_url():
    out = render_digest_html(SAMPLE_POSTINGS, None)
    assert "dashboard" not in out


def test_render_subject():
    assert render_subject(SAMPLE_POSTINGS).startswith("ClassQuest: 1 new match —")
