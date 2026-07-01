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

# A 32-portal sweep is prone to transient timeouts; retry those a couple times.
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 2  # in addition to the initial attempt

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
        # Set True once any feed responds this run; lets run_all tell a genuinely
        # empty portal apart from an unreachable one (so we never silently miss it).
        self.reachable: bool = False
        self._client = httpx.Client(
            headers=DEFAULT_HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )

    # -- shared helpers -------------------------------------------------

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """HTTP request with retries on transient timeouts/transport errors.
        4xx/5xx (raise_for_status) are NOT retried — a 404 is a permanent miss."""
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    time.sleep(1.0 * (attempt + 1))
        assert last_exc is not None
        raise last_exc

    def get(self, url: str) -> httpx.Response:
        """GET with retries, then sleep to stay polite."""
        response = self.request("GET", url)
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
            category, location, description, posting_date, closing_date,
            employment_type
        """
        raise NotImplementedError
