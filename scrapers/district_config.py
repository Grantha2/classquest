# ClassQuest — District Configuration
# User is seeking ELEMENTARY positions only.
# All Applitrack districts target only:
#   - "Elementary School Teaching"
#   - "Special Services"
# Middle School Teaching and High School Teaching are intentionally excluded.

ELEMENTARY_CATEGORIES = [
    "Elementary School Teaching",
    "Special Services",
]

DISTRICTS = [
    # --- CPS (Taleo — separate scraper) ---
    {
        "district_id": "cps",
        "name": "Chicago Public Schools",
        "platform": "taleo",
        "portal_url": "https://cpsk12il.taleo.net/careersection/3/jobsearch.ftl?lang=en",
        # CPS Taleo: filter by these keywords to get elementary-level postings only
        "target_keywords": ["Elementary Teacher", "Primary", "Special Education", "Early Childhood"],
    },

    # --- Frontline / Applitrack Districts ---
    {
        "district_id": "cusd200",
        "name": "Wheaton Warrenville CUSD 200",
        "platform": "applitrack",
        "slug": "cusd200",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "d203",
        "name": "Naperville Unit 203",
        "platform": "applitrack",
        "slug": "d203",
        "base_url": "https://www.generalasp.com",  # older Frontline domain — same platform
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "d300",
        "name": "Algonquin Unit 300",
        "platform": "applitrack",
        "slug": "d300",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "ip204",
        "name": "Indian Prairie Unit 204",
        "platform": "applitrack",
        "slug": "ip204",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "d365",
        "name": "Valley View 365U",
        "platform": "applitrack",
        "slug": "d365",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "d131",
        "name": "Aurora East Unit 131",
        "platform": "applitrack",
        "slug": "d131",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "d303",
        "name": "St. Charles Unit 303",
        "platform": "applitrack",
        "slug": "d303",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "lc202",
        "name": "Plainfield Unit 202",
        "platform": "applitrack",
        "slug": "lc202",  # note: slug is lc202, not 'plainfield'
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "u46",
        "name": "Elgin Unit 46",
        "platform": "applitrack",
        "slug": "u46",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "d129",
        "name": "Aurora West Unit 129",
        "platform": "applitrack",
        "slug": "d129",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "sd54",
        "name": "Schaumburg Elementary District 54",
        "platform": "applitrack",
        "slug": "sd54",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "d308",
        "name": "Oswego Unit 308",
        "platform": "applitrack",
        "slug": "d308",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "ccsd15",
        "name": "Palatine CCSD 15",
        "platform": "applitrack",
        "slug": "ccsd15",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
    {
        "district_id": "waukeganschools",
        "name": "Waukegan Unit 60",
        "platform": "applitrack",
        "slug": "waukeganschools",
        "base_url": "https://www.applitrack.com",
        "target_categories": ELEMENTARY_CATEGORIES,
    },
]
