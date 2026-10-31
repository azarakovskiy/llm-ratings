"""Strict Intelligence score/matching-task-cost comparison across efforts.

Only included models enter this advice universe. Independent source scores,
area indexes, timing and capability floors never enter its comparisons.
"""

import math

from .identity import EFFORTS


def aa_points(ratings):
    """Every finite Intelligence configuration with valid matching task cost."""
    return [(r.model_key, r.effort, r.cost, r.score) for r in ratings
            if r.source == "aa" and r.effort is not None
            and r.score is not None and math.isfinite(r.score)
            and r.cost is not None and math.isfinite(r.cost) and r.cost >= 0]


def pareto(pts):
    """Upper envelope by index, ordered by cost — the frontier path line.

    Equal score and cost do not strictly dominate each other: retain both.
    """
    by_cost = sorted(pts, key=lambda p: (p[2], -p[3], p[0], p[1]))
    frontier, best = [], -math.inf
    for p in by_cost:
        if p[3] > best or (frontier and p[3] == best and p[2] == frontier[-1][2]):
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


def alternatives(pts, score, cost):
    """Up to three strictly cheaper Intelligence points within five points."""
    candidates = [p for p in pts if p[2] < cost and p[3] >= score - 5]
    candidates.sort(key=lambda p: (p[2], -p[3], EFFORTS.index(p[1]), p[0]))
    return candidates[:3]
