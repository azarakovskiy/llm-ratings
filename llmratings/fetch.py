"""Acquisition seam. Ticket 11: fixture backend only — saved source payloads
served instead of HTTP. Ticket 15 replaces the body of fetch_all with live
fetches; the contract below is the seam: fetch_all returns {source: raw
payload dict}, and anything below that (identity join, tiering, ranking,
rendering) never touches the network or the fixture files."""

import json
from pathlib import Path

# Display names for error messages — "naming the source" per the failure contract.
SOURCES = {"deepswe": "DeepSWE", "aa": "Artificial Analysis"}

# Fixture file per source; Terminal-Bench joins in ticket 13.
FILES = {"deepswe": "deepswe.json", "aa": "aa.json"}


class SourceError(Exception):
    """A source could not be read. `.source` is the SOURCES key."""

    def __init__(self, source, detail):
        self.source = source
        super().__init__(f"{SOURCES[source]}: {detail}")


def fetch_all(fixtures_dir):
    """Read every source's saved payload from fixtures_dir.

    Returns {source: dict} — the raw JSON payloads, verbatim. Any missing or
    unreadable fixture fails with a SourceError naming the source: no silent
    partial tables.
    """
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
