# Database Guide

## Schema sources

The authoritative base schema is `supabase/schema.sql`. Incremental migration files in `supabase/` add fields such as location coordinates, immutable first-seen timestamps, grade levels, scrape run telemetry, and scoring timestamps.

Apply migrations in filename order for existing projects. New projects should start with `schema.sql`, then run later numbered migrations if they are not already folded into the base schema.

## Core tables

### `job_postings`

Stores normalized postings from district portals.

Important fields:

- `district_id`, `district_name`: source district identity.
- `title`, `description`, `category`, `location`: user-visible posting content and scraper filter inputs.
- `external_url`, `external_id`: source link and deduplication key.
- `is_active`: whether the posting is still believed open.
- `first_seen_at`, `scraped_at`, `scored_at`: lifecycle and freshness metadata.
- `relevance_score`, `relevance_reason`: AI scoring output.
- `latitude`, `longitude`, `geocoded_address`, `geocode_status`: map, distance-filter, and geocoding lifecycle support.
- `grade_levels`: extracted grade tags for filtering.

Operational notes:

- Use stable source identifiers whenever possible. If a portal lacks an ID, derive one deterministically from the canonical URL.
- Do not overwrite `first_seen_at` during routine upserts.
- Preserve inactive historical rows so tracker records and analytics remain meaningful.

### `user_profile`

Stores the authenticated user's resume text, preferences, home-base location, and free-form ideal-role inputs.

Operational notes:

- Profile rows are user-owned and must remain protected by RLS.
- Resume extraction stores text, not the original PDF file, in the current implementation.
- The scraper scoring pipeline selects the most complete profile for the single-user scoring model.

### `application_tracker`

Stores user-specific workflow state for a posting.

Typical statuses are `saved`, `applied`, `interviewing`, `rejected`, and `offered`. Keep status values synchronized with tracker UI types and validation logic.

### `geocode_cache`

Caches geocoding lookups so repeated scraper runs do not repeatedly bill or rate-limit against the Google Geocoding API.

### `scrape_runs`

Records scrape execution telemetry. Use this for historical visibility and future alerting around portal health.

## RLS and access model

- Browser and route-handler access should use anon/session-aware Supabase clients.
- User-owned tables such as `user_profile` and `application_tracker` must be scoped to `auth.uid()`.
- Public job posting reads are acceptable for authenticated app usage, but writes should be limited to trusted server contexts.
- Python scrapers use the service role key and therefore bypass RLS; keep those credentials restricted to GitHub Actions, local operator shells, and server-side secret stores.

## Migration checklist

When adding or changing columns:

1. Create a numbered SQL migration in `supabase/`.
2. Update `supabase/schema.sql` if the change should be part of fresh installs.
3. Update shared TypeScript types in `lib/types.ts` when the app reads or writes the field.
4. Update Python normalization/upsert logic when scrapers own the field.
5. Update API documentation and any route validation.
6. Run `npm run typecheck`, `npm run build`, and relevant scraper tests.

## Query patterns

- Dashboard queries should filter active postings and sort by relevance/freshness.
- Distance filters require both posting coordinates and a user home-base coordinate.
- Tracker queries must join only the current user's tracker rows to posting details.
- Scoring jobs select postings with `scored_at IS NULL` plus postings whose `scored_at` is older than the selected profile `updated_at`, then respect the per-run cap.
