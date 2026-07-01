# Scraper System

## Goals

The scraper system maximizes recall of relevant Chicagoland elementary classroom postings while avoiding obvious non-target roles before they reach AI scoring. It should be reliable enough to run unattended several times per day.

## Key files

| File | Responsibility |
|---|---|
| `scrapers/district_config.py` | Source-of-truth district registry, platform settings, category targets, and consortium configuration. |
| `scrapers/base_scraper.py` | Shared scraper interface and posting shape. |
| `scrapers/applitrack_scraper.py` | Frontline/Applitrack list and detail parsing. |
| `scrapers/cps_taleo_scraper.py` | CPS Taleo search API parsing. |
| `scrapers/title_filter.py` | Keep/drop logic for grades 1-6 classroom relevance. |
| `scrapers/scorer.py` | Anthropic relevance scoring. |
| `scrapers/geocode.py` | Google geocoding and cache lookup helpers. |
| `scrapers/run_all.py` | Orchestrator used by GitHub Actions and local runs. |
| `scrapers/audit.py` | Read-only coverage and filter diagnostics. |
| `scrapers/test_title_filter.py` | Regression tests for filtering and geocode query behavior. |

## Orchestrator lifecycle

1. Load environment variables and Supabase service-role client.
2. Load the most complete user profile for scoring context.
3. Iterate configured districts.
4. Fetch and parse postings with a platform-specific scraper.
5. Apply title/category filters and normalize records.
6. Upsert active postings and preserve lifecycle fields.
7. Retire stale postings only when the source scrape is trustworthy.
8. Geocode missing locations when an API key is configured.
9. Score never-scored postings and postings whose `scored_at` predates the profile update, capped per run for API cost control.
10. Print a summary of district successes, new postings, scored postings, and errors.

## Filtering policy

ClassQuest targets grades 1-6 general classroom roles. The filter should keep elementary classroom, bilingual elementary, interventionist, and relevant special-services roles while dropping high school, middle school, athletics, administrative, substitute-only, aide/paraprofessional, and non-certified support roles unless explicitly needed.

When changing filters:

- Add or update regression cases in `scrapers/test_title_filter.py`.
- Run the audit script to inspect raw vs. kept counts and drop reasons.
- Prefer conservative keep decisions for ambiguous elementary classroom postings, then let Claude scoring rank them down if needed.

## Adding a district

1. Identify the platform and canonical public job URL.
2. Add an entry to `scrapers/district_config.py` with a stable `district_id`.
3. Confirm whether the source has usable external IDs; otherwise define a deterministic fallback.
4. Run `python scrapers/audit.py` and inspect raw count, kept count, and drop reasons.
5. Run `python -m pytest scrapers/ -q` if pytest is installed.
6. Document any portal-specific behavior in the config comment or this guide.

## Scoring

Scoring runs for postings with `scored_at IS NULL` and for postings scored before the selected profile was last updated. The selected profile is resolved by `CLASSQUEST_USER_EMAIL` when configured, otherwise by the most complete profile row. The scorer defaults to the cheaper `claude-haiku-4-5-20251001`; set `SCORER_MODEL=claude-sonnet-4-6` when higher-quality scoring is worth the cost. The prompt must keep non-elementary or non-classroom roles at the bottom of the range even if they contain attractive keywords. Failed scoring should leave `scored_at` unchanged so a future run can retry.

## Geocoding

Geocoding processes rows with `geocode_status='pending'`, builds stable district-aware queries, and checks `geocode_cache` before calling Google. Successful lookups set coordinates and `geocode_status='ok'`; confirmed misses are cached as failed. Transient API failures leave rows pending so a future run can retry. Missing coordinates should degrade UI distance/map behavior gracefully rather than failing ingestion.

## Retirement safety

Never retire existing postings after a failed, unreachable, authenticated, blocked, or obviously incomplete scrape. Empty results are not proof of closure unless the scraper can positively distinguish an empty successful portal from a fetch failure.

## Local commands

```bash
python scrapers/audit.py
python -m pytest scrapers/ -q
python scrapers/run_all.py
```

`run_all.py` requires Supabase service credentials and scoring/geocoding keys for full behavior. `audit.py` is the safer first command because it is read-only.
