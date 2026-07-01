# Security and Privacy

## Data handled

ClassQuest can store personally sensitive job-search data, including account identifiers, resume text extracted from PDFs, profile preferences, home-base location, and application statuses/notes.

## Secret handling

- Never commit real environment variables, API keys, service-role keys, cookies, or credentials.
- `SUPABASE_SERVICE_KEY` belongs only in trusted server/operator contexts such as GitHub Actions secrets or a local maintainer shell.
- `NEXT_PUBLIC_*` variables are public by design; do not put secrets in them.
- Rotate keys if they are printed in logs, committed, or shared outside intended secret stores.

## Authentication and authorization

- Supabase Auth is the identity provider.
- Middleware refreshes sessions and protects dashboard/profile/tracker routes.
- User-owned data must be scoped by the authenticated user and RLS policies.
- Do not trust client-supplied `user_id`; derive ownership from the current session.

## Logging guidance

Safe to log:

- District IDs, counts, run durations, HTTP status summaries, and non-sensitive error classes.

Avoid logging:

- Resume text, profile free-form text, exact home address, API keys, access tokens, cookies, and full raw HTML if it may contain personal data.

## Third-party APIs

- Anthropic receives posting text and profile context for scoring. Keep prompts focused and avoid sending unnecessary personal data.
- Google receives location queries for geocoding. Prefer school/district addresses over personal data when possible; for home-base geocoding, send only what the user intentionally saved.
- Supabase stores all application data and enforces RLS for user-facing paths.

## Dependency and supply-chain notes

- Use the committed lockfiles for reproducible installs.
- Review dependency upgrades for breaking auth, parsing, or rendering behavior.
- Treat scraper dependencies as production dependencies because scheduled ingestion depends on them.

## Security checklist for changes

- Does the change expose new data to the browser or API response?
- Does it require a new secret? If so, document storage locations and rotation expectations.
- Does it bypass RLS or use service-role credentials? If so, keep it out of user-reachable routes.
- Does it add logs? If so, verify logs do not include sensitive text or credentials.
- Does it integrate a new third party? If so, document what data is sent and why.
