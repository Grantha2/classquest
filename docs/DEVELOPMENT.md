# Local Development

## Prerequisites

- Node.js compatible with Next.js 14.
- npm, using the committed `package-lock.json`.
- Python 3.11 for scrapers.
- Supabase project or local-compatible credentials for authenticated app flows.
- Optional: Google Geocoding API key and Anthropic API key for full enrichment.

## Install and run the web app

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. The root route redirects to `/dashboard` for authenticated users or `/login` for unauthenticated users.

## Environment variables

| Variable | Used by | Required for |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Web app | Browser/server Supabase client creation. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Web app | Browser/server authenticated requests. |
| `SUPABASE_URL` | Scrapers | Service-role ingestion. |
| `SUPABASE_SERVICE_KEY` | Scrapers | Upserts, retirements, scoring updates, cache writes. |
| `ANTHROPIC_API_KEY` | Scrapers | Relevance scoring. |
| `GOOGLE_MAPS_API_KEY` | Web API and scrapers | Profile home-base and posting geocoding. |
| `CLASSQUEST_USER_EMAIL` | Scrapers | Selecting the intended profile when needed. |
| `SCORER_MODEL` | Scrapers | Optional override for the Anthropic scoring model. |
| `GITHUB_DISPATCH_TOKEN` | Web API | Optional token to dispatch `scrape.yml` after scoring-relevant profile saves. |
| `GITHUB_REPO` | Web API | Optional `owner/repo` override for workflow dispatch; defaults to `Grantha2/classquest`. |

Do not commit `.env.local` or any real secret value.

## Quality commands

```bash
npm run typecheck
npm run build
python -m pytest scrapers/ -q
python scrapers/audit.py
```

Use `npm run build` as the primary web-app integration check because it compiles App Router pages, route handlers, middleware, and TypeScript under Next.js.

## Coding conventions

- Keep shared domain shapes in `lib/types.ts` synchronized with API responses and UI props.
- Keep Supabase client creation in `lib/supabase/*`; do not duplicate auth client setup throughout the app.
- Avoid exposing service-role keys to any browser or route code that can be reached by end users.
- Never wrap imports in `try/catch`; let missing dependency errors fail clearly.
- Add docs updates alongside behavior changes.

## Troubleshooting

### Login redirects unexpectedly

Check `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, Supabase email confirmation settings, and middleware cookie handling.

### Dashboard is empty

Confirm active postings exist, migrations have been applied, and `/api/jobs` is returning data for the authenticated session. If distance filtering is enabled, verify profile home-base coordinates and posting coordinates.

### Scraper run inserts nothing

Run `python scrapers/audit.py` first. Check portal reachability, district config slugs, title-filter drop reasons, and Supabase service credentials.

### Scores stay null

Verify `ANTHROPIC_API_KEY`, postings with missing/stale `scored_at`, a complete profile row or `CLASSQUEST_USER_EMAIL`, and the per-run scoring cap.

### Map markers are missing

Verify `GOOGLE_MAPS_API_KEY`, `geocode_cache`, posting location fields, and that dashboard responses include latitude/longitude.
