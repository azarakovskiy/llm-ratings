"""Frontier and domination over AA configurations — the recommendation set.

The intelligence axis is AA's Intelligence Index only: mixing sources into the
envelope would let a model win on a metric it only leads on by noise (09).

Frontier = AA index vs $/task over every (model × effort) configuration: a
config is on the frontier when no other config has ≥ index at ≤ per-task cost
(one side strict). Dominated configs get their best strict replacement —
same-effort first, cross-effort fallback; maximize AA gain, tie-break maximize
saving (e.g. Sol max → Opus 5 high: same rating, save $0.01).
"""


def aa_points(ratings):
    """[(model_key, effort, cost, ii)] — every AA config with index and price."""
    return [(r.model_key, r.effort, r.cost, r.score) for r in ratings
            if r.source == "aa" and r.effort is not None
            and r.score is not None and r.cost is not None]


def pareto(pts):
    """Upper envelope by index, ordered by cost — the frontier path line.

    Equal-cost configs: higher index sorts first and dominates the lower
    (one side strict), so ties never both join the frontier.
    """
    by_cost = sorted(pts, key=lambda p: (p[2], -p[3]))
    frontier, best = [], -1.0
    for p in by_cost:
        if p[3] > best:
            best = p[3]
            frontier.append(p)
    return frontier


def frontier_set(pts):
    return {(m, e) for m, e, c, ii in pareto(pts)}


def dominator(pts, key, effort, ii, cost):
    """Best strict replacement for config (key, effort):
    (gain, saved, model_key, effort, ii, cost), or None when undominated.
    Same-effort candidates first — advice stays in the table's frame; the
    cross-effort fallback surfaces strictly-better tradeoffs at other efforts.
    """
    def best(cands):
        return max(cands, key=lambda t: (t[0], t[1])) if cands else None

    def cands(same_effort):
        for m2, e2, c2, ii2 in pts:
            if (m2, e2) == (key, effort):
                continue
            if same_effort and e2 != effort:
                continue
            if ii2 >= ii and c2 <= cost and (ii2 > ii or c2 < cost):
                yield (ii2 - ii, cost - c2, m2, e2, ii2, c2)

    return best(list(cands(True))) or best(list(cands(False)))
