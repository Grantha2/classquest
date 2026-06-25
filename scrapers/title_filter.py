"""Title-level relevance filter — runs on every posting BEFORE any DB write or
Claude call, so irrelevant rejects cost nothing.

Scope: grades 1-6 general elementary classroom teaching. Excludes special
education (all forms), kindergarten-only, PreK/early childhood, secondary,
admin, athletics, and non-teaching support roles.

Grade-band rules (matters most for grade-less facets like CPS "Teacher" and
Palatine "Certified Teaching Vacancies"):
  * A span that reaches into grades 1-6 is KEPT even if it starts at K/PreK
    ("K-2", "PreK-3", "(K-8)", "4th - 5th").
  * Kindergarten-ONLY and PreK-ONLY are dropped.
  * Secondary bands (6-8, 7-8, 9-12, 7th/8th/9th-12th) are dropped.
  * Year ranges (e.g. "2026-2027") must NOT be mistaken for grade spans.

The lists are intentionally tunable as we observe live titles.
"""

import re

# Hard exclusions — always reject, regardless of any elementary signal.
HARD_EXCLUDE = [
    # secondary / out-of-band grade markers
    r"\bhigh school\b", r"\bHS\b", r"\bsecondary\b",
    r"\b(9th|10th|11th|12th)\b",
    r"\bmiddle school\b", r"\bjunior high\b", r"\bjr\.? high\b", r"\b(7th|8th)\b",
    r"\b6\s*-\s*8\b", r"\b7\s*-\s*8\b", r"\b6\s*-\s*12\b", r"\b7\s*-\s*12\b",
    r"\b9\s*-\s*12\b", r"\b8\s*-\s*12\b",
    # special education (all forms) + related services
    r"\bspecial ed", r"\bsped\b", r"\bresource (teacher|room)\b",
    r"\bself-contained\b", r"\bdiverse learner", r"\bcross-categorical\b", r"\bLBS1\b",
    r"\bitinerant\b", r"\bdeaf\b", r"\bblind\b",
    r"\bvisually impaired\b", r"\bhearing impaired\b", r"\bhard of hearing\b",
    # "specials" / non-general-classroom subjects (scope is general elementary
    # classroom only). NOTE: the (?<!language ) guard keeps "Language Arts" / ELA.
    r"(?<!language )\barts?\b", r"\bmusic\b", r"\bband\b", r"\borchestra\b",
    r"\bchoir\b", r"\bchorus\b", r"\bdrama\b", r"\btheat(?:er|re)\b", r"\bdance\b",
    r"\bphysical ed", r"\bphys\.? ?ed\b", r"\bP\.?E\.?\b",
    r"\bcoordinator\b",
    # admin / non-teaching / support
    r"\bprincipal\b", r"\bdean\b", r"\bsuperintendent\b", r"\bdirector\b",
    r"\bcoach\b", r"\bathletic", r"\bcustodian\b", r"\bmaintenance\b",
    r"\bbus\b", r"\bdriver\b", r"\btransportation\b", r"\bsecretary\b",
    r"\bclerk\b", r"\bregistrar\b", r"\baide\b", r"\bpara(professional|educator)?\b",
    r"\bliaison\b", r"\bCNA\b", r"\bassistant\b",  # teaching/instructional/program assistant
    r"\bmonitor\b", r"\bsupervisor\b", r"\bsecurity\b",
    r"\bcafeteria\b", r"\bfood service\b", r"\bnutrition\b", r"\bnurse\b",
    r"\bspeech\b", r"\bSLP\b", r"\boccupational therap", r"\bphysical therap",
    r"\bpsychologist\b", r"\bsocial worker\b", r"\bcounselor\b",
    r"\binterpreter\b", r"\bsubstitute\b", r"\bstudent teacher\b",
]

# A title references an early-childhood band (kindergarten / PreK / preschool).
EARLY_BAND = re.compile(
    r"\b(kindergarten|pre-?k|preschool|early childhood|early learner)\b", re.IGNORECASE
)

# GRADE signal: the role explicitly reaches into grades 1-6. Only these rescue
# an early-childhood/kindergarten title. Deliberately avoids bare multi-digit
# numbers so year ranges like "2026-2027" don't register.
GRADE_SIGNAL = [
    # "Elementary" as a role, but NOT a school name ("Jefferson Elementary School")
    # — while still allowing the literal title "Elementary School Teacher".
    r"\belementary\b(?!\s+school\b)", r"\belementary school teacher\b",
    r"\bprimary\b", r"\bintermediate\b",
    r"\b(1st|2nd|3rd|4th|5th|6th)\b",
    r"\b(first|second|third|fourth|fifth|sixth)\s+grade\b",
    r"\bgrades?\s*[1-6]\b",
    r"\bk\s*-\s*[1-8]\b",          # K-1 .. K-8
    r"\bpre-?k\s*-\s*[1-8]\b",     # PreK-1 .. PreK-8
    r"\b[1-6]\s*-\s*[1-8]\b",      # 1-6, 2-5, 4-5 (single-digit grade ranges)
]

# SUBJECT signal: in-scope general-ed role keywords. These count toward
# inclusion for grade-less facets, but do NOT rescue an early-childhood title
# (e.g. "Bilingual Early Childhood" stays excluded).
SUBJECT_SIGNAL = [r"\bclassroom teacher\b", r"\bbilingual\b", r"\bdual language\b"]

# Words that mark an actual teaching role. Required for ALL-category portals
# (consortiums) where non-teaching postings are mixed in.
TEACHING_WORD = [r"\bteacher\b", r"\bteaching\b", r"\beducator\b", r"\binstructor\b"]

_HARD = [re.compile(p, re.IGNORECASE) for p in HARD_EXCLUDE]
_GRADE = [re.compile(p, re.IGNORECASE) for p in GRADE_SIGNAL]
_SUBJECT = [re.compile(p, re.IGNORECASE) for p in SUBJECT_SIGNAL]
_TEACH = [re.compile(p, re.IGNORECASE) for p in TEACHING_WORD]


def _has_grade_signal(text: str) -> bool:
    return any(p.search(text) for p in _GRADE)


def _has_keep_signal(text: str) -> bool:
    return _has_grade_signal(text) or any(p.search(text) for p in _SUBJECT)


def _has_teaching_word(text: str) -> bool:
    return any(p.search(text) for p in _TEACH)


def is_relevant_title(
    title: str,
    from_elementary_category: bool,
    require_teaching_word: bool = False,
) -> bool:
    """True if the posting should be kept (scraped, stored, scored).

    require_teaching_word: set for ALL-category portals (e.g. district
    consortiums) where non-teaching roles are mixed in and the title must
    explicitly name a teaching role.
    """
    t = title or ""

    # 1. Hard non-elementary roles — always out.
    for p in _HARD:
        if p.search(t):
            return False

    # 2. Early-childhood band: keep ONLY if a real grade span reaches grades 1-6
    #    (e.g. "K-2", "PreK-3"). A subject keyword alone does not rescue it.
    if EARLY_BAND.search(t) and not _has_grade_signal(t):
        return False

    # 3. A named elementary category already guarantees the band.
    if from_elementary_category:
        return True

    # 4. Grade-less facets (CPS, Palatine, consortiums) need a positive signal.
    if not _has_keep_signal(t):
        return False
    # 5. All-category portals additionally require an explicit teaching role.
    if require_teaching_word and not _has_teaching_word(t):
        return False
    return True
