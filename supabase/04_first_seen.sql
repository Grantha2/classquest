-- ClassQuest — accurate "new" detection.
-- Bug: "new" relied on is_new + mark_old_postings(scraped_at), but the scraper
-- refreshes scraped_at on every run, so postings never aged out and EVERYTHING
-- looked new. Fix: track an immutable first_seen_at and base "new" on that.
-- Run in the Supabase SQL editor. Idempotent.

ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ;

-- Backfill existing rows as "old" so today's run doesn't flag the whole backlog
-- as new. Future inserts get NOW() via the default below.
UPDATE job_postings SET first_seen_at = NOW() - INTERVAL '2 days' WHERE first_seen_at IS NULL;

ALTER TABLE job_postings ALTER COLUMN first_seen_at SET DEFAULT NOW();
CREATE INDEX IF NOT EXISTS idx_job_postings_first_seen ON job_postings (first_seen_at DESC);

-- Age is_new off first_seen_at (immutable) instead of scraped_at (refreshed).
CREATE OR REPLACE FUNCTION mark_old_postings()
RETURNS void AS $$
  UPDATE job_postings SET is_new = FALSE
  WHERE first_seen_at < NOW() - INTERVAL '24 hours' AND is_new = TRUE;
$$ LANGUAGE sql;
