"""Role table rendering (tickets 11–14, 18).

One role under its active objective: each model enters the table at its
objective-selected configuration (cap = highest AA index / ppi = best
price-per-intelligence / price = cheapest above the capability floor), so
efforts mix per row — the per-row Effort column is what keeps the mixed
table legible (ticket 18). ★ frontier section first, then ✗ dominated rows
each annotated with its best replacement arrow; frontier path line across
efforts at the top. DSW/AA/TB grade columns are per-source quintiles at
each row's own effort; the TB column grades TB's best-agent-collapsed
ratings and shows `—` at efforts v2.1 doesn't cover (low/medium). Ticket
14: the Spd column renders the speed tier; each row also carries the value
tier (PPI grade) and price tier (cost grade) for the detail view. Ticket
18: roles come from a checked-in roles.json (tab order = file order; users
add roles by editing the file), the `o` objective override swaps the lens,
and the detail view gains cheaper near-equal alternatives plus the
OpenRouter context field.
"""

import json
from pathlib import Path

from .identity import best_tb
from .rank import aa_points, dominator, frontier_set, pareto
from .tier import grades

OBJECTIVES = ("cap", "ppi", "price")

OBJECTIVE_LABEL = {"price": "cheapest first", "ppi": "best PPI first",
                   "cap": "best capability first"}

HEADER = (f"{'DSW':>3} {'AA':>3} {'TB':>3}  {'Model':<17} {'Effort':<6} "
          f"{'Provider':<9} {'$/task':>7} {'ΔAA':>6} {'Δ$':>8} {'PPI':>5} "
          f"{'Spd':>4}  {'*':>1}")

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
    txt = f"→ {ds.models[m2].name} {e2}: {g}"
    if saved > 0:
        txt += f", save {fmt_money(saved)}"
    return txt


def load_roles(path):
    """roles.json → list of role dicts, tab order = file order. The schema
    (name, description, capacity incl. speed guidance, objective, floor) is
    validated so a broken user edit fails loudly at startup instead of
    rendering a half table."""
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, ValueError) as e:
        raise ValueError(f"cannot read roles file {path}: {e}") from e
    if not isinstance(doc, list) or not doc:
        raise ValueError(f"roles file {path} must hold a non-empty list")
    roles = []
    for i, r in enumerate(doc):
        if not isinstance(r, dict):
            raise ValueError(f"roles file {path}[{i}] is not an object")
        name = r.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"roles file {path}[{i}] missing a name")
        desc = r.get("description")
        cap = r.get("capacity")
        if not isinstance(desc, str) or not desc:
            raise ValueError(f"role {name!r} missing a description")
        if not isinstance(cap, str) or not cap:
            raise ValueError(f"role {name!r} missing capacity guidance")
        objective = r.get("objective")
        if objective not in OBJECTIVES:
            raise ValueError(f"role {name!r} objective must be one of "
                             f"{', '.join(OBJECTIVES)}")
        floor = r.get("floor", 2)
        if not isinstance(floor, int) or not 1 <= floor <= 5:
            raise ValueError(f"role {name!r} floor must be an integer 1..5")
        roles.append(dict(name=name, description=desc, capacity=cap,
                          objective=objective, floor=floor))
    return roles


def _cell(v, width):
    return f"{'—' if v is None else v:>{width}}"


def _fmt_row(r):
    cost = fmt_money(r["cost"]) if r["cost"] is not None else "n/a"
    ppi = fmt_ppi(r["ppi"]) if r["ppi"] is not None else "n/a"
    return (f"{_cell(r['dsw'], 3)} {_cell(r['aa'], 3)} {_cell(r['tb'], 3)}  "
            f"{r['model']:<17} {r['effort']:<6} {r['provider']:<9} "
            f"{cost:>7} {r['d_aa']:>6} {r['d_cost']:>8} {ppi:>5} "
            f"{_cell(r['spd'], 4)}  {r['mark']}")


def _add_deltas(rows):
    """Δ columns vs the row above within the section (visible sort order)."""
    prev = None
    for r in rows:
        ok = (prev is not None and r["ii"] is not None and prev["ii"] is not None
              and r["cost"] is not None and prev["cost"] is not None)
        if ok:
            r["d_aa"] = f"{r['ii'] - prev['ii']:+.1f}"
            r["d_cost"] = fmt_delta(r["cost"] - prev["cost"])
        else:
            r["d_aa"] = r["d_cost"] = "—"
        prev = r


