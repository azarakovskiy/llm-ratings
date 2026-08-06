"""Category table rendering (tickets 11–14).

One category at its fixed effort, sorted by the category's league axis so the
Δ columns read the ladder: ★ frontier section first, then ✗ dominated rows
each annotated with its best replacement arrow. Frontier path line across
efforts at the top. DSW/AA/TB grade columns are per-source quintiles at that
effort; the TB column grades TB's best-agent-collapsed ratings and shows `—`
at efforts v2.1 doesn't cover (low/medium). Ticket 14: the Spd column renders
the speed tier; each row also carries the value tier (PPI grade) and price
tier (cost grade) for the detail view.
"""

from .identity import best_tb
from .rank import aa_points, dominator, frontier_set, pareto
from .tier import grades

# (name, fixed effort, league axis) — axes: "price" (cheapest best) |
# "value"/"capability" (5 = best). Locked by 07; the sort per axis is
# ticket 12, the tier columns are ticket 14.
CATEGORIES = [
    ("Chores", "low", "price"),
    ("Everyday", "medium", "value"),
    ("Deliberate", "high", "capability"),
    ("Deep", "max", "capability"),
    ("Best Value", "high", "value"),
]

AXIS_LABEL = {"price": "cheapest first", "value": "best PPI first",
               "capability": "best capability first"}

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


def category_rows(ds, cat):
    """Every table row for a category at its fixed effort, unsorted.

    A row exists for the category's effort when the included model has
    ≥1 rating at that effort from any source (so an AA-only config of an
    included model — e.g. Kimi K3 at low — still renders, with `—` in the
    sources that don't rate it at that effort).
    """
    _, effort, _ = cat
    included = _included(ds)
    rated_at_effort = {r.model_key for r in ds.ratings if r.effort == effort}
    pts = _pts(ds)
    fr = frontier_set(pts)
    doms = {(m, e): dominator(pts, m, e, ii, c) for m, e, c, ii in pts}
    dsw_g = _source_grades(ds, "deepswe", effort)
    aa_g = _source_grades(ds, "aa", effort)
    # TB grades bin over the collapsed set — one rating per (model × effort)
    # after best-agent collapse, so no agent inflates the bin.
    tb_best = best_tb(ds.ratings, effort)
    tb_g = grades([r.score for r in tb_best.values() if r.score is not None])

    rows = []
    for key in sorted(included & rated_at_effort):
        m = ds.models[key]
        dsw = next((r for r in ds.ratings
                    if r.source == "deepswe" and r.model_key == key and r.effort == effort), None)
        aa = next((r for r in ds.ratings
                   if r.source == "aa" and r.model_key == key and r.effort == effort), None)
        tb = tb_best.get(key)
        ii = aa.score if aa else None
        cost = aa.cost if aa else None
        speed = aa.speed if aa else None
        rows.append(dict(
            key=key, model=m.name, effort=effort, provider=m.provider,
            dsw=dsw_g.get(dsw.score) if dsw and dsw.score is not None else None,
            aa=aa_g.get(aa.score) if aa and aa.score is not None else None,
            tb=tb_g.get(tb.score) if tb and tb.score is not None else None,
            cost=cost, ii=ii, speed=speed,
            ppi=(ii / cost) if (ii is not None and cost is not None) else None,
            frontier=(key, effort) in fr,
            dom=doms.get((key, effort)),
        ))

    # Ticket 14: the three independent 1–5 grades per model, each binned over
    # its own axis's valid set within this category's table. Value = grade of
    # the row's PPI — the PPI column's numerator is the AA Intelligence Index
    # (ticket 11), so the set is single-source by construction and the value
    # tier ranks intelligence-per-dollar on the same AA axis as the frontier.
    # Speed = AA tokens/s grade (benchmark durations never enter); price =
    # cost grade, 1 = cheapest. Equal values never split across bins; small
    # sets yield fewer than five populated grades. Price tier feeds the
    # detail view in a later ticket.
    value_g = grades([r["ppi"] for r in rows if r["ppi"] is not None])
    speed_g = grades([r["speed"] for r in rows if r["speed"] is not None])
    price_g = grades([r["cost"] for r in rows if r["cost"] is not None],
                     reverse=False)
    for r in rows:
        r["value"] = value_g.get(r["ppi"])
        r["spd"] = speed_g.get(r["speed"])
        r["price_tier"] = price_g.get(r["cost"])
    return rows


def _league_key(r, axis):
    """Sort key for the category's league axis; missing values sort last.

    price: per-task cost ascending (cheapest first); value: PPI descending;
    capability: AA index descending — the grade order itself, since grades
    are monotonic in the index (tier.grades bins distinct values).
    """
    if axis == "price":
        c = r["cost"]
        return (c is None, c if c is not None else float("inf"))
    if axis == "value":
        v = r["ppi"]
    elif axis == "capability":
        v = r["ii"]
    else:
        raise ValueError(f"unknown league axis: {axis!r}")
    return (v is None, -v if v is not None else float("inf"))


def table(ds, category_name="Chores", effort=None, min_aa=None):
    """(rendered lines, display-ordered row dicts) for one category at one
    effort (ticket 16 extends ticket 12's render): `effort` overrides the
    category's fixed effort (the `e` key); `min_aa` cuts the table to the
    top capability bands by AA grade (the `f` key: 5 = top band, 4 = top
    two). The frontier path line is the cross-effort ladder and stays whole
    under both."""
    name, fixed, axis = next(c for c in CATEGORIES if c[0] == category_name)
    effort = effort or fixed
    pts = _pts(ds)

    path = " → ".join(f"{ds.models[m].name} {e} {ii:.0f} @ {fmt_money(c)}"
                      for m, e, c, ii in pareto(pts))
    lines = [f"{name} — {effort} effort — {AXIS_LABEL[axis]}", "",
             "frontier: " + path, "", HEADER]

    rows = category_rows(ds, (name, effort, axis))
    if min_aa is not None:
        rows = [r for r in rows if r["aa"] is not None and r["aa"] >= min_aa]

    def league(r):
        return _league_key(r, axis)

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


def render(ds, category_name="Chores", effort=None, min_aa=None):
    """Rendered table lines for one category — batch-mode entry (ticket 12:
    --category picks; ticket 16 adds the effort override and AA-band filter
    that the TUI's `table` call shares)."""
    lines, _ = table(ds, category_name, effort, min_aa)
    return lines


def detail(ds, row, category_name):
    """Detail-view lines for one table row (ticket 16, spec §6): per-source
    raw grades and ranks, the PPI division (rating ÷ cost), list price,
    price tier, speed, frontier/dominated status, and the source-disagreement
    flag. The flag is set when the capability grades of the sources that
    rate this model at this effort disagree by ≥2 — the 09 prototype's rule:
    a grade gap that wide means the sources tell different stories, and
    disagreement is meaning, not noise to average away."""
    name, fixed, axis = next(c for c in CATEGORIES if c[0] == category_name)
    key, effort = row["key"], row["effort"]
    m = ds.models[key]
    out = [f"{m.name} {effort} — {m.provider}",
           f"{name} · effort {effort} · league: {AXIS_LABEL[axis]}", ""]

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
        pr = aa.raw.get("pricing") or {}
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
    return out
