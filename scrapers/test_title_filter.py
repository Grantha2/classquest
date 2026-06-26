"""Tests for the title relevance filter + geocode query builder.

Run:  scrapers/.venv/Scripts/python.exe -m pytest scrapers/ -q
These lock in the keep/drop decisions tuned against live data so future edits
to the regex lists don't silently change recall.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))  # import flat modules under pytest

import pytest  # noqa: E402

from title_filter import extract_grades, is_relevant_title  # noqa: E402
from run_all import _district_town, _geocode_query  # noqa: E402


# (title, from_elementary_category, require_teaching_word, expected_keep)
CASES = [
    # --- named elementary category (from_elem=True): only hard-excludes apply ---
    ("2nd Grade Teacher", True, False, True),
    ("Elementary Classroom Teacher", True, False, True),
    ("Elementary School Teacher", True, False, True),
    ("K-2 Teacher", True, False, True),
    ("Language Arts Teacher", True, False, True),
    ("Assistant Teacher", True, False, True),           # classroom role -> keep
    # hard exclusions
    ("Special Education Teacher", True, False, False),
    ("Speech Language Pathologist", True, False, False),
    ("School Psychologist", True, False, False),
    ("Teaching Assistant", True, False, False),
    ("Classroom Teaching Assistant", True, False, False),
    ("Program Assistant", True, False, False),
    ("Paraprofessional", True, False, False),
    ("Teacher Aide", True, False, False),
    ("Custodian", True, False, False),
    ("Music Teacher", True, False, False),
    ("Art Teacher", True, False, False),
    ("Orchestra Teacher", True, False, False),
    ("Band Director", True, False, False),
    ("K-8 Physical Education Teacher", True, False, False),
    ("Athletic Coach", True, False, False),
    ("Assistant Principal", True, False, False),
    ("8th Grade Teacher", True, False, False),
    ("High School Math Teacher", True, False, False),
    ("Middle School Teacher", True, False, False),
    ("Hearing Itinerant Teacher", True, False, False),  # SpEd-adjacent
    # early-childhood band
    ("Kindergarten Teacher", True, False, False),
    ("PreK Teacher", True, False, False),
    ("Kindergarten Teacher - Jefferson Elementary School", True, False, False),
    ("PreK-3 Teacher", True, False, True),              # span into grade 1+
    ("(K-8) Reading Teacher", True, False, True),
    # --- grade-less facets (from_elem=False): need a positive signal ---
    ("Elementary Teacher", False, True, True),
    ("1st Grade Teacher", False, True, True),
    ("4th - 5th Gen Ed", False, False, True),
    ("Teacher", False, True, False),                    # bare -> drop
    ("Spanish Teacher 2026-2027", False, True, False),  # year is not a grade
    ("3rd Grade Teacher 2026-2027", False, True, True),
    ("Bilingual Japanese 2026-2027", False, False, True),   # ccsd15: teaching-scoped
    # all-category consortiums (require_teaching_word=True)
    ("6th Grade Jazz Band", False, True, False),
    ("Bilingual Home School Liaison", False, True, False),
    ("1:1 Elementary School CNA", False, True, False),
    ("Bilingual EL Specialist (teacher)", False, True, True),
    # adjacent instructional specialist roles (surfaced per product decision)
    ("Reading Specialist", False, True, True),
    ("Math Interventionist", False, True, True),
    ("ELL Specialist", False, True, True),
    ("Literacy Coach", False, True, False),             # coach -> excluded
]


@pytest.mark.parametrize("title,from_elem,rtw,expected", CASES)
def test_is_relevant_title(title, from_elem, rtw, expected):
    assert is_relevant_title(title, from_elem, rtw) is expected


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Fox Lake Grade School District", "Fox Lake"),
        ("Itasca School District 10", "Itasca"),
        ("Chicago Public Schools", "Chicago"),
        ("South Holland School District 151", "South Holland"),
        ("Community Unit School District 200", ""),  # no town in the name
    ],
)
def test_district_town(name, expected):
    assert _district_town(name) == expected


def test_geocode_query_generic_school_gets_town():
    q = _geocode_query({"location": "Stanton", "district_name": "Fox Lake Grade School District"})
    assert q == "Stanton School, Fox Lake, IL"


def test_geocode_query_distinctive_school_skips_town():
    # A distinctive name shouldn't get a (possibly-wrong) district-brand "town".
    q = _geocode_query(
        {"location": "Jonas E. Salk Elementary School", "district_name": "Valley View 365U"}
    )
    assert "Valley View" not in q
    assert q.endswith(", IL")


def test_geocode_query_address_passthrough():
    q = _geocode_query(
        {"location": "1419 East 89th Street (Mcdowell)", "district_name": "Chicago Public Schools"}
    )
    assert "1419 East 89th Street" in q


@pytest.mark.parametrize(
    "title,expected",
    [
        ("2nd Grade Teacher", [2]),
        ("4th - 5th Gen Ed", [4, 5]),
        ("K-2 Teacher", [1, 2]),
        ("PreK-3 Regular Teacher", [1, 2, 3]),
        ("(K-8) Reading Teacher", [1, 2, 3, 4, 5, 6]),
        ("Grade 3 Bilingual", [3]),
        ("5th Grade ELA Teacher 2026-2027", [5]),   # year is not a grade
        ("Elementary Classroom Teacher", []),        # no explicit grade
    ],
)
def test_extract_grades(title, expected):
    assert extract_grades(title) == expected
