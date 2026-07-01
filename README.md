# ClassQuest 🎒

> Find your classroom.

![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E?logo=supabase&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/AI-Claude-D97757)
![Vercel](https://img.shields.io/badge/Deploy-Vercel-000?logo=vercel&logoColor=white)
[![Scrape](https://github.com/Grantha2/classquest/actions/workflows/scrape.yml/badge.svg)](https://github.com/Grantha2/classquest/actions/workflows/scrape.yml)

A personal job aggregator + application tracker for an elementary educator job-hunting in Chicagoland. It scrapes **32 district portals** — individual districts, county ROE consortiums, and CPS — 3× daily, filters to **grades 1–6 general-classroom** teaching, scores each posting for relevance with Claude, **geocodes it onto an interactive map**, and presents a ranked feed with a "within N miles" radius filter and a Kanban application tracker. Closed positions retire automatically.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS |
| Auth + DB | Supabase (PostgreSQL + Supabase Auth) |
| Scrapers | Python 3.11 · `httpx` · `BeautifulSoup4` · `supabase-py` · Playwright (CPS fallback) |
| AI ranking | Anthropic Claude API (`claude-sonnet-4-6`) |
| Maps | Leaflet + OpenStreetMap (CARTO) tiles · Google Geocoding API |
| Cron | GitHub Actions (3× daily) |
| Deploy | Vercel |

## Engineering documentation

Comprehensive maintainer documentation now lives in [`docs/README.md`](docs/README.md). Start there for architecture, database, API, scraper, operations, security, development, and contribution guides.

## Project layout

```
app/                     Next.js App Router
  page.tsx               redirect → /dashboard or /login
  login/                 Supabase email/password auth
  dashboard/             ranked job feed (server guard + client feed)
  profile/               resume upload + preferences
  tracker/               drag-and-drop Kanban board
  api/
    jobs/                GET ranked postings
    profile/             GET/POST profile · resume/ POST PDF → text
    tracker/             GET/POST application status
components/              JobCard, FilterBar, RelevanceChip, StatusBadge, NavBar, Logo
lib/
  supabase/              browser + server + middleware clients (@supabase/ssr)
  types.ts               shared types
  districts.ts           district + subject reference data (mirrors scraper config)
middleware.ts            session refresh + route protection
supabase/schema.sql      run this in the Supabase SQL editor
scrapers/                Python scraper system (see below)
.github/workflows/       scrape.yml cron
```

> **Note on structure:** the original spec sketched a top-level `api/` folder. In the
> App Router, route handlers must live under `app/api/**/route.ts`, so that's where
> they are. The Supabase client is split into `lib/supabase/{client,server,middleware}.ts`
> so auth/RLS works correctly on both the server and the browser.

---

## Setup (do these in order)

### 1. Install & run the web app locally

```bash
npm install
cp .env.example .env.local   # then fill in the values (see below)
npm run dev                  # http://localhost:3000
```

### 2. Create the Supabase project + schema

1. Create a project at [supabase.com](https://supabase.com).
2. **SQL Editor → New query →** paste the contents of [`supabase/schema.sql`](supabase/schema.sql) and run it. This creates `job_postings`, `user_profile`, `application_tracker`, `geocode_cache`, the `mark_old_postings()` function, and the RLS policies.
   - *Upgrading an existing project?* Run [`supabase/02_location.sql`](supabase/02_location.sql) to add the geocoding/home-base columns.
3. **Project Settings → API** — copy the values into your env (next step).

### 3. Environment variables

Fill `.env.local` (web app) — and set the server-side keys in GitHub Actions and/or Vercel wherever the relevant runtime uses them:

| Variable | Where it's used | Notes |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | browser + server | Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | browser + server | anon/public key |
| `SUPABASE_URL` | Python scrapers | same as project URL |
| `SUPABASE_SERVICE_KEY` | Python scrapers | **service role** key — bypasses RLS, server-only, never expose |
| `ANTHROPIC_API_KEY` | scorer | from [console.anthropic.com](https://console.anthropic.com) |
| `GOOGLE_MAPS_API_KEY` | geocoding (scraper + `/api/profile`) | Google Cloud Geocoding API, billing enabled; server-only |
| `CLASSQUEST_USER_EMAIL` | scraper profile selection | recommended GitHub Actions secret for choosing the intended profile |
| `SCORER_MODEL` | scorer | optional Anthropic model override; defaults to the low-cost scorer model |
| `GITHUB_DISPATCH_TOKEN` | `/api/profile` | optional Vercel/server token to dispatch `scrape.yml` after scoring-relevant profile changes |
| `GITHUB_REPO` | `/api/profile` | optional `owner/repo` override for workflow dispatch |

### 4. Create your login + profile

1. Run the app, go to `/login`, **Sign up** with your email/password.
   - If Supabase email confirmation is on, confirm via the emailed link (or disable confirmations under **Authentication → Providers → Email** for a single-user app).
2. Go to `/profile`, upload your resume PDF, add target specializations, pick preferred districts, and describe your ideal role. This profile is what Claude scores postings against.

### 5. Run the scrapers locally (optional smoke test)

```bash
cd scrapers
python -m venv .venv && .venv/Scripts/activate   # Windows
#   source .venv/bin/activate                     # macOS/Linux
pip install -r requirements.txt
playwright install chromium                       # only needed for the CPS fallback
# from the repo root, with SUPABASE_URL / SUPABASE_SERVICE_KEY set; add ANTHROPIC_API_KEY and GOOGLE_MAPS_API_KEY for scoring/geocoding:
python scrapers/run_all.py
```

The orchestrator prints a run summary: districts scraped, new postings, postings scored, and per-district errors. A failed district never crashes the run.

### 6. Wire the cron (GitHub Actions)

1. Push this repo to GitHub.
2. **Repo Settings → Secrets and variables → Actions** — add `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_MAPS_API_KEY`, and `CLASSQUEST_USER_EMAIL`; optionally add `SCORER_MODEL`.
3. **Actions tab → "ClassQuest — Scrape Job Postings" → Run workflow** to test the manual trigger. After that it runs at 7am / 12pm / 5pm CST.

### 7. Deploy to Vercel

1. Import the repo at [vercel.com](https://vercel.com).
2. Add the web app env vars in the Vercel project settings (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `GOOGLE_MAPS_API_KEY`, plus optional `GITHUB_DISPATCH_TOKEN` / `GITHUB_REPO` for immediate re-scoring dispatch).
3. Deploy. The app is the project root (no monorepo config needed).

---

## How elementary-only is enforced (two layers)

1. **Scraper layer** — Applitrack scrapers only fetch `Elementary School Teaching`
   and `Special Services` categories; CPS is filtered to elementary keywords.
2. **Scorer layer** — Claude is instructed to auto-score any non-elementary posting
   (middle/high school, admin, athletics, support) a **1**, even if it slips through.

## Scoring behavior

- Scored against the **most complete** `user_profile` row (`run_all.get_user_profile`), not
  whatever row is first — so an empty stray row can't make every score generic.
- Postings are scored when `scored_at` is missing or older than the selected profile `updated_at`, so profile edits can refresh scores without re-scoring every run.
- Capped at 150 postings/run to bound API cost.
- A scoring failure leaves `scored_at` unchanged so it is retried next run; it never crashes.

## Coverage audit & tests

- `python scrapers/audit.py` — read-only per-portal report: reachable? · raw fetched · kept ·
  why the rest were dropped (by filter rule). Use it to confirm we're not silently
  over-filtering or missing an unreachable portal.
- `scrapers/.venv/Scripts/python.exe -m pytest scrapers/ -q` — locks in the title-filter
  keep/drop decisions and the geocode query builder. (`pytest` is a dev-only dependency.)

## Known limitations

- **Single user.** Scoring uses one profile for the whole DB. Correct for one job-seeker; a
  second user would need per-user scoring (each posting scored per profile).

## Phase 2 (not in scope)

AI-assisted application submission, email alerts for high-relevance postings,
resume/cover-letter tailoring, and interview prep. Today, **View Posting →** links
out to each district's original posting for manual application.
```

> Build verified: `npm run build` passes (all routes + middleware compile); the Applitrack
> parser and CPS Taleo normalizer are covered by offline unit tests.