def _source_grades(ds, source, effort):
    """{score: 1–5 grade} for one source's ratings at an effort — the grade
    bins are per source, never blended (spec §5)."""
    return grades([r.score for r in ds.ratings
                   if r.source == source and r.effort == effort
                   and r.score is not None])


def _included(ds):
    """Spec §3: a model appears iff it has ≥1 DeepSWE/TB rating."""
    return {r.model_key for r in ds.ratings
            if r.source in ("deepswe", "tb") and r.effort is not None}


def _pts(ds):
    """AA configs of included models only — AA's unrated long tail never
    enters the frontier envelope, the arrows, or the path line."""
    return [p for p in aa_points(ds.ratings) if p[0] in _included(ds)]


def _speed_grades(ds, effort):
    """{tokens/s: 1–5} over AA rows at one effort — the per-effort bins the
    price-lens tie-break uses. (The table's Spd column bins over the table's
    own rows, ticket 14; the tie-break needs a stable per-effort ordering.)"""
    return grades([r.speed for r in ds.ratings
                   if r.source == "aa" and r.effort == effort
                   and r.speed is not None])


def _select(ds, key, objective, floor):
    """The model's best AA configuration under the objective, or None when
    no configuration qualifies (no AA rows; no priced row under ppi; nothing
    above the floor under price). Returns the Rating itself, so the row's
    effort/score/cost/speed all come from one source row."""
    cfgs = [r for r in ds.ratings
            if r.source == "aa" and r.model_key == key and r.effort is not None
            and r.score is not None]
    if not cfgs:
        return None
    if objective == "cap":
        return min(cfgs, key=lambda r: (-r.score,
                                        r.cost if r.cost is not None
                                        else float("inf")))
    if objective == "ppi":
        priced = [r for r in cfgs if r.cost is not None and r.cost > 0]
        if not priced:
            return None
        return max(priced, key=lambda r: (r.score / r.cost, r.score))
    # price lens: cheapest configuration above the capability floor; on a
    # cost tie, higher AA index, then higher speed tier.
    above = [r for r in cfgs if r.cost is not None
             and _source_grades(ds, "aa", r.effort).get(r.score, 0) >= floor]
    if not above:
        return None

    def tie(r):
        return (-r.score, -_speed_grades(ds, r.effort).get(r.speed, 0))

    return min(above, key=lambda r: (r.cost, tie(r)))


def objective_rows(ds, role, objective):
    """Every table row for a role under its active objective — each model at
    its objective-selected configuration, unsorted. A model with no
    qualifying configuration does not appear (ticket 18: the source-only
    long tail is absent from ranked tables)."""
    included = _included(ds)
    pts = _pts(ds)
    fr = frontier_set(pts)
    doms = {(m, e): dominator(pts, m, e, ii, c) for m, e, c, ii in pts}
    tb_best = {}

    rows = []
    for key in sorted(included):
        sel = _select(ds, key, objective, role["floor"])
        if sel is None:
            continue
        effort = sel.effort
        m = ds.models[key]
        dsw = next((r for r in ds.ratings
                    if r.source == "deepswe" and r.model_key == key
                    and r.effort == effort), None)
        collapsed = tb_best.setdefault(effort, best_tb(ds.ratings, effort))
        tb = collapsed.get(key)
        dsw_g = _source_grades(ds, "deepswe", effort)
        aa_g = _source_grades(ds, "aa", effort)
        # TB grades bin over the collapsed set — one rating per (model ×
        # effort) after best-agent collapse, so no agent inflates the bin.
        tb_g = grades([r.score for r in collapsed.values()
                       if r.score is not None])
        rows.append(dict(
            key=key, model=m.name, effort=effort, provider=m.provider,
            dsw=dsw_g.get(dsw.score) if dsw and dsw.score is not None else None,
            aa=aa_g.get(sel.score),
            tb=tb_g.get(tb.score) if tb and tb.score is not None else None,
            cost=sel.cost, ii=sel.score, speed=sel.speed,
            ppi=(sel.score / sel.cost) if sel.cost is not None else None,
            frontier=(key, effort) in fr,
            dom=doms.get((key, effort)),
        ))

    # Ticket 14: the three independent 1–5 grades per model, each binned over
    # its own axis's valid set within this role's table. Value = grade of the
    # row's PPI — the PPI column's numerator is the AA Intelligence Index
    # (ticket 11), so the set is single-source by construction and the value
    # tier ranks intelligence-per-dollar on the same AA axis as the frontier.
    # Speed = AA tokens/s grade (benchmark durations never enter); price =
    # cost grade, 1 = cheapest. Equal values never split across bins; small
    # sets yield fewer than five populated grades.
    value_g = grades([r["ppi"] for r in rows if r["ppi"] is not None])
    speed_g = grades([r["speed"] for r in rows if r["speed"] is not None])
    price_g = grades([r["cost"] for r in rows if r["cost"] is not None],
                     reverse=False)
    for r in rows:
        r["value"] = value_g.get(r["ppi"])
        r["spd"] = speed_g.get(r["speed"])
        r["price_tier"] = price_g.get(r["cost"])
    return rows


