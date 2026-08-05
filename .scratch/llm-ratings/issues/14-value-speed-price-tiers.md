# 14 Value, speed, price tiers

Type: task
Status: resolved
Blocked by: 11

## What to build

The two remaining tier axes plus the price tier, completing the three independent 1–5 grades per model, all recomputed per refresh:

- **value tier** — price-per-intelligence (source rating ÷ AA per-task cost of the category's effort variant), binned 1–5 over the PPI set, 5 = best. No AA price → no PPI, no value tier.
- **speed tier** — AA median output tokens/s at the category's effort variant, binned 1–5, 5 = best. Benchmark-run durations (DeepSWE duration/task, TB trial duration) are excluded — harness artifacts, not a speed axis.
- **price tier** — per-task cost, 1 = cheapest … 5 = most expensive, binned over the priced set.

Binning rules from the spec: quintiles over each axis's own valid set; equal values never split across bins (a small set can yield fewer than five populated tiers). The `Spd` column joins the table; price tier feeds the detail view in a later ticket.

## Acceptance criteria

- [ ] Value/speed/price tiers binned 1–5 over each axis's own valid set
- [ ] Small sets yield fewer than five populated tiers; equal values never split across bins
- [ ] Model with no AA price shows no value tier/PPI
- [ ] `Spd` column renders the speed tier; benchmark durations never enter the speed axis
- [ ] Tiers recompute from the data of the run (fixture change → tier change)

## Answer

Shipped in worktree `llm-ratings-t14`, branch `t14-value-speed-price`, commit `3bfde52` (worktree clean). `tier.py`'s `grades()` generalizes with `reverse=False` for the price axis (1 = cheapest … 5 = most expensive); equal values never split, small sets yield fewer than five populated tiers (unchanged core rule). `render.py`'s `category_rows` computes all three independent 1–5 grades per model over the category's own valid set: value = grade of the row's PPI (AA Intelligence Index ÷ AA per-task cost — the ticket-11 PPI column basis, single-source like the frontier), speed = grade of AA median output tokens/s, price = cost grade (feeds the later detail view); `Spd` column added to HEADER/`_fmt_row`, rendering `—` where a model has no AA row at the effort. Benchmark durations never enter the speed axis: `identity.py` maps only AA `median_output_tokens_per_second` into `Rating.speed` (DSW/TB rows carry `speed=None` — Terra renders Spd `—`).

Tests: 22/22 green (17 pre-existing + 5 new). Coverage: `Spd` renders 5/4/3/2/1 on the main fixture; equal speeds share a bin with only 2 of 5 tiers populated; adding one speed changes a bin (tiers recompute from run data); no AA price → PPI n/a while speed still grades. /code-review against 3d25727: 1 P3 standards smell fixed (hoisted shared test helpers); 1 P1 spec finding (value tier must use per-source PPI: DSW/TB ratings ÷ cost) — **rejected with documented reasoning**: ticket frames "three independent 1–5 grades per model" and "the PPI set" (singular), per-source PPI would yield up to three value grades per model and break the single-PPI-column table contract §6; spec §5 deliberately omits the "never blended" clause for value (it has it for capability); basis made explicit in a render.py comment. All five acceptance criteria met.
