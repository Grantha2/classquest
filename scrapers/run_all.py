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
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

from applitrack_scraper import ApplitrackScraper
from cps_taleo_scraper import CPSTaleoScraper
from district_config import DISTRICTS
from scorer import score_posting

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
    """Insert new postings, refresh scraped_at on existing ones.

    Returns the number of newly-inserted rows.
    """
    if not postings:
        return 0

    existing = (
        supabase.table("job_postings")
        .select("external_id")
        .eq("district_id", district_id)
        .execute()
    )
    existing_ids = {row["external_id"] for row in (existing.data or [])}

    new_rows = [p for p in postings if p["external_id"] not in existing_ids]
    existing_ids_seen = [
        p["external_id"] for p in postings if p["external_id"] in existing_ids
    ]

    # Refresh scraped_at on postings we've seen before (keeps score + is_new).
    for i in range(0, len(existing_ids_seen), 100):
        batch = existing_ids_seen[i : i + 100]
        if batch:
            supabase.table("job_postings").update({"scraped_at": now}).eq(
                "district_id", district_id
            ).in_("external_id", batch).execute()

    if new_rows:
        payload = [
            {col: row.get(col) for col in INSERT_COLUMNS} | {"is_new": True}
            for row in new_rows
        ]
        supabase.table("job_postings").insert(payload).execute()

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


def get_user_profile(supabase: Client) -> dict[str, Any]:
    """ClassQuest is a single-user app; use the first profile row if present."""
    res = supabase.table("user_profile").select("*").limit(1).execute()
    if res.data:
        return res.data[0]
    print("[profile] no user_profile row found — scoring with empty profile")
    return {}


def main() -> None:
    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    profile = get_user_profile(supabase)

    districts_scraped = 0
    total_new = 0
    errors: list[str] = []

    for config in DISTRICTS:
        district_id = config["district_id"]
        print(f"\n=== {config['name']} ({district_id}) ===")
        try:
            scraper = make_scraper(config)
            try:
                postings = scraper.fetch_all_postings()
            finally:
                scraper.close()
            print(f"  found {len(postings)} posting(s)")
            new_count = upsert_postings(supabase, district_id, postings, now)
            print(f"  inserted {new_count} new posting(s)")
            districts_scraped += 1
            total_new += new_count
        except Exception as exc:  # noqa: BLE001 - isolate per-district failures
            msg = f"{district_id}: {exc}"
            errors.append(msg)
            print(f"  [ERROR] {msg}")

    print("\n=== Scoring unscored postings ===")
    scored, score_errors = score_unscored(supabase, profile)

    # Roll postings older than 24h out of the "new" state.
    try:
        supabase.rpc("mark_old_postings").execute()
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] mark_old_postings failed: {exc}")

    print("\n========== RUN SUMMARY ==========")
    print(f"Districts scraped : {districts_scraped}/{len(DISTRICTS)}")
    print(f"New postings      : {total_new}")
    print(f"Postings scored   : {scored}")
    print(f"Scoring errors    : {score_errors}")
    print(f"District errors   : {len(errors)}")
    for err in errors:
        print(f"  - {err}")
    print("=================================")


if __name__ == "__main__":
    main()
