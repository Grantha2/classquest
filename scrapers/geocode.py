"""Google Geocoding helper for the scraper.

Resolves a free-text location (a school name + town, or a full address) to
lat/lng. Returns:
  * {"lat": float, "lng": float, "formatted_address": str} on success
  * {"failed": True} on a definitive no-result (ZERO_RESULTS) — don't retry
  * None on a transient error (network / rate limit / missing key) — retry later
"""

from __future__ import annotations

import os
from typing import Any

import httpx

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode(query: str, api_key: str | None = None) -> dict[str, Any] | None:
    api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key or not query:
        return None
    try:
        resp = httpx.get(
            GOOGLE_GEOCODE_URL,
            params={"address": query, "key": api_key, "region": "us"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        print(f"  [geocode] error for {query!r}: {exc}")
        return None

    status = data.get("status")
    if status == "OK" and data.get("results"):
        result = data["results"][0]
        loc = result["geometry"]["location"]
        return {
            "lat": loc["lat"],
            "lng": loc["lng"],
            "formatted_address": result.get("formatted_address"),
        }
    if status == "ZERO_RESULTS":
        return {"failed": True}
    # OVER_QUERY_LIMIT / REQUEST_DENIED / INVALID_REQUEST -> transient, retry later.
    print(f"  [geocode] status={status} for {query!r}")
    return None
