# 14 Value, speed, price tiers

Type: task
Status: ready-for-agent
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
