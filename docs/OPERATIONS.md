# Operations Runbook

## Production surfaces

| Surface | Owner action |
|---|---|
| Vercel project | Hosts the Next.js app and stores web environment variables. |
| Supabase project | Stores auth, Postgres data, RLS policies, and SQL functions. |
| GitHub Actions | Runs scheduled scraper workflow and stores scraper secrets. |
| Anthropic Console | Provides the scoring API key. |
| Google Cloud | Provides the Geocoding API key and billing controls. |

## Scheduled scraping

The workflow `.github/workflows/scrape.yml` runs at 13:00, 18:00, and 23:00 UTC, corresponding to the intended 7am, noon, and 5pm Central Standard Time schedule. It can also be started manually with `workflow_dispatch`.

Required GitHub Actions secrets:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_MAPS_API_KEY`
- `CLASSQUEST_USER_EMAIL`
- Optional: `SCORER_MODEL`

Optional Vercel/server environment variables for best-effort profile-save re-scoring:

- `GITHUB_DISPATCH_TOKEN`
- `GITHUB_REPO`

## Deployment checklist

1. Apply pending Supabase migrations in order.
2. Verify Vercel environment variables are present.
3. Verify GitHub Actions secrets are present.
4. Run `npm run build` locally or in CI.
5. Deploy through Vercel.
6. Manually run the scrape workflow after schema or scraper changes.
7. Open the dashboard and verify job cards, score badges, distance filters, map markers, and tracker behavior.

## Routine health checks

- Review the latest GitHub Actions scrape logs for per-district errors.
- Run `python scrapers/audit.py` after district, platform, or filter changes.
- Spot-check high-value districts on their original portals when raw-vs-kept counts change sharply.
- Monitor Supabase table growth and API usage.
- Monitor Anthropic and Google spend/rate limits.

## Incident response

### Scrape workflow fails globally

1. Inspect the GitHub Actions log.
2. Check whether dependency installation, environment variables, or Supabase connectivity failed.
3. Re-run manually after fixing the root cause.
4. Do not run retirement-only repair scripts unless you have confirmed current portal data is trustworthy.

### One district fails

1. Confirm the source portal loads in a browser.
2. Run `python scrapers/audit.py` and isolate the district output.
3. Update slug, base URL, parser, or skip configuration as needed.
4. Add a regression test if parser behavior changed.

### Dashboard errors after migration

1. Confirm all SQL files were applied in order.
2. Check that route handlers and shared types agree with the schema.
3. Run `npm run typecheck` and `npm run build`.
4. Inspect Vercel function logs for the exact route error.

### Bad scores or irrelevant postings

1. Inspect title-filter drop/keep decisions.
2. Confirm the intended profile row is complete.
3. Null scores only for affected postings if a deliberate re-score is needed.
4. Re-run the scraper with scoring enabled.

## Backup and recovery

Use Supabase backups/point-in-time recovery according to the project plan. Before manual data repairs, export affected rows or run the repair inside a transaction that can be rolled back.
