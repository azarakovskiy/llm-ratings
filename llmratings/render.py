"""Category table rendering (tickets 11–13).

One category at its fixed effort, sorted by the category's league axis so the
Δ columns read the ladder: ★ frontier section first, then ✗ dominated rows
each annotated with its best replacement arrow. Frontier path line across
efforts at the top. DSW/AA/TB grade columns are per-source quintiles at that
effort; the TB column grades TB's best-agent-collapsed ratings and shows `—`
at efforts v2.1 doesn't cover (low/medium).
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

_AXIS_LABEL = {"price": "cheapest first", "value": "best PPI first",
               "capability": "best capability first"}

HEADER = (f"{'DSW':>3} {'AA':>3} {'TB':>3}  {'Model':<17} {'Effort':<6} "
          f"{'Provider':<9} {'$/task':>7} {'ΔAA':>6} {'Δ$':>8} {'PPI':>5}  {'*':>1}")

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
            f"{cost:>7} {r['d_aa']:>6} {r['d_cost']:>8} {ppi:>5}  {r['mark']}")


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
        rows.append(dict(
            model=m.name, effort=effort, provider=m.provider,
            dsw=dsw_g.get(dsw.score) if dsw and dsw.score is not None else None,
            aa=aa_g.get(aa.score) if aa and aa.score is not None else None,
            tb=tb_g.get(tb.score) if tb and tb.score is not None else None,
            cost=cost, ii=ii,
            ppi=(ii / cost) if (ii is not None and cost is not None) else None,
            frontier=(key, effort) in fr,
            dom=doms.get((key, effort)),
        ))
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


def render(ds, category_name="Chores"):
    """Rendered table lines for one category (ticket 12: --category picks)."""
    name, effort, axis = next(c for c in CATEGORIES if c[0] == category_name)
    pts = _pts(ds)

    path = " → ".join(f"{ds.models[m].name} {e} {ii:.0f} @ {fmt_money(c)}"
                      for m, e, c, ii in pareto(pts))
    lines = [f"{name} — {effort} effort — {_AXIS_LABEL[axis]}", "",
             "frontier: " + path, "", HEADER]

    rows = category_rows(ds, (name, effort, axis))

    def league(r):
        return _league_key(r, axis)

    frows = sorted((r for r in rows if r["frontier"]), key=league)
    drows = sorted((r for r in rows if not r["frontier"]), key=league)
    _add_deltas(frows)
    _add_deltas(drows)

    lines.append("★ frontier — nothing beats these on rating AND price")
    for r in frows:
        r["mark"] = "*"
        lines.append(_fmt_row(r))
    lines.append("✗ dominated — take the arrow instead")
    for r in drows:
        r["mark"] = ""
        lines.append(_fmt_row(r))
        if r["dom"]:
            lines.append("    " + arrow_text(r["dom"], ds))
    return lines
