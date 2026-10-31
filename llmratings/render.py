"""Shared selected-index policy and its batch/session presentation.

One measured configuration per included model, with direct objective order
kept separate from the Intelligence table's frontier-first sections.
"""

import json
import math
from pathlib import Path

from .identity import EFFORTS, best_tb
from .rank import aa_points, alternatives, dominator, frontier_set, pareto
from .tier import grades

OBJECTIVES = ("cap", "ppi", "price")
VIEW_LABEL = {"table": "Model table", "picks": "Provider picks"}
PROVIDER_SHORTCUTS = ("OpenAI", "Anthropic", "Google", "DeepSeek", "xAI")
CAPABILITY_FILTERS = (None, 5, 4)

OBJECTIVE_LABEL = {"cap": "Highest capability", "ppi": "Best value",
                   "price": "Lowest qualifying price"}
INDEX_FIELD = {"intelligence": "score", "coding": "coding_score",
               "agentic": "agentic_score"}
INDEX_LABEL = {"intelligence": "Intelligence", "coding": "Coding",
               "agentic": "Agentic"}
EFFORT_LABEL = dict(zip(EFFORTS, ("Low", "Medium", "High", "Extra high", "Maximum")))
INDEX_NOTE = {
    "intelligence": "Intelligence is a published-score proxy, not universal task success.",
    "coding": "Coding is a published-score proxy, not measured review accuracy. "
              "The complete current Coding formula is not established.",
    "agentic": "Agentic is a published-score proxy, not proof of multi-agent "
               "coordination. The complete current Agentic formula is not established.",
}

ATTRIBUTION = ("Ratings and prices from Artificial Analysis — "
               "https://artificialanalysis.ai (attribution per their terms)")


def fmt_money(v):
    if v >= 1000:
        return f"${v / 1000:.2f}k"
    if v >= 1:
        return f"${v:.2f}"
    body = f"{v:.4f}" if v < 0.01 else f"{v:.3f}"
    return "$" + body.rstrip("0").rstrip(".")


def fmt_delta(v):
    sign = "-" if v < 0 else "+"
    return f"{sign}{fmt_money(abs(v))}"


def fmt_ppi(v):
    return f"{v / 1000:.1f}k" if v >= 1000 else f"{v:.0f}"


def arrow_text(d, ds):
    gain, saved, m2, e2, ii2, c2 = d
    g = f"+{gain:g} pts" if gain else "same rating"
    txt = f"→ {ds.models[m2].name} {EFFORT_LABEL[e2]}: {g}"
    if saved > 0:
        txt += f", save {fmt_money(saved)}"
    return txt


def load_roles(path):
    """Validate the editable, file-ordered role catalog before acquisition."""
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise ValueError(f"cannot read roles file {path}: {e}") from e
    if not isinstance(doc, list) or not doc:
        raise ValueError(f"roles file {path} must hold a non-empty list")
    roles, names = [], set()
    for i, r in enumerate(doc):
        if not isinstance(r, dict):
            raise ValueError(f"roles file {path}[{i}] is not an object")
        for field in ("name", "description", "capacity"):
            if not isinstance(r.get(field), str) or not r[field].strip():
                raise ValueError(f"roles file {path}[{i}] needs non-empty {field}")
        name = r["name"]
        if name in names:
            raise ValueError(f"roles file {path} repeats role name {name!r}")
        names.add(name)
        index = r.get("index")
        if not isinstance(index, str) or index not in INDEX_FIELD:
            raise ValueError(f"role {name!r} index must be one of "
                             f"{', '.join(INDEX_FIELD)}")
        objective = r.get("objective")
        if not isinstance(objective, str) or objective not in OBJECTIVES:
            raise ValueError(f"role {name!r} objective must be one of "
                             f"{', '.join(OBJECTIVES)}")
        floor = r.get("floor", 2)
        if type(floor) is not int or not 1 <= floor <= 5:
            raise ValueError(f"role {name!r} floor must be an integer 1..5")
        roles.append(dict(name=name, description=r["description"],
                          capacity=r["capacity"], index=index,
                          objective=objective, floor=floor))
    return roles


def _finite(value):
    return value is not None and math.isfinite(value)


def _ratio(r):
    """Only finite Intelligence points per matching positive task USD."""
    if not (_finite(r.score) and _finite(r.cost) and r.cost > 0):
        return None
    value = r.score / r.cost
    return value if math.isfinite(value) else None


def _source_grades(ds, source, effort):
    return grades([r.score for r in ds.ratings
                   if r.source == source and r.effort == effort
                   and _finite(r.score)])


def _capability_grades(ds, index):
    field = INDEX_FIELD[index]
    return grades([getattr(r, field) for r in ds.ratings
                   if r.source == "aa" and r.effort in EFFORTS
                   and _finite(getattr(r, field))])


