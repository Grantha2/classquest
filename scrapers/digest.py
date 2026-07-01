"""Daily email digest — proactive surfacing of new high-match postings.

Runs from the scrape cron (GitHub Actions), NOT from Vercel, so there are no
serverless timeouts and no extra hosting cost. Behavior:

  * Opt-in on /profile (user_profile.digest_opt_in) with a min-score knob.
  * At most one email per day (digest_last_sent_at, 20h guard) — but if the
    7am run has nothing to say, the 12pm/5pm runs re-check, so a strong
    afternoon posting still goes out same-day.
  * Contents: active postings first seen in the last 24h scoring >=
    digest_min_score, best first.
  * No matches -> no email (silence beats noise).

Provider: Resend (plain HTTPS POST — no SDK). Env:
  RESEND_API_KEY      required to send
  RESEND_FROM         optional, default "ClassQuest <onboarding@resend.dev>"
                      (Resend's test sender: delivers only to the account
                      owner's email — fine for a single-user app)
  CLASSQUEST_USER_EMAIL  recipient (falls back to the profile's auth email)
  CLASSQUEST_APP_URL  optional, adds an "open dashboard" link
"""

from __future__ import annotations

import html
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

RESEND_ENDPOINT = "https://api.resend.com/emails"
DEFAULT_FROM = "ClassQuest <onboarding@resend.dev>"
MIN_GAP_HOURS = 20  # "once a day", tolerant of cron jitter
WINDOW_HOURS = 24  # "new" = first seen inside this window
MAX_POSTINGS = 20


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def digest_due(last_sent_at: str | None, now: datetime) -> bool:
    """True if it's been >= MIN_GAP_HOURS since the last digest (or never sent).
    An unparseable timestamp counts as never-sent."""
    last = _parse_ts(last_sent_at)
    if last is None:
        return True
    return now - last >= timedelta(hours=MIN_GAP_HOURS)


def fetch_digest_postings(
    supabase: Any, min_score: int, now: datetime
) -> list[dict[str, Any]]:
    cutoff = (now - timedelta(hours=WINDOW_HOURS)).isoformat()
    return (
        supabase.table("job_postings")
        .select(
            "title, district_name, location, external_url, relevance_score,"
            " relevance_reason, closing_date, employment_type"
        )
        .eq("is_active", True)
        .gte("first_seen_at", cutoff)
        .gte("relevance_score", min_score)
        .order("relevance_score", desc=True)
        .limit(MAX_POSTINGS)
        .execute()
    ).data or []


def _chip(text: str, color: str) -> str:
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:999px;'
        f'font-size:12px;font-weight:600;background:{color};color:#fff;">{text}</span>'
    )


def render_subject(postings: list[dict[str, Any]]) -> str:
    n = len(postings)
    top = postings[0]["title"] if postings else ""
    return f"ClassQuest: {n} new match{'es' if n != 1 else ''} — {top}"[:140]


def render_digest_html(postings: list[dict[str, Any]], app_url: str | None) -> str:
    rows = []
    for p in postings:
        title = html.escape(p.get("title") or "Untitled")
        district = html.escape(p.get("district_name") or "")
        location = html.escape(p.get("location") or "")
        reason = html.escape(p.get("relevance_reason") or "")
        url = html.escape(p.get("external_url") or "#", quote=True)
        score = p.get("relevance_score")
        extras = []
        if p.get("employment_type") == "full_time":
            extras.append("Full-time")
        elif p.get("employment_type") == "part_time":
            extras.append("Part-time")
        if p.get("closing_date"):
            extras.append(f"closes {html.escape(str(p['closing_date']))}")
        meta = " · ".join(x for x in [district, location, *extras] if x)
        rows.append(
            f"""<tr><td style="padding:14px 0;border-bottom:1px solid #e2e8f0;">
  {_chip(f"{score}/10", "#0284c7")}
  <a href="{url}" style="font-size:16px;font-weight:700;color:#0f172a;text-decoration:none;margin-left:6px;">{title}</a>
  <div style="color:#64748b;font-size:13px;margin-top:4px;">{meta}</div>
  {f'<div style="color:#475569;font-size:13px;font-style:italic;margin-top:4px;">&ldquo;{reason}&rdquo;</div>' if reason else ''}
  <div style="margin-top:6px;"><a href="{url}" style="color:#0284c7;font-size:13px;font-weight:600;">View posting &rarr;</a></div>
</td></tr>"""
        )
    footer = (
        f'<p style="margin-top:20px;"><a href="{html.escape(app_url.rstrip("/") + "/dashboard", quote=True)}"'
        f' style="color:#0284c7;font-weight:600;">Open your ClassQuest dashboard &rarr;</a></p>'
        if app_url
        else ""
    )
    return f"""<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px;margin:0 auto;color:#0f172a;">
  <h2 style="margin-bottom:4px;">🎒 ClassQuest daily digest</h2>
  <p style="color:#64748b;margin-top:0;">New grades 1&ndash;6 postings from the last 24 hours that match your profile.</p>
  <table style="width:100%;border-collapse:collapse;">{''.join(rows)}</table>
  {footer}
  <p style="color:#94a3b8;font-size:12px;margin-top:24px;">You get this because the daily digest is on in your
  ClassQuest profile. Turn it off on the Profile page.</p>
</div>"""


def _recipient(supabase: Any, profile: dict[str, Any]) -> str | None:
    email = os.environ.get("CLASSQUEST_USER_EMAIL")
    if email:
        return email
    user_id = profile.get("user_id")
    if not user_id:
        return None
    try:
        resp = supabase.auth.admin.list_users()
        users = resp if isinstance(resp, list) else getattr(resp, "users", []) or []
        match = next((u for u in users if getattr(u, "id", None) == user_id), None)
        return getattr(match, "email", None) if match else None
    except Exception as exc:  # noqa: BLE001
        print(f"  [digest] recipient lookup failed: {exc}")
        return None


def send_via_resend(to: str, subject: str, html_body: str) -> None:
    api_key = os.environ["RESEND_API_KEY"]
    sender = os.environ.get("RESEND_FROM") or DEFAULT_FROM
    resp = httpx.post(
        RESEND_ENDPOINT,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"from": sender, "to": [to], "subject": subject, "html": html_body},
        timeout=30,
    )
    resp.raise_for_status()


def send_daily_digest(supabase: Any, profile: dict[str, Any]) -> str:
    """Send the digest if due. Returns a one-line status for the run summary.
    Never raises past the caller's try/except — a digest failure must not
    affect scraping/scoring."""
    if not profile or not profile.get("digest_opt_in"):
        return "skipped (not opted in)"
    if not os.environ.get("RESEND_API_KEY"):
        return "skipped (RESEND_API_KEY not set)"

    now = datetime.now(timezone.utc)
    if not digest_due(profile.get("digest_last_sent_at"), now):
        return "skipped (already sent today)"

    min_score = int(profile.get("digest_min_score") or 7)
    postings = fetch_digest_postings(supabase, min_score, now)
    if not postings:
        return f"skipped (no new postings scoring >= {min_score} in the last {WINDOW_HOURS}h)"

    to = _recipient(supabase, profile)
    if not to:
        return "skipped (no recipient email — set CLASSQUEST_USER_EMAIL)"

    app_url = os.environ.get("CLASSQUEST_APP_URL")
    send_via_resend(to, render_subject(postings), render_digest_html(postings, app_url))

    supabase.table("user_profile").update(
        {"digest_last_sent_at": now.isoformat()}
    ).eq("user_id", profile["user_id"]).execute()
    return f"sent {len(postings)} posting(s) to {to}"
