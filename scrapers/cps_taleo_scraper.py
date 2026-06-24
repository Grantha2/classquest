"""Scraper for Chicago Public Schools (Oracle Taleo portal).

Taleo is JS-rendered, but it is backed by a JSON REST endpoint that returns
the full job board without a login. We try that first (fast, clean) and fall
back to Playwright headless rendering only if the REST call fails.

CPS has 1,200+ postings, so we filter aggressively by ``target_keywords``
(see district_config.py) to keep only elementary-level certified roles.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from base_scraper import BaseScraper, DEFAULT_HEADERS

REST_PATH = "/careersection/rest/jobboard/job/list"
PAGE_SIZE_GUESS = 25
MAX_PAGES = 60  # safety cap (~1,500 postings)


class CPSTaleoScraper(BaseScraper):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.portal_url: str = config["portal_url"]
        self.target_keywords: list[str] = config.get("target_keywords", [])
        parsed = urlparse(self.portal_url)
        self.origin = f"{parsed.scheme}://{parsed.netloc}"

    # -- filtering ------------------------------------------------------

    def _matches(self, title: str) -> bool:
        if not self.target_keywords:
            return True
        lowered = title.lower()
        return any(kw.lower() in lowered for kw in self.target_keywords)

    # -- normalization --------------------------------------------------

    def _job_url(self, job_id: str) -> str:
        return (
            f"{self.origin}/careersection/3/jobdetail.ftl"
            f"?job={job_id}&lang=en"
        )

    @staticmethod
    def _read_columns(req: dict[str, Any]) -> dict[str, str]:
        """Taleo returns each requisition's fields as a `column` list of
        {columnName, value/noLink}. Flatten into a name->value dict."""
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
            cols.get("TITLE")
            or req.get("descriptor")
            or req.get("title")
            or ""
        ).strip()
        if not title:
            return None

        job_id = str(
            req.get("jobId")
            or req.get("contestNo")
            or cols.get("CONTESTNUMBER")
            or ""
        ).strip()
        if not job_id:
            return None

        location = (cols.get("LOCATION") or req.get("location") or "").strip() or None
        category = (
            cols.get("JOBFIELD")
            or cols.get("CATEGORY")
            or req.get("jobField")
            or "Certified Teaching"
        )
        posting_date = (
            cols.get("POSTINGDATE") or req.get("postingDate") or None
        )

        return {
            "district_id": self.district_id,
            "district_name": self.district_name,
            "title": title,
            "external_id": job_id,
            "external_url": req.get("jobUrl") or self._job_url(job_id),
            "category": category,
            "location": location,
            "description": None,
            "posting_date": posting_date,
            "closing_date": None,
        }

    # -- REST strategy --------------------------------------------------

    def _fetch_via_rest(self) -> list[dict[str, Any]]:
        url = f"{self.origin}{REST_PATH}"
        headers = {
            **DEFAULT_HEADERS,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        postings: list[dict[str, Any]] = []

        for page_no in range(1, MAX_PAGES + 1):
            body = {
                "multilineEnabled": False,
                "ignoreLimitError": True,
                "language": "en",
                "pageNo": page_no,
            }
            resp = self._client.post(url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            requisitions = (
                data.get("requisitionList")
                or data.get("requisitions")
                or []
            )
            if not requisitions:
                break

            for req in requisitions:
                # Some payloads nest the requisition under a key.
                req = req.get("requisition", req) if isinstance(req, dict) else req
                if not isinstance(req, dict):
                    continue
                normalized = self._normalize(req)
                if normalized and self._matches(normalized["title"]):
                    postings.append(normalized)

            self.polite_sleep()
            if len(requisitions) < PAGE_SIZE_GUESS:
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
                page.wait_for_selector("a.titlelink, .article a", timeout=20000)

                rows = page.query_selector_all("a.titlelink, .article a")
                for row in rows:
                    title = (row.inner_text() or "").strip()
                    href = row.get_attribute("href") or ""
                    if not title or not href:
                        continue
                    external_url = href if href.startswith("http") else f"{self.origin}{href}"
                    # external_id from the job query param when present
                    qs = urlparse(external_url).query
                    job_id = ""
                    for part in qs.split("&"):
                        if part.startswith("job="):
                            job_id = part.split("=", 1)[1]
                    if not self._matches(title):
                        continue
                    postings.append(
                        {
                            "district_id": self.district_id,
                            "district_name": self.district_name,
                            "title": title,
                            "external_id": job_id or external_url,
                            "external_url": external_url,
                            "category": "Certified Teaching",
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
            postings = self._fetch_via_rest()
            if postings:
                return postings
            print("  [cps] REST returned no rows; trying Playwright fallback")
        except (httpx.HTTPError, ValueError) as exc:
            print(f"  [cps] REST endpoint failed ({exc}); trying Playwright fallback")

        return self._fetch_via_playwright()
