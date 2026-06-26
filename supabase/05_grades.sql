-- ClassQuest — grade-level filtering.
-- Stores the grade levels (1-6) named in each posting's title so the dashboard
-- can filter by grade. Run in the Supabase SQL editor. Idempotent.

ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS grade_levels SMALLINT[];
-- GIN index for fast array-overlap filtering (grade_levels && ARRAY[3]).
CREATE INDEX IF NOT EXISTS idx_job_postings_grades ON job_postings USING GIN (grade_levels);

-- The scraper backfills existing rows (grade_levels IS NULL) from their titles
-- on the next run; new postings get grades on insert.
