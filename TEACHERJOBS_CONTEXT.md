# TeacherJobs App — Full Context Document for Claude Code
## Purpose
Build a web-hosted job aggregation platform for an educator seeking teaching positions in Chicagoland. The app scrapes district job portals on a cron schedule, ranks postings by relevance to the user's profile using Claude AI, and presents a live dashboard. This is the MVP. Phase 2 will add AI-assisted application submission.

---

## Architecture Overview

### Frontend
- **Framework:** Next.js (App Router)
- **Deploy:** Vercel
- **Auth:** Supabase Auth (email/password login for the educator)
- **UI:** Tailwind CSS — clean, mobile-friendly dashboard

### Backend
- **API Layer:** Next.js API routes (Node.js) hosted on Vercel
- **Database:** Supabase (PostgreSQL) — stores job postings, user profile, relevance scores, application tracking status
- **Scrapers:** Python scripts using `httpx` + `BeautifulSoup4` (static HTML scraping), with `Playwright` stubbed in for JS-heavy portals
- **Cron Scheduler:** GitHub Actions (free tier) — runs scrapers 3x daily (7am, 12pm, 5pm CST)
- **AI Ranking:** Anthropic Claude API (`claude-sonnet-4-6`) — compares each job posting to the user's saved profile and assigns a relevance score 1-10 with a short explanation

### Key Data Flow
1. GitHub Actions cron triggers Python scraper scripts
2. Each scraper fetches job listings from a district portal
3. New/updated postings are upserted into Supabase `job_postings` table
4. For each new posting, a Claude API call scores relevance against the user's profile
5. User logs into the Next.js app, sees a ranked feed of postings
6. Each card shows: title, district, grade level, subject, posted date, relevance score, and a "View & Apply" link to the original portal

---

## Database Schema (Supabase / PostgreSQL)

### `job_postings`
```sql
CREATE TABLE job_postings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  district_id TEXT NOT NULL,           -- e.g. 'cps', 'cusd200', 'd203'
  district_name TEXT NOT NULL,          -- e.g. 'Chicago Public Schools'
  title TEXT NOT NULL,
  description TEXT,
  category TEXT,                        -- e.g. 'Elementary School Teaching'
  location TEXT,                        -- school name within district
  posting_date DATE,
  closing_date DATE,
  external_url TEXT NOT NULL,           -- link to original posting
  external_id TEXT,                     -- unique ID from the portal if available
  raw_html TEXT,                        -- raw scraped HTML for detail page
  is_new BOOLEAN DEFAULT TRUE,
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  relevance_score INTEGER,              -- 1-10, set by Claude API
  relevance_reason TEXT,               -- Claude's explanation
  UNIQUE(district_id, external_id)
);
```