def _league_key(r, objective):
    """Sort key for the active objective; missing values sort last.

    price: per-task cost ascending (cheapest first); ppi: PPI descending;
    cap: AA index descending — the grade order itself, since grades are
    monotonic in the index (tier.grades bins distinct values).
    """
    if objective == "price":
        c = r["cost"]
        return (c is None, c if c is not None else float("inf"))
    if objective == "ppi":
        v = r["ppi"]
    elif objective == "cap":
        v = r["ii"]
    else:
        raise ValueError(f"unknown objective: {objective!r}")
    return (v is None, -v if v is not None else float("inf"))


def table(ds, role, objective=None, min_aa=None):
    """(rendered lines, display-ordered row dicts) for one role under its
    active objective (ticket 18): `objective` overrides the role's default
    (the `o` key); `min_aa` cuts the table to the top capability bands by AA
    grade (the `f` key: 5 = top band, 4 = top two). The frontier path line
    is the cross-effort ladder and stays whole under both."""
    objective = objective or role["objective"]
    pts = _pts(ds)
    path = " → ".join(f"{ds.models[m].name} {e} {ii:.0f} @ {fmt_money(c)}"
                      for m, e, c, ii in pareto(pts))
    floor_txt = f" · floor {role['floor']}" if objective == "price" else ""
    lines = [f"{role['name']} — objective {objective} — "
             f"{OBJECTIVE_LABEL[objective]}{floor_txt}",
             f"{role['name']}: {role['description']}",
             f"capacity: {role['capacity']}",
             "", f"frontier: {path}", "", HEADER]

    rows = objective_rows(ds, role, objective)
    if min_aa is not None:
        rows = [r for r in rows if r["aa"] is not None and r["aa"] >= min_aa]

    def league(r):
        return _league_key(r, objective)

    frows = sorted((r for r in rows if r["frontier"]), key=league)
    drows = sorted((r for r in rows if not r["frontier"]), key=league)
    _add_deltas(frows)
    _add_deltas(drows)

    if frows:
        lines.append("★ frontier — nothing beats these on rating AND price")
        for r in frows:
            r["mark"] = "*"
            lines.append(_fmt_row(r))
    if drows:
        lines.append("✗ dominated — take the arrow instead")
        for r in drows:
            r["mark"] = ""
            lines.append(_fmt_row(r))
            if r["dom"]:
                lines.append("    " + arrow_text(r["dom"], ds))
    return lines, frows + drows


def render(ds, role, objective=None, min_aa=None):
    """Rendered table lines for one role — batch-mode entry (ticket 12:
    --role picks; ticket 18: the role's objective selects each model's
    effort, and `objective` overrides it — the TUI's `table` call shares
    this)."""
    lines, _ = table(ds, role, objective, min_aa)
    return lines


def _alternatives(ds, row):
    """Cheaper near-equal configurations for the detail view (ticket 18):
    price < the row's price and AA index ≥ the row's − 5 (one constant
    band), top 3, price-sorted."""
    if row["ii"] is None or row["cost"] is None:
        return []
    cands = [(m, e, c, ii) for m, e, c, ii in _pts(ds)
             if c < row["cost"] and ii >= row["ii"] - 5]
    cands.sort(key=lambda t: t[2])
    return cands[:3]


