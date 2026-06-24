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

    # Schaumburg SD54: SchoolSpring platform, NOT Frontline. Excluded from MVP —
    # needs a separate recon pass.
    # {"district_id": "sd54", "platform": "schoolspring",
    #  "portal_url": "https://sd54.schoolspring.com/"},
]
