"""Read-only coverage audit — answers "are we capturing 100% of relevant postings?"

For each portal it reports: reachable? · raw postings the feed returned · how many
we keep · and a breakdown of WHY the rest were dropped (by filter rule). Run it on
demand to catch silent over-filtering or an unreachable/broken portal. Writes
nothing to the DB.

Usage:
    python scrapers/audit.py                 # all portals
    python scrapers/audit.py dupage cps d34  # specific ones
"""

from __future__ import annotations

import re
import sys
from collections import Counter

from bs4 import BeautifulSoup

from applitrack_scraper import ApplitrackScraper, _deescape
from cps_taleo_scraper import CPSTaleoScraper
from district_config import DISTRICTS
from title_filter import classify_title

_TITLE_JOBID = re.compile(r"\s*JobID:\s*\d+\s*$")


def _raw_applitrack_titles(scraper: ApplitrackScraper) -> list[str]:
    titles: list[str] = []
    for category in (scraper.target_categories or [None]):
        js = scraper._fetch_output(category)
        if not js:
            continue
        soup = BeautifulSoup(_deescape(js), "html.parser")
        for ul in soup.find_all("ul", class_="postingsList"):
            el = ul.select_one("table.title") or ul.find("td")
            if el:
                t = _TITLE_JOBID.sub("", el.get_text(" ", strip=True)).strip()
                if t:
                    titles.append(t)
    return titles


def audit_one(cfg: dict) -> dict:
    if cfg["platform"] == "taleo":
        s = CPSTaleoScraper(cfg)
        kept = len(s.fetch_all_postings())  # CPS filters inline
        out = {"reachable": s.reachable, "raw": None, "kept": kept, "reasons": Counter()}
        s.close()
        return out

    s = ApplitrackScraper(cfg)
    titles = _raw_applitrack_titles(s)
    out = {"reachable": s.reachable, "raw": len(titles), "kept": 0, "reasons": Counter()}
    s.close()
    fe, rtw = cfg.get("from_elementary_category", True), cfg.get("require_teaching_keyword", False)
    for t in titles:
        keep, reason = classify_title(t, fe, rtw)
        if keep:
            out["kept"] += 1
        else:
            out["reasons"][reason] += 1
    return out


def main() -> None:
    selected = set(sys.argv[1:])
    districts = [d for d in DISTRICTS if not selected or d["district_id"] in selected]

    total_raw = total_kept = 0
    unreachable: list[str] = []
    all_reasons: Counter = Counter()

    print(f"{'district':16} {'reach':6} {'raw':>5} {'kept':>5}  top drop reasons")
    print("-" * 80)
    for cfg in districts:
        did = cfg["district_id"]
        try:
            r = audit_one(cfg)
        except Exception as exc:  # noqa: BLE001
            print(f"{did:16} {'ERROR':6}  {exc}")
            continue
        if not r["reachable"]:
            unreachable.append(did)
        if r["raw"]:
            total_raw += r["raw"]
        total_kept += r["kept"]
        all_reasons.update(r["reasons"])
        top = ", ".join(f"{k}×{v}" for k, v in r["reasons"].most_common(3))
        raw_s = "-" if r["raw"] is None else str(r["raw"])
        print(f"{did:16} {('OK' if r['reachable'] else 'UNREACH'):6} {raw_s:>5} {r['kept']:>5}  {top}")

    print("-" * 80)
    print(f"TOTAL  raw(applitrack)={total_raw}  kept={total_kept}")
    print(f"UNREACHABLE: {unreachable or 'none'}")
    print("\nTop drop reasons across all portals:")
    for reason, n in all_reasons.most_common(12):
        print(f"  {n:4}  {reason}")


if __name__ == "__main__":
    main()
