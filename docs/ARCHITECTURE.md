# Architecture

## Product purpose

ClassQuest is a personal job aggregation and application-tracking system for an elementary educator job search in Chicagoland. The system scrapes district portals, filters postings for grades 1-6 classroom relevance, scores postings against a saved profile, geocodes locations, and presents a ranked dashboard plus Kanban tracker.

## Runtime components

| Component | Technology | Responsibility |
|---|---|---|
| Web app | Next.js 14 App Router, React, Tailwind CSS | Authenticated dashboard, profile management, tracker, map, API route handlers. |
| Auth | Supabase Auth via `@supabase/ssr` | Email/password login and session refresh in middleware. |
| Database | Supabase Postgres | Job postings, user profile, tracker rows, geocode cache, scrape run telemetry. |
| Scrapers | Python 3.11, httpx, BeautifulSoup, optional Playwright fallback | Fetch district portals, normalize postings, retire closed jobs, enrich scores/locations. |
| AI scoring | Anthropic Claude API | Relevance score and explanation for unscored postings. |
| Geocoding | Google Geocoding API + cache table | Coordinates for school/job locations and user home base. |
| Scheduling | GitHub Actions | Runs `python scrapers/run_all.py` three times per day and on demand. |
| Hosting | Vercel | Serves the Next.js app and route handlers. |

## Source layout

```text
app/                    Next.js pages and API route handlers
components/             Shared React UI components
lib/                    Shared TypeScript clients, domain types, districts, utilities
scrapers/               Python scraper, scorer, geocoder, audit, and tests
supabase/               Base schema and incremental SQL migrations
docs/                   Engineering documentation
.github/workflows/      Scheduled scraper workflow
```

## Main data flows

### Scheduled ingestion

1. GitHub Actions starts the `scrape` job from `.github/workflows/scrape.yml`.
2. The workflow installs Python dependencies from `scrapers/requirements.txt`.
3. `scrapers/run_all.py` loads district definitions from `scrapers/district_config.py`.
4. Each district scraper fetches raw listings and normalizes records to the shared posting shape.
5. The orchestrator upserts postings through the Supabase service role key.
6. The run retires postings that were previously active but no longer present, while avoiding destructive retirement when a portal fails or returns no reliable data.
7. Unscored postings are sent to `scrapers/scorer.py` and updated with `relevance_score` and `relevance_reason`.
8. Location data is geocoded through `scrapers/geocode.py` and cached.
9. A row is inserted into `scrape_runs` for dashboard freshness and operational visibility.

### Authenticated web usage

1. `middleware.ts` refreshes Supabase sessions and protects authenticated routes.
2. Dashboard, profile, and tracker pages use server-side guards before rendering client components.
3. Browser components call `app/api/**/route.ts` handlers for profile, jobs, resume extraction, and tracker updates.
4. Profile saves can dispatch `scrape.yml` best-effort when scoring-relevant fields change.
5. Route handlers create server Supabase clients that preserve the user session and rely on RLS for user-owned data.

## Design decisions and invariants

- **Single-profile scoring:** postings are scored once against the most complete user profile. Multi-user personalized scoring would require a schema and pipeline redesign.
- **Service role is scraper-only:** Python ingestion needs broad write access and therefore uses `SUPABASE_SERVICE_KEY`; browser and user-facing route code must never expose it.
- **Filter before scoring:** title/category filtering keeps irrelevant middle/high school, support, athletics, administrative, and non-classroom roles away from expensive scoring.
- **No silent portal failure:** scraper errors are isolated per district and included in run summaries so one bad portal does not crash the whole scrape.
- **Retirement must be conservative:** do not mark old postings inactive when the current run cannot prove a portal was successfully scraped.
- **Route handlers live under `app/api`:** this follows Next.js App Router conventions.

## Extension points

- Add districts in `scrapers/district_config.py` and cover edge cases with scraper tests or `scrapers/audit.py` output.
- Add posting fields with a Supabase migration, parser update, shared type update, API update, and UI filter/card update.
- Add user-facing features as App Router pages/components and keep API contracts documented in `docs/API.md`.