def _included(ds):
    """Only independently rated models, including source-only identities."""
    return {r.model_key for r in ds.ratings if r.source in ("deepswe", "tb")}


def creators(ds):
    """Every known catalog creator, independent of inclusion and eligibility."""
    return sorted({m.provider for m in ds.models.values() if m.provider != "—"},
                  key=str.casefold)


def _pts(ds, provider):
    included = _included(ds)
    return [p for p in aa_points(ds.ratings) if p[0] in included
            and (provider is None or ds.models[p[0]].provider == provider)]


def _league_key(configuration, objective, index):
    """The complete comparison, shared by effort selection and model order."""
    score = getattr(configuration, INDEX_FIELD[index])
    tail = (EFFORTS.index(configuration.effort), configuration.model_key)
    if index != "intelligence":
        return (-score, *tail)
    cost = configuration.cost
    if objective == "cap":
        return (-score, cost, *tail)
    if objective == "ppi":
        return (-_ratio(configuration), -score, cost, *tail)
    return (cost, -score, *tail)


def _select(configs, index, objective, floor, capability):
    """Return the selected Rating and an explicit reason when none qualifies."""
    if not configs:
        return None, "No measured Artificial Analysis configuration"
    scored = [r for r in configs if _finite(getattr(r, INDEX_FIELD[index]))]
    if not scored:
        return None, f"No finite {INDEX_LABEL[index]} score at any measured effort"
    if index == "intelligence":
        scored = [r for r in scored if _finite(r.cost) and r.cost >= 0]
        if not scored:
            return None, ("No finite non-negative matching Intelligence benchmark "
                          "task cost at a scored effort")
        if objective == "ppi":
            scored = [r for r in scored if _ratio(r) is not None]
            if not scored:
                return None, ("Best value requires a positive matching Intelligence "
                              "benchmark task cost and finite Capability per dollar")
        elif objective == "price":
            scored = [r for r in scored if capability[r.score] >= floor]
            if not scored:
                return None, f"No scored/priced configuration meets capability grade ≥ {floor}"
    return min(scored, key=lambda r: _league_key(r, objective, index)), None


