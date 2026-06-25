-- ClassQuest — posting retirement (hide closed positions).
-- Run this in the Supabase SQL editor on an existing project. Idempotent.

-- The scraper sets this FALSE when a posting drops out of a district's feed
-- (i.e. it closed/filled), and TRUE again if it reappears. The feed shows only
-- active postings.
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
CREATE INDEX IF NOT EXISTS idx_job_postings_active ON job_postings (is_active);
