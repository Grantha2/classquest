"""Scraper for Frontline / Applitrack district portals.

Covers 13 of the 14 districts. Only the slug (and occasionally base_url)
changes between districts — see district_config.py.

Strategy (per the ClassQuest spec):
  * Fetch each target_category separately via the category-filtered URL.
  * The ?embed=1 variant returns clean static HTML (no nav chrome).
  * Job links contain ``AppliTrackJobId`` in the href.
  * external_id is the ``AppliTrackJobId`` query param.
  * Be polite: 1s between requests (handled by BaseScraper.get).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from base_scraper import BaseScraper


class ApplitrackScraper(BaseScraper):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.slug: str = config["slug"]
        self.base_url: str = config.get("base_url", "https://www.applitrack.com")
        self.target_categories: list[str] = config.get("target_categories", [])

    # -- URL construction ----------------------------------------------

    def get_postings_url(self, category: str | None = None) -> str:
        """Category-filtered listing URL. ?embed=1 -> clean static HTML."""
        if category:
            cat = category.replace(" ", "+")
            return (
                f"{self.base_url}/{self.slug}/OnlineApp/default.aspx"
                f"?Category={cat}&embed=1"
            )
        # Fallback: all postings, clean embed view.
        return (
            f"{self.base_url}/{self.slug}/OnlineApp/JobPostings/view.asp"
            f"?embed=1&all=1"
        )

    # -- listing parsing -----------------------------------------------

    def parse_listing_page(
        self, html: str, category: str, page_url: str
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        postings: list[dict[str, Any]] = []

        for link in soup.select("a[href*='AppliTrackJobId']"):
            href = link.get("href")
            if not href:
                continue
            external_url = urljoin(page_url, href)
            qs = parse_qs(urlparse(external_url).query)
            external_id = (qs.get("AppliTrackJobId") or [None])[0]
            title = link.get_text(strip=True)
            if not external_id or not title:
                continue

            postings.append(
                {
                    "district_id": self.district_id,
                    "district_name": self.district_name,
                    "title": title,
                    "external_id": external_id,
                    "external_url": external_url,
                    "category": category,
                    "location": None,
                    "description": None,
                    "posting_date": None,
                    "closing_date": None,
                }
            )
        return postings

    # -- detail parsing -------------------------------------------------

    def fetch_posting_detail(self, url: str) -> str:
        """Return the job description text from an individual posting page."""
        try:
            resp = self.get(url)
        except Exception as exc:  # noqa: BLE001 - log and degrade gracefully
            print(f"  [warn] detail fetch failed {url}: {exc}")
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")

        node = soup.select_one("#jobPostingDescription, .jobPostingDescription")
        if node:
            return node.get_text(" ", strip=True)

        # Fallback: the largest <div> by text length is almost always the body.
        divs = soup.find_all("div")
        if divs:
            largest = max(divs, key=lambda d: len(d.get_text(strip=True)))
            return largest.get_text(" ", strip=True)
        return ""

    # -- orchestration --------------------------------------------------

    def fetch_all_postings(self) -> list[dict[str, Any]]:
        # Dedupe across categories by external_id (first category wins).
        by_id: dict[str, dict[str, Any]] = {}

        for category in self.target_categories:
            url = self.get_postings_url(category)
            try:
                resp = self.get(url)
            except Exception as exc:  # noqa: BLE001
                print(
                    f"  [warn] listing fetch failed "
                    f"{self.district_id}/{category}: {exc}"
                )
                continue

            for posting in self.parse_listing_page(resp.text, category, url):
                by_id.setdefault(posting["external_id"], posting)

        # Enrich with descriptions from each detail page.
        for posting in by_id.values():
            posting["description"] = self.fetch_posting_detail(
                posting["external_url"]
            )

        return list(by_id.values())
