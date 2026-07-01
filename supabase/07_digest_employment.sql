-- ClassQuest — daily email digest opt-in + employment type (FT/PT).
-- Run in the Supabase SQL editor. Idempotent.

-- ── Digest preferences (one user; lives on the profile) ──
-- The scrape cron sends at most one digest per day (guarded by
-- digest_last_sent_at) with new postings scoring >= digest_min_score.
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS digest_opt_in BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS digest_min_score SMALLINT NOT NULL DEFAULT 7;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS digest_last_sent_at TIMESTAMPTZ;

-- ── Employment type, parsed from the posting text ──
-- 'full_time' | 'part_time' | NULL (unknown / not stated).
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS employment_type TEXT;
CREATE INDEX IF NOT EXISTS idx_job_postings_employment ON job_postings (employment_type);