def detail(ds, row, role, objective=None):
    """Detail-view lines for one table row (tickets 16, 18): per-source raw
    grades and ranks, the PPI division (rating ÷ cost), list price, price
    tier, speed, the OpenRouter context field, frontier/dominated status,
    the source-disagreement flag, and up to three cheaper near-equal
    alternatives. The flag is set when the capability grades of the sources
    that rate this model at this effort disagree by ≥2 — the 09 prototype's
    rule: a grade gap that wide means the sources tell different stories,
    and disagreement is meaning, not noise to average away."""
    objective = objective or role["objective"]
    key, effort = row["key"], row["effort"]
    m = ds.models[key]
    floor_txt = f" · floor {role['floor']}" if objective == "price" else ""
    out = [f"{m.name} {effort} — {m.provider}",
           f"{role['name']} · objective {objective} · "
           f"{OBJECTIVE_LABEL[objective]}{floor_txt}", ""]

    tb_best = best_tb(ds.ratings, effort)

    def rating(source):
        if source == "tb":
            return tb_best.get(key)
        return next((r for r in ds.ratings
                     if r.source == source and r.model_key == key
                     and r.effort == effort), None)

    def rank(source, score):
        """(rank, n) of `score` within its source's set at this effort —
        TB ranks over the collapsed set, the set its grade bins over."""
        if source == "tb":
            scores = [r.score for r in tb_best.values() if r.score is not None]
        else:
            scores = [r.score for r in ds.ratings
                      if r.source == source and r.effort == effort
                      and r.score is not None]
        n = len(scores)
        return (1 + sum(1 for s in scores if s > score), n)

    graded = []
    for row_key, label, source in (("dsw", "DeepSWE", "deepswe"),
                                   ("aa", "AA", "aa"),
                                   ("tb", "TB", "tb")):
        r = rating(source)
        grade = row[row_key]
        if r is None or r.score is None or grade is None:
            out.append(f"{label:<8} grade —   no {label} row at {effort} effort")
            continue
        raw = f"{r.score:.3f}" if r.score < 1 else f"{r.score:.1f}"
        rk = rank(source, r.score)
        out.append(f"{label:<8} grade {grade}   raw {raw:<8} "
                   f"rank {rk[0]} of {rk[1]} rated at this effort")
        graded.append((label, grade))

    if row["ppi"] is not None:
        out.append(f"PPI      {fmt_ppi(row['ppi'])} = {row['ii']:.1f} / "
                   f"{fmt_money(row['cost'])}   value grade {row['value']}")
    else:
        out.append("PPI      n/a — no AA price at this effort")

    aa = rating("aa")
    tier = row["price_tier"]
    tier_txt = "—" if tier is None else tier
    if aa is not None:
        pr = aa.pricing
        inp, outp = pr.get("price_1m_input_tokens"), pr.get("price_1m_output_tokens")
        if inp is not None and outp is not None:
            out.append(f"list price  ${inp:.2f}/${outp:.2f} per M in/out "
                       f"({effort} variant)   price tier {tier_txt}")
        else:
            out.append(f"list price  n/a   price tier {tier_txt}")
    else:
        out.append("list price  n/a   price tier —")

    if row["speed"] is not None:
        out.append(f"speed     {row['speed']:.1f} t/s   speed tier {row['spd']}")
    else:
        out.append("speed     —   no AA speed at this effort")

    if m.context_length is not None:
        ctx = (f"{m.context_length / 1000:.0f}k"
               if m.context_length >= 1000 else str(m.context_length))
        out.append(f"context   {ctx} tokens"
                   + (f"   {m.modalities}" if m.modalities else ""))
    else:
        out.append("context   n/a — no OpenRouter row for this model")

    if row["frontier"]:
        out.append("frontier * — no other configuration beats this on rating AND price")
    elif row["dom"]:
        out.append("dominated — " + arrow_text(row["dom"], ds))
    else:
        out.append("not ranked — no AA price, so no frontier/dominated position")

    if len(graded) >= 2:
        lo = min(graded, key=lambda t: t[1])
        hi = max(graded, key=lambda t: t[1])
        if hi[1] - lo[1] >= 2:
            out.append(f"sources disagree ({lo[0]} {lo[1]} vs {hi[0]} {hi[1]} "
                       f"at {effort}): that's meaning, not noise — the "
                       "sources measure different things")

    alts = _alternatives(ds, row)
    if alts:
        out.append("")
        out.append("alternatives — cheaper, within 5 AA pts, price-sorted:")
        for m2, e2, c2, ii2 in alts:
            out.append(f"  {ds.models[m2].name} {e2} — {fmt_money(c2)}, "
                       f"ΔAA {ii2 - row['ii']:+.1f}")
    return out
