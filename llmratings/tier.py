"""1–5 capability grades, quintile-binned over each source's own rated set at
an effort. 5 = best. Equal values never split across bins, so a small set can
yield fewer than five populated grades (spec §5, ticket 14 tests this on
small sets)."""


def grades(values):
    """{value: grade} over distinct values; ties share a bin."""
    order = sorted(set(values), reverse=True)
    n = len(order)
    return {v: 6 - ((i * 5) // n + 1) for i, v in enumerate(order)}
