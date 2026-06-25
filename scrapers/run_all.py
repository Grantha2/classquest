"""ClassQuest scraper orchestrator — entrypoint for the GitHub Actions cron.

Flow:
  1. Load every district from district_config.
  2. Run the right scraper per platform (Applitrack / Taleo).
  3. Upsert results into Supabase (insert new, refresh scraped_at on existing).
  4. Score newly-found (and any still-unscored) postings with Claude.
  5. Mark postings older than 24h as not-new.
  6. Print a run summary.

One failed district never crashes the whole run.
"""

from __future__ import annotations

import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

from applitrack_scraper import ApplitrackScraper
from cps_taleo_scraper import CPSTaleoScraper
from district_config import DISTRICTS
from geocode import geocode
from scorer import score_posting

# Reuse the web app's local env file, then fall back to a plain .env.
load_dotenv(".env.local")
load_dotenv()

# Columns we write from scraped data (relevance_* is set later by the scorer).
INSERT_COLUMNS = (
    "district_id",
    "district_name",
    "title",
    "description",
    "category",
    "location",
    "posting_date",
    "closing_date",
    "external_url",
    "external_id",
)

MAX_SCORE_PER_RUN = 150  # bound Claude API cost per run
MAX_GEOCODE_PER_RUN = 250  # bound Google Geocoding calls per run


def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]  # service role — bypasses RLS
    return create_client(url, key)


def make_scraper(config: dict[str, Any]):
    platform = config.get("platform")
    if platform == "applitrack":
        return ApplitrackScraper(config)
    if platform == "taleo":
        return CPSTaleoScraper(config)
    raise ValueError(f"Unknown platform: {platform}")


def upsert_postings(
    supabase: Client, district_id: str, postings: list[dict[str, Any]], now: str
) -> int:
    """Insert new postings, refresh+reactivate seen ones, and retire postings
    that have dropped out of the feed (closed/filled).

    Returns the number of newly-inserted rows.
    """
    if not postings:
        # Empty result: don't retire anything (could be a transient/quiet feed).
        return 0

    current_ids = {p["external_id"] for p in postings}

    existing = (
        supabase.table("job_postings")
        .select("external_id")
        .eq("district_id", district_id)
        .execute()
    )
    existing_ids = {row["external_id"] for row in (existing.data or [])}

    new_rows = [p for p in postings if p["external_id"] not in existing_ids]
    seen_ids = [eid for eid in current_ids if eid in existing_ids]
    stale_ids = [eid for eid in existing_ids if eid not in current_ids]

    # Refresh + reactivate postings we've seen this run (keeps score + is_new).
    for i in range(0, len(seen_ids), 100):
        batch = seen_ids[i : i + 100]
        if batch:
            supabase.table("job_postings").update(
                {"scraped_at": now, "is_active": True}
            ).eq("district_id", district_id).in_("external_id", batch).execute()

    # Retire postings no longer in the feed (closed / filled).
    for i in range(0, len(stale_ids), 100):
        batch = stale_ids[i : i + 100]
        if batch:
            supabase.table("job_postings").update({"is_active": False}).eq(
                "district_id", district_id
            ).in_("external_id", batch).execute()

    if new_rows:
        payload = [
            {col: row.get(col) for col in INSERT_COLUMNS}
            | {"is_new": True, "is_active": True}
            for row in new_rows
        ]
        supabase.table("job_postings").insert(payload).execute()

    if stale_ids:
        print(f"  retired {len(stale_ids)} closed posting(s)")

    return len(new_rows)


