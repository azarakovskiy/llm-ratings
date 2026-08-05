# LLM Ratings PoC — build-ready spec

Status: ready-for-agent

## Problem Statement

Picking an LLM for a task means weighing dozens of models against each other — benchmark ratings, prices, and reasoning-effort behavior all published on separate sites, in different units, by different organizations. The market moves weekly: ratings update, models enter and leave, prices change. Today there is no quick way to ask "what is the current best cheap model for chores, or the best reasoning per dollar at high effort" and get one ranked answer built from the same data moment. The user's anchor example: DeepSeek Flash ≈ ChatGPT Luna 5.6 at high/extra-high effort (even at max) but far cheaper — yet for the best reasoning the expensive model still wins. The tool must surface exactly that tradeoff, from current published data, without the user opening five leaderboards.

## Solution

A CLI you run whenever you want advice. On each run it fetches the current ratings and prices from three public sources — DeepSWE, Terminal-Bench v2.1, Artificial Analysis — joins them onto canonical model identities, and drops you into an interactive terminal UI. You pick a use-case category (Chores, Everyday, Deliberate, Deep, Best Value); the table ranks models at that category's reasoning effort, structured around the frontier — the configurations nothing beats on intelligence at equal-or-lower price — with dominated rows annotated by their best replacement. Ratings, prices, and tiers are all recomputed from the data fetched on that run: the answer is as current as the sources. A line in the output attributes Artificial Analysis as required by their terms.

## User Stories

1. As a CLI user, I want to run one command and get the current LLM market, so that I don't have to visit multiple leaderboards.
2. As a CLI user, I want the tool to fetch fresh data on every run, so that my advice reflects the current moment rather than a stale snapshot.
3. As a CLI user, I want a clear setup error when the Artificial Analysis API key is missing, so that I never get silently broken tables.
4. As a CLI user, I want five use-case categories to choose from, so that I can frame my question as "cheap, balanced, deliberate, deep, or best value".
5. As a CLI user, I want to navigate categories with ←/→ or 1–5, so that switching context takes one keystroke.
6. As a CLI user, I want each category to fix the reasoning effort, so that the table compares models on the effort I'd actually use them at (Chores→low, Everyday→medium, Deliberate→high, Deep→max, Best Value→high).
7. As a CLI user, I want a ★ frontier section at the top of the table, so that the recommendations nothing beats on intelligence at equal-or-lower per-task cost are the first thing I see.
8. As a CLI user, I want a ✗ dominated section below the frontier, so that I can see the also-rans and why they lose.
9. As a CLI user, I want every dominated row annotated with its best replacement ("→ Sol medium: same rating, save $0.33"), so that I know exactly what to buy instead.
10. As a CLI user, I want same-effort replacements preferred, so that advice stays in the table's frame before it jumps efforts.
11. As a CLI user, I want cross-effort replacement fallback, so that a strictly-better tradeoff at another effort is surfaced even when no same-effort replacement exists.
12. As a CLI user, I want a frontier path line across efforts at the top, so that I can see the cross-effort ladder (Flash low → … → Opus 5) in one glance.
13. As a CLI user, I want to see per-source benchmark grades (DeepSWE, AA, Terminal-Bench) as columns, so that I can see where a model leads and where it lags instead of one blended number.
14. As a CLI user, I want a `—` where a source has no row at this effort, so that the table doesn't fake a grade.
15. As a CLI user, I want the per-task cost as the price column, so that the price, the intelligence-per-dollar, and the frontier axis all use one consistent number.
16. As a CLI user, I want ΔAA and Δ$ columns against the row above, so that near-ties read as small numbers (Luna 0.5 pts from Kimi) rather than hidden closeness.
17. As a CLI user, I want each row to show its effort, so that I can tell which configuration a row represents when efforts mix.
18. As a CLI user, I want the effort override key `e`, so that I can see the same category at a different reasoning effort.
19. As a CLI user, I want the effort override to reset when I switch categories, so that I never carry a stale effort into a different context.
20. As a CLI user, I want the capability filter key `f` (all → cap 5 → cap ≥4), so that I can cut the table to the top capability bands.
21. As a CLI user, I want ↑/↓ navigation, so that I can move through rows without a mouse.
22. As a CLI user, I want Enter on a row to open a detail view, so that I can see why this rating and why this band.
23. As a CLI user, I want the detail view to show per-source raw grades and ranks, the PPI division, list price, price tier, speed, and frontier/dominated status, so that I can audit any recommendation.
24. As a CLI user, I want a source-disagreement flag in the detail view, so that I know when sources tell different stories about a model.
25. As a CLI user, I want Esc to go back and q to quit, so that navigation never traps me.
26. As a CLI user, I want an attribution line in the output, so that the tool honors Artificial Analysis's terms.
27. As a CLI user, I want price tiers (1–5, 1 = cheapest) recomputed per run, so that "cheap vs expensive" reflects the current priced set.
28. As a CLI user, I want capability, value, and speed tiers per model, so that I can judge a model on three independent axes instead of one blended grade.
29. As a CLI user, I want models with no Artificial Analysis price shown as price n/a, so that the table never invents a price.
30. As a CLI user, I want open- and closed-weight models both included, so that the advice matches the whole market.
31. As a CLI user, I want a model included as long as a chosen source rates it, so that benchmark curation — not a rating floor — decides who shows up.
32. As a CLI user, I want Terminal-Bench rows collapsed to the best agent per (model × effort), so that an agent-vs-agent leaderboard reads as a model table.
33. As a CLI user, I want the tables to stay current as models enter and leave, so that a new frontier model appears without me changing anything.

