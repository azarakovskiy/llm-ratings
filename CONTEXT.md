# LLM Ratings — domain glossary

- **model** — a canonical AI model identity, anchored to an Artificial Analysis row: stable UUID as key, AA `name` as display name. Source strings (DeepSWE, Terminal-Bench) map onto it via an alias table.
- **provider** — the model's creator as listed by Artificial Analysis; a display/grouping attribute, not a pricing dimension.
- **rating** — a published benchmark score from a chosen source. A model carries one rating per (source × reasoning effort); Terminal-Bench rows are agent×model pairs and collapse to the best agent per (model × effort) for display.
- **reasoning effort** — the effort setting a rating was produced at (low … max); DeepSWE and AA both key ratings and prices per effort. Each category fixes an effort: Chores→low, Everyday→medium, Deliberate→high, Deep→max, Best Value→high.
- **price** — the money number in tables: Artificial Analysis's per-task cost of the model's effort variant (PPI denominator, frontier x, price-tier input — one consistent basis). AA list price per effort variant appears in the row detail view; no other price source is in scope.
- **frontier** — the recommendation set: a (model × effort) configuration whose AA index no other configuration beats at equal-or-lower per-task cost (Pareto upper envelope over every model × effort). Marked `*` in tables; the frontier path line shows the cross-effort ladder.
- **dominated** — a configuration with a strict replacement: some other configuration has ≥ rating at ≤ cost (one side strict). Tables annotate dominated rows with their best replacement ("→ X: +N pts, save $Y"; same-effort replacements preferred, cross-effort fallback — e.g. Sol max → Sol medium, same rating, save $0.33).
- **price tier** — a relative bucket of price, 1 = cheapest … 5 = most expensive, recomputed from the priced set on each refresh.
- **price-per-intelligence** — a source rating divided by Artificial Analysis's per-task cost at the category's effort; the value tier's raw number, per (model × source × category). No AA price → no PPI.
- **capability tier** — relative grade (1–5, 5 = best) of a model's rating within its source's rated set at a given effort; computed per source, never blended across sources.
- **value tier** — relative grade (1–5, 5 = best) of price-per-intelligence within its source's set at a given effort.
- **speed tier** — relative grade (1–5, 5 = best) of AA median output tokens/s at a given effort.
- **cost** — benchmark-run expenditure (DeepSWE's Modal cost, Terminal-Bench's per-run cost); a different basis from price, never mixed with it.
