"""Acquisition seam. The contract below is the seam: fetch_all returns
{source: raw payload dict}, and anything below that (identity join, tiering,
ranking, rendering) never touches the network or the fixture files.

Ticket 11: fixture backend — saved source payloads served instead of HTTP.
Ticket 15: fetch_all(None) replaces that with live HTTP for all three sources
(DeepSWE static JSON; Artificial Analysis paginated API with x-api-key;
Terminal-Bench GitHub contents listing plus one raw JSON per submission).
Fixture mode is unchanged and stays the offline test seam; live mode is
exercised offline against a local origin via the LLM_RATINGS_HTTP_BASE
override (test seam only — it swaps the origin of every live URL).
"""

import json
import os
import re
import urllib.request
from pathlib import Path

# Display names for error messages — "naming the source" per the failure contract.
SOURCES = {"deepswe": "DeepSWE", "aa": "Artificial Analysis",
           "tb": "Terminal-Bench"}

# Fixture file per source. TB's live fetch is a listing plus one JSON per
# submission; the fixture serves both in one file: {"listing": [...],
# "submissions": {filename: row}}.
FILES = {"deepswe": "deepswe.json", "aa": "aa.json", "tb": "tb.json"}

# Live endpoints (spec §2). The TB listing entries carry the per-entry raw
# URL (download_url) — that is the raw.githubusercontent.com address.
_DEEPSWE = "/artifacts/v1.1/leaderboard-live.json"
_AA = "/api/v2/language/models/free"
_TB_LISTING = "/repos/harbor-framework/terminal-bench-2-1/contents/leaderboard/submissions"
_AA_PAGE_SIZE = 200
_TIMEOUT = 30
# Submission files are named <date>-<org>-<model>-<effort>-<agent>.json; the
# listing also carries non-submission entries (.gitkeep, directories) — only
# .json entries are submissions, skip the rest.
_TB_FILE = re.compile(r".+\.json$")


class SourceError(Exception):
    """A source could not be read. `.source` is the SOURCES key."""

    def __init__(self, source, detail):
        self.source = source
        super().__init__(f"{SOURCES[source]}: {detail}")


def _get_json(url, headers=None):
    """GET url and parse JSON. OSError/ValueError propagate to the caller."""
    h = {"User-Agent": "llm-ratings/0.1.0"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read())


def _get(source, url, headers=None):
    """GET and parse JSON; any failure raises a SourceError naming the source."""
    try:
        return _get_json(url, headers)
    except (OSError, ValueError) as e:
        raise SourceError(source, f"GET {url} failed: {e}") from e


def _live_deepswe(base):
    return _get("deepswe", base + _DEEPSWE)


def _live_aa(base, api_key):
    """Paginated free-tier API (page_size capped at 200): fetch pages until
    one returns fewer than page_size rows (~3 pages at the current model
    count), then merge into one payload with every page's rows."""
    url = f"{base}{_AA}"
    rows, page = [], 1
    while True:
        doc = _get("aa", f"{url}?page_size={_AA_PAGE_SIZE}&page={page}",
                   {"x-api-key": api_key})
        if not isinstance(doc, dict):
            raise SourceError("aa",
                              f"GET {url} page {page} returned a non-object payload")
        batch = doc.get("data")
        if not isinstance(batch, list):
            raise SourceError("aa", f"GET {url} page {page} has no data list")
        rows += batch
        if len(batch) < _AA_PAGE_SIZE:
            break
        page += 1
        if page > 100:
            raise SourceError("aa", "pagination runaway — more than 100 pages")
    doc["data"] = rows
    return doc


def _live_tb(base):
    """GitHub contents listing, then one raw fetch per submission entry.
    Any single submission failure fails the whole source — no partial tables."""
    listing_url = f"{base}{_TB_LISTING}"
    listing = _get("tb", listing_url)
    if not isinstance(listing, list):
        raise SourceError("tb", f"listing is not an array: {listing_url}")
    submissions = {}
    for entry in listing:
        if not isinstance(entry, dict):
            raise SourceError("tb", f"listing entry is not an object: {entry!r}")
        name = entry.get("name")
        if not _TB_FILE.match(name or ""):
            continue
        raw_url = entry.get("download_url")
        if not raw_url:
            raise SourceError("tb", f"listing entry has no download_url: {name!r}")
        submissions[name] = _get("tb", raw_url)
    return {"listing": listing, "submissions": submissions}


# Default origins per source (spec §2). The LLM_RATINGS_HTTP_BASE override
# swaps all three for a single test origin.
_ORIGINS = {"deepswe": "https://deepswe.datacurve.ai",
            "aa": "https://artificialanalysis.ai",
            "tb": "https://api.github.com"}


def _origin(source):
    return os.environ.get("LLM_RATINGS_HTTP_BASE") or _ORIGINS[source]


def _fetch_live():
    """Fetch every source over HTTP. Any single source failure raises a
    SourceError naming it before any output — no silent partial tables."""
    api_key = os.environ.get("LLM_RATINGS_AA_API_KEY", "")
    if not api_key:
        # The CLI checks this before fetching (the ticket-11 setup error);
        # the guard keeps the seam honest for direct fetch_all(None) callers.
        raise SourceError("aa", "LLM_RATINGS_AA_API_KEY is not set")
    return {"deepswe": _live_deepswe(_origin("deepswe")),
            "aa": _live_aa(_origin("aa"), api_key),
            "tb": _live_tb(_origin("tb"))}


def fetch_all(fixtures_dir):
    """Acquire every source's payload.

    fixtures_dir=None → live HTTP (ticket 15); otherwise serve the saved
    payloads from fixtures_dir (the test seam — no network). Either way the
    return is {source: dict}, the raw JSON payloads verbatim. Any failed live
    fetch or missing/unreadable fixture raises a SourceError naming the
    source: no silent partial tables.
    """
    if fixtures_dir is None:
        return _fetch_live()
    d = Path(fixtures_dir)
    out = {}
    for source, fname in FILES.items():
        p = d / fname
        if not p.is_file():
            raise SourceError(source, f"fixture file not found: {p}")
        try:
            out[source] = json.loads(p.read_text())
        except (OSError, json.JSONDecodeError) as e:
            raise SourceError(source, f"cannot read fixture {p}: {e}")
    return out
