# 12 Five categories with league-axis sorts

Type: task
Status: resolved
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

## Answer

Shipped in worktree `llm-ratings-t12`, branch `t12-five-categories`, commit `227ff16` (worktree clean). `--category` flag (Chores / Everyday / Deliberate / Deep / Best Value) replaces the hardcoded Chores view; each category renders at its fixed effort (low/medium/high/max/high) and sorts both ★ frontier and ✗ dominated sections by its league axis (Chores → per-task cost asc, Everyday → PPI desc, Deliberate → AA capability desc, Deep → AA capability desc, Best Value → PPI desc) via `_league_key` in `llmratings/render.py`. Δ columns compute against the row above within each sorted section, so near-ties read as small numbers in every category; `—` where a source has no row at the effort (unchanged ticket-11 cell contract); unknown category → argparse "invalid choice" listing the five names, exit 2. Frontier membership, domination, arrows unchanged.

Tests: 22/22 green (`python3 -m unittest discover -s tests`), extended in the existing subprocess style with a `FiveCategories` class covering fixed-effort rendering, per-axis order across both sections, Δ-ladder values, `—`, and the unknown-category error. /code-review against 3d25727: 1 spec coverage gap (Δ-ladder asserted for 3/5 categories — fixed) and 3 standards smells fixed (implicit-else axis dispatch now explicit + ValueError, hoisted sort-key lambda, rewritten misleading comment); 2 harmless smells left with notes. All five acceptance criteria met and smoke-verified per category plus the error path.
