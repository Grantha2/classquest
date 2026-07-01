-- ClassQuest — per-scrape run record.
-- Gives the dashboard a reliable, scrape-driven "last scraped / N new this run"
-- instead of inferring freshness from row timestamps. Run in the SQL editor.

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

-- Scraper (service role) writes; the app reads the latest row for the header.
GRANT SELECT ON public.scrape_runs TO anon, authenticated;
GRANT ALL ON public.scrape_runs TO service_role;
ALTER TABLE scrape_runs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "read scrape_runs" ON scrape_runs;
CREATE POLICY "read scrape_runs" ON scrape_runs FOR SELECT USING (true);
