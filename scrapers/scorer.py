"""Claude relevance scoring for ClassQuest job postings.

Cost discipline (the contract):
  * Cheap model — Haiku.
  * The profile is stable across a run, so it lives in the SYSTEM prefix with a
    cache_control breakpoint: across the up-to-150 calls of a run, the profile
    prefix is prompt-cached. (Haiku's minimum cacheable prefix is ~4096 tokens;
    a small profile silently skips the cache, which is harmless.)
  * Only the per-posting content goes in the (uncached) user message.
  * run_all decides WHAT to score: unscored rows + rows whose scored_at is
    older than the profile's updated_at — never the whole table every run.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import anthropic

MODEL = "claude-haiku-4-5"
MAX_TOKENS = 300

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


SCORING_RULES = """You are a relevance scoring assistant for a GENERAL elementary classroom teacher
job seeker in the Chicago area. The user is seeking general elementary classroom
teaching positions for grades 1-6 only. You receive one job posting per message
and score it 1-10 for relevance to the user profile below.
10 = perfect match (general elementary classroom, grades 1-6). 1 = not relevant.
Automatically score a 1 for any position that is special education (all forms),
kindergarten-only, PreK/early childhood, middle/junior high/high school, administration,
athletics, or non-teaching support staff (e.g. speech pathologist, aide, custodian) —
even if it slipped through the category filter. A grade span that includes grade 1 or
above (e.g. "K-2") is acceptable; only kindergarten-ONLY or PreK-only should score 1.
In the reason, speak directly to the user ("you"), referencing their profile —
this is shown on the job card as "why this score".
Always return JSON only, no other text:
{"score": <integer 1-10>, "reason": "<1-2 sentence explanation>"}"""


def _join(value: Any, default: str = "Not specified") -> str:
    if isinstance(value, (list, tuple)):
        items = [str(v) for v in value if v]
        return ", ".join(items) if items else default
    if value:
        return str(value)
    return default


def build_system(user_profile: dict[str, Any]) -> list[dict[str, Any]]:
    """Scoring rules + profile as a single cacheable system block.

    Must be byte-identical across calls within a run for the prompt cache to
    hit — keep anything per-posting OUT of here.
    """
    resume = (user_profile.get("resume_text") or "")[:4000]
    profile_block = f"""USER PROFILE:
- Target subjects/specializations: {_join(user_profile.get('target_subjects'))}
- Preferred districts: {_join(user_profile.get('preferred_districts'))}
- Ideal role: {_join(user_profile.get('ideal_role_description'))}
- Must-haves: {_join(user_profile.get('must_haves'))}
- Nice-to-haves: {_join(user_profile.get('nice_to_haves'))}
- Resume: {resume or 'Not provided'}"""
    return [
        {
            "type": "text",
            "text": f"{SCORING_RULES}\n\n{profile_block}",
            "cache_control": {"type": "ephemeral"},
        }
    ]


def build_user_message(job_posting: dict[str, Any]) -> str:
    description = (job_posting.get("description") or "Not available")[:1500]
    return f"""JOB POSTING:
- Title: {job_posting.get('title', 'Not specified')}
- District: {job_posting.get('district_name', 'Not specified')}
- Category: {job_posting.get('category', 'Not specified')}
- School/Location: {_join(job_posting.get('location'))}
- Employment type: {_join(job_posting.get('employment_type'))}
- Closing date: {_join(job_posting.get('closing_date'))}
- Description: {description}

Score this posting for the user. JSON only."""


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
        message = _get_client().messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=build_system(user_profile),
            messages=[{"role": "user", "content": build_user_message(job_posting)}],
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