def score_unscored(supabase: Client, profile: dict[str, Any]) -> tuple[int, int]:
    """Score postings with relevance_score IS NULL. Returns (scored, errors)."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[score] ANTHROPIC_API_KEY not set — skipping scoring")
        return (0, 0)

    rows = (
        supabase.table("job_postings")
        .select("*")
        .is_("relevance_score", "null")
        .limit(MAX_SCORE_PER_RUN)
        .execute()
    )
    unscored = rows.data or []
    scored = errors = 0

    for row in unscored:
        result = score_posting(row, profile)
        if result["score"] is None:
            errors += 1
            continue
        supabase.table("job_postings").update(
            {
                "relevance_score": result["score"],
                "relevance_reason": result["reason"],
            }
        ).eq("id", row["id"]).execute()
        scored += 1

    return (scored, errors)


def _district_town(name: str) -> str:
    """Pull the town out of a district name, e.g.
    'Fox Lake Grade School District' -> 'Fox Lake',
    'Itasca School District 10' -> 'Itasca',
    'Chicago Public Schools' -> 'Chicago'."""
    t = re.sub(r"\bpublic schools\b", " ", name, flags=re.IGNORECASE)
    t = re.sub(
        r"\b(community unit|community consolidated|consolidated|grade|elementary"
        r"|public|township|unit|cusd|ccsd|esd|sd)\b",
        " ",
        t,
        flags=re.IGNORECASE,
    )
    t = re.sub(r"\bschool district[s]?\b|\bschools?\b|\bdistrict\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"#?\d+[A-Za-z]?\b", " ", t)
    return re.sub(r"\s+", " ", t).strip(" ,.#-")


def _geocode_query(row: dict[str, Any]) -> str:
    """Build an accurate geocoding query: '<School>, <Town>, IL'.

    Uses the school name + the town parsed from the district, so a bare school
    name ('Stanton') doesn't get mis-geocoded onto a lake."""
    loc = (row.get("location") or "").strip()
    district = row.get("district_name", "")

    # Drop non-location placeholders.
    loc = re.sub(
        r"\b(to be determined|tbd|multiple locations|districtwide|district-school"
        r"|no travel|district wide|various)\b.*",
        "",
        loc,
        flags=re.IGNORECASE,
    ).strip(" -,/")

    # Location already carries full state context — trust it.
    if re.search(r",\s*IL\b|illinois", loc, re.IGNORECASE):
        return loc

    town = _district_town(district)
    has_address = bool(re.search(r"\d{2,6}\s+\S+\s+\S", loc))  # "1419 East 89th St"
    parts: list[str] = []

    if loc and has_address:
        parts.append(loc)
        if town:
            parts.append(town)
    elif loc:
        # A bare school name — make it read as a school.
        school = (
            loc
            if re.search(r"school|elementary|academy|primary|center|intermediate", loc, re.IGNORECASE)
            else f"{loc} School"
        )
        parts.append(school)
        # Only add the town when the name is GENERIC (e.g. "Stanton"); a
        # distinctive name ("Jonas E. Salk Elementary") is best found by Google
        # directly, and a wrong "town" (a district brand like "Valley View")
        # would pull the pin off-target.
        core = re.sub(
            r"\b(elementary|middle|high|junior|jr|sr|senior|school|center|primary"
            r"|intermediate|academy|grade|the|of|at)\b",
            " ",
            school,
            flags=re.IGNORECASE,
        )
        distinctive = re.findall(r"[A-Za-z]{2,}", core)
        if len(distinctive) < 2:
            parts.append(town or district)
    else:
        parts.append(town or district)

    parts.append("IL")
    return re.sub(r"\s+", " ", ", ".join(p for p in parts if p)).strip()


