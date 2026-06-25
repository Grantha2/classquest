-- ClassQuest — location/geocoding migration.
-- Run this in the Supabase SQL editor on an existing project. Idempotent.

-- Coordinates on each posting (filled in by the scraper's geocoding pass).
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS geocoded_address TEXT;
ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS geocode_status TEXT DEFAULT 'pending';
-- 'pending' = not yet geocoded · 'ok' = has coords · 'failed' = no result (don't retry)

CREATE INDEX IF NOT EXISTS idx_job_postings_geocode_status ON job_postings (geocode_status);
CREATE INDEX IF NOT EXISTS idx_job_postings_latlng ON job_postings (latitude, longitude);

-- Shared cache so a school/address is only geocoded once across postings + runs.
CREATE TABLE IF NOT EXISTS geocode_cache (
  query TEXT PRIMARY KEY,            -- normalized location query
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  formatted_address TEXT,
  status TEXT NOT NULL DEFAULT 'ok', -- 'ok' | 'failed'
  geocoded_at TIMESTAMPTZ DEFAULT NOW()
);
-- Lock it down: only the scraper's service-role key (which bypasses RLS) touches
-- this table. Enabling RLS with NO policy denies all anon/authenticated access.
ALTER TABLE geocode_cache ENABLE ROW LEVEL SECURITY;
-- The service_role still needs table privileges (RLS bypass != GRANT).
GRANT ALL ON public.geocode_cache TO service_role;

-- Home base for "within N miles" filtering.
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS home_address TEXT;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS home_latitude DOUBLE PRECISION;
ALTER TABLE user_profile ADD COLUMN IF NOT EXISTS home_longitude DOUBLE PRECISION;
