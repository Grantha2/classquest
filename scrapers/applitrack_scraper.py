"""Scraper for Frontline / Applitrack district portals.

Covers 13 of the 14 districts. Each district carries its own exact
``target_categories`` and a ``from_elementary_category`` flag — see
district_config.py. Category labels differ per portal and an exact-string miss
returns 0 silently.

How the portal actually works (verified live against cusd200):
  * The public ``view.asp`` / ``default.aspx`` pages are thin JS shells.
  * The real job list is served by ``Output.asp``, which returns JavaScript
    that ``document.write``s the postings HTML. We fetch it directly (PRIMARY).
  * ``Output.asp?Category=<cat>`` filters server-side to that category.
  * Each posting is a ``<ul class='postingsList' id='p<JOBID>_'>`` whose
    ``<table class='title'>`` holds the title and ``<p>`` tags the description.
  * FALLBACK: if Output.asp yields 0 for a district, parse the static
    ``default.aspx?Category=<cat>&all=1`` page (anchors carrying AppliTrackJobId).

Every title is run through ``title_filter.is_relevant_title`` before it is
returned, so non-teaching / out-of-grade postings never reach the DB or scorer.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from base_scraper import BaseScraper
from title_filter import is_relevant_title

# Frontline data hosts that serve Output.asp / default.aspx (tried in order).
FRONTLINE_HOSTS = [
    "https://www.applitrack.com",
    "https://www.generalasp.com",
]

_POSTING_ID_RE = re.compile(r"^p(\d+)")
_JOBID_QS_RE = re.compile(r"AppliTrackJobId=(\d+)")
# Consortium postings carry the real member district: "...District: <Name> Additional Information..."
_DISTRICT_FIELD_RE = re.compile(
    r"\bDistrict:\s*(.+?)\s+(?:Additional Information|Date |Closing|Position Type|$)",
    re.IGNORECASE,
)
_DATE_RE = re.compile(r"Date Posted:\s*([0-1]?\d/[0-3]?\d/\d{4})")
_LOCATION_RE = re.compile(
    r"Location:\s*(.+?)\s*(?:Additional Information|Show/Hide|Date Available"
    r"|Date Posted|Position Type|Attachment|SUMMARY|Closing|Email To|Print|Apply|$)",
    re.IGNORECASE,
)
# Output.asp builds postings by concatenating document.write('...') calls. A
# single posting can span a boundary, e.g.  ...title>'); document.write('Bilingual...
# Stitch those boundaries back together before parsing so titles aren't polluted.
_DOCWRITE_GLUE = re.compile(
    r"""['"]\s*\)\s*;?\s*document\.write(?:ln)?\s*\(\s*['"]"""
)


def _deescape(js_text: str) -> str:
    """Stitch document.write boundaries, then decode JS string escapes (\\' \\" \\/)."""
    stitched = _DOCWRITE_GLUE.sub("", js_text)
    return stitched.replace("\\/", "/").replace("\\'", "'").replace('\\"', '"')


def _date_to_iso(mmddyyyy: str) -> str | None:
    try:
        mo, d, y = mmddyyyy.split("/")
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    except (ValueError, TypeError):
        return None


def _extract_fields(block_text: str) -> dict[str, Any]:
    """Pull Location / Date Posted out of a posting block's text."""
    out: dict[str, Any] = {"location": None, "posting_date": None}
    dm = _DATE_RE.search(block_text)
    if dm:
        out["posting_date"] = _date_to_iso(dm.group(1))
    lm = _LOCATION_RE.search(block_text)
    if lm:
        loc = lm.group(1).strip(" -| ")
        out["location"] = loc[:120] or None
    return out


