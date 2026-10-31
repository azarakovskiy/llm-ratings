"""Shared selected-index policy and its batch/session presentation.

One measured configuration per included model, with direct objective order
kept separate from the Intelligence table's frontier-first sections.
"""

import json
import math
from pathlib import Path

from .identity import EFFORTS, best_tb
from .rank import aa_points, dominator, frontier_set, pareto
from .tier import grades

OBJECTIVES = ("cap", "ppi", "price")

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


def _pts(ds):
    included = _included(ds)
    return [p for p in aa_points(ds.ratings) if p[0] in included]


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


def query(ds, role, objective=None, min_grade=None):
    """One shared consumer result, in direct objective order.

    Capability references precede eligibility. Selected-row axis grades precede
    display constraints. Unranked records are not recommendations; excluded
    records passed measurement requirements but failed the display constraint.
    Intelligence advisory points stay floor-free and display-filter-free.
    """
    objective = objective or role["objective"]
    if objective not in OBJECTIVES:
        raise ValueError(f"unknown objective: {objective!r}")
    index = role["index"]
    capability = _capability_grades(ds, index)
    supported = index == "intelligence" or objective == "cap"
    unavailable = None if supported else (
        f"Unavailable objective: {OBJECTIVE_LABEL[objective]} for "
        f"{INDEX_LABEL[index]}. No matching {INDEX_LABEL[index]} benchmark "
        "task cost is established; select Highest capability.")
    pts = _pts(ds) if supported and index == "intelligence" else []
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
    status = "unavailable_objective" if unavailable else "ok" if rows else "no_qualifying"
    constraint = ("All capability grades" if min_grade is None else
                  f"capability grade ≥ {min_grade}")
    if objective == "price":
        constraint += f"; price floor grade ≥ {role['floor']}"
    reason = unavailable
    if status == "no_qualifying":
        reason = (f"No qualifying configuration — {role['name']} · "
                  f"{INDEX_LABEL[index]} · {OBJECTIVE_LABEL[objective]} · {constraint}")
    return dict(index=index, objective=objective, status=status, reason=reason,
                rows=rows, unranked=unranked, excluded=excluded, points=pts)


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


def table(ds, role, objective=None, min_grade=None):
    """Render the shared result; Intelligence sections do not define pick order."""
    result = query(ds, role, objective, min_grade)
    index, objective = result["index"], result["objective"]
    intelligence = index == "intelligence"
    floor = f" · capability floor ≥ {role['floor']}" if objective == "price" else ""
    lines = [f"{role['name']} — {INDEX_LABEL[index]} — "
             f"{OBJECTIVE_LABEL[objective]}{floor}",
             f"{role['name']}: {role['description']}",
             f"Capacity guidance: {role['capacity']}",
             INDEX_NOTE[index]]
    if result["reason"]:
        lines.extend(("", result["reason"]))
    rows = result["rows"]
    if result["status"] != "unavailable_objective" and intelligence:
        path = " → ".join(
            f"{ds.models[m].name} {EFFORT_LABEL[e]} {score:g} @ {fmt_money(cost)}"
            for m, e, cost, score in pareto(result["points"]))
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
        if intelligence:
            sections = [
                ("Frontier — no strict improvement in Intelligence score/task cost",
                 [r for r in rows if r["frontier"]]),
                ("Dominated — strict replacement within all included models",
                 [r for r in rows if not r["frontier"]]),
            ]
        else:
            sections = [(f"Direct {INDEX_LABEL[index]} score order", rows)]
        for title, section in sections:
            if not section:
                continue
            lines.append(title)
            if intelligence:
                _add_deltas(section)
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


def render(ds, role, objective=None, min_grade=None):
    lines, _ = table(ds, role, objective, min_grade)
    return lines


def _alternatives(ds, row):
    if row["index"] != "intelligence":
        return []
    cands = [(m, e, c, score) for m, e, c, score in _pts(ds)
             if c < row["cost"] and score >= row["score"] - 5]
    cands.sort(key=lambda p: (p[2], -p[3], EFFORTS.index(p[1]), p[0]))
    return cands[:3]


