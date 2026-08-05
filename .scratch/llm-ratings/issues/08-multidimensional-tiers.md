# 08 Multi-dimensional tiers

Type: grilling
Blocked by: 07
Status: resolved

## Question

How is tiering computed — multi-dimensional (capability tier vs value tier vs speed), from data, recomputed per refresh so models move as ratings change? What exactly is "price-per-intelligence" per category, and where does the reasoning-effort axis sit?

## Answer

Grilled 2026-08-05, six decisions:

**1. Tier shape — three independent grades.** Each model carries capability, value, and speed tiers, each a 1–5 relative grade recomputed per refresh (models move as ratings/prices change). Which grade ranks a category's table is 09's call, not 08's.

**2. Effort axis — the category fixes the effort.** Chores→low, Everyday→medium, Deliberate→high, Deep→max, Best Value→high. A category's ratings, prices, and tiers are all computed at that effort, mapped onto each source's scale: DeepSWE low/medium/high/xhigh/max; TB v2.1 only has high/xhigh/max rows (so Chores/Everyday are fed by DeepSWE + AA); AA effort variants are separate rows.

**3. Capability — per-source grades.** Capability tier = that source's rating at the category's effort, quintile-binned relative to the models that source rates at that effort. Never blended across sources: DeepSWE-A vs TB-C is meaning (05/07), not noise to average.

**4. Price-per-intelligence.** Per (model × source × category) = source rating ÷ AA per-task cost of the category's effort variant. Value tier = its 1–5 bin. No AA price → no PPI and no value tier (06's rule). AA's per-task cost is the same denominator for every source, keeping within-source PPI comparisons valid; the number is tied to AA's task definition (note for 10).

**5. Binning — quintiles.** Each axis bins 1–5 over its own valid set: price over the priced set (per 06); capability over the source's rated set at that effort; value over the PPI set; speed over models with an AA speed row. Equal values never split across bins, so a small set can yield fewer than five populated tiers. Bins recomputed every run. Direction: capability/value/speed 5 = best; price keeps 06's 1 = cheapest.

**6. Speed — AA median output tokens/s** at the category's effort variant, binned 1–5. Benchmark-run durations (DeepSWE duration/task, TB trial duration) are excluded — harness artifacts, not a speed axis.
