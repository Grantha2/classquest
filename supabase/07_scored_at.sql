-- ClassQuest — re-score when the profile changes (cost-efficiently).
-- Each posting records when it was scored. The scraper re-scores a posting when
-- it's unscored OR was scored before the user's profile was last updated — so
-- editing your preferences refreshes the scores (capped per run to bound cost).
-- Run in the Supabase SQL editor. Idempotent.

ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS scored_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_job_postings_scored_at ON job_postings (scored_at);
