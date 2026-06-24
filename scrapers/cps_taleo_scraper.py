"""Scraper for Chicago Public Schools (Oracle Taleo portal).

CPS has NO elementary category — all teachers sit under the broad ``Teacher``
facet (~600+ postings across K-12). So inclusion is done by the shared title
filter (``is_relevant_title(..., from_elementary_category=False)``), which
requires a positive elementary signal in the title.

Strategy:
  1. PRIMARY: the Taleo ``searchResults.json`` REST endpoint (no login),
     paginated by 25 via startIndex/stopIndex. Optionally narrowed by the
     Teacher facet's ``jobField`` code if one is configured (an optimization —
     correctness comes from the title filter, not the facet).
  2. FALLBACK: Playwright headless render of the search page, scraping the
     results table (#JobTableBody rows, td.jobTitle).

Dedup key: the Taleo requisition id (``reqId``). Detail page lives at
``jobdetail.ftl?lang=en&job=<reqId>`` (description in
``#requisitionDescriptionInterface``) — not fetched per-posting by default to
keep request volume sane; can be added once CPS is validated live.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from base_scraper import BaseScraper, DEFAULT_HEADERS
from title_filter import is_relevant_title

PAGE_SIZE = 25
MAX_PAGES = 60  # safety cap (~1,500 postings)


class CPSTaleoScraper(BaseScraper):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.portal_url: str = config["portal_url"]
        self.from_elementary_category: bool = config.get(
            "from_elementary_category", False
        )
        parsed = urlparse(self.portal_url)
        self.origin = f"{parsed.scheme}://{parsed.netloc}"
        self.json_endpoint: str = config.get(
            "json_endpoint",
            f"{self.origin}/careersection/rest/jobboard/searchResults.json",
        )
        # Optional Teacher-facet narrowing. Discover once via Playwright (click
        # the Teacher facet, capture the XHR jobField value) and set it here or
        # in district_config as "jobfield_code". None => pull all + title-filter.
        self.jobfield_code: str | None = config.get("jobfield_code")

    # -- filtering ------------------------------------------------------

    def _keep(self, title: str) -> bool:
        return is_relevant_title(title, self.from_elementary_category)

    # -- normalization --------------------------------------------------

    def _job_url(self, req_id: str) -> str:
        return f"{self.origin}/careersection/3/jobdetail.ftl?lang=en&job={req_id}"

    @staticmethod
    def _read_columns(req: dict[str, Any]) -> dict[str, str]:
        out: dict[str, str] = {}
        for col in req.get("column", []) or []:
            if not isinstance(col, dict):
                continue
            name = (col.get("columnName") or "").upper()
            value = col.get("noLink") or col.get("value") or ""
            if name:
                out[name] = value
        return out

    def _normalize(self, req: dict[str, Any]) -> dict[str, Any] | None:
        cols = self._read_columns(req)
        title = (
            cols.get("TITLE") or req.get("descriptor") or req.get("title") or ""
        ).strip()
        if not title:
            return None

        req_id = str(
            req.get("reqId")
            or req.get("jobId")
            or req.get("contestNo")
            or cols.get("REQID")
            or ""
        ).strip()
        if not req_id:
            return None

        location = (cols.get("LOCATION") or req.get("location") or "").strip() or None
        category = (
            cols.get("JOBFIELD") or cols.get("CATEGORY") or req.get("jobField") or "Teacher"
        )
        posting_date = cols.get("POSTINGDATE") or req.get("postingDate") or None

        return {
            "district_id": self.district_id,
            "district_name": self.district_name,
            "title": title,
            "external_id": req_id,
            "external_url": req.get("jobUrl") or self._job_url(req_id),
            "category": category,
            "location": location,
            "description": None,
            "posting_date": posting_date,
            "closing_date": None,
        }

    # -- JSON strategy --------------------------------------------------

    def _fetch_via_json(self) -> list[dict[str, Any]]:
        headers = {**DEFAULT_HEADERS, "Accept": "application/json"}
        postings: list[dict[str, Any]] = []

        for page in range(MAX_PAGES):
            start = page * PAGE_SIZE
            params = {
                "lang": "en",
                "careersection": "3",
                "searchParams.sortBy": "POSTING_DATE",
                "searchParams.sortOrder": "DESC",
                "searchParams.startIndex": str(start),
                "searchParams.stopIndex": str(start + PAGE_SIZE),
            }
            if self.jobfield_code:
                params["searchParams.jobField"] = self.jobfield_code

            resp = self._client.get(self.json_endpoint, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            requisitions = (
                data.get("requisitionList") or data.get("requisitions") or []
            )
            if not requisitions:
                break

            for req in requisitions:
                if isinstance(req, dict):
                    req = req.get("requisition", req)
                if not isinstance(req, dict):
                    continue
                normalized = self._normalize(req)
                if normalized and self._keep(normalized["title"]):
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
                page.wait_for_selector("#JobTableBody tr, a.titlelink", timeout=20000)

                rows = page.query_selector_all("#JobTableBody tr")
                for row in rows:
                    link = row.query_selector("td.jobTitle a, a.titlelink")
                    if not link:
                        continue
                    title = (link.inner_text() or "").strip()
                    href = link.get_attribute("href") or ""
                    if not title or not href or not self._keep(title):
                        continue
                    external_url = href if href.startswith("http") else f"{self.origin}{href}"
                    req_id = ""
                    for part in urlparse(external_url).query.split("&"):
                        if part.startswith("job="):
                            req_id = part.split("=", 1)[1]
                    postings.append(
                        {
                            "district_id": self.district_id,
                            "district_name": self.district_name,
                            "title": title,
                            "external_id": req_id or external_url,
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
            postings = self._fetch_via_json()
            if postings:
                return postings
            print("  [cps] JSON returned no rows; trying Playwright fallback")
        except (httpx.HTTPError, ValueError) as exc:
            print(f"  [cps] JSON endpoint failed ({exc}); trying Playwright fallback")

        return self._fetch_via_playwright()
