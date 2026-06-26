# ClassQuest — Roadmap & Agent Workstreams

A map from where ClassQuest is **today (live)** to the **envisioned product**, broken into
discrete workstreams that additional specialized agents can own in parallel. Each workstream is
written to be handed to a fresh agent with enough context to act, and notes what needs a
**human/product decision** vs. what an agent can do autonomously.

---

## 1. Where ClassQuest is today (live & autonomous)

| Area | State |
|---|---|
| **Scraping** | 32 portals, 3×/day GitHub Actions cron. CPS (Taleo `searchjobs` JSON) + 13 individual Applitrack districts + 4 DuPage sub-consortiums + **5 county ROE consortiums** (DuPage/Cook/Kane/Lake/Will) + N/NW Cook districts. |
| **Relevance** | Grades 1–6 general-classroom title filter (`title_filter.classify_title`), Claude (`claude-sonnet-4-6`) scoring 1–10 against the user's profile. |
| **Reliability** | Reachability detection + HTTP retries (never silently miss a portal), closed-posting **retirement** (`is_active`), `scrapers/audit.py` coverage report, 62 pytest cases. |
| **Data** | Supabase Postgres; geocoded (Google, cached); immutable `first_seen_at`; `grade_levels`. ~234 postings across 46 districts. |
| **App** | Next.js 14 dashboard: ranked feed, **map** (Leaflet, score-colored), filters (district, grade, distance/radius from home base, subject, min-score, new-24h), Kanban tracker, resume/profile. |

## 2. The envisioned ClassQuest (the gap to close)

> Comprehensive Chicagoland visibility → personalized ranking → **proactive surfacing** (alerts)
> → **assisted application** (cover letters, prep) → eventually **automated application**.

Concretely, still ahead: total-coverage assurance, richer posting data (FT/PT, salary), proactive
email digests, AI application support (cover letters / interview prep / resume tailoring), and the
Phase-2 automated application agent. Plus the open question of whether this stays a personal tool
or becomes a multi-user product.

---

## 3. Agent workstreams

Each can be spawned as a background agent. **A–D are independent and parallelizable now.**
E depends on good data + profile; F is high-risk and gated on decisions; G/H are cross-cutting.

### A. Coverage & Scraper-Health Agent  ·  *recall is the north star*
- **Owns:** capturing 100% of relevant postings across (and beyond) Chicagoland; portal health.
- **First tasks:** find Berwyn South 100's slug; add McHenry County + remaining collar districts; recon the SchoolSpring platform (SD54) and Kendall/Grundy (`roe24`); run `audit.py` on a schedule and flag any `UNREACHABLE` or `raw≫kept` drift; tune `title_filter` from the drop-log.
- **Deliverables:** verified `district_config.py` entries; a recurring coverage report; filter PRs.
- **Human decision:** how far to expand geographically; the **"427 no-signal" recall lever** (keep tight vs. loosen ambiguous grade-less "Teacher" titles and let the scorer arbitrate).
- **Reuse:** `scrapers/audit.py`, `classify_title` (returns drop reasons), the consortium + `skip_district_numbers` pattern.

### B. Data Quality & Enrichment Agent  ·  *richer fields = better filters & scoring*
- **Owns:** structured posting data beyond title/location.
- **First tasks:** parse **employment type (FT/PT)** from the Applitrack posting block → unblocks the FT/PT filter; extract salary/stipend, contract length, start date; harden free-text parsing (`_LOCATION_RE`, `_DISTRICT_FIELD_RE`) against drift; strengthen cross-source dedup.
- **Deliverables:** new columns + parsers + pytest cases; the FT/PT filter end-to-end.
- **Reuse:** `applitrack_scraper.parse_output` (already extracts Position Type / Date / Location), `run_all.extract_grades` as a parsing template.

