# 12 Five categories with league-axis sorts

Type: task
Status: ready-for-agent
Blocked by: 11

## What to build

All five use-case categories selectable and each ranked on its own axis. A `--category` flag (Chores / Everyday / Deliberate / Deep / Best Value) replaces the hardcoded Chores view. Each category fixes its reasoning effort — Chores→low, Everyday→medium, Deliberate→high, Deep→max, Best Value→high — and sorts both table sections by its league axis so the Δ columns read the ladder:

- Chores → per-task cost ascending (cheapest first)
- Everyday → PPI descending
- Deliberate → capability grade (AA) descending
- Deep → capability grade (AA) descending
- Best Value → PPI descending

Sources without a row at a category's effort show `—` (TB at low/medium), already handled by the 11 column contract. Frontier membership, domination, and arrows are unchanged — only the selected effort and sort order differ per category.

## Acceptance criteria

- [ ] `--category` accepts all five names; each renders at its fixed effort
- [ ] Sort order correct per category league axis (cheapest / PPI desc / capability desc)
- [ ] Δ columns read the ladder in every category (near-ties visible as small numbers)
- [ ] `—` where a source has no row at the category's effort
- [ ] Unknown category name → clear error, nonzero exit
