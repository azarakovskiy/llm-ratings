"""Identity join and the normalized row model.

Canonical model = an AA model. Key: the AA base slug — the free API issues a
fresh UUID per reasoning-effort variant (gpt-5-6-luna-low and gpt-5-6-luna
carry different ids), so the variant UUID is not a model key; base slugs are
what the checked-in alias table keys on. Display name = AA name minus the
effort parenthetical; provider = AA model_creator name.

DeepSWE/TB model strings map onto AA base slugs via the alias table. A rated
model with no AA row (or whose alias resolves to nothing in the data) keeps a
source-only identity: key "dsw:<name>", provider "—", no price, no PPI.

Rating rows attach wholesale — the original source row is kept on every
Rating; nothing is discarded.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .fetch import SourceError

EFFORTS = ("low", "medium", "high", "xhigh", "max")

# AA effort variants are separate rows; the effort lives in the name's trailing
# parenthetical: "GPT-5.6 Luna (low)", "Claude Opus 5 (Adaptive Reasoning, Low
# Effort)", "DeepSeek V4 Flash 0731 (Reasoning, Max Effort)". "(Non-reasoning,
# High Effort)" is NOT an effort variant.
_EFFORT_TAIL = re.compile(r"(?:.*?,\s*)?(low|medium|high|xhigh|max)(?:\s+effort)?$", re.I)


@dataclass
class Model:
    key: str            # AA base slug, or "dsw:<name>" for source-only models
    name: str
    provider: str


@dataclass
class Rating:
    source: str         # "deepswe" | "aa" ("tb" joins in ticket 13)
    model_key: str
    effort: str | None  # None = source row with no effort setting — never a config
    score: float | None
    cost: float | None  # AA per-task cost, AA rows only — the table price
    speed: float | None  # AA median output tokens/s, AA rows only
    ci_lo: float | None
    ci_hi: float | None
    raw: dict           # original source row — nothing discarded


@dataclass
class Dataset:
    models: dict[str, Model]
    ratings: list[Rating]


def load_aliases(path):
    """Alias table: {source model string: AA base slug}, checked in."""
    return json.loads(Path(path).read_text())


def parse_aa_effort(name):
    """Reasoning effort of an AA row from its display name, or None when the
    row is not an effort variant (non-reasoning, or no parenthetical)."""
    if not name.endswith(")"):
        return None
    tail = name[name.rfind("(") + 1:-1].strip()
    if "non-reasoning" in tail.lower():
        return None
    m = _EFFORT_TAIL.fullmatch(tail)
    return m.group(1).lower() if m else None


def aa_base_slug(slug, effort):
    """Model base slug: variant slug minus its trailing effort suffix."""
    if effort and slug.endswith("-" + effort):
        return slug[:-(len(effort) + 1)]
    return slug


def display_name(name):
    """AA display name minus the trailing parenthetical: 'GPT-5.6 Luna (low)'
    -> 'GPT-5.6 Luna'; 'Claude Opus 5 (Adaptive Reasoning, Max Effort)' ->
    'Claude Opus 5'."""
    if name.endswith(")"):
        name = name[:name.rfind("(")].rstrip()
    return name


def build(aliases, raw):
    """Join raw source payloads onto canonical models. Returns a Dataset."""
    models, ratings = {}, []

    aa = raw.get("aa")
    if not isinstance(aa, dict) or not isinstance(aa.get("data"), list):
        raise SourceError("aa", "payload has no data list")
    for row in aa["data"]:
        if not isinstance(row, dict):
            raise SourceError("aa", "payload row is not an object")
        slug = row.get("slug") or ""
        name = row.get("name") or slug
        if not slug:
            raise SourceError("aa", f"row missing slug: {name!r}")
        effort = parse_aa_effort(name)
        base = aa_base_slug(slug, effort)
        creator = (row.get("model_creator") or {})
        models.setdefault(base, Model(base, display_name(name), creator.get("name") or "—"))
        ev = row.get("evaluations") or {}
        perf = row.get("performance") or {}
        cost = ((row.get("artificial_analysis_intelligence_index_cost") or {})
                .get("cost_per_task") or {}).get("total_cost")
        ratings.append(Rating(
            "aa", base, effort,  # effort None = non-reasoning row: attached wholesale, never a config
            ev.get("artificial_analysis_intelligence_index"),
            cost, perf.get("median_output_tokens_per_second"),
            None, None, row))

    ds = raw.get("deepswe")
    if not isinstance(ds, dict) or not isinstance(ds.get("rows"), list):
        raise SourceError("deepswe", "payload has no rows list")
    for row in ds["rows"]:
        if not isinstance(row, dict):
            raise SourceError("deepswe", "payload row is not an object")
        name = row.get("model")
        if not name:
            raise SourceError("deepswe", f"row missing model: {row!r}")
        effort = row.get("reasoning_effort")
        if effort not in EFFORTS:
            effort = None  # e.g. a model with no effort setting — attached, never a config
        alias = aliases.get(name)
        if alias and alias in models:
            key = alias
        else:
            key = "dsw:" + name  # source-only identity: no AA row in the data
            models.setdefault(key, Model(key, name, "—"))
        ratings.append(Rating(
            "deepswe", key, effort,
            row.get("pass_at_1"), None, None,
            row.get("ci_lo"), row.get("ci_hi"), row))

    return Dataset(models, ratings)