## Implementation Decisions

### 1. Runtime and shape

- A single interactive CLI program. Language not charted by the map; **recommend Python** — the 09 table prototype is Python, all three sources are HTTP+JSON, and a TUI is one mature dependency (textual, or plain ANSI if the build session prefers zero deps). Build session confirms before starting; this is the only open implementation choice.
- Modules, one per seam: `fetch` (sources → normalized rows), `identity` (alias join), `tier` (bins), `rank` (frontier/domination), `render` (TUI). The spec below fixes the contracts between them.

### 2. Sources & acquisition

- Ingest exactly three sources; each fetched live on every run — no vendored snapshot, no cache, no daemon.
- **DeepSWE v1.1** — `GET https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`, no auth. Rows are model × reasoning-effort configurations (low…max incl. max): rating (pass@1 + CI), cost/task, tokens, duration, task count. Rolling, event-driven updates.
- **Terminal-Bench v2.1** — enumerate `GET https://api.github.com/repos/harbor-framework/terminal-bench-2-1/contents/leaderboard/submissions` (unauthenticated GitHub API), then fetch each entry's JSON via `raw.githubusercontent.com`; files named `<date>-<org>-<model>-<effort>-<agent>.json`, each carrying accuracy ± CI, effort, cost USD, avg trial duration, token counts. Apache-2.0. v2.1 offers only high/xhigh/max efforts. Rows are agent × model pairs.
- **Artificial Analysis** — `GET https://artificialanalysis.ai/api/v2/language/models/free?page_size=200` with `x-api-key` header; paginate (page_size capped at 200, ~591 models → 3 pages). Per-row: stable UUID `id`, slug, name, creator, release date, Intelligence Index (score + version), median output tokens/s, in/out list prices, per-task cost. Free tier: 100 req/day — ample at a few runs/day. API only, never scrape (ToS). Attribution required on all tiers.
- **Key location:** env var `LLM_RATINGS_AA_API_KEY`, user-held, never in the repo. Missing key → clear setup error and nonzero exit before any output.
- **Fetch failure contract:** any source fetch failure → clear error naming the source and nonzero exit. No silent partial tables.
- **Attribution:** a visible attribution line in every run's output (AA requirement).

### 3. Identity and data model