def detail(ds, row, role, objective=None):
    """Independent source evidence for the actual objective-selected effort."""
    objective = objective or role["objective"]
    index, effort, key = row["index"], row["effort"], row["key"]
    model = ds.models[key]
    selected = row["configuration"]
    label = EFFORT_LABEL[effort]
    out = [f"{model.name} {label} — {model.provider}",
           f"{role['name']} · {INDEX_LABEL[index]} · {OBJECTIVE_LABEL[objective]}",
           INDEX_NOTE[index], ""]
    graded = []
    for source, name, grade in (
            ("deepswe", "DeepSWE", row["dsw"]),
            ("aa", f"Artificial Analysis {INDEX_LABEL[index]} score", row["grade"]),
            ("tb", "Terminal-Bench", row["tb"])):
        rating = row["ratings"][source]
        score = getattr(rating, INDEX_FIELD[index]) if source == "aa" else (
            rating.score if rating else None)
        if rating is None or not _finite(score) or grade is None:
            out.append(f"{name} grade — · no {name} row at {label} effort")
            continue
        if source == "aa":
            scores = [getattr(r, INDEX_FIELD[index]) for r in ds.ratings
                      if r.source == "aa" and r.effort in EFFORTS
                      and _finite(getattr(r, INDEX_FIELD[index]))]
            population = "across measured efforts"
        elif source == "tb":
            scores = [r.score for r in best_tb(ds.ratings, effort).values()
                      if _finite(r.score)]
            population = f"at {label} effort, best agent per model"
        else:
            scores = [r.score for r in ds.ratings
                      if r.source == source and r.effort == effort and _finite(r.score)]
            population = f"at {label} effort"
        rank = 1 + sum(s > score for s in scores)
        out.append(f"{name} grade {grade} · raw {score:g} · "
                   f"rank {rank} of {len(scores)} {population}")
        graded.append((name, grade))
    out.append("")
    for other, field in INDEX_FIELD.items():
        if other != index:
            score = getattr(selected, field)
            out.append(f"Artificial Analysis {INDEX_LABEL[other]} score: "
                       f"{score if score is not None else '—'} · separate index evidence")
    if index == "intelligence":
        out.append(f"Benchmark task cost: {fmt_money(row['cost'])} · "
                   f"price tier {row['price_tier']} (1 cheapest)")
        if row["ppi"] is None:
            out.append("Capability per dollar: — · requires positive matching task cost")
        else:
            out.append(f"Capability per dollar: {fmt_ppi(row['ppi'])} = "
                       f"{row['score']:g} / {fmt_money(row['cost'])} · "
                       f"value grade {row['value']}")
        out.append("Capability per dollar means Intelligence points per matching "
                   "benchmark-task USD, not predicted production-task return.")
    else:
        out.append("Cost-based advice unavailable: no matching area-index task cost. "
                   "The separate Coding Agent Index is not a substitute.")
        cost = selected.cost
        out.append("Intelligence benchmark task cost (separate workload evidence): "
                   + (fmt_money(cost) if _finite(cost) and cost >= 0 else "—"))
    pricing = selected.pricing
    inp, output = pricing.get("price_1m_input_tokens"), pricing.get("price_1m_output_tokens")
    if inp is not None and output is not None:
        out.append(f"Token list price: ${inp:.2f}/${output:.2f} per million "
                   "input/output tokens · not benchmark task cost")
    else:
        out.append("Token list price: —")
    for name, value, unit in (
            ("Time to first answer token (including thinking)",
             selected.first_answer_seconds, "seconds"),
            ("Time to first token", selected.first_token_seconds, "seconds"),
            ("Estimated response time for 500 answer tokens",
             selected.response_500_tokens_seconds, "seconds"),
            ("Output tokens per second", selected.speed, "tokens/s")):
        out.append(f"{name}: {value if value is not None else '—'} {unit}")
    out.append(f"Output-speed grade: {row['spd'] if row['spd'] is not None else '—'}"
               " · timing never selects or orders configurations")
    if model.context_length is not None:
        out.append(f"Context: {model.context_length:g} tokens"
                   + (f" · {model.modalities}" if model.modalities else ""))
    else:
        out.append("Context: — · no OpenRouter context evidence")
    out.append("OpenRouter 30-day token share: unavailable · display-only")
    if index == "intelligence":
        if row["frontier"]:
            out.append("Frontier · no strict Intelligence score/task-cost improvement")
        elif row["dom"]:
            out.append("Dominated · " + arrow_text(row["dom"], ds))
    if len(graded) >= 2:
        lo, hi = min(graded, key=lambda p: p[1]), max(graded, key=lambda p: p[1])
        if hi[1] - lo[1] >= 2:
            out.append(f"sources disagree ({lo[0]} {lo[1]} vs {hi[0]} {hi[1]} "
                       f"at {label}): different benchmark populations, not "
                       "measurements to average")
    alternatives = _alternatives(ds, row)
    if alternatives:
        out.extend(("", "Cheaper alternatives · within 5 Intelligence points, "
                    "sorted by Benchmark task cost:"))
        for other, other_effort, cost, score in alternatives:
            out.append(f"  {ds.models[other].name} {EFFORT_LABEL[other_effort]} — "
                       f"{fmt_money(cost)}, score change {score - row['score']:+.1f}")
    return out