class ApplitrackScraper(BaseScraper):
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.slug: str = config["slug"]
        self.base_url: str = config.get("base_url", "https://www.applitrack.com")
        self.target_categories: list[str] = config.get("target_categories", [])
        self.from_elementary_category: bool = config.get(
            "from_elementary_category", True
        )
        # Consortium portals list every job type under one slug; require an
        # explicit teaching role in the title to filter out support staff.
        self.require_teaching_word: bool = config.get(
            "require_teaching_keyword", False
        )
        # Regional ROE consortiums aggregate many member districts. We parse the
        # real district onto each posting, and skip district numbers we already
        # cover via individual configs (avoids duplicates).
        self.is_consortium: bool = config.get("is_consortium", False)
        self.skip_district_numbers: set[str] = set(
            str(n) for n in config.get("skip_district_numbers", [])
        )

    # -- URL construction ----------------------------------------------

    def _hosts(self) -> list[str]:
        hosts = [self.base_url.rstrip("/")]
        for h in FRONTLINE_HOSTS:
            if h not in hosts:
                hosts.append(h)
        return hosts

    def output_url(self, host: str, category: str | None) -> str:
        url = f"{host}/{self.slug}/OnlineApp/JobPostings/Output.asp"
        if category:
            return f"{url}?Category={quote_plus(category)}"
        return f"{url}?category=all"

    def default_aspx_url(self, host: str, category: str) -> str:
        return (
            f"{host}/{self.slug}/onlineapp/default.aspx"
            f"?Category={quote_plus(category)}&all=1"
        )

    def posting_url(self, external_id: str) -> str:
        """Public, browser-renderable URL for a single posting.

        Minimal form only — the &AppliTrackLayoutMode=detail&AppliTrackViewPosting=1
        suffix breaks consortium portals (they return "no openings")."""
        return (
            f"{self.base_url.rstrip('/')}/{self.slug}/onlineapp/jobpostings/"
            f"view.asp?AppliTrackJobId={external_id}"
        )

    # -- fetching -------------------------------------------------------

    def _fetch_output(self, category: str | None) -> str | None:
        last_exc: Exception | None = None
        for host in self._hosts():
            try:
                resp = self.get(self.output_url(host, category))
                if "postingsList" in resp.text or "AppliTrackOutput" in resp.text:
                    self.reachable = True
                    return resp.text
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
        if last_exc:
            print(f"  [warn] Output.asp fetch failed {self.district_id}/{category}: {last_exc}")
        return None

    def _fetch_default_aspx(self, category: str) -> str | None:
        for host in self._hosts():
            try:
                resp = self.get(self.default_aspx_url(host, category))
                if "AppliTrackJobId" in resp.text:
                    self.reachable = True
                    return resp.text
            except Exception:  # noqa: BLE001
                continue
        return None

    # -- parsing --------------------------------------------------------

    def _keep(self, title: str) -> bool:
        return is_relevant_title(
            title, self.from_elementary_category, self.require_teaching_word
        )

    def parse_output(self, js_text: str, category: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(_deescape(js_text), "html.parser")
        postings: list[dict[str, Any]] = []

        for ul in soup.find_all("ul", class_="postingsList"):
            m = _POSTING_ID_RE.match(ul.get("id") or "")
            if not m:
                continue
            external_id = m.group(1)

            block_text = ul.get_text(" ", strip=True)
            title_el = ul.select_one("table.title")
            raw_title = (
                title_el.get_text(" ", strip=True)
                if title_el
                else (ul.find("td").get_text(" ", strip=True) if ul.find("td") else "")
            )
            # The title cell carries a trailing "JobID: 9995" — drop it.
            title = re.sub(r"\s*JobID:\s*\d+\s*$", "", raw_title).strip()
            if not title or not self._keep(title):
                continue

            # Consortium feeds: resolve the real member district and skip any
            # district we already cover via an individual config (dedup).
            district_name = self.district_name
            if self.is_consortium:
                dm = _DISTRICT_FIELD_RE.search(block_text)
                if dm:
                    district_name = dm.group(1).strip()
                    nums = re.findall(r"\d+", district_name)
                    if nums and nums[-1] in self.skip_district_numbers:
                        continue

            paras = ul.find_all("p")
            description = " ".join(p.get_text(" ", strip=True) for p in paras).strip()
            if not description:
                if title_el:
                    title_el.extract()
                text = ul.get_text(" ", strip=True)
                for junk in ("Email To A Friend", "Print Version", "Apply", "Tell A Friend", "Share"):
                    text = text.replace(junk, " ")
                description = re.sub(r"\s+", " ", text).strip() or None

            fields = _extract_fields(block_text)
            postings.append(
                {
                    "district_id": self.district_id,
                    "district_name": district_name,
                    "title": title,
                    "external_id": external_id,
                    "external_url": self.posting_url(external_id),
                    "category": category,
                    "location": fields["location"],
                    "description": description or None,
                    "posting_date": fields["posting_date"],
                    "closing_date": None,
                }
            )
        return postings

    def parse_default_aspx(self, html: str, category: str) -> list[dict[str, Any]]:
        """Best-effort static fallback: anchors carrying AppliTrackJobId."""
        soup = BeautifulSoup(html, "html.parser")
        by_id: dict[str, dict[str, Any]] = {}

        for a in soup.select("a[href*='AppliTrackJobId']"):
            m = _JOBID_QS_RE.search(a.get("href", ""))
            if not m:
                continue
            external_id = m.group(1)
            title = re.sub(
                r"\s*JobID:\s*\d+\s*$", "", a.get_text(" ", strip=True)
            ).strip()
            if not title or not self._keep(title):
                continue
            by_id.setdefault(
                external_id,
                {
                    "district_id": self.district_id,
                    "district_name": self.district_name,
                    "title": title,
                    "external_id": external_id,
                    "external_url": self.posting_url(external_id),
                    "category": category,
                    "location": None,
                    "description": None,
                    "posting_date": None,
                    "closing_date": None,
                },
            )
        return list(by_id.values())

    # -- orchestration --------------------------------------------------

    def fetch_all_postings(self) -> list[dict[str, Any]]:
        # Dedupe across categories by external_id (first category wins).
        by_id: dict[str, dict[str, Any]] = {}

        # No target_categories => fetch the all-categories view (consortiums).
        categories = self.target_categories or [None]

        for category in categories:
            label = category or "Teaching"
            found: list[dict[str, Any]] = []
            js_text = self._fetch_output(category)  # None -> ?category=all
            if js_text:
                found = self.parse_output(js_text, label)
            if not found and category is not None:
                # Output.asp had nothing for this category — try the static page.
                html = self._fetch_default_aspx(category)
                if html:
                    found = self.parse_default_aspx(html, label)

            for posting in found:
                by_id.setdefault(posting["external_id"], posting)

        return list(by_id.values())
