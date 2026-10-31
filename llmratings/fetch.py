"""Acquisition seam. fetch_all returns {source: raw payload} plus
`_provenance`: acquisition mode, actual UTC fetch time, source URLs, available
source dates and fixture snapshot/synthetic evidence. Original rows stay intact.
Nothing below this boundary touches the network or fixture files.

Ticket 11: fixture backend — saved source payloads served instead of HTTP.
Ticket 15: fetch_all(None) replaces that with live HTTP for all three sources
(DeepSWE static JSON; Artificial Analysis paginated API with x-api-key;
Terminal-Bench GitHub contents listing plus one raw JSON per submission).
Ticket 18: OpenRouter `GET /api/v1/models` joins as best-effort enrichment
(context_length/modalities for the detail view) — a failure yields "or": None
and the run proceeds. Fixture mode is unchanged and stays the offline test
seam; live mode is exercised offline against a local origin via the
LLM_RATINGS_HTTP_BASE override (test seam only — it swaps the origin of every
live URL).

Fixture metadata comes from optional provenance.json, not file modification
times. Fictional model names and synthetic sources are separate explicit flags;
an offline file alone establishes neither. A fixture read today is not a new
measurement. Source URLs exclude credentials, headers and non-pagination query
parameters. Paginated source dates belong to their individual page URLs.
"""

import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

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
_OR = "/api/v1/models"
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


def source_url(value):
    """An auditable HTTP URL without user info, secrets or request headers."""
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            return None
        query = urlencode([(key, val) for key, val in parse_qsl(parts.query)
                           if key in ("page", "page_size")])
        return urlunsplit((parts.scheme, parts.netloc.rsplit("@", 1)[-1],
                           parts.path, query, ""))
    except ValueError:
        return None


def _source_dates(doc):
    """Keep published date labels; none is relabelled as a measurement date."""
    if not isinstance(doc, dict):
        return {}
    dates = {key: doc[key] for key in ("generated_at", "updated_at", "date", "snapshot_date")
             if isinstance(doc.get(key), str)}
    job = doc.get("latest_job")
    if isinstance(job, dict) and isinstance(job.get("finished_at"), str):
        dates["latest_job.finished_at"] = job["finished_at"]
    return dates


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
        raise SourceError(source, f"GET {source_url(url)} failed: {e}") from e


def _live_deepswe(base):
    return _get("deepswe", base + _DEEPSWE)


def _live_aa(base, api_key, provenance):
    """Paginated free-tier API (page_size capped at 200): fetch pages until
    one returns fewer than page_size rows (~3 pages at the current model
    count), then merge into one payload with every page's rows."""
    url = f"{base}{_AA}"
    rows, page = [], 1
    provenance["urls"] = []
    provenance["pages"] = []
    while True:
        page_url = f"{url}?page_size={_AA_PAGE_SIZE}&page={page}"
        doc = _get("aa", page_url, {"x-api-key": api_key})
        if not isinstance(doc, dict):
            raise SourceError("aa",
                              f"GET {url} page {page} returned a non-object payload")
        batch = doc.get("data")
        if not isinstance(batch, list):
            raise SourceError("aa", f"GET {url} page {page} has no data list")
        provenance["urls"].append(source_url(page_url))
        provenance["pages"].append({
            "url": source_url(page_url), "start": len(rows), "stop": len(rows) + len(batch),
            "intelligence_index_version": doc.get("intelligence_index_version"),
            "source_dates": _source_dates(doc)})
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
        if not isinstance(name, str):
            raise SourceError("tb", "listing entry has no string name")
        if not _TB_FILE.match(name):
            continue
        raw_url = entry.get("download_url")
        if not isinstance(raw_url, str) or not source_url(raw_url):
            raise SourceError("tb", f"listing entry has no download_url: {name!r}")
        submissions[name] = _get("tb", raw_url)
    return {"listing": listing, "submissions": submissions}


# Default origins per source (spec §2). The LLM_RATINGS_HTTP_BASE override
# swaps all of them for a single test origin.
_ORIGINS = {"deepswe": "https://deepswe.datacurve.ai",
            "aa": "https://artificialanalysis.ai",
            "tb": "https://api.github.com",
            "or": "https://openrouter.ai"}


