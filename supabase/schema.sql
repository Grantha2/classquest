-- ClassQuest — Supabase schema.
-- Run this in the Supabase SQL editor (Database → SQL Editor → New query).
-- Safe to re-run: uses IF NOT EXISTS / CREATE OR REPLACE / DROP POLICY IF EXISTS.

-- ─────────────────────────────────────────────────────────────
-- Job postings from all district scrapers
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS job_postings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  district_id TEXT NOT NULL,
  district_name TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT,
  location TEXT,              -- school name within district
  posting_date DATE,
  closing_date DATE,
  external_url TEXT NOT NULL,
  external_id TEXT,           -- unique ID from the portal
  raw_html TEXT,
  is_new BOOLEAN DEFAULT TRUE,
  is_active BOOLEAN DEFAULT TRUE,  -- FALSE once a posting drops out of the feed (closed)
  first_seen_at TIMESTAMPTZ DEFAULT NOW(),  -- immutable; basis for "new" (scraped_at is refreshed each run)
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  relevance_score INTEGER,    -- 1-10, set by Claude API
  relevance_reason TEXT,      -- Claude's explanation
  scored_at TIMESTAMPTZ,      -- when scored; re-scored when the profile is updated after this
  grade_levels SMALLINT[],    -- grades 1-6 named in the title (for the grade filter)
  employment_type TEXT,       -- 'full_time' | 'part_time' | NULL (not stated)
  latitude DOUBLE PRECISION,  -- set by the geocoding pass
  longitude DOUBLE PRECISION,
  geocoded_address TEXT,
  geocode_status TEXT DEFAULT 'pending',  -- 'pending' | 'ok' | 'failed'
  UNIQUE (district_id, external_id)
);

CREATE INDEX IF NOT EXISTS idx_job_postings_score ON job_postings (relevance_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_job_postings_posting_date ON job_postings (posting_date DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_job_postings_district ON job_postings (district_id);
CREATE INDEX IF NOT EXISTS idx_job_postings_active ON job_postings (is_active);
CREATE INDEX IF NOT EXISTS idx_job_postings_first_seen ON job_postings (first_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_postings_grades ON job_postings USING GIN (grade_levels);
CREATE INDEX IF NOT EXISTS idx_job_postings_geocode_status ON job_postings (geocode_status);
CREATE INDEX IF NOT EXISTS idx_job_postings_latlng ON job_postings (latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_job_postings_scored_at ON job_postings (scored_at);
CREATE INDEX IF NOT EXISTS idx_job_postings_employment ON job_postings (employment_type);

-- Shared geocode cache so a school/address is only looked up once.
-- Service-role-only (scraper); RLS enabled with no policy denies anon/authenticated.
CREATE TABLE IF NOT EXISTS geocode_cache (
  query TEXT PRIMARY KEY,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  formatted_address TEXT,
  status TEXT NOT NULL DEFAULT 'ok',  -- 'ok' | 'failed'
  geocoded_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE geocode_cache ENABLE ROW LEVEL SECURITY;
GRANT ALL ON public.geocode_cache TO service_role;

-- Per-scrape run record (scrape-driven freshness for the dashboard header).
CREATE TABLE IF NOT EXISTS scrape_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_at TIMESTAMPTZ DEFAULT NOW(),
  districts_scraped INTEGER,
  new_postings INTEGER,
  geocoded INTEGER,
  scored INTEGER,
  unreachable INTEGER,
  active_total INTEGER
);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_run_at ON scrape_runs (run_at DESC);
GRANT SELECT ON public.scrape_runs TO anon, authenticated;
GRANT ALL ON public.scrape_runs TO service_role;
ALTER TABLE scrape_runs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "read scrape_runs" ON scrape_runs;
CREATE POLICY "read scrape_runs" ON scrape_runs FOR SELECT USING (true);

-- Auto-mark postings as not-new after 24 hours.
-- Call from a Supabase scheduled job, or from run_all.py after each scrape.
CREATE OR REPLACE FUNCTION mark_old_postings()
RETURNS void AS $$
  UPDATE job_postings SET is_new = FALSE
  WHERE first_seen_at < NOW() - INTERVAL '24 hours' AND is_new = TRUE;
$$ LANGUAGE sql;

-- ─────────────────────────────────────────────────────────────
-- User profile — one per user.
-- NOTE: grade_level is intentionally omitted. ClassQuest is elementary-only.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_profile (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) UNIQUE,
  resume_text TEXT,
  target_subjects TEXT[],         -- e.g. ['General Elementary', 'Reading', 'STEM']
  preferred_districts TEXT[],     -- district_id values the user prioritizes
  ideal_role_description TEXT,    -- freeform "what I'm looking for"
  must_haves TEXT,
  nice_to_haves TEXT,
  home_address TEXT,              -- ZIP or address for "within N miles" filtering
  home_latitude DOUBLE PRECISION,
  home_longitude DOUBLE PRECISION,
  digest_opt_in BOOLEAN NOT NULL DEFAULT FALSE,   -- daily email digest (scrape cron)
  digest_min_score SMALLINT NOT NULL DEFAULT 7,
  digest_last_sent_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────
-- Application tracker
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS application_tracker (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  job_posting_id UUID REFERENCES job_postings(id),
  status TEXT DEFAULT 'saved',    -- 'saved','applied','interviewing','rejected','offered'
  notes TEXT,
  applied_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (user_id, job_posting_id)
);

-- ─────────────────────────────────────────────────────────────
-- Row Level Security
-- ─────────────────────────────────────────────────────────────
ALTER TABLE user_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE application_tracker ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can only access their own profile" ON user_profile;
CREATE POLICY "Users can only access their own profile"
  ON user_profile FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can only access their own tracker" ON application_tracker;
CREATE POLICY "Users can only access their own tracker"
  ON application_tracker FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- job_postings has NO RLS: it is shared, read-only reference data for any
-- logged-in user. The Python scrapers write to it with the service-role key,
-- which bypasses RLS regardless.
