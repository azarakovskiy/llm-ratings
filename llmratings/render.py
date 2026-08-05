"""Chores table rendering (tickets 11 + 14).

One category at its fixed effort, sorted by the category's league axis so the
Δ columns read the ladder: ★ frontier section first, then ✗ dominated rows
each annotated with its best replacement arrow. Frontier path line across
efforts at the top. TB column renders — until ticket 13 wires the source.
Ticket 14: the Spd column renders the speed tier; each row also carries the
value tier (PPI grade) and price tier (cost grade) for the detail view.
"""

from .rank import aa_points, dominator, frontier_set, pareto
from .tier import grades

# (name, fixed effort, league axis) — axes: "price" (cheapest best) |
# "value"/"capability" (5 = best). All five are locked by 07; tickets 12/14
# generalize the sort and add the tier columns.
CATEGORIES = [
    ("Chores", "low", "price"),
    ("Everyday", "medium", "value"),
    ("Deliberate", "high", "capability"),
    ("Deep", "max", "capability"),
    ("Best Value", "high", "value"),
]

_AXIS_LABEL = {"price": "cheapest first"}

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
    return (f"{_cell(r['dsw'], 3)} {_cell(r['aa'], 3)} {'—':>3}  "
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
    dsw_g = grades([r.score for r in ds.ratings
                    if r.source == "deepswe" and r.effort == effort and r.score is not None])
    aa_g = grades([r.score for r in ds.ratings
                   if r.source == "aa" and r.effort == effort and r.score is not None])

    rows = []
    for key in sorted(included & rated_at_effort):
        m = ds.models[key]
        dsw = next((r for r in ds.ratings
                    if r.source == "deepswe" and r.model_key == key and r.effort == effort), None)
        aa = next((r for r in ds.ratings
                   if r.source == "aa" and r.model_key == key and r.effort == effort), None)
        ii = aa.score if aa else None
        cost = aa.cost if aa else None
        speed = aa.speed if aa else None
        rows.append(dict(
            model=m.name, effort=effort, provider=m.provider,
            dsw=dsw_g.get(dsw.score) if dsw and dsw.score is not None else None,
            aa=aa_g.get(aa.score) if aa and aa.score is not None else None,
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


def _league_key(r):
    """Chores axis: per-task cost ascending; unpriced rows sort last."""
    c = r["cost"]
    return (c is None, c if c is not None else float("inf"))


def render(ds, category_name="Chores"):
    """Rendered table lines for one category (ticket 11: Chores)."""
    name, effort, axis = next(c for c in CATEGORIES if c[0] == category_name)
    pts = _pts(ds)

    path = " → ".join(f"{ds.models[m].name} {e} {ii:.0f} @ {fmt_money(c)}"
                      for m, e, c, ii in pareto(pts))
    lines = [f"{name} — {effort} effort — {_AXIS_LABEL[axis]}", "",
             "frontier: " + path, "", HEADER]

    rows = category_rows(ds, (name, effort, axis))
    frows = sorted((r for r in rows if r["frontier"]), key=_league_key)
    drows = sorted((r for r in rows if not r["frontier"]), key=_league_key)
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
