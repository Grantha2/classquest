"""Title-level relevance filter — runs on every posting BEFORE any DB write or
Claude call, so irrelevant rejects cost nothing.

Scope: grades 1-6 general elementary classroom teaching. Excludes special
education (all forms), kindergarten-only, PreK/early childhood, secondary,
admin, athletics, and non-teaching support roles.

The exclude/keep lists are intentionally tunable as we observe live titles.
"""

import re

# Reject if title matches ANY exclude pattern. The kindergarten rule allows K
# only when paired with grade 1+ (so "K-2" passes, "Kindergarten Teacher" fails).
TITLE_EXCLUDE = [
    r"\bkindergarten\b(?!.*\b(1st|2nd|3rd|first|second|third|grade [1-6]))",
    r"\bpre-?k\b", r"\bpreschool\b", r"\bearly childhood\b", r"\bearly learner",
    r"\bspecial ed", r"\bsped\b", r"\bresource (teacher|room)\b",
    r"\bself-contained\b", r"\bdiverse learner", r"\bcross-categorical\b", r"\bLBS1\b",
    # SpEd-adjacent itinerant / related-services roles (still special education)
    r"\bitinerant\b", r"\bdeaf\b", r"\bblind\b",
    r"\bvisually impaired\b", r"\bhearing impaired\b", r"\bhard of hearing\b",
    r"\bhigh school\b", r"\bHS\b", r"\bsecondary\b",
    r"\b(9th|10th|11th|12th)\b", r"\b9-12\b", r"\b6-8\b", r"\b7-8\b",
    r"\bmiddle school\b", r"\bjunior high\b", r"\bjr\.? high\b", r"\b(7th|8th) grade\b",
    r"\bprincipal\b", r"\bdean\b", r"\bsuperintendent\b", r"\bdirector\b",
    r"\bcoach\b", r"\bathletic", r"\bcustodian\b", r"\bmaintenance\b",
    r"\bbus\b", r"\bdriver\b", r"\btransportation\b", r"\bsecretary\b",
    r"\bclerk\b", r"\bregistrar\b", r"\baide\b", r"\bpara(professional|educator)?\b",
    r"\bprogram assistant\b", r"\bmonitor\b", r"\bsupervisor\b", r"\bsecurity\b",
    r"\bcafeteria\b", r"\bfood service\b", r"\bnutrition\b", r"\bnurse\b",
    r"\bspeech\b", r"\bSLP\b", r"\boccupational therap", r"\bphysical therap",
    r"\bpsychologist\b", r"\bsocial worker\b", r"\bcounselor\b",
    r"\binterpreter\b", r"\bsubstitute\b", r"\bstudent teacher\b",
]

# Positive elementary signals — required ONLY for mixed categories (CPS, Palatine).
TITLE_KEEP = [
    r"\belementary\b", r"\bprimary\b", r"\bintermediate\b",
    r"\b(1st|2nd|3rd|4th|5th|6th) grade\b",
    r"\bgrade [1-6]\b", r"\bgrades? [1-6]", r"\bK-[1-6]\b", r"\bK-8\b", r"\bK-6\b",
    r"\b1-[1-6]\b", r"\bclassroom teacher\b", r"\bbilingual\b", r"\bdual language\b",
]


def is_relevant_title(title: str, from_elementary_category: bool) -> bool:
    """True if the posting should be kept (scraped, stored, scored)."""
    t = (title or "").lower()
    for pat in TITLE_EXCLUDE:
        if re.search(pat, t, re.IGNORECASE):
            return False
    if from_elementary_category:
        return True
    return any(re.search(pat, t, re.IGNORECASE) for pat in TITLE_KEEP)
