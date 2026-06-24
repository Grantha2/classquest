"""Abstract base class shared by all ClassQuest district scrapers."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

# Polite, descriptive User-Agent on every request (per scraping ethics notes).
USER_AGENT = "ClassQuest/1.0 (personal-use educator job aggregator)"

# Be a polite scraper — minimum delay between requests to the same portal.
REQUEST_DELAY_SECONDS = 1.0

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class BaseScraper(ABC):
    """Common HTTP plumbing + the interface every scraper implements."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.district_id: str = config["district_id"]
        self.district_name: str = config["name"]
        self._client = httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=20.0,
            follow_redirects=True,
        )

    # -- shared helpers -------------------------------------------------

    def get(self, url: str) -> httpx.Response:
        """GET with the shared client, then sleep to stay polite."""
        response = self._client.get(url)
        response.raise_for_status()
        self.polite_sleep()
        return response

    @staticmethod
    def polite_sleep() -> None:
        time.sleep(REQUEST_DELAY_SECONDS)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BaseScraper":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- interface ------------------------------------------------------

    @abstractmethod
    def fetch_all_postings(self) -> list[dict[str, Any]]:
        """Return a list of normalized posting dicts.

        Each dict should contain at least:
            district_id, district_name, title, external_url, external_id,
            category, location, description, posting_date, closing_date
        """
        raise NotImplementedError
