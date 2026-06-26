"""Scraper for Chicago Public Schools (Oracle Taleo portal).

CPS has NO elementary category — all teachers sit under the broad ``Teacher``
JOB_FIELD facet (~664 postings across K-12). Inclusion to grades 1-6 is done by
the shared title filter (``is_relevant_title(..., from_elementary_category=False)``).

PRIMARY (verified live): the Taleo ``searchjobs`` POST API.
  * POST {search_endpoint}?lang=en&portal={portal_id}
  * Headers: Content-Type application/json, tz GMT-05:00, with session cookies
    (seed them with a GET to the portal first).
  * Body scopes results to the Teacher facet via JOB_FIELD = jobfield_code.
  * Caveat: a malformed body still returns HTTP 200 with the literal text
    "An Error Occurred in TEE" — so validate the body is JSON, not just status.
  * Response: top-level ``requisitionList[]``; each record has ``jobId``,
    ``contestNo`` (e.g. "260001CQ"), and positional ``column[]`` =
    [Title, Location, Posting Date]. Paginate via ``pageNo`` (page size 25).
  * Dedup + detail key is ``contestNo`` (NOT the numeric jobId):
    jobdetail.ftl?job={contestNo}.

FALLBACK: Playwright render of the search page (#JobTableBody rows).
"""

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

import httpx

from base_scraper import BaseScraper, DEFAULT_HEADERS
from title_filter import is_relevant_title

PAGE_SIZE = 25
MAX_PAGES = 40  # safety cap (~1,000 postings)
TEE_ERROR = "An Error Occurred in TEE"