def geocode_postings(supabase: Client) -> tuple[int, int]:
    """Geocode postings with geocode_status='pending', using a shared cache.

    Returns (geocoded_ok, failed)."""
    if not os.environ.get("GOOGLE_MAPS_API_KEY"):
        print("[geocode] GOOGLE_MAPS_API_KEY not set — skipping geocoding")
        return (0, 0)

    rows = (
        supabase.table("job_postings")
        .select("id, location, district_id, district_name")
        .eq("geocode_status", "pending")
        .limit(MAX_GEOCODE_PER_RUN)
        .execute()
    ).data or []

    ok = failed = 0
    for row in rows:
        query = _geocode_query(row)

        cached = (
            supabase.table("geocode_cache")
            .select("*")
            .eq("query", query)
            .limit(1)
            .execute()
        ).data
        entry = cached[0] if cached else None

        if entry is None:
            result = geocode(query)
            if result is None:
                continue  # transient — leave pending, retry next run
            if result.get("failed"):
                entry = {"query": query, "status": "failed"}
            else:
                entry = {
                    "query": query,
                    "latitude": result["lat"],
                    "longitude": result["lng"],
                    "formatted_address": result.get("formatted_address"),
                    "status": "ok",
                }
            supabase.table("geocode_cache").upsert(entry, on_conflict="query").execute()
            time.sleep(0.1)  # be gentle on the API

        if entry.get("status") == "ok":
            supabase.table("job_postings").update(
                {
                    "latitude": entry["latitude"],
                    "longitude": entry["longitude"],
                    "geocoded_address": entry.get("formatted_address"),
                    "geocode_status": "ok",
                }
            ).eq("id", row["id"]).execute()
            ok += 1
        else:
            supabase.table("job_postings").update({"geocode_status": "failed"}).eq(
                "id", row["id"]
            ).execute()
            failed += 1

    return (ok, failed)


def get_user_profile(supabase: Client) -> dict[str, Any]:
    """ClassQuest is a single-user app; use the first profile row if present."""
    res = supabase.table("user_profile").select("*").limit(1).execute()
    if res.data:
        return res.data[0]
    print("[profile] no user_profile row found - scoring with empty profile")
    return {}


def main() -> None:
    # Optional CLI filter: `python scrapers/run_all.py cusd200 d203`
    # runs only those district_ids. No args = all districts.
    selected = set(sys.argv[1:])
    districts = [d for d in DISTRICTS if not selected or d["district_id"] in selected]
    if selected:
        print(f"Filtering to {len(districts)} district(s): {', '.join(sorted(selected))}")

    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    profile = get_user_profile(supabase)

    districts_scraped = 0
    total_new = 0
    errors: list[str] = []

    for config in districts:
        district_id = config["district_id"]
        print(f"\n=== {config['name']} ({district_id}) ===")
        try:
            scraper = make_scraper(config)
            try:
                postings = scraper.fetch_all_postings()
            finally:
                scraper.close()
            if not postings:
                # Empty is a valid result (e.g. d303/d129 have nothing posted
                # right now) — not a failure.
                print("  0 postings (none posted right now) - ok")
            else:
                print(f"  found {len(postings)} posting(s)")
            new_count = upsert_postings(supabase, district_id, postings, now)
            if postings:
                print(f"  inserted {new_count} new posting(s)")
            districts_scraped += 1
            total_new += new_count
        except Exception as exc:  # noqa: BLE001 - isolate per-district failures
            msg = f"{district_id}: {exc}"
            errors.append(msg)
            print(f"  [ERROR] {msg}")

    print("\n=== Geocoding new postings ===")
    geocoded, geocode_failed = geocode_postings(supabase)

    print("\n=== Scoring unscored postings ===")
    scored, score_errors = score_unscored(supabase, profile)

    # Roll postings older than 24h out of the "new" state.
    try:
        supabase.rpc("mark_old_postings").execute()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] mark_old_postings failed: {exc}")

    print("\n========== RUN SUMMARY ==========")
    print(f"Districts scraped : {districts_scraped}/{len(districts)}")
    print(f"New postings      : {total_new}")
    print(f"Geocoded          : {geocoded} (failed {geocode_failed})")
    print(f"Postings scored   : {scored}")
    print(f"Scoring errors    : {score_errors}")
    print(f"District errors   : {len(errors)}")
    for err in errors:
        print(f"  - {err}")
    print("=================================")


if __name__ == "__main__":
    main()
