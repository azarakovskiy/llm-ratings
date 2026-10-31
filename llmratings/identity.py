"""Identity join and the normalized row model.

Canonical model = an AA model. Key: the AA base slug — the free API issues a
fresh UUID per reasoning-effort variant (gpt-5-6-luna-low and gpt-5-6-luna
carry different ids), so the variant UUID is not a model key; base slugs are
what the checked-in alias table keys on. Display name = AA name minus the
effort parenthetical; provider = AA model_creator name.

DeepSWE/TB model strings map onto AA base slugs via the alias table. A rated
model with no AA row (or whose alias resolves to nothing in the data) keeps a
source-only identity: key "dsw:<name>", provider "—", no price, no PPI — and
no objective-selected configuration, so it never enters a role table (ticket
18).

Rating rows attach wholesale: `raw` always contains the original source row.
For AA, `score` is Intelligence; `coding_score` and `agentic_score` stay
independent. `cost` is only Intelligence cost_per_task.total_cost, never
suite expenditure or token list prices. `pricing` keeps the four published
USD-per-million input/output/cache figures separately. Every optional numeric
field is finite or None, including malformed nested objects; a published zero
stays zero. No metric is copied between effort variants.

Timing fields retain first-answer seconds (including thinking), first-token
seconds, output tokens/s (`speed`), and the published synthetic response time
for 500 answer tokens. They are not interchangeable or whole-agent durations.
The Free route's exact prompt preset/provider aggregation and complete current
Coding/Agentic formulas are not established; these are not creator-endpoint
performance claims or area-index task costs.

Dataset.provenance carries fetch mode/time, source URLs and available historical
snapshot/source dates. Each Rating adds its source URL and reported AA index
version; TB retains the individual submission URL and recency date. Fixture
mode and synthetic flags must not be presented as current live measurements.

OpenRouter catalog rows supply context/modalities only. Dataset.openrouter_models
maps a supplied canonical_slug through its catalog id and the existing alias/
model join to the AA key. No permaslug is inferred from an id. Original catalog
rows remain on Model.catalog_rows. token_share_30d is explicitly unavailable:
no verified 30-day feed/coverage/denominator/aggregation is implemented, and
isolated rankings, top-50 absence or catalog fields cannot establish a share.
"""

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from .fetch import SourceError, source_url

EFFORTS = ("low", "medium", "high", "xhigh", "max")

# Terminal-Bench v2.1 offers only these efforts (source survey, 2026-08-05);
# rows at any other effort attach wholesale but are never table configs, so
# the TB column is `—` at low/medium (spec §4).
TB_EFFORTS = ("high", "xhigh", "max")


def best_tb(ratings, effort):
    """{model_key: the rating to grade} for TB at effort — agent × model rows
    collapse to the best-scoring agent per (model × effort), ties broken by
    the most recent submission date (spec §3, story 32)."""
    best = {}
    for r in ratings:
        if r.source != "tb" or r.effort != effort or r.score is None:
            continue
        prev = best.get(r.model_key)
        if prev is None or (r.score, r.date or "") > (prev.score, prev.date or ""):
            best[r.model_key] = r
    return best

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
    context_length: int | None = None   # OpenRouter enrichment (ticket 18)
    modalities: str | None = None       # "in: text, image; out: text"
    catalog_rows: list[dict] = field(default_factory=list)
    token_share_30d: float | None = None  # No verified 30-day coverage, never zero


@dataclass
class Rating:
    source: str         # "deepswe" | "aa" | "tb"
    model_key: str
    effort: str | None  # None = source row with no effort setting — never a config
    score: float | None  # AA Intelligence, DeepSWE pass@1, or TB accuracy
    cost: float | None  # Matching AA Intelligence cost_per_task.total_cost only
    speed: float | None  # AA median output tokens/s, AA rows only
    ci_lo: float | None
    ci_hi: float | None
    raw: dict           # original source row — nothing discarded
    agent: str | None = None   # TB submission agent (rows are agent × model)
    date: str | None = None    # TB submission date — the recency tie-break
    coding_score: float | None = None
    agentic_score: float | None = None
    first_answer_seconds: float | None = None  # Includes thinking
    first_token_seconds: float | None = None
    response_500_tokens_seconds: float | None = None  # Published synthetic estimate
    pricing: dict[str, float | None] = field(default_factory=dict)  # USD / 1M tokens
    intelligence_index_version: str | float | None = None
    source_url: str | None = None