class CPSTaleoScraper(BaseScraper):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.portal_url: str = config["portal_url"]
        self.from_elementary_category: bool = config.get(
            "from_elementary_category", False
        )
        parsed = urlparse(self.portal_url)
        self.origin = f"{parsed.scheme}://{parsed.netloc}"
        self.search_endpoint: str = config.get(
            "search_endpoint",
            f"{self.origin}/careersection/rest/jobboard/searchjobs",
        )
        self.portal_id: str = config.get("portal_id", "")
        self.jobfield_code: str | None = config.get("jobfield_code")

    # -- filtering ------------------------------------------------------

    def _keep(self, title: str) -> bool:
        return is_relevant_title(title, self.from_elementary_category)

    # -- request body ---------------------------------------------------

    def _build_body(self, page_no: int) -> dict[str, Any]:
        job_field_values = [self.jobfield_code] if self.jobfield_code else []
        return {
            "multilineEnabled": False,
            "sortingSelection": {
                "sortBySelectionParam": "3",
                "ascendingSortingOrder": "false",
            },
            "fieldData": {
                "fields": {"KEYWORD": "", "LOCATION": "", "CATEGORY": ""},
                "valid": True,
            },
            "filterSelectionParam": {
                "searchFilterSelections": [
                    {"id": "POSTING_DATE", "selectedValues": []},
                    {"id": "LOCATION", "selectedValues": []},
                    {"id": "JOB_FIELD", "selectedValues": job_field_values},
                ]
            },
            "advancedSearchFiltersSelectionParam": {
                "searchFilterSelections": [
                    {"id": "ORGANIZATION", "selectedValues": []},
                    {"id": "LOCATION", "selectedValues": []},
                    {"id": "JOB_FIELD", "selectedValues": []},
                    {"id": "JOB_NUMBER", "selectedValues": []},
                    {"id": "URGENT_JOB", "selectedValues": []},
                    {"id": "EMPLOYEE_STATUS", "selectedValues": []},
                    {"id": "STUDY_LEVEL", "selectedValues": []},
                ]
            },
            "pageNo": page_no,
        }

    # -- normalization --------------------------------------------------

    def _job_url(self, contest_no: str) -> str:
        return f"{self.origin}/careersection/3/jobdetail.ftl?job={contest_no}"

    @staticmethod
    def _clean_location(value: Any) -> str | None:
        if not value:
            return None
        s = str(value).strip()
        # Location is sometimes a JSON-encoded string; pull readable text out.
        if s[:1] in "[{":
            try:
                data = json.loads(s)
                if isinstance(data, dict):
                    s = " ".join(str(v) for v in data.values() if v)
                elif isinstance(data, list):
                    s = " ".join(str(v) for v in data if v)
            except (ValueError, TypeError):
                pass
        return s[:120] or None

    def _normalize(self, req: dict[str, Any]) -> dict[str, Any] | None:
        cols = req.get("column") or []
        contest_no = str(req.get("contestNo") or "").strip()
        job_id = str(req.get("jobId") or "").strip()

        if cols and isinstance(cols[0], str):
            # Verified positional shape: [Title, Location, Posting Date].
            title = cols[0].strip()
            location = self._clean_location(cols[1]) if len(cols) > 1 else None
            posting_date = (
                cols[2].strip() if len(cols) > 2 and isinstance(cols[2], str) else None
            )
        else:
            # Dict-style fallback (older Taleo payloads).
            flat: dict[str, str] = {}
            for col in cols:
                if isinstance(col, dict):
                    name = (col.get("columnName") or "").upper()
                    if name:
                        flat[name] = col.get("noLink") or col.get("value") or ""
            title = (flat.get("TITLE") or req.get("descriptor") or "").strip()
            location = self._clean_location(flat.get("LOCATION"))
            posting_date = flat.get("POSTINGDATE") or None

        if not title:
            return None
        external_id = contest_no or job_id
        if not external_id:
            return None

        return {
            "district_id": self.district_id,
            "district_name": self.district_name,
            "title": title,
            "external_id": external_id,  # contestNo is the dedup/detail key
            "external_url": self._job_url(contest_no or job_id),
            "category": "Teacher",
            "location": location,
            "description": None,
            "posting_date": None,  # raw Taleo date format varies; leave for scorer
            "closing_date": None,
        }

    # -- searchjobs strategy -------------------------------------------

    def _fetch_via_searchjobs(self) -> list[dict[str, Any]]:
        # Seed Taleo session cookies (the POST needs them).
        try:
            self._client.get(self.portal_url)
            self.polite_sleep()
        except Exception:  # noqa: BLE001
            pass

        url = f"{self.search_endpoint}?lang=en&portal={self.portal_id}"
        headers = {
            **DEFAULT_HEADERS,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "tz": "GMT-05:00",
        }

        postings: list[dict[str, Any]] = []
        seen: set[str] = set()

        for page_no in range(1, MAX_PAGES + 1):
            resp = self.request("POST", url, json=self._build_body(page_no), headers=headers)
            if TEE_ERROR in resp.text:
                print("  [cps] searchjobs returned a TEE error; stopping")
                break
            try:
                data = resp.json()
            except ValueError:
                print("  [cps] searchjobs response was not JSON; stopping")
                break
            self.reachable = True  # endpoint responded with valid JSON

            requisitions = data.get("requisitionList") or []
            if not requisitions:
                break

            for req in requisitions:
                if not isinstance(req, dict):
                    continue
                normalized = self._normalize(req)
                if not normalized or normalized["external_id"] in seen:
                    continue
                seen.add(normalized["external_id"])
                if self._keep(normalized["title"]):
                    postings.append(normalized)

            self.polite_sleep()
            if len(requisitions) < PAGE_SIZE:
                break

        return postings

    # -- Playwright fallback -------------------------------------------

    def _fetch_via_playwright(self) -> list[dict[str, Any]]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("  [cps] playwright not installed; skipping fallback")
            return []

        postings: list[dict[str, Any]] = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(user_agent=DEFAULT_HEADERS["User-Agent"])
                page.goto(self.portal_url, wait_until="networkidle", timeout=45000)
                self.reachable = True
                page.wait_for_selector("#JobTableBody tr, a.titlelink", timeout=20000)

                for row in page.query_selector_all("#JobTableBody tr"):
                    link = row.query_selector("td.jobTitle a, a.titlelink")
                    if not link:
                        continue
                    title = (link.inner_text() or "").strip()
                    href = link.get_attribute("href") or ""
                    if not title or not href or not self._keep(title):
                        continue
                    external_url = href if href.startswith("http") else f"{self.origin}{href}"
                    contest = ""
                    for part in urlparse(external_url).query.split("&"):
                        if part.startswith("job="):
                            contest = part.split("=", 1)[1]
                    postings.append(
                        {
                            "district_id": self.district_id,
                            "district_name": self.district_name,
                            "title": title,
                            "external_id": contest or external_url,
                            "external_url": external_url,
                            "category": "Teacher",
                            "location": None,
                            "description": None,
                            "posting_date": None,
                            "closing_date": None,
                        }
                    )
                browser.close()
        except Exception as exc:  # noqa: BLE001
            print(f"  [cps] playwright fallback failed: {exc}")
        return postings

    # -- orchestration --------------------------------------------------

    def fetch_all_postings(self) -> list[dict[str, Any]]:
        try:
            postings = self._fetch_via_searchjobs()
            if postings:
                return postings
            print("  [cps] searchjobs returned no rows; trying Playwright fallback")
        except (httpx.HTTPError, ValueError) as exc:
            print(f"  [cps] searchjobs failed ({exc}); trying Playwright fallback")

        return self._fetch_via_playwright()