### C. Frontend & UX Agent  ·  *daily-use polish*
- **Owns:** the dashboard/tracker experience.
- **First tasks:** **bilingual filter toggle** (a dedicated chip; today it's a fuzzy subject match); saved searches; mobile/responsive pass; accessibility; loading/empty states; map clustering when markers are dense.
- **Deliverables:** components/pages, all behind `npm run build`.
- **Reuse:** `components/FilterBar.tsx` (district/grade multi-select patterns), `lib/types.ts` `JobFilters`.

### D. Notifications Agent  ·  *proactive surfacing*
- **Owns:** the daily email digest + alerts.
- **First tasks:** integrate an email provider (**Resend** recommended), a `subscriptions` model + opt-in UI, a digest cron (GitHub Actions or Supabase scheduled fn) querying `first_seen_at >= last 24h` filtered to the user's preferences/score, and a templated email.
- **Deliverables:** email pipeline + cron + opt-in toggle on `/profile`.
- **Human decision:** provider + cadence (daily/instant for high-score) + sender domain.

### E. AI Application-Assist Agent  ·  *reduce application friction (Phase 2, low-risk)*
- **Owns:** Claude-generated artifacts per posting.
- **First tasks:** "Generate tailored cover letter" (from profile + JD), interview-prep questions from the JD, resume-tailoring suggestions for high-score postings.
- **Deliverables:** per-posting actions in the UI + server routes.
- **Depends on:** B (good JD/description text) + a complete profile. **Human decision:** cost ceiling.
- **Reuse:** `scrapers/scorer.py` Anthropic patterns; the `description` already stored per posting.

### F. Application-Automation Agent  ·  *the big Phase-2 swing — high risk*
- **Owns:** AI-assisted form-filling/submission to Applitrack/Taleo using the stored profile.
- **First tasks:** Playwright flow that logs in, maps fields, drafts answers, and **stops for human approval** before submit; per-portal field maps.
- **Human decision (significant):** ethics/ToS, credential storage, and **mandatory human-in-the-loop** gates. Scope this carefully before any build.

### G. QA / Reliability Agent  ·  *cross-cutting*
- **Owns:** correctness as the system grows.
- **First tasks:** expand pytest (scraper parsing, geocode, dedup); a Playwright/e2e smoke for the app; cron-failure alerting; periodic `audit.py` diffing.
- **Reuse:** `scrapers/test_title_filter.py` (62 cases), `audit.py`.

### H. Platform / Multi-user Agent  ·  *only if it becomes a product*
- **Owns:** per-user scoring, RLS-correct multi-tenancy, auth/billing.
- **Human decision (foundational):** **is ClassQuest a personal tool or a product?** This fork changes data model + scoring (today scoring is single-profile by design — see README "Known limitations").

---

## 4. Coordination & sequencing

- **Run in parallel now:** A (coverage), B (data), C (UX), D (notifications) — separate surfaces, low conflict.
- **Sequential / gated:** E after B; F after an explicit ethics/scope decision; H after the personal-vs-product decision.
- **Cross-cutting:** G should review every other stream's PRs.
- **Shared guardrails for any agent:** keep `pytest scrapers/` + `npm run build` green; run `scrapers/audit.py` after filter/config changes; never weaken the retirement "empty scrape = don't retire" guard; respect the single-profile scoring contract until H is decided.

## 5. Immediate next actions (you + me, before scaling out)

1. **Run migrations** `04_first_seen.sql` + `05_grades.sql` (gating: the feed errors without `first_seen_at`).
2. **Set `CLASSQUEST_USER_EMAIL`** + ensure `/profile` is filled → then **backfill grades** and **null + re-score** so every score reflects the real profile. *(Both ready to run on my side once the migrations are confirmed.)*
3. **Decide the "427 no-signal" recall lever** (tight vs. loosen) — the single biggest recall knob.
4. **Commit + deploy** the current batch (Vercel) so the app is reachable beyond localhost.
5. **Pick an email provider** to unblock workstream D.

## 6. How additional agents help *you and me*

- **They offload me** on the parallelizable, well-scoped streams (A coverage recon, B parsing, C UI, G tests) so I can stay on integration + the trickier judgment calls.
- **They surface decisions to you** rather than guessing: each stream above lists the human/product calls (geography, recall lever, email provider, personal-vs-product, automation ethics).
- **They stay safe** by following the shared guardrails (§4) and the existing tests/audit as the contract.

> Brief any agent with: this file + the README + `scrapers/audit.py` output, and the one decision its
> stream is blocked on. That's enough for it to start cold.
