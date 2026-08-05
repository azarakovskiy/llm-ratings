#!/usr/bin/env python3
"""PROTOTYPE — throwaway, the answer lives in ticket 09 (Ranking & output).

Question: what should the per-category ranking OUTPUT be?
Verdicts so far (user, 2026-08-05): shape D — league bands + advice columns,
per category, as an interactive TUI (category nav, capability filter, effort
override, Enter drill-down, Esc back). The chart experiment is DEAD — user:
"the chart looks absolutely terrible… the table should be structured to
communicate such data". This iteration moves the frontier/dominated/near-tie
message INTO the table:

  * frontier rows are marked * (no other configuration beats them on rating
    AND price — AA index vs cost/task, over every model × effort)
  * dominated rows carry an inline "→ pick instead" line (gain + saving)
  * ΔAA / Δ$ columns vs the row above make closeness visible: Luna shows
    +2.0 pts / +$0.02 over Flash, Opus +1.0 / +$0.75 over Sol — near-ties
    read off the ladder instead of hiding in band membership
  * layout (user-picked, V2): ★ frontier section first, then ✗ dominated
    with their arrows; effort shown per row next to the model name

Data is seeded from the user's AA screenshots (approximate read-offs):
Flash 69 @ $0.02, Luna 71 @ $0.042, Sol 77 @ $0.22, Opus 5 78 @ $1.3, ...
The PPI column is aa ÷ cost/task, matching the frontier's x.

Run:  python3 .scratch/llm-ratings/table-prototype.py
"""

import curses

# model → (provider, [(effort, aa index, cost USD/task, deepswe %), ...])
# aa/cost from the user's screenshots where read-off; deepswe from screenshot 3
# where listed, else invented; tb dropped from the prototype (no tb in the charts)
MODELS = {
    "DeepSeek V4 Flash": ("DeepSeek", [
        ("low", 45, 0.006, 42), ("medium", 54, 0.009, 48), ("high", 61, 0.012, 53),
        ("xhigh", 66, 0.016, 56), ("max", 69, 0.020, 59)]),
    "GPT-5.6 Luna": ("OpenAI", [
        ("low", 44, 0.021, 44), ("medium", 50.5, 0.019, 49), ("high", 63.5, 0.023, 55),
        ("xhigh", 68.5, 0.024, 58), ("max", 71, 0.042, 61)]),
    "GPT-5.6 Terra": ("OpenAI", [
        ("low", 45, 0.06, 41), ("medium", 65, 0.14, 47), ("high", 72, 0.24, 52),
        ("xhigh", 74, 0.30, 55), ("max", 76, 0.35, 58)]),
    "GPT-5.6 Sol": ("OpenAI", [
        ("low", 58, 0.10, 45), ("medium", 77, 0.22, 61), ("high", 77, 0.38, 64),
        ("xhigh", 77, 0.46, 66), ("max", 77, 0.55, 67)]),
    "GPT-5.5": ("OpenAI", [
        ("low", 43.5, 0.18, 40), ("medium", 50.5, 0.35, 53), ("high", 53, 0.60, 56),
        ("xhigh", 54.8, 0.85, 58)]),
    "Claude Opus 5": ("Anthropic", [("max", 78, 1.3, 73)]),
    "Claude Sonnet 5": ("Anthropic", [("max", 71, 1.1, 48)]),
    "Kimi K3": ("Moonshot", [("max", 71.5, 0.37, 69)]),
    "GLM-5.2": ("Zhipu", [("max", 68.5, 0.25, 35)]),
    "Grok 4.5": ("xAI", [("high", 72.5, 0.29, 49)]),
    "Muse Spark 1.1": ("Muse", [("xhigh", 74, 0.40, 66)]),
    "MiniMax-M3": ("MiniMax", [("medium", 58.5, 0.16, 45)]),
    "Qwen3.7 Max": ("Alibaba", [("max", 66, 1.25, 50)]),
    "Gemini 3.6 Flash": ("Google", [("max", 69, 0.70, 40)]),
    "Claude 4.5 Haiku": ("Anthropic", [("max", 44, 0.45, 30)]),
    "gpt-oss-120b": ("OpenAI", [("high", 30.5, 0.065, 25)]),
}

# speed tokens/s per model (fake-constant across efforts; AA median)
SPEED = {"DeepSeek V4 Flash": 310, "GPT-5.6 Luna": 145, "GPT-5.6 Terra": 220, "GPT-5.6 Sol": 180,
         "GPT-5.5": 160, "Claude Opus 5": 95, "Claude Sonnet 5": 120, "Kimi K3": 160,
         "GLM-5.2": 150, "Grok 4.5": 200, "Muse Spark 1.1": 170, "MiniMax-M3": 190,
         "Qwen3.7 Max": 130, "Gemini 3.6 Flash": 140, "Claude 4.5 Haiku": 210, "gpt-oss-120b": 260}

