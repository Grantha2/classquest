"""Claude relevance scoring for ClassQuest job postings."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import anthropic

# Model is configurable. Default to a CHEAP model (Haiku) for bulk scoring — set
# SCORER_MODEL=claude-sonnet-4-6 for higher-quality scoring.
MODEL = os.environ.get("SCORER_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 300

# Static instructions + rules + output format. Cached across the run (it never
# changes), so only the per-posting tokens cost full price.
STATIC_SYSTEM = (
    "You are a relevance scoring assistant for a GENERAL elementary classroom teacher "
    "job seeker in the Chicago area, seeking grades 1-6 general-classroom teaching only.\n\n"
    "Score each posting 1-10 for relevance to the user's profile. "
    "10 = perfect match (general elementary classroom, grades 1-6). 1 = not relevant.\n"
    "Automatically score a 1 for: special education (all forms), kindergarten-only, "
    "PreK/early childhood, middle/junior high/high school, administration, athletics, or "
    "non-teaching support staff (speech pathologist, aide, custodian) — even if it slipped "
    'through the category filter. A grade span including grade 1+ (e.g. "K-2") is acceptable; '
    "only kindergarten-ONLY or PreK-only score 1.\n\n"
    'Return ONLY valid JSON, no other text: {"score": <integer 1-10>, "reason": "<1-2 sentences>"}'
)


def _join(value: Any, default: str = "Not specified") -> str:
    if isinstance(value, (list, tuple)):
        items = [str(v) for v in value if v]
        return ", ".join(items) if items else default
    if value:
        return str(value)
    return default


def build_profile_block(user_profile: dict[str, Any]) -> str:
    """The user's profile — identical across all postings in a run (so it's cached)."""
    resume = (user_profile.get("resume_text") or "")[:1000]
    return f"""USER PROFILE:
- Target subjects/specializations: {_join(user_profile.get('target_subjects'))}
- Preferred districts: {_join(user_profile.get('preferred_districts'))}
- Ideal role: {_join(user_profile.get('ideal_role_description'))}
- Must-haves: {_join(user_profile.get('must_haves'))}
- Resume summary: {resume}"""


def build_job_block(job_posting: dict[str, Any]) -> str:
    description = (job_posting.get("description") or "Not available")[:1500]
    return f"""JOB POSTING:
- Title: {job_posting.get('title', 'Not specified')}
- District: {job_posting.get('district_name', 'Not specified')}
- Category: {job_posting.get('category', 'Not specified')}
- School/Location: {_join(job_posting.get('location'))}
- Description: {description}

Score this posting for the user above. JSON only."""


def _parse_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a model response."""
    text = text.strip()
    # Strip markdown code fences if present.
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def score_posting(
    job_posting: dict[str, Any], user_profile: dict[str, Any]
) -> dict[str, Any]:
    """Return {"score": int|None, "reason": str|None}.

    On any API/parse error, returns score=None so the caller can retry later.
    """
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            # Cache the static instructions + the user profile (same every call in
            # a run) so re-scoring a whole feed costs mostly just per-posting tokens.
            system=[
                {"type": "text", "text": STATIC_SYSTEM},
                {
                    "type": "text",
                    "text": build_profile_block(user_profile),
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            messages=[{"role": "user", "content": build_job_block(job_posting)}],
        )
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        )
        data = _parse_json(text)
        score = int(data["score"])
        score = max(1, min(10, score))  # clamp to valid range
        reason = str(data.get("reason", "")).strip() or None
        return {"score": score, "reason": reason}
    except Exception as exc:  # noqa: BLE001 - never let scoring crash a run
        title = job_posting.get("title", "<unknown>")
        print(f"  [scorer] failed to score '{title}': {exc}")
        return {"score": None, "reason": None}
