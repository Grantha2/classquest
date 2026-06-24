"""Claude relevance scoring for ClassQuest job postings."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import anthropic

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 300

SYSTEM_PROMPT = (
    "You are a relevance scoring assistant for a GENERAL elementary classroom teacher \n"
    "job seeker in the Chicago area. The user is seeking general elementary classroom \n"
    "teaching positions for grades 1-6 only. You receive a job posting and a user \n"
    "profile. You return only valid JSON."
)


def _join(value: Any, default: str = "Not specified") -> str:
    if isinstance(value, (list, tuple)):
        items = [str(v) for v in value if v]
        return ", ".join(items) if items else default
    if value:
        return str(value)
    return default


def build_user_message(job_posting: dict[str, Any], user_profile: dict[str, Any]) -> str:
    resume = (user_profile.get("resume_text") or "")[:1000]
    description = (job_posting.get("description") or "Not available")[:1500]
    return f"""USER PROFILE:
- Target subjects/specializations: {_join(user_profile.get('target_subjects'))}
- Preferred districts: {_join(user_profile.get('preferred_districts'))}
- Ideal role: {_join(user_profile.get('ideal_role_description'))}
- Must-haves: {_join(user_profile.get('must_haves'))}
- Resume summary: {resume}

JOB POSTING:
- Title: {job_posting.get('title', 'Not specified')}
- District: {job_posting.get('district_name', 'Not specified')}
- Category: {job_posting.get('category', 'Not specified')}
- School/Location: {_join(job_posting.get('location'))}
- Description: {description}

TASK:
Score this job posting for relevance to this user on a scale of 1-10.
10 = perfect match (general elementary classroom, grades 1-6). 1 = not relevant.
Automatically score a 1 for any position that is special education (all forms),
kindergarten-only, PreK/early childhood, middle/junior high/high school, administration,
athletics, or non-teaching support staff (e.g. speech pathologist, aide, custodian) —
even if it slipped through the category filter. A grade span that includes grade 1 or
above (e.g. "K-2") is acceptable; only kindergarten-ONLY or PreK-only should score 1.
Return JSON only, no other text:
{{"score": <integer 1-10>, "reason": "<1-2 sentence explanation>"}}"""


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
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_user_message(job_posting, user_profile)}
            ],
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