def query(ds, role, objective=None, min_grade=None, provider=None, view="table"):
    """One shared consumer result, in direct objective order.

    Capability references precede eligibility. Selected-row axis grades precede
    display constraints. Unranked records are not recommendations; excluded
    records passed measurement requirements but failed the display constraint.
    Intelligence advisory points stay floor-free and display-filter-free.
    """
    override = objective
    objective = objective or role["objective"]
    if view not in VIEW_LABEL:
        raise ValueError(f"unknown view: {view!r}")
    if min_grade not in CAPABILITY_FILTERS:
        raise ValueError(f"unknown capability display filter: {min_grade!r}")
    catalog_creators = creators(ds)
    if provider is not None and provider not in (*catalog_creators, *PROVIDER_SHORTCUTS):
        raise ValueError(f"unknown provider: {provider!r}")
    provider_label = provider or "All providers"
    if objective not in OBJECTIVES:
        raise ValueError(f"unknown objective: {objective!r}")
    index = role["index"]
    capability = _capability_grades(ds, index)
    supported = index == "intelligence" or objective == "cap"
    unavailable = None if supported else (
        f"Unavailable objective: {OBJECTIVE_LABEL[objective]} for "
        f"{INDEX_LABEL[index]}. No matching {INDEX_LABEL[index]} benchmark "
        "task cost is established; select Highest capability.")
    scope = dict(kind=("global" if provider is None else "provider")
                 if supported and index == "intelligence" else "unavailable",
                 provider=provider,
                 label=("Global comparison — All providers" if provider is None else
                        f"Creator-local comparison — {provider}")
                 if supported and index == "intelligence" else
                 f"Cost-based advice unavailable for {INDEX_LABEL[index]}")
    pts = _pts(ds, provider) if supported and index == "intelligence" else []
    frontier = frontier_set(pts)
    measurements, configurations = {}, {}
    for r in ds.ratings:
        measurements.setdefault(r.model_key, []).append(r)
        if r.source == "aa" and r.effort in EFFORTS:
            configurations.setdefault(r.model_key, []).append(r)
    rows, unranked = [], []
    tb_by_effort = {}
    source_grades, tb_grades_by_effort = {}, {}
    for key in sorted(_included(ds)):
        model = ds.models[key]
        base = dict(key=key, model=model.name, provider=model.provider,
                    measurements=measurements.get(key, []))
        sel, reason = ((None, unavailable) if unavailable else
                       _select(configurations.get(key, []), index, objective,
                               role["floor"], capability))
        if sel is None:
            unranked.append(dict(base, reason=reason, configuration=None))
            continue
        effort = sel.effort
        dsw = next((r for r in measurements[key] if r.source == "deepswe"
                    and r.effort == effort), None)
        if effort not in tb_by_effort:
            tb_by_effort[effort] = best_tb(ds.ratings, effort)
            source_grades[effort] = _source_grades(ds, "deepswe", effort)
            tb_grades_by_effort[effort] = grades(
                [r.score for r in tb_by_effort[effort].values() if _finite(r.score)])
        collapsed = tb_by_effort[effort]
        tb = collapsed.get(key)
        tb_grades = tb_grades_by_effort[effort]
        score = getattr(sel, INDEX_FIELD[index])
        intelligence = index == "intelligence"
        rows.append(dict(
            base, index=index, effort=effort, configuration=sel,
            score=score, grade=capability[score],
            ratings={"aa": sel, "deepswe": dsw, "tb": tb},
            dsw=source_grades[effort].get(dsw.score) if dsw else None,
            tb=tb_grades.get(tb.score) if tb else None,
            cost=sel.cost if intelligence else None,
            ppi=_ratio(sel) if intelligence else None,
            speed=sel.speed, first_answer_seconds=sel.first_answer_seconds,
            frontier=(key, effort) in frontier if intelligence else None,
            dom=dominator(pts, key, effort, score, sel.cost) if intelligence else None,
            alternatives=alternatives(pts, score, sel.cost) if intelligence else [],
            advisory_scope=scope,
        ))
    value_grades = grades([r["ppi"] for r in rows if r["ppi"] is not None])
    speed_grades = grades([r["speed"] for r in rows if _finite(r["speed"])])
    price_grades = grades([r["cost"] for r in rows if r["cost"] is not None],
                          reverse=False)
    for row in rows:
        row["value"] = value_grades.get(row["ppi"])
        row["spd"] = speed_grades.get(row["speed"])
        row["price_tier"] = price_grades.get(row["cost"])
    rows.sort(key=lambda r: _league_key(r["configuration"], objective, index))
    excluded = []
    if min_grade is not None:
        excluded = [dict(r, reason=f"Capability display requires grade ≥ {min_grade}")
                    for r in rows if r["grade"] < min_grade]
        rows = [r for r in rows if r["grade"] >= min_grade]
    if provider is not None:
        rows = [r for r in rows if r["provider"] == provider]
        excluded = [r for r in excluded if r["provider"] == provider]
        unranked = [r for r in unranked if r["provider"] == provider]
    status = "unavailable_objective" if unavailable else "ok" if rows else "no_qualifying"
    constraint = ("All capability grades" if min_grade is None else
                  f"capability grade ≥ {min_grade}")
    if objective == "price" and index == "intelligence":
        constraint += f"; price floor grade ≥ {role['floor']}"
    selected = (f"{role['name']} · {INDEX_LABEL[index]} · "
                f"{OBJECTIVE_LABEL[objective]} · {provider_label} · {constraint}")
    reason = f"{unavailable} — {selected}" if unavailable else None
    if status == "no_qualifying":
        reason = f"No qualifying configuration — {selected}"
    if index == "intelligence":
        sections = [
            dict(label=f"Frontier — no strict Intelligence score/task-cost improvement "
                 f"· {scope['label']}", rows=[r for r in rows if r["frontier"]]),
            dict(label=f"Dominated — strict replacement · {scope['label']}",
                 rows=[r for r in rows if not r["frontier"]]),
        ] if supported else []
        for section in sections:
            _add_deltas(section["rows"])
    else:
        sections = [dict(label=f"Direct {INDEX_LABEL[index]} score order", rows=rows)]
    table_rows = [r for section in sections for r in section["rows"]]
    by_creator = {name: [] for name in ([provider] if provider else catalog_creators)}
    for row in rows:
        if row["provider"] in by_creator:
            by_creator[row["provider"]].append(row)
    picks, without_picks = [], []
    for name, candidates in by_creator.items():
        missing = [r for r in unranked if r["provider"] == name]
        filtered = [r for r in excluded if r["provider"] == name]
        group = dict(provider=name, primary=candidates[0] if candidates else None,
                     runner_up=candidates[1] if len(candidates) > 1 else None,
                     reason=None, unranked=missing, excluded=filtered)
        if candidates:
            if len(candidates) == 1:
                group["reason"] = "No qualifying runner-up"
            picks.append(group)
        else:
            why = unavailable or "; ".join(sorted(
                {r["reason"] for r in missing + filtered})) or (
                "No models meet the inclusion boundary: at least one "
                "DeepSWE or Terminal-Bench rating is required")
            group["reason"] = f"No qualifying configuration — {name} · {why}"
            without_picks.append(group)
    recoveries = []
    if provider is not None:
        recoveries.append(dict(action="all_providers", label="All providers"))
    if min_grade is not None:
        recoveries.append(dict(action="clear_capability", label="Clear capability filter"))
    if not supported:
        recoveries.append(dict(action="highest_capability", label="Highest capability"))
    if override is not None:
        recoveries.append(dict(action="role_default", label="Use role default"))
    return dict(role=role, index=index, objective=objective, objective_override=override,
                provider=provider, provider_label=provider_label, min_grade=min_grade,
                view=view, status=status, reason=reason, advisory_scope=scope,
                rows=rows, unranked=unranked, excluded=excluded, points=pts,
                frontier_path=pareto(pts), sections=sections, table_rows=table_rows,
                picks=picks, providers_without_picks=without_picks,
                creators=catalog_creators, shortcuts=PROVIDER_SHORTCUTS,
                recovery_actions=recoveries)