EFFORT_ORDER = ["low", "medium", "high", "xhigh", "max"]

# name, default effort, league axis ("price" 1=cheapest best | "capability"/"value" 5=best)
CATEGORIES = [
    ("Chores",     "low",    "price"),
    ("Everyday",   "medium", "value"),
    ("Deliberate", "high",   "capability"),
    ("Deep",       "max",    "capability"),
    ("Best Value", "high",   "value"),
]

FILTERS = [("all", None), ("cap = 5", lambda r: r["ag"][0] == 5), ("cap >= 4", lambda r: r["ag"][0] >= 4)]


def buckets(vals, ascending=False):
    """quintile buckets over distinct values: {value: (grade, rank, n)}, 1 = best; ties never split (08)."""
    order = sorted(set(vals), reverse=not ascending)
    n = len(order)
    return {v: ((order.index(v) * 5) // n + 1, order.index(v) + 1, n) for v in order}


def best5(tup):
    g, rank, n = tup
    return (6 - g, rank, n)


def build(name, effort, axis):
    rows = []
    for mname, (prov, pts) in MODELS.items():
        for e, ii, cost, dsw in pts:
            if e == effort:
                rows.append(dict(model=mname, provider=prov, dsw=dsw, ii=ii, cost=cost,
                                 ppi=ii / cost, spd=SPEED[mname], effort=effort))
    if not rows:
        return None
    ds, aa = buckets([r["dsw"] for r in rows]), buckets([r["ii"] for r in rows])
    ps = buckets([r["cost"] for r in rows], True)
    vs = buckets([r["ppi"] for r in rows])
    ss = buckets([r["spd"] for r in rows])
    for r in rows:
        r.update(dg=best5(ds[r["dsw"]]), ag=best5(aa[r["ii"]]), pg=ps[r["cost"]],
                 vg=best5(vs[r["ppi"]]), sg=best5(ss[r["spd"]]))
    return dict(name=name, effort=effort, axis=axis, rows=rows)


def band_of(row, axis):
    return {"price": lambda r: r["pg"][0], "capability": lambda r: r["ag"][0], "value": lambda r: r["vg"][0]}[axis](row)


def sort_key(row, axis):
    return {"price": lambda r: (r["cost"],), "capability": lambda r: (-r["ag"][0], -r["ii"]),
            "value": lambda r: (-r["vg"][0], -r["ppi"])}[axis](row)


# ---------------------------------------------------------------------------
# frontier / domination over every model × effort configuration (AA vs cost)
# ---------------------------------------------------------------------------

def all_points():
    """[(model, effort, cost, aa, dsw)] over every model x effort."""
    pts = []
    for name, (_, rows) in MODELS.items():
        for effort, ii, cost, dsw in rows:
            pts.append((name, effort, cost, ii, dsw))
    return pts


def pareto(pts):
    """upper envelope by AA: points with no other point at >= AA and <= cost."""
    by_cost = sorted(pts, key=lambda p: p[2])
    frontier, best = [], -1.0
    for p in by_cost:
        if p[3] > best:
            best = p[3]
            frontier.append(p)
    return frontier


ALL_PTS = all_points()
FRONTIER = {(m, e) for m, e, c, ii, dsw in pareto(ALL_PTS)}


def dominator_of(m, e, ii, c):
    """best strict replacement for config (m,e): same-effort first, else any effort;
    max AA gain, tie-break max saving. Same-effort keeps advice in the table's frame;
    the cross-effort fallback surfaces e.g. Sol max → Sol medium (equal rating)."""
    def best(cands):
        return max(cands, key=lambda t: (t[0], t[1])) if cands else None
    same = [(ii2 - ii, c - c2, m2, e2, ii2, c2)
            for (m2, e2, c2, ii2, dsw) in ALL_PTS
            if (m2, e2) != (m, e) and e2 == e and ii2 >= ii and c2 <= c and (ii2 > ii or c2 < c)]
    if same:
        return best(same)
    any_ = [(ii2 - ii, c - c2, m2, e2, ii2, c2)
            for (m2, e2, c2, ii2, dsw) in ALL_PTS
            if (m2, e2) != (m, e) and ii2 >= ii and c2 <= c and (ii2 > ii or c2 < c)]
    return best(any_)


DOMS = {}
for _m, _e, _c, _ii, _dsw in ALL_PTS:
    d = dominator_of(_m, _e, _ii, _c)
    if d:
        DOMS[(_m, _e)] = d


def adv_text(d):
    gain, saved, m, e, ii, c = d
    g = f"+{gain:g} pts" if gain else "same rating"
    return f"→ {m} {e}: {g}" + (f", save {fmt_money(saved)}" if saved > 0 else "")


def frontier_path():
    return "frontier: " + " → ".join(f"{m} {e} {ii:.0f} @ {fmt_money(c)}"
                                     for m, e, c, ii, dsw in pareto(ALL_PTS))


# ---------------------------------------------------------------------------
# table layouts
# ---------------------------------------------------------------------------

def fmt_money(v):
    if v >= 1000:
        return f"${v/1000:.2f}k"
    if v >= 1:
        return f"${v:.2f}"
    return f"${v:.3f}"


def fmt_delta(v):
    s = "-" if v < 0 else "+"
    a = abs(v)
    if a >= 1000:
        return f"{s}${a/1000:.2f}k"
    if a >= 1:
        return f"{s}${a:.2f}"
    return f"{s}${a:.3f}"


def fmt_ppi(v):
    return f"{v/1000:.1f}k" if v >= 1000 else f"{v:.0f}"


def fmt_row(r):
    return (f"{r['dg'][0]:>3} {r['ag'][0]:>3}  {r['model']:<17} {r['effort']:<6} "
            f"{r['provider']:<9} {fmt_money(r['cost']):>7} {r['d_aa']:>6} {r['d_cost']:>8} "
            f"{fmt_ppi(r['ppi']):>5} {r['spd']:>3}  {r['mark']}")


def add_deltas(rows):
    """Δ columns vs the row above in the visible sort order."""
    prev = None
    for r in rows:
        if prev is None:
            r["d_aa"], r["d_cost"] = "—", "—"
        else:
            r["d_aa"] = f"{r['ii'] - prev['ii']:+.1f}"
            r["d_cost"] = fmt_delta(r["cost"] - prev["cost"])
        prev = r


def table_lines(cat, filt):
    """V2 layout (user-picked): ★ frontier section, then ✗ dominated with pick-instead lines.
    Within each section, rows follow the category's league axis (price→cheapest first,
    capability→grade/AA desc, value→PPI desc) so the Δ columns read the league ladder."""
    rows = [r for r in cat["rows"] if not filt[1] or filt[1](r)]
    key = lambda r: sort_key(r, cat["axis"])
    frows = sorted((r for r in rows if (r["model"], r["effort"]) in FRONTIER), key=key)
    drows = sorted((r for r in rows if (r["model"], r["effort"]) not in FRONTIER), key=key)
    add_deltas(frows)
    add_deltas(drows)
    lines, selectable = [("text", frontier_path())], []
    lines.append(("sep", "★ frontier — nothing beats these on rating AND price"))
    for r in frows:
        r["mark"] = "*"
        lines.append(("row", r))
        selectable.append(len(lines) - 1)
    if drows:
        lines.append(("sep", "✗ dominated — take the arrow instead"))
        for r in drows:
            r["mark"] = ""
            lines.append(("row", r))
            selectable.append(len(lines) - 1)
            if (r["model"], r["effort"]) in DOMS:
                lines.append(("adv", "    " + adv_text(DOMS[(r["model"], r["effort"])])))
    return lines, selectable


def rank_text(tup):
    g, rank, n = tup
    return f"rank {rank} of {n} rated at this effort"


def detail_lines(cat, r):
    out = [
        f"{r['model']} {r['effort']} — {r['provider']}",
        f"{cat['name']} · effort {cat['effort']} · league: {cat['axis']}",
        f"band {cat['axis']} {band_of(r, cat['axis'])}",
        "",
        "source   grade  raw              why",
        f"DeepSWE  {r['dg'][0]}     {r['dsw']:>5.1f}% pass@1     {rank_text(r['dg'])}",
        f"AA       {r['ag'][0]}     {r['ii']:>5.1f} index       {rank_text(r['ag'])}",
        "",
        f"price    {fmt_money(r['cost'])}  AA cost/task, {cat['effort']} variant   price tier {r['pg'][0]} ({rank_text(r['pg']).replace('rated', 'priced')})",
        f"PPI      {fmt_ppi(r['ppi'])}  = {r['ii']:.1f} / {fmt_money(r['cost'])}       value grade {r['vg'][0]}",
        f"speed    {r['sg'][0]}     {r['spd']} t/s              {rank_text(r['sg'])}",
    ]
    key = (r["model"], r["effort"])
    if key in FRONTIER:
        out += ["", "frontier * — no other configuration beats this on rating and price"]
    elif key in DOMS:
        out += ["", f"dominated — {adv_text(DOMS[key])}"]
    if abs(r["dg"][0] - r["ag"][0]) >= 2:
        out += [
            "",
            f"sources disagree (DeepSWE {r['dg'][0]} vs AA {r['ag'][0]}): that's meaning, not noise —",
            "the sources measure different things (software tasks vs the II index).",
        ]
    return out


# ---------------------------------------------------------------------------
# TUI
# ---------------------------------------------------------------------------

COL_HEAD = f"{'DSW':>3} {'AA':>3}  {'Model':<17} {'Effort':<6} {'Provider':<9} {'$/task':>7} {'ΔAA':>6} {'Δ$':>8} {'PPI':>5} {'Spd':>3}"


def draw(stdscr, lines, header, footer, cursor=None):
    h, w = stdscr.getmaxyx()
    stdscr.erase()
    for i, txt in enumerate(header):
        if i < h:
            stdscr.addnstr(i, 0, txt, w - 1, curses.A_BOLD)
    y = len(header)
    for i, (kind, payload) in enumerate(lines):
        if y >= h - len(footer) - 1:
            break
        if kind == "sep":
            stdscr.addnstr(y, 0, "-" * 56 + f"  {payload}", w - 1)
        elif kind == "text":
            stdscr.addnstr(y, 0, payload, w - 1)
        elif kind == "adv":
            stdscr.addnstr(y, 0, payload, w - 1, curses.A_DIM)
        else:
            attr = curses.A_REVERSE if cursor is not None and i == cursor else 0
            stdscr.addnstr(y, 0, fmt_row(payload), w - 1, attr)
        y += 1
    for i, txt in enumerate(footer):
        if y + i < h:
            stdscr.addnstr(y + i, 0, txt, w - 1)
    stdscr.refresh()


def run(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    idx, cursor, filt = 0, 0, 0
    override = None          # effort override; None = category default (08)
    detail = None            # row being inspected
    while True:
        effort = override or CATEGORIES[idx][1]
        cat = build(CATEGORIES[idx][0], effort, CATEGORIES[idx][2])
        if detail is not None:
            lines = [("text", l) for l in detail_lines(cat, detail)]
            header = ["LLM RATINGS — detail", ""]
            footer = ["Esc back · ←/→ other category · q quit", ""]
            draw(stdscr, lines, header, footer)
            k = stdscr.getch()
            if k == ord("q"):
                return
            if k == 27:
                detail = None
            elif k in (curses.KEY_LEFT, curses.KEY_RIGHT):
                idx = (idx + (1 if k == curses.KEY_RIGHT else -1)) % len(CATEGORIES)
                detail = None; cursor = 0; override = None
            continue
        lines, selectable = table_lines(cat, FILTERS[filt])
        if cursor >= len(selectable):
            cursor = len(selectable) - 1
        eff_label = f"effort {effort}" + ("" if override is not None else " (default)")
        header = [f"LLM RATINGS — {cat['name']} · {eff_label} · league: {cat['axis']}", COL_HEAD, ""]
        footer = [f"filter: {FILTERS[filt][0]} · Δ = vs row above      "
                  f"←/→ or 1-5 category · ↑/↓ move · f filter · e effort · Enter detail · Esc/q quit", ""]
        draw(stdscr, lines, header, footer, cursor=selectable[cursor])
        k = stdscr.getch()
        if k in (27, ord("q")):
            return
        elif k == curses.KEY_LEFT:
            idx = (idx - 1) % len(CATEGORIES); cursor = 0; override = None
        elif k == curses.KEY_RIGHT:
            idx = (idx + 1) % len(CATEGORIES); cursor = 0; override = None
        elif ord("1") <= k <= ord("5"):
            idx = k - ord("1"); cursor = 0; override = None
        elif k == curses.KEY_UP:
            cursor = max(0, cursor - 1)
        elif k == curses.KEY_DOWN:
            cursor = min(len(selectable) - 1, cursor + 1)
        elif k == ord("f"):
            filt = (filt + 1) % len(FILTERS); cursor = 0
        elif k == ord("e"):
            if override is None:
                override = EFFORT_ORDER[0]
            else:
                i = EFFORT_ORDER.index(override) + 1
                override = EFFORT_ORDER[i] if i < len(EFFORT_ORDER) else None
            cursor = 0
        elif k in (10, 13, curses.KEY_ENTER):
            detail = lines[selectable[cursor]][1]


def main():
    print("Interactive TUI — ★ frontier / ✗ dominated sections. Esc/q quits.")
    curses.wrapper(run)


if __name__ == "__main__":
    main()