@dataclass
class Dataset:
    models: dict[str, Model]
    ratings: list[Rating]
    provenance: dict = field(default_factory=dict)
    openrouter_models: dict[str, str] = field(default_factory=dict)  # permaslug -> AA key


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


def _join(aliases, models, name, prefix):
    """Resolve a source model string to a canonical model key. The alias table
    maps source strings to AA base slugs; an alias with no AA row in the data
    keeps a source-only identity `prefix:<name>` (spec §3)."""
    alias = aliases.get(name)
    if alias and alias in models:
        return alias
    key = prefix + name
    models.setdefault(key, Model(key, name, "—"))
    return key


def _object(value):
    """Optional source objects may be absent, null or malformed."""
    return value if isinstance(value, dict) else {}


def _metric(value):
    """A published finite JSON number, including zero; never coerce strings."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return value if math.isfinite(value) else None
    except OverflowError:
        return None


def build(aliases, raw):
    """Join raw source payloads onto canonical models. Returns a Dataset."""
    models, ratings = {}, []
    provenance = _object(raw.get("_provenance"))
    sources = _object(provenance.get("sources"))
    urls = {}
    for source, evidence in sources.items():
        evidence = _object(evidence)
        candidates = evidence.get("urls")
        if isinstance(candidates, list):
            urls[source] = next((url for value in candidates
                                 if (url := source_url(value))), None)
    pages = _object(sources.get("aa")).get("pages") or []

    aa = raw.get("aa")
    if not isinstance(aa, dict) or not isinstance(aa.get("data"), list):
        raise SourceError("aa", "payload has no data list")
    for index, row in enumerate(aa["data"]):
        if not isinstance(row, dict):
            raise SourceError("aa", "payload row is not an object")
        slug = row.get("slug") or ""
        name = row.get("name") or slug
        if not isinstance(slug, str) or not slug:
            raise SourceError("aa", f"row missing slug: {name!r}")
        if not isinstance(name, str):
            raise SourceError("aa", "row name is not a string")
        effort = parse_aa_effort(name)
        base = aa_base_slug(slug, effort)
        creator = _object(row.get("model_creator"))
        provider = creator.get("name")
        provider = provider if isinstance(provider, str) and provider else "—"
        models.setdefault(base, Model(base, display_name(name), provider))
        ev = _object(row.get("evaluations"))
        perf = _object(row.get("performance"))
        cost = _object(_object(row.get("artificial_analysis_intelligence_index_cost"))
                       .get("cost_per_task")).get("total_cost")
        pricing = _object(row.get("pricing"))
        page = next((p for p in pages if p["start"] <= index < p["stop"]), {})
        ratings.append(Rating(
            "aa", base, effort,  # None = non-reasoning row, attached but never a config
            _metric(ev.get("artificial_analysis_intelligence_index")),
            _metric(cost), _metric(perf.get("median_output_tokens_per_second")),
            None, None, row,
            coding_score=_metric(ev.get("artificial_analysis_coding_index")),
            agentic_score=_metric(ev.get("artificial_analysis_agentic_index")),
            first_answer_seconds=_metric(
                perf.get("median_time_to_first_answer_token_seconds")),
            first_token_seconds=_metric(
                perf.get("median_time_to_first_token_seconds")),
            response_500_tokens_seconds=_metric(
                perf.get("median_end_to_end_response_time_seconds")),
            pricing={key: _metric(pricing.get(key)) for key in (
                "price_1m_input_tokens", "price_1m_output_tokens",
                "price_1m_cache_hit_tokens", "price_1m_cache_write_tokens")},
            intelligence_index_version=page.get(
                "intelligence_index_version", aa.get("intelligence_index_version")),
            source_url=page.get("url", urls.get("aa"))))

    ds = raw.get("deepswe")
    if not isinstance(ds, dict) or not isinstance(ds.get("rows"), list):
        raise SourceError("deepswe", "payload has no rows list")
    for row in ds["rows"]:
        if not isinstance(row, dict):
            raise SourceError("deepswe", "payload row is not an object")
        name = row.get("model")
        if not isinstance(name, str) or not name:
            raise SourceError("deepswe", f"row missing model: {row!r}")
        effort = row.get("reasoning_effort")
        if effort not in EFFORTS:
            effort = None  # e.g. a model with no effort setting — attached, never a config
        key = _join(aliases, models, name, "dsw:")
        ratings.append(Rating(
            "deepswe", key, effort,
            _metric(row.get("pass_at_1")), None, None,
            _metric(row.get("ci_lo")), _metric(row.get("ci_hi")), row,
            source_url=urls.get("deepswe")))

    tb = raw.get("tb")
    if not isinstance(tb, dict) or not isinstance(tb.get("submissions"), dict):
        raise SourceError("tb", "payload has no submissions object")
    listing = tb.get("listing")
    tb_urls = {entry.get("name"): source_url(entry.get("download_url"))
               for entry in (listing if isinstance(listing, list) else [])
               if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    for fname, row in tb["submissions"].items():
        if not isinstance(row, dict):
            raise SourceError("tb", f"submission {fname!r} is not an object")
        sf = _object(row.get("source_filter"))
        name = sf.get("model_name")
        if not isinstance(name, str) or not name:
            raise SourceError("tb", f"submission missing model_name: {fname!r}")
        effort = sf.get("reasoning_effort")
        if effort not in TB_EFFORTS:
            effort = None  # v2.1 covers high/xhigh/max only — attach, never a config
        metrics = _object(row.get("metrics"))
        acc = _metric(metrics.get("accuracy"))
        stderr = _metric(metrics.get("accuracy_stderr"))
        key = _join(aliases, models, name, "tb:")
        date = _object(row.get("metadata")).get("date")
        agent = sf.get("agent")
        ratings.append(Rating(
            "tb", key, effort, acc, None, None,
            _metric(acc - stderr) if acc is not None and stderr is not None else None,
            _metric(acc + stderr) if acc is not None and stderr is not None else None,
            row, agent=agent if isinstance(agent, str) else None,
            date=date if isinstance(date, str) else None,
            source_url=tb_urls.get(fname)))

    # Catalog enrichment is best effort, never a rating, provider or share feed.
    # The actual permaslug -> catalog id -> alias hop remains available to
    # consumers without inventing or authenticating a rankings endpoint.
    openrouter_models = {}
    or_doc = raw.get("or")
    if isinstance(or_doc, dict) and isinstance(or_doc.get("data"), list):
        for row in or_doc["data"]:
            if not isinstance(row, dict):
                continue
            rid = row.get("id")
            if not isinstance(rid, str):
                continue
            key = aliases.get(rid) or rid.split("/", 1)[-1]
            m = models.get(key)
            if m is None:
                continue
            m.catalog_rows.append(row)
            permaslug = row.get("canonical_slug")
            if isinstance(permaslug, str) and permaslug:
                openrouter_models[permaslug] = key
            ctx = row.get("context_length")
            if m.context_length is None and type(ctx) is int and ctx > 0:
                m.context_length = ctx
            arch = row.get("architecture")
            if m.modalities is None and isinstance(arch, dict):
                m.modalities = _modalities(arch)

    return Dataset(models, ratings, provenance, openrouter_models)


def _modalities(arch):
    """"in: text, image; out: text" from OpenRouter's architecture lists."""
    ins = arch.get("input_modalities")
    outs = arch.get("output_modalities")
    ins = [value for value in ins if isinstance(value, str)] if isinstance(ins, list) else []
    outs = [value for value in outs if isinstance(value, str)] if isinstance(outs, list) else []
    parts = []
    if ins:
        parts.append("in: " + ", ".join(ins))
    if outs:
        parts.append("out: " + ", ".join(outs))
    return "; ".join(parts) or None