def _cell(value, width):
    return f"{'—' if value is None else value:>{width}}"


def _add_deltas(rows):
    previous = None
    for row in rows:
        row["score_change"] = row["score"] - previous["score"] if previous else None
        row["cost_change"] = row["cost"] - previous["cost"] if previous else None
        previous = row


def _fmt_row(row, intelligence):
    text = (f"  {row['model']:<20} {EFFORT_LABEL[row['effort']]:<10} "
            f"{row['provider']:<12} {row['score']:>18g} {row['grade']:>16} "
            f"{_cell(row['dsw'], 13)} {_cell(row['tb'], 20)}")
    if intelligence:
        ratio = fmt_ppi(row["ppi"]) if row["ppi"] is not None else "—"
        delta = (f"{row['score_change']:+.1f}" if row["score_change"] is not None else "—")
        cost_delta = (fmt_delta(row["cost_change"])
                      if row["cost_change"] is not None else "—")
        text += (f" {fmt_money(row['cost']):>19} {ratio:>20} "
                 f"{delta:>12} {cost_delta:>16}")
    text += (f" {_cell(row['first_answer_seconds'], 26)}"
             f" {_cell(row['speed'], 24)}")
    return text


def table(ds, role, objective=None, min_grade=None, provider=None, *, result=None):
    """Render the shared result; Intelligence sections do not define pick order."""
    if result is None:
        result = query(ds, role, objective, min_grade, provider)
    role = result["role"]
    index, objective = result["index"], result["objective"]
    intelligence = index == "intelligence"
    floor = (f" · capability floor ≥ {role['floor']}"
             if objective == "price" and intelligence else "")
    lines = [f"{role['name']} — {INDEX_LABEL[index]} — "
             f"{OBJECTIVE_LABEL[objective]}{floor}",
             f"{role['name']}: {role['description']}",
             f"Capacity guidance: {role['capacity']}",
             INDEX_NOTE[index],
             f"Provider selection: {result['provider_label']} · "
             f"{result['advisory_scope']['label']}"]
    if result["reason"]:
        lines.extend(("", result["reason"]))
    rows = result["rows"]
    if result["status"] != "unavailable_objective" and intelligence:
        path = " → ".join(
            f"{ds.models[m].name} {EFFORT_LABEL[e]} {score:g} @ {fmt_money(cost)}"
            for m, e, cost, score in result["frontier_path"])
        lines.extend(("", f"frontier: {path or '—'}"))
    displayed = []
    if rows:
        header = (f"  {'Model':<20} {'Effort':<10} {'Provider':<12} "
                  f"{INDEX_LABEL[index] + ' score':>18} {'Capability grade':>16} "
                  f"{'DeepSWE grade':>13} {'Terminal-Bench grade':>20}")
        if intelligence:
            header += (f" {'Benchmark task cost':>19} {'Capability per dollar':>20} "
                       f"{'Score change':>12} {'Task cost change':>16}")
        header += f" {'Time to first answer token':>26} {'Output tokens per second':>24}"
        lines.extend(("", header))
        for section in result["sections"]:
            if not section["rows"]:
                continue
            lines.append(section["label"])
            section = section["rows"]
            for row in section:
                lines.append(_fmt_row(row, intelligence))
                if row["dom"]:
                    lines.append("    " + arrow_text(row["dom"], ds))
            displayed.extend(section)
    for title, records in (("Unranked included models", result["unranked"]),
                           ("Excluded by capability display", result["excluded"])):
        if records:
            lines.extend(("", title + ":"))
            lines.extend(f"- {r['model']} [{r['key']}]: {r['reason']}" for r in records)
    return lines, displayed


def render(ds, role, objective=None, min_grade=None, provider=None, *, result=None):
    lines, _ = table(ds, role, objective, min_grade, provider, result=result)
    return lines


