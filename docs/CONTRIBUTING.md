# Contributing Guide

## Workflow

1. Read the root `README.md` and the relevant document in `docs/` before changing code.
2. Make a focused change with matching tests or verification.
3. Update documentation in the same change when behavior, setup, schema, operations, or security changes.
4. Run the smallest relevant checks plus the broader checks listed below when practical.
5. Commit with a concise message describing the user-visible or operational change.

## Recommended checks

- `npm run typecheck` for TypeScript correctness.
- `npm run build` for Next.js route/page/middleware integration.
- `python -m pytest scrapers/ -q` for scraper/filter regressions.
- `python scrapers/audit.py` for coverage and portal diagnostics after scraper changes.

## Pull request checklist

- [ ] The change is scoped and explained.
- [ ] Relevant docs were updated.
- [ ] New environment variables are documented.
- [ ] Schema changes include SQL migration files and type updates.
- [ ] Scraper changes include tests or audit output.
- [ ] User-owned data remains protected by authenticated sessions and RLS.
- [ ] No secrets or sensitive personal data were committed.

## Coding-agent guidance

- Prefer small, reviewable patches.
- Do not weaken scraper retirement safety.
- Do not convert the product to multi-user scoring without an explicit product decision.
- Do not expose service-role keys outside trusted ingestion contexts.
- Keep final responses and PR descriptions explicit about tests run and limitations.
