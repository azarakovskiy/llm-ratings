"""1–5 grades, quintile-binned over an axis's own valid set of values.
Equal values never split across bins, so a small set can yield fewer than
five populated grades (spec §5, ticket 14 tests this on small sets)."""


def grades(values, reverse=True):
    """{value: 1–5} over distinct values; ties share a bin.

    reverse=True  -> 5 = best (capability, value, speed axes).
    reverse=False -> 1 = cheapest … 5 = most expensive (price axis).
    """
    order = sorted(set(values), reverse=reverse)
    n = len(order)
    if reverse:
        return {v: 6 - ((i * 5) // n + 1) for i, v in enumerate(order)}
    return {v: (i * 5) // n + 1 for i, v in enumerate(order)}
