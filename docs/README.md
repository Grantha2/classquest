# ClassQuest Engineering Documentation

This directory is the canonical engineering handbook for ClassQuest. It complements the root README (setup-oriented) with operational, architectural, and contribution guidance for maintainers and future agents.

## Documentation map

| Document | Purpose | Primary audience |
|---|---|---|
| [Architecture](./ARCHITECTURE.md) | System context, runtime boundaries, request/data flows, and major design decisions. | Engineers changing app, scraper, or data flows. |
| [Database](./DATABASE.md) | Supabase schema, migrations, RLS expectations, lifecycle fields, and query patterns. | Engineers changing persistence, migrations, or API routes. |
| [API Reference](./API.md) | Route handlers, auth expectations, request/response shapes, and error handling. | Frontend/backend engineers integrating app routes. |
| [Scraper System](./SCRAPERS.md) | District registry, scraper lifecycle, scoring, geocoding, retirement, audit, and tests. | Engineers maintaining coverage and scraper reliability. |
| [Local Development](./DEVELOPMENT.md) | Environment setup, commands, test matrix, coding conventions, and troubleshooting. | Any contributor running ClassQuest locally. |
| [Operations Runbook](./OPERATIONS.md) | Deployments, cron, secrets, monitoring, incident response, and recovery tasks. | Maintainers operating production. |
| [Security & Privacy](./SECURITY.md) | Secret handling, RLS boundaries, service-role usage, user data, and safe logging. | Engineers and operators handling data or credentials. |
| [Contributing Guide](./CONTRIBUTING.md) | Change workflow, PR checklist, documentation expectations, and review guidance. | Human contributors and coding agents. |

## Keep these docs current

Update the relevant document in the same pull request whenever a change affects architecture, schema, routes, scraper behavior, environment variables, operations, or security posture. If a behavior is intentionally different from these docs, treat the mismatch as a bug in either the code or documentation.
