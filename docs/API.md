# API Reference

All user-facing API routes are Next.js App Router route handlers under `app/api`. They are intended to be called by authenticated browser sessions unless noted otherwise.

## Authentication model

- Session cookies are maintained by Supabase SSR helpers.
- `middleware.ts` refreshes sessions and redirects unauthenticated users away from protected pages.
- Route handlers should create server Supabase clients and validate the current user before reading or mutating user-owned data.

## Routes

### `GET /api/jobs`

Returns ranked job postings for the dashboard feed.

Supported query parameters:

- `district`: repeatable district IDs.
- `grade`: repeatable grade values from 1 through 6; matches `grade_levels` overlap.
- `subject`: fuzzy search across title, category, and description.
- `minScore`: minimum `relevance_score`; defaults to `1`.
- `isNew=true`: first seen in the last 24 hours based on immutable `first_seen_at`.
- `dateRange=7d|30d`: posting-date freshness filter.
- `sortBy=relevance|date|distance`: relevance is the default; distance applies after coordinates are supplied.
- `page`: one-based page number for paginated feed responses.
- `all=1`: map mode; returns up to the route cap without page slicing.
- `lat`, `lng`, `radius`: home-base radius filter; SQL uses a bounding box and the route computes exact miles.

Expected behavior:

- Returns only active postings with scoring and location fields needed by cards, filters, and map markers.
- Keeps sensitive profile data out of responses.
- Uses `{ jobs, page, pageSize, total }` for both paginated and map-mode responses.

Typical response shape:

```json
{
  "jobs": [
    {
      "id": "uuid",
      "district_id": "d203",
      "district_name": "Naperville Unit 203",
      "title": "Elementary Teacher",
      "location": "Example Elementary",
      "relevance_score": 9,
      "relevance_reason": "Strong match for elementary classroom experience.",
      "external_url": "https://...",
      "latitude": 41.0,
      "longitude": -88.0,
      "distance_mi": 12.4,
      "first_seen_at": "2026-07-01T00:00:00Z"
    }
  ],
  "page": 1,
  "pageSize": 25,
  "total": 1
}
```

### `GET /api/profile`

Returns the current user's profile.

Expected behavior:

- Requires an authenticated user.
- Returns `{ profile: null }` if no row exists yet, or `{ profile }` with the saved row if present.

### `POST /api/profile`

Creates or updates the current user's profile.

Expected behavior:

- Requires an authenticated user.
- Accepts resume text, target subjects, preferred districts, free-form role preferences, and `home_address`.
- Geocodes home-base changes when enough location information is provided and `GOOGLE_MAPS_API_KEY` is configured.
- Upserts by user identity rather than trusting a client-supplied `user_id`.
- Triggers the scrape workflow best-effort when scoring-relevant fields change, if `GITHUB_DISPATCH_TOKEN` is configured.

### `POST /api/profile/resume`

Extracts text from an uploaded resume PDF.

Expected behavior:

- Requires an authenticated user.
- Accepts multipart form data with a PDF file.
- Persists the extracted text into `user_profile.resume_text` and returns `{ resume_text }`.
- Rejects missing, unsupported, unreadable, or textless uploads with a clear client error.

### `GET /api/tracker`

Returns the current user's application tracker data joined with posting details for the Kanban board.

Expected behavior:

- Requires an authenticated user.
- Returns only tracker rows owned by the current user.
- Includes enough posting data for cards to be recognizable without duplicating full job payloads.

### `POST /api/tracker`

Creates or updates a tracker row.

Expected behavior:

- Requires an authenticated user.
- Accepts a job posting ID, status, and optional notes.
- Upserts the row for the current user and posting.
- Automatically stamps `applied_at` when the status is `applied`.
- Validates status values against the tracker column set used by the UI.

## Error handling conventions

- `401` for unauthenticated requests.
- `400` for invalid input or missing required fields.
- `404` when a requested user-owned object or posting cannot be found.
- `500` for unexpected server errors, with logs that do not include secrets or full resume text.

## Adding an API route

1. Add `app/api/<name>/route.ts`.
2. Use the server Supabase client from `lib/supabase/server.ts`.
3. Validate authentication before touching user-owned data.
4. Define request and response types in `lib/types.ts` when the contract is shared with UI code.
5. Document the route here and add tests or a manual verification note.
