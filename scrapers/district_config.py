# ClassQuest — District Configuration (recon-aligned)
#
# Scope: GRADES 1-6, general elementary classroom teaching only.
# Excluded up front: special education (all forms), kindergarten-only, PreK/early
# childhood. Mixed spans that include grade 1+ (e.g. "K-2") are kept by the title
# filter (see title_filter.py).
#
# IMPORTANT: category labels differ per portal. An exact-string mismatch returns
# ZERO jobs silently (no error). Do NOT normalize these strings — they are the
# exact labels each portal uses.
#
# `from_elementary_category`:
#   True  -> the category itself guarantees the elementary band; the title filter
#            only strips SpEd / K-only stragglers.
#   False -> the category spans all grades (CPS "Teacher" facet, Palatine
#            "Certified Teaching Vacancies"); the title filter additionally REQUIRES
#            a positive elementary signal in the title.

DISTRICTS = [
    # CPS: no elementary category. Use the verified Taleo `searchjobs` POST API
    # scoped to the Teacher JOB_FIELD facet (1205 -> 664), then hard title-filter
    # for K-6 (the facet still spans all grade bands). from_elementary_category=False.
    {
        "district_id": "cps",
        "name": "Chicago Public Schools",
        "platform": "taleo",
        "portal_url": "https://cpsk12il.taleo.net/careersection/3/jobsearch.ftl?lang=en",
        "search_endpoint": "https://cpsk12il.taleo.net/careersection/rest/jobboard/searchjobs",
        "portal_id": "4140430395",
        "jobfield_code": "2740430395",  # "Teacher" category facet
        "from_elementary_category": False,
    },

    {
        "district_id": "cusd200",
        "name": "Wheaton Warrenville CUSD 200",
        "platform": "applitrack",
        "slug": "cusd200",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary School Teaching"],
        "from_elementary_category": True,
    },
    {
        "district_id": "d203",
        "name": "Naperville Unit 203",
        "platform": "applitrack",
        "slug": "d203",
        "base_url": "https://www.generalasp.com",  # different domain — same platform
        "target_categories": ["Elementary School Teaching"],
        "from_elementary_category": True,
    },
    {
        "district_id": "d300",
        "name": "Algonquin Unit 300",
        "platform": "applitrack",
        "slug": "d300",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary School Teaching", "Dual Language Teacher"],
        "from_elementary_category": True,
    },
    {
        "district_id": "ip204",
        "name": "Indian Prairie Unit 204",
        "platform": "applitrack",
        "slug": "ip204",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary School Teaching"],
        "from_elementary_category": True,
    },
    {
        "district_id": "d365",
        "name": "Valley View 365U",
        "platform": "applitrack",
        "slug": "d365",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary School Teaching"],
        "from_elementary_category": True,
    },
    {
        "district_id": "d131",
        "name": "Aurora East Unit 131",
        "platform": "applitrack",
        "slug": "d131",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary Teaching"],  # NO "School"
        "from_elementary_category": True,
    },
    {
        "district_id": "d303",
        "name": "St. Charles Unit 303",
        "platform": "applitrack",
        "slug": "d303",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary School Teaching"],  # none posted now — monitor
        "from_elementary_category": True,
    },
    {
        "district_id": "lc202",
        "name": "Plainfield Unit 202",
        "platform": "applitrack",
        "slug": "lc202",  # slug is lc202, not 'plainfield'
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary School Teaching"],
        "from_elementary_category": True,
    },
    {
        "district_id": "u46",
        "name": "Elgin Unit 46",
        "platform": "applitrack",
        "slug": "u46",
        "base_url": "https://www.applitrack.com",
        # inverted naming; dropped "Teacher Early Learners" (PreK)
        "target_categories": ["Teacher Elementary", "Teacher Bilingual"],
        "from_elementary_category": True,
    },
    {
        "district_id": "d129",
        "name": "Aurora West Unit 129",
        "platform": "applitrack",
        "slug": "d129",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary School Teaching"],  # none posted now — monitor
        "from_elementary_category": True,
    },
    {
        "district_id": "d308",
        "name": "Oswego Unit 308",
        "platform": "applitrack",
        "slug": "d308",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Elementary School Teaching"],
        "from_elementary_category": True,
    },
    {
        "district_id": "ccsd15",
        "name": "Palatine CCSD 15",
        "platform": "applitrack",
        "slug": "ccsd15",
        "base_url": "https://www.applitrack.com",
        # no grade split — title signal required
        "target_categories": ["Certified Teaching Vacancies"],
        "from_elementary_category": False,
    },
    {
        "district_id": "waukeganschools",
        "name": "Waukegan Unit 60",
        "platform": "applitrack",
        "slug": "waukeganschools",
        "base_url": "https://www.applitrack.com",
        "target_categories": ["Teaching - Elementary"],  # dash in name
        "from_elementary_category": True,
    },

    # --- DuPage County elementary districts near Wheaton ---
    # These are consortium / single-district Frontline portals with no clean
    # elementary category, so we fetch ALL categories and rely on the title
    # filter (from_elementary_category=False + require_teaching_keyword=True) to
    # isolate grades 1-6 teaching roles. Postings span multiple member districts;
    # the school/location identifies which one (and is geocoded for the map).
    {
        "district_id": "gec",
        "name": "Glenbard Elem Consortium (Glen Ellyn 41 / Lombard 44 / Villa Park 45 / CCSD 89)",
        "platform": "applitrack",
        "slug": "gec",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "swdp",
        "name": "SW DuPage Consortium (Winfield 34 / West Chicago 33)",
        "platform": "applitrack",
        "slug": "swdp",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d15",
        "name": "Marquardt SD 15 (Glendale Heights)",
        "platform": "applitrack",
        "slug": "d15",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d93",
        "name": "CCSD 93 (Bloomingdale / Carol Stream)",
        "platform": "applitrack",
        "slug": "d93",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },

    # --- North/NW Cook individual districts (not in the scook consortium) ---
    {
        "district_id": "d34",
        "name": "Glenview SD 34",
        "platform": "applitrack",
        "slug": "d34",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d25",
        "name": "Arlington Heights SD 25",
        "platform": "applitrack",
        "slug": "d25",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d62",
        "name": "Des Plaines CCSD 62",
        "platform": "applitrack",
        "slug": "d62",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d64",
        "name": "Park Ridge-Niles CCSD 64",
        "platform": "applitrack",
        "slug": "d64",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "ccsd59",
        "name": "Elk Grove Township CCSD 59",
        "platform": "applitrack",
        "slug": "ccsd59",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d57",
        "name": "Mount Prospect SD 57",
        "platform": "applitrack",
        "slug": "d57",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d68",
        "name": "Skokie SD 68",
        "platform": "applitrack",
        "slug": "d68",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d69",
        "name": "Skokie-Morton Grove SD 69",
        "platform": "applitrack",
        "slug": "d69",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },
    {
        "district_id": "d98",
        "name": "Berwyn North SD 98",
        "platform": "applitrack",
        "slug": "d98",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
    },

    # --- Regional county ROE / HR consortiums (aggregate MANY districts) ---
    # Fetch all categories; the title filter isolates grades 1-6 teaching. Each
    # posting's real member district is parsed from its "District:" field and
    # used as the label. Districts we already cover via the individual configs
    # above are skipped (skip_district_numbers, scoped per-county to avoid
    # number collisions) so jobs aren't duplicated.
    {
        "district_id": "dupage",
        "name": "DuPage County ROE",
        "platform": "applitrack",
        "slug": "dupage",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
        "is_consortium": True,
        # already covered: cusd200, d203, ip204, gec(41/44/45/89), swdp(34/33), d15, d93, d308
        "skip_district_numbers": ["200", "203", "204", "41", "44", "45", "89", "34", "33", "15", "93", "308"],
    },
    {
        "district_id": "scook",
        "name": "Suburban Cook County Consortium",
        "platform": "applitrack",
        "slug": "scook",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
        "is_consortium": True,
        # already covered: ccsd15 (Palatine), d308 (Oswego)
        "skip_district_numbers": ["15", "308"],
    },
    {
        "district_id": "kane",
        "name": "Kane County HR Consortium",
        "platform": "applitrack",
        "slug": "kane",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
        "is_consortium": True,
        # already covered: d303, d131, d129, u46, d300
        "skip_district_numbers": ["303", "131", "129", "46", "300"],
    },
    {
        "district_id": "lake",
        "name": "Lake County Schools Consortium",
        "platform": "applitrack",
        "slug": "lake",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
        "is_consortium": True,
        # already covered: waukeganschools (60)
        "skip_district_numbers": ["60"],
    },
    {
        "district_id": "willcounty",
        "name": "Will County ROE Consortium",
        "platform": "applitrack",
        "slug": "willcounty",
        "base_url": "https://www.applitrack.com",
        "target_categories": [],
        "from_elementary_category": False,
        "require_teaching_keyword": True,
        "is_consortium": True,
        # already covered: d365, lc202, d308, ip204, d203
        "skip_district_numbers": ["365", "202", "308", "204", "203"],
    },

    # Schaumburg SD54: SchoolSpring platform, NOT Frontline. Excluded from MVP —
    # needs a separate recon pass.
    # {"district_id": "sd54", "platform": "schoolspring",
    #  "portal_url": "https://sd54.schoolspring.com/"},
]
