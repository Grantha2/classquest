-- ClassQuest — scoring freshness (close the profile → scoring loop).
-- Tracks WHEN each posting was scored so the scorer can re-score stale rows
-- after the profile changes (scored_at < user_profile.updated_at).
-- Run in the Supabase SQL editor. Idempotent.

ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS scored_at TIMESTAMPTZ;

-- Backfill already-scored rows so stale detection works from day one.
-- scraped_at ≈ "recently touched"; any future profile save is > it, which
-- correctly marks these rows stale against the new profile.
UPDATE job_postings
SET scored_at = scraped_at
WHERE relevance_score IS NOT NULL AND scored_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_job_postings_scored_at ON job_postings (scored_at);