### `user_profile`
```sql
CREATE TABLE user_profile (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  resume_text TEXT,                     -- parsed text from uploaded resume
  target_subjects TEXT[],              -- e.g. ['Math', 'Science']
  target_grade_levels TEXT[],          -- e.g. ['K-5', '6-8', '9-12']
  preferred_districts TEXT[],          -- district_id values
  ideal_role_description TEXT,         -- freeform "what I'm looking for" paragraph
  must_haves TEXT,                      -- freeform
  nice_to_haves TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### `application_tracker`
```sql
CREATE TABLE application_tracker (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  job_posting_id UUID REFERENCES job_postings(id),
  status TEXT DEFAULT 'saved',         -- 'saved', 'applied', 'interviewing', 'rejected', 'offered'
  notes TEXT,
  applied_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## District Scraper Registry

### Platform Summary
| Platform | Count | Scraping Approach |
|---|---|---|
| Frontline / Applitrack | 13 of 14 districts | Static HTML — `httpx` + `BeautifulSoup4` |
| Taleo (Oracle) | 1 district (CPS) | JSON REST endpoint via undocumented API |
| SchoolSpring | 0 (SD54 redirects to Applitrack) | N/A |

---

### District 1: Chicago Public Schools (CPS)
- **district_id:** `cps`
- **Platform:** Oracle Taleo
- **Portal URL:** `https://cpsk12il.taleo.net/careersection/3/jobsearch.ftl?lang=en`
- **Scraping Approach:** Taleo exposes a REST-like JSON endpoint. The job list can be fetched without login.
- **Key Endpoint to investigate:**
  ```
  GET https://cpsk12il.taleo.net/careersection/3/jobsearch.ftl?lang=en
  ```
  Taleo portals typically have an underlying JSON endpoint at a path like:
  ```
  POST https://cpsk12il.taleo.net/careersection/rest/jobboard/job/list
  ```
  Claude Code should use browser DevTools network inspection or Playwright to capture the actual XHR call and replicate it with `httpx`.
- **Notes:** CPS has 1,200+ postings. Must filter by category (Teaching, Certified) to reduce noise. The portal is JS-heavy but the underlying data call is JSON — do NOT use raw HTML scraping here.
- **Filter Categories to target:** Teacher, Counselor, Social Worker, Special Education
- **Login Required:** No for viewing postings

---

### Districts 2–13: Frontline / Applitrack Districts

All use the same platform. The scraper template is identical — only the `{slug}` changes.

#### Applitrack Scraper Pattern

**List page URL:**
```
https://www.applitrack.com/{slug}/OnlineApp/JobPostings/view.asp?embed=1&all=1
```

**Category-filtered URL (for teaching jobs only):**
```
https://www.applitrack.com/{slug}/OnlineApp/default.aspx?Category=Elementary+School+Teaching
https://www.applitrack.com/{slug}/OnlineApp/default.aspx?Category=High+School+Teaching
https://www.applitrack.com/{slug}/OnlineApp/default.aspx?Category=Middle+School+Teaching
https://www.applitrack.com/{slug}/OnlineApp/default.aspx?Category=Special+Services
```

**HTML Structure (confirmed via live fetch):**
- Job listings render as anchor links grouped by category
- Each category is a clickable link: `[Category Name (N)](url)` where N = count
- Clicking "All Jobs" → `?all=1` → shows all postings with count
- Individual posting pages are linked from the list view
- The `?embed=1` variant returns a cleaner HTML without navigation chrome — USE THIS for scraping

**Scraping strategy:**
1. Fetch `view.asp?embed=1&all=1` with `httpx`
2. Parse with `BeautifulSoup4` — find all `<a>` tags linking to individual postings
3. For each posting link, fetch the detail page to get full description
4. Extract: title, category, location (school), posting date, closing date, external URL

**Static HTML:** Yes — no JavaScript rendering needed for list page. Detail pages may vary.

#### Applitrack District Registry

| District | district_id | Slug | Portal URL | Notes |
|---|---|---|---|---|
| Wheaton Warrenville CUSD 200 | `cusd200` | `cusd200` | `https://www.applitrack.com/cusd200/OnlineApp/default.aspx` | Categories confirmed live: Elementary (3), Middle (3), High School (7) teaching |
| Naperville Unit 203 | `d203` | `d203` | `https://www.generalasp.com/d203/onlineapp/default.aspx` | Uses older `generalasp.com` domain — same platform, different base URL |
| Algonquin Unit 300 | `d300` | `d300` | `https://www.applitrack.com/d300/onlineapp/default.aspx` | Standard Applitrack |
| Indian Prairie Unit 204 | `ip204` | `ip204` | `https://www.applitrack.com/ip204/onlineapp/default.aspx` | Standard Applitrack |
| Valley View 365U | `d365` | `d365` | `https://www.applitrack.com/d365/onlineapp/default.aspx` | Also has landing page at vvsd.org/careers |
| Aurora East Unit 131 | `d131` | `d131` | `https://www.applitrack.com/d131/onlineapp/default.aspx` | Standard Applitrack |
| St. Charles Unit 303 | `d303` | `d303` | `https://www.applitrack.com/d303/onlineapp/default.aspx` | Currently heavy on Athletics/Support — still worth scraping teaching categories |
| Plainfield Unit 202 | `lc202` | `lc202` | `https://www.applitrack.com/lc202/onlineapp/jobpostings/view.asp` | Note: slug is `lc202` not `plainfield` |
| Elgin Unit 46 | `u46` | `u46` | `https://www.applitrack.com/u46/onlineapp/default.aspx` | Has custom hub at `careers.u-46.org` that redirects here. Also has older `generalasp.net/u46` |
| Aurora West Unit 129 | `d129` | `d129` | `https://www.applitrack.com/d129/onlineapp/default.aspx` | Standard Applitrack |
| Schaumburg Elementary 54 | `sd54` | `sd54` | `https://www.applitrack.com/sd54/onlineapp/default.aspx` | Listed as SchoolSpring in research but confirmed Applitrack at this URL |
| Oswego Unit 308 | `d308` | `d308` | `https://www.applitrack.com/d308/onlineapp/default.aspx?all=1` | Standard Applitrack |
| Palatine Elementary 15 | `ccsd15` | `ccsd15` | `https://www.applitrack.com/ccsd15/onlineapp/default.aspx` | Standard Applitrack |
| Waukegan Unit 60 | `waukeganschools` | `waukeganschools` | `https://www.applitrack.com/waukeganschools/onlineapp/jobpostings/view.asp` | Standard Applitrack |

**Note on GeneralASP districts (Naperville 203, Elgin 46 older URL):**
- `generalasp.com` and `generalasp.net` are older Frontline domains
- HTML structure is identical to `applitrack.com` — same scraper works, just swap base URL
- Use `applitrack.com` URL for Elgin (u46) — the `careers.u-46.org` hub redirects there

---

## Python Scraper Architecture

### File Structure
```
/scrapers
  __init__.py
  base_scraper.py          # Abstract base class
  applitrack_scraper.py    # Handles all 13 Frontline districts
  cps_taleo_scraper.py     # Handles CPS Taleo portal
  district_config.py       # Registry of all districts + slugs
  run_all.py               # Orchestrator — called by cron
  requirements.txt
```

### `district_config.py` skeleton
```python
DISTRICTS = [
    {
        "district_id": "cps",
        "name": "Chicago Public Schools",
        "platform": "taleo",
        "base_url": "https://cpsk12il.taleo.net/careersection/3/",
        "target_categories": ["Teacher", "Certified", "Special Education"],
    },
    {
        "district_id": "cusd200",
        "name": "Wheaton Warrenville CUSD 200",
        "platform": "applitrack",
        "slug": "cusd200",
        "base_url": "https://www.applitrack.com",
        "target_categories": [
            "Elementary School Teaching",
            "Middle School Teaching",
            "High School Teaching",
            "Special Services",
        ],
    },
    {
        "district_id": "d203",
        "name": "Naperville Unit 203",
        "platform": "applitrack",
        "slug": "d203",
        "base_url": "https://www.generalasp.com",  # older domain
        "target_categories": [
            "Elementary School Teaching",
            "Middle School Teaching",
            "High School Teaching",
            "Special Services",
        ],
    },
    # ... add remaining districts from registry table above
]
```

### `applitrack_scraper.py` skeleton
```python
import httpx
from bs4 import BeautifulSoup
from datetime import date

class ApplitrackScraper:
    def __init__(self, district_config):
        self.config = district_config
        self.slug = district_config["slug"]
        self.base_url = district_config.get("base_url", "https://www.applitrack.com")

    def get_postings_url(self, category=None):
        if category:
            return f"{self.base_url}/{self.slug}/OnlineApp/default.aspx?Category={category.replace(' ', '+')}"
        return f"{self.base_url}/{self.slug}/OnlineApp/JobPostings/view.asp?embed=1&all=1"

    def fetch_all_postings(self):
        """Fetch all teaching-category postings and return list of dicts."""
        postings = []
        for category in self.config.get("target_categories", []):
            url = self.get_postings_url(category)
            try:
                response = httpx.get(url, timeout=15, follow_redirects=True)
                response.raise_for_status()
                postings.extend(self.parse_listing_page(response.text, category))
            except Exception as e:
                print(f"Error fetching {self.config['district_id']} / {category}: {e}")
        return postings

    def parse_listing_page(self, html, category):
        """Parse Applitrack listing page HTML — returns list of posting dicts."""
        soup = BeautifulSoup(html, "html.parser")
        postings = []
        # TODO: Claude Code to identify exact selectors by inspecting live HTML
        # Applitrack listings are in <table> or <ul> structures with job title links
        # Each link has href pointing to individual posting detail page
        for link in soup.select("a[href*='AppliTrackJobId']"):
            postings.append({
                "title": link.get_text(strip=True),
                "external_url": link["href"],
                "category": category,
                "district_id": self.config["district_id"],
                "district_name": self.config["name"],
                "scraped_at": date.today().isoformat(),
            })
        return postings

    def fetch_posting_detail(self, url):
        """Fetch individual posting page and extract description."""
        try:
            response = httpx.get(url, timeout=15, follow_redirects=True)
            soup = BeautifulSoup(response.text, "html.parser")
            # TODO: Claude Code to identify description container selector
            description_div = soup.select_one(".posting-description, #jobDescription, .jobPostingDescription")
            return description_div.get_text(strip=True) if description_div else ""
        except Exception as e:
            print(f"Error fetching detail {url}: {e}")
            return ""
```

---

## Claude AI Relevance Scoring

### Prompt Template
```python
def build_relevance_prompt(job_posting, user_profile):
    return f"""
You are evaluating a job posting for a teacher job seeker in the Chicago area.

USER PROFILE:
- Target subjects: {', '.join(user_profile['target_subjects'])}
- Target grade levels: {', '.join(user_profile['target_grade_levels'])}
- Preferred districts: {', '.join(user_profile['preferred_districts'])}
- What they are looking for: {user_profile['ideal_role_description']}
- Must-haves: {user_profile['must_haves']}
- Resume summary: {user_profile['resume_text'][:1000]}

JOB POSTING:
- Title: {job_posting['title']}
- District: {job_posting['district_name']}
- Category: {job_posting['category']}
- Location: {job_posting.get('location', 'Not specified')}
- Description: {job_posting.get('description', 'Not available')[:1500]}

TASK:
Score this job posting for relevance to this user on a scale of 1-10.
10 = perfect match. 1 = completely irrelevant.
Return JSON only, no other text:
{{"score": <integer 1-10>, "reason": "<1-2 sentence explanation>"}}
"""
```

---

## Cron Schedule (GitHub Actions)

### `.github/workflows/scrape.yml`
```yaml
name: Scrape Job Postings

on:
  schedule:
    - cron: '0 13 * * *'   # 7am CST (UTC-6)
    - cron: '0 18 * * *'   # 12pm CST
    - cron: '0 23 * * *'   # 5pm CST
  workflow_dispatch:         # manual trigger for testing

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r scrapers/requirements.txt
      - run: python scrapers/run_all.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## Next.js App Structure

```
/app
  /dashboard          # Main feed — ranked job postings
  /profile            # User uploads resume, sets preferences
  /tracker            # Application tracking board (Kanban-style)
  /api
    /jobs             # GET /api/jobs — returns ranked postings from Supabase
    /profile          # GET/POST /api/profile — user profile CRUD
    /tracker          # GET/POST /api/tracker — application status updates
```

### Key Dashboard Features (MVP)
- **"New" badge** on postings added in last 24 hours
- **Relevance score chip** (color-coded: green 8-10, yellow 5-7, gray 1-4)
- **Filter bar:** by district, grade level, category, date range, min relevance score
- **Sort:** by relevance score (default), by posting date
- **Card actions:** "Save", "Mark Applied", "View Original" (external link to portal)
- **"Applied" tracker tab** — shows all jobs she's engaged with and their status

---

## MVP Build Order for Claude Code

1. **Supabase setup** — create tables per schema above, configure auth
2. **Python scraper MVP** — implement `ApplitrackScraper` for 3 districts (cusd200, d203, d300), get data flowing into Supabase
3. **CPS Taleo scraper** — use Playwright to capture XHR call, replicate with httpx
4. **Claude ranking function** — implement `score_posting()` that calls Anthropic API
5. **Next.js dashboard** — job feed with filters, relevance scores, New badges
6. **Profile page** — resume upload (parse to text), preference form
7. **Application tracker** — status board
8. **GitHub Actions cron** — wire up and test
9. **Deploy to Vercel** — env vars, Supabase connection
10. **Add remaining 10 Applitrack districts** — clone scraper config

---

## Scraping Ethics & Reliability Notes

- **Respect rate limits:** Add `time.sleep(1-2)` between requests per district
- **User-Agent:** Set a descriptive User-Agent string: `"TeacherJobsApp/1.0 (personal use job aggregator)"`
- **Robots.txt:** Check each portal's robots.txt before scraping — most school district portals don't restrict crawlers
- **Dedup strategy:** Use `UNIQUE(district_id, external_id)` in DB — upsert on conflict, update `scraped_at`
- **Error handling:** Log failures per district, don't let one failed scraper kill the whole run
- **Playwright fallback stub:** If a district portal goes JS-heavy or blocks httpx, swap to Playwright headless Chrome — stub is already in `base_scraper.py`

---

## Environment Variables Required

```
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
ANTHROPIC_API_KEY=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

---

## Phase 2 Roadmap (Not MVP)

- **AI Application Agent:** Playwright-powered agent that logs into each district portal on behalf of the user, fills application forms using her stored profile, and submits. Claude coordinates field mapping.
- **Email notifications:** Alert user when new high-relevance postings appear
- **Oak Park SD 97 + OPRF 200 + Evanston D65 + D202:** Research and add these portals (likely also Applitrack)
- **Resume tailoring:** Claude generates a tailored cover letter for each high-score posting
- **Interview prep:** Claude generates practice questions based on the job description