def _origin(source):
    return os.environ.get("LLM_RATINGS_HTTP_BASE") or _ORIGINS[source]


def _live_or(base):
    """OpenRouter model catalog — best-effort enrichment (ticket 18): any
    failure returns None and the run proceeds without the context field.
    It deliberately does NOT raise SourceError — the hard-fail contract
    covers the three rating sources only."""
    try:
        return _get_json(base + _OR)
    except (OSError, ValueError):
        return None


def _fetch_live(provenance):
    """Fetch all ratings or fail before advice. Catalog enrichment is optional."""
    api_key = os.environ.get("LLM_RATINGS_AA_API_KEY", "")
    if not api_key:
        # Keep the seam honest for direct fetch_all(None) consumers too.
        raise SourceError("aa", "LLM_RATINGS_AA_API_KEY is not set")
    return {"deepswe": _live_deepswe(_origin("deepswe")),
            "aa": _live_aa(_origin("aa"), api_key, provenance["aa"]),
            "tb": _live_tb(_origin("tb")),
            "or": _live_or(_origin("or"))}


def fetch_all(fixtures_dir):
    """Acquire raw sources and `_provenance` through the sole live/fixture seam.

    Missing/unreadable rating sources fail by name; OpenRouter is best effort.
    A fixture's optional provenance.json supplies historical snapshot dates,
    fictional_model_names and per-source synthetic flags. Unknown dates stay
    unknown, never inferred from run time.
    """
    mode = "fixture" if fixtures_dir is not None else "live"
    origins = _ORIGINS if fixtures_dir is not None else {
        source: _origin(source) for source in (*FILES, "or")}
    paths = {"deepswe": _DEEPSWE, "aa": f"{_AA}?page_size={_AA_PAGE_SIZE}",
             "tb": _TB_LISTING, "or": _OR}
    sources = {source: {"urls": [source_url(origins[source] + path)],
                        "snapshot_date": None, "synthetic": None}
               for source, path in paths.items()}
    provenance = {"mode": mode, "fetched_at": datetime.now(timezone.utc).isoformat(),
                  "sources": sources}
    if fixtures_dir is None:
        out = _fetch_live(sources)
    else:
        d = Path(fixtures_dir)
        out = {}
        for source, fname in FILES.items():
            p = d / fname
            if not p.is_file():
                raise SourceError(source, f"fixture file not found: {p}")
            try:
                out[source] = json.loads(p.read_text())
            except (OSError, ValueError) as e:
                raise SourceError(source, f"cannot read fixture {p}: {e}") from e
        # Catalog and fixture history are optional, not rating-source failures.
        out["or"] = None
        for filename in ("or.json", "provenance.json"):
            try:
                doc = json.loads((d / filename).read_text())
            except (OSError, ValueError):
                continue
            if filename == "or.json":
                out["or"] = doc
            elif isinstance(doc, dict):
                if isinstance(doc.get("fictional_model_names"), bool):
                    provenance["fictional_model_names"] = doc["fictional_model_names"]
                if not isinstance(doc.get("sources"), dict):
                    continue
                for source, evidence in doc["sources"].items():
                    if source not in sources or not isinstance(evidence, dict):
                        continue
                    if isinstance(evidence.get("snapshot_date"), str):
                        sources[source]["snapshot_date"] = evidence["snapshot_date"]
                    if isinstance(evidence.get("synthetic"), bool):
                        sources[source]["synthetic"] = evidence["synthetic"]
    for source in sources:
        if not sources[source].get("pages"):
            sources[source]["source_dates"] = _source_dates(out.get(source))
    tb = out.get("tb")
    listing = tb.get("listing") if isinstance(tb, dict) else None
    for entry in listing if isinstance(listing, list) else []:
        url = source_url(entry.get("download_url")) if isinstance(entry, dict) else None
        if url and url not in sources["tb"]["urls"]:
            sources["tb"]["urls"].append(url)
    out["_provenance"] = provenance
    return out