- **Canonical model = an Artificial Analysis row**: stable UUID as key, AA `name` as display name, AA `creator` as provider. Source strings from DeepSWE/TB map onto AA rows via a checked-in alias table — normalized source string → AA slug, ~25–30 models at PoC scale, seeded once. A rated model with no AA row keeps a source-only identity: no price, no price tier, no PPI/value/speed grades, effectively absent from ranked tables.
- **Inclusion rule:** a model appears iff it has ≥1 rating row from DeepSWE or Terminal-Bench v2.1. No numeric rating floor; open- and closed-weight both. AA's long tail of unrated models never enters tables.
- **Rating rows attach wholesale** to the canonical model — nothing discarded. A row carries (source, effort, score, CI, agent where TB). Tables display one rating per (model × source × effort): TB collapses its agent × model rows to the best-scoring agent per (model × effort), ties broken by recency; DeepSWE and AA need no collapse.
- **Price rows** carry AA list in/out USD per effort variant, plus AA per-task cost per effort variant.
- Per-source ratings disagreeing is meaning, not noise — never average sources together.

### 4. Categories

- Five use-case categories, each a stereotype profile that fixes the reasoning effort:

```
Chores     cheap >> fast; minimal reasoning; quality floor only   → low effort
Everyday   balanced on all four                                   → medium
Deliberate high reasoning; quality over price; speed flexible     → high
Deep       max reasoning; best quality wins; price/speed irrelevant → max
Best Value best intelligence per dollar at high effort            → high
```

- **Vision is a capability tag, not a category** — it filters models, never ranks them. No vision column in the v1 table.
- Effort maps onto each source's scale: DeepSWE low/medium/high/xhigh/max; TB v2.1 high/xhigh/max only (so Chores/Everyday are fed by DeepSWE + AA, and TB shows `—` at those efforts); AA effort variants are separate rows.

### 5. Tiering (from the 08 prototype's shape)

- Three **independent** 1–5 grades per model, recomputed per refresh (models move as ratings/prices change):
  - **capability tier** — that source's rating at the category's effort, quintile-binned relative to the models that source rates at that effort. Per source, never blended across sources. 5 = best.
  - **value tier** — price-per-intelligence, binned 1–5 over the PPI set. 5 = best.
  - **speed tier** — AA median output tokens/s at the category's effort variant, binned 1–5. 5 = best. Benchmark-run durations (DeepSWE duration/task, TB trial duration) are excluded — harness artifacts, not a speed axis.
  - **price tier** — relative bucket of per-task cost, 1 = cheapest … 5 = most expensive, binned over the priced set.
- **Binning:** quintiles over each axis's own valid set; equal values never split across bins, so a small set can yield fewer than five populated tiers. Bins recomputed every run.
- **price-per-intelligence (PPI)** per (model × source × category) = source rating ÷ AA per-task cost of the category's effort variant. AA's per-task cost is the same denominator for every source, keeping within-source PPI comparisons valid. No AA price → no PPI, no value tier. The number is tied to AA's task definition — it's AA's benchmark task, not a universal unit.

### 6. Ranking and output (from the 09 prototype; the table structure IS the recommendation)

- **Frontier** = AA Intelligence Index vs $/task over every (model × effort) configuration, AA-only: a configuration is on the frontier when no other configuration has ≥ AA index at ≤ per-task cost (one side strict). One intelligence axis — mixing sources into the envelope would let a model win on a metric it only leads on by noise. Marked `*`.
- **Domination:** each non-frontier row gets its best strict replacement — same-effort first, cross-effort fallback (surfaces e.g. Sol max → Sol medium: same rating, save $0.33); maximize AA gain, tie-break maximize saving. Annotated on the row ("→ X: +N pts, save $Y").
- **Table layout per category** (at the category's effort):
  1. Frontier path line — the cross-effort ladder of frontier configurations (Flash low → … → Opus 5).
  2. `★ frontier` section — frontier configurations, sorted by the category's league axis.
  3. `✗ dominated` section — every remaining row with its replacement arrow.
- **Sort within sections** by the category's league axis so the Δ columns read the ladder: Chores → cheapest first; Everyday → PPI desc; Deliberate → capability grade / AA desc; Deep → capability grade / AA desc; Best Value → PPI desc.
- **Columns:** `DSW | AA | TB | Model | Effort | Provider | $/task | ΔAA | Δ$ | PPI | Spd | *`
  - DSW/AA/TB = per-source capability grades (1–5), `—` where the source has no row at this effort (TB at low/medium).
  - $/task = AA per-task cost of the row's effort variant — the PPI denominator, the frontier x, the Δ$ base, the price-tier input, one consistent basis. List price per effort variant appears in the detail view only.
  - ΔAA / Δ$ vs the row above within the section — near-ties read off the ladder; no closeness threshold or marker.
  - Effort per row, so mixed-effort comparisons stay legible.
- **Interactive TUI contract:**
  - Category nav ←/→ or 1–5; row nav ↑/↓; `f` capability filter cycling all → cap=5 → cap≥4 (banding key = AA grade); `e` effort override cycling low→medium→high→xhigh→max→default, **reset on category switch**; Enter drill-down; Esc back; q quit.
- **Detail view (Enter):** per-source raw grades + ranks, PPI division (rating ÷ cost), list price, price tier, speed, frontier/dominated status, source-disagreement flag.
- **Freshness:** fetch on every run. Ratings move weekly and models enter/leave, so snapshots go stale and a scheduler is a daemon the CLI doesn't need. `--snapshot` is a noted possible later add if the free-tier quota ever bites; not in v1.
- Chart renderings are out — the user rejected charts; the frontier/dominated/near-tie message is structural to the table.

### 7. Test seam (user-confirmed)

- Single seam at the **fetch boundary**: the CLI accepts an offline fixture mode that serves saved source responses (DeepSWE live JSON, TB submission JSONs, AA pages) instead of HTTP — no network in tests. Everything below the seam (identity join, tiering, ranking, rendering) is exercised end-to-end through the real CLI.

## Testing Decisions

- **What makes a good test:** observable external behavior only — rendered table content, TUI state transitions, exit codes. Not internal functions, not implementation details.
- **What is tested:** the whole CLI through the fixture seam. Representative scenarios: frontier membership and `*` markers; domination arrows (same-effort preferred over cross-effort; arrow text "+N pts, save $Y"); ΔAA/Δ$ values and sort order per category; effort override cycle and reset-on-category-switch; capability filter states; TB `—` at low/medium efforts; best-agent collapse; price-tier/PPI/speed binning on small sets (fewer than five populated tiers); missing-AA-key error and nonzero exit; attribution line present; source-fetch-failure error path.
- **Fixture strategy:** saved copies of the real source payloads (a small curated subset is fine — e.g. ~6 models spanning frontier/dominated, open/closed, with and without AA rows), plus hand-built edge fixtures (ties, no-AA-price models, empty sets). Fixtures live under the feature's scratch dir.
- **Prior art:** greenfield — no existing tests in this repo. The 09 table prototype (`.scratch/llm-ratings/table-prototype.py`) is the manual precursor the fixture scenarios are derived from.

## Out of Scope

- Non-CLI surfaces — web UI, dashboards (chart renderings explicitly rejected by the user).
- Integrating advice into OMP or any harness — the tool advises; it doesn't route.
- Running benchmarks or inference — consumes published ratings only.
- SWE-Atlas-QnA as a ratings source.
- Provider-level pricing (OpenRouter vs direct) — AA list price is the price; AA per-task cost is the table price.
- Snapshotting, caching, or scheduled refresh (`--snapshot` noted, not built).
- Vision as a category, or any vision column.
- DeepSWE/TB run costs in pricing — benchmark-run expenditure on a different basis, never mixed into the price column.
- Rating floors, license filtering, or any inclusion rule beyond "≥1 rating from a chosen source".

## Further Notes

- Language recommendation (Python) is the build session's to-confirm; everything else in this spec is locked by tickets 05–09.
- AA per-task cost is tied to AA's task definition — comparisons are within-source and within-moment, which is exactly the PoC's claim.
- Alias table (~25–30 models) is seeded once from the current DeepSWE/TB model strings and checked in; a model that later appears in a source without an alias degrades to source-only identity rather than blocking the run.
- AA key: env var `LLM_RATINGS_AA_API_KEY`, user-held. Attribution line required in every run.
- Ratings, prices, and tiers are relative to the current data moment — tables change as sources update; that is the feature, not a bug.
