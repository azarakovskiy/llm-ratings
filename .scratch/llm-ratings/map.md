# LLM Ratings: build-ready spec for the model-advice PoC

## Destination

A build-ready spec for a PoC CLI that prints per-category model ranking tables — model, rating, price, price-per-intelligence, tier — fed from public LLM benchmark sources (DeepSWE, Terminal-Bench v2.1, artificialanalysis.ai). The map is done when five decisions are locked: sources & acquisition, model identity & pricing, stereotypical categories, tiering, ranking & output. A build session then executes the spec.

## Notes

- Domain: model-selection advice. A "rating" is a published benchmark score; ratings change and models enter/leave the market, so the tables reflect the current moment. Build a CONTEXT.md glossary (domain-modeling) as terms resolve: model, provider, category, tier, rating, price-per-intelligence, effort.
- HITL tickets: grilling + domain-modeling. AFK tickets: research for source surveys, task for the final spec. The output-table shape was settled by /prototype iteration inside 09 (frontier sections, not static tables).
- Sources overlap but each adds unique coverage (05); a model may rate differently per source — disagreement is meaning for per-model per-tier semantics (07/08), not noise to average away.
- Interaction (09, supersedes the earlier static-tables lean): an interactive TUI — category nav, capability filter, effort override, Enter drill-down. The output table is structured around the frontier: ★ frontier section (AA vs $/task over every model × effort) then ✗ dominated rows with best-replacement arrows; ΔAA/Δ$ vs the row above carry near-ties. Chart renderings are out (user rejected).
- User's anchor example: DeepSeek Flash ≈ ChatGPT Luna 5.6 at high/extra-high effort (even Max) but far cheaper — yet for the best reasoning the expensive model still wins.

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance, then zoom the link for the detail the ticket holds -->
- [01 DeepSWE source survey](issues/01-deepswe-source-survey.md) — public static JSON at /artifacts/v1.1/leaderboard-live.json (no auth/API): 19 models × reasoning-effort configs (per-effort: yes, incl. max), pass@1+CI, cost/tokens/duration/steps; Apache-2.0 repo, gated HF tasks, training-canary; rolling updates as models drop.
- [02 Terminal-Bench v2 source survey](issues/02-terminal-bench-source-survey.md) — tbench.ai serves full scrapable HTML leaderboards (v2.0: 142 accuracy-only rows Oct'25–May'26; v2.1: 17 rows with per-effort max/high/xhigh + cost, May–Jul'26), v2.1 rows also as GitHub JSON submissions, Apache-2.0, no latency/throughput on any surface; pick v2.1 for per-effort ratings.
- [03 SWE-Atlas-QnA source survey](issues/03-swe-atlas-qna-source-survey.md) — Scale's open 124-task codebase-QnA dataset (Apache-2.0) + live leaderboard (Task Resolve Rate ±95% CI, ~21 models, HTML-scrape only, irregular updates); no per-effort split, no latency data.
- [04 Artificial Analysis source survey](issues/04-artificial-analysis-source-survey.md) — Free-key API (100 req/day) exposes Intelligence Index v4.1, median speed, in/out prices for ~591 models, effort variants as separate rows; Pro ($417/mo) adds blended pricing + percentiles; attribution required, redistribution bespoke.
- [05 Choose sources](issues/05-choose-sources.md) — ingest DeepSWE + Terminal-Bench v2.1 (GitHub JSONs) + Artificial Analysis free tier; SWE-Atlas-QnA dropped; live fetch per run, no caching; AA key in `LLM_RATINGS_AA_API_KEY` (user-held, verified valid), attribution line in output.
- [06 Model identity & pricing](issues/06-model-identity-and-pricing.md) — identity anchored to AA (stable UUID key, AA name as display, creator as provider; checked-in alias table maps DeepSWE/TB strings onto AA slugs); price = AA list per effort-variant, signal = 5 relative price tiers (1–5, recomputed per refresh), DeepSWE/TB run-costs excluded, per-provider pricing out of scope; tables include models rated by ≥1 chosen source (benchmark curation = usage proxy, no rating floor, open+closed both); all rating rows attach to the model, TB collapses to best agent per (model × effort) on display.
- [07 Stereotypical categories](issues/07-stereotypical-categories.md) — five use-case categories consolidated from OMP's 10 roles + 7 agents: Chores (cheap>>fast), Everyday (balanced), Deliberate (high reasoning, quality over price), Deep (max reasoning, price irrelevant), Best Value (intelligence per dollar); Vision is a capability tag, not a category.
- [08 Multi-dimensional tiers](issues/08-multidimensional-tiers.md) — three independent 1–5 grades per model (capability per source, value, speed), quintile-binned over per-axis valid sets, recomputed per refresh; category fixes the effort (Chores→low, Everyday→medium, Deliberate→high, Deep→max, Best Value→high); price-per-intelligence = source rating ÷ AA per-task cost at that effort.
- [09 Ranking & output](issues/09-ranking-and-output.md) — interactive TUI (category nav, ↑/↓, capability filter, effort override with reset-on-switch, Enter detail/Esc back); table = ★ frontier section (AA vs $/task over all model×effort, AA-only) + ✗ dominated section with best-replacement arrows (same-effort first); ΔAA/Δ$ vs row above for near-ties; effort shown per row; price = AA per-task cost in tables (list price in detail); DSW|AA|TB grade columns with `—` where TB v2.1 lacks the effort; freshness = fetch per run, no cache/snapshot/daemon.
- [10 Write the PoC spec](issues/10-write-poc-spec.md) — `.scratch/llm-ratings/spec.md` written, `ready-for-agent`; the destination artifact. All five decisions locked; the map is complete. Test seam (user-confirmed): fetch boundary — offline fixture mode tests the full CLI with no network. One open item for the build session: language (Python recommended).
- [11 Tracer bullet: fixture-fed pipeline end to end (Chores table)](issues/11-tracer-bullet-chores-table.md) — `llmratings/` package ships: fixture mode renders the Chores table per spec (★ frontier + ✗ dominated with same-effort-first arrows, ΔAA/Δ$, path line, per-source quintile grades, TB `—`), 14 CLI contract tests green. Deviations: model key = AA base slug (free API's UUID is per-effort-variant, not stable); fixture has 21 AA rows (GPT-5.5 has no max variant); Terra's AA rows deliberately excluded for the source-only span; model keyed by alias slug, source-only as `dsw:<name>`.
- [12 Five categories with league-axis sorts](issues/12-five-categories-league-sorts.md) — `--category` (Chores/Everyday/Deliberate/Deep/Best Value) replaces the hardcoded Chores view; each category fixes its effort (low/medium/high/max/high) and sorts ★/✗ sections by its league axis (price asc / PPI desc / capability desc); Δ columns read the ladder per category, `—` where a source lacks the effort, unknown name → exit 2. Shipped `227ff16` on `t12-five-categories` (worktree `llm-ratings-t12`), 22/22 tests green, reviewed.
- [13 Terminal-Bench v2.1 source with best-agent collapse](issues/13-terminal-bench-source.md) — TB v2.1 third source: agent×model rows collapse to best agent per (model × effort), recency tie-break; TB grade column at high/xhigh/max, `—` at low/medium; 11-submission synthesized fixture in survey shape; fetch failure names the source. Shipped `9c2c021` on `t13-terminal-bench` (worktree `llm-ratings-t13`), 27/27 tests green, reviewed. Note: tickets 12–14 landed as parallel branches off `3d25727` — merging needs conflict sequencing (all touch render.py/test_cli.py).
- [14 Value, speed, price tiers](issues/14-value-speed-price-tiers.md) — the three independent 1–5 grades per model: value (PPI = AA index ÷ AA cost, 5 = best), speed (AA median tok/s, 5 = best; benchmark durations excluded), price (1 = cheapest); quintile-binned per axis's own valid set, equal values never split, recomputed per refresh; `Spd` column joins the table. Shipped `3bfde52` on `t14-value-speed-price` (worktree `llm-ratings-t14`), 22/22 tests green, reviewed; P1 "per-source PPI" finding rejected — single-PPI-column contract §6 keeps AA-only basis.

## Not yet specified

<!-- fog: in-scope but not sharp enough to ticket; graduates as the frontier advances -->

- (none — the vision-tag sourcing fog was moot: 07 makes vision a capability tag, not a category, and 09's table has no vision column; cleared at 09's resolution.)



## Out of scope

<!-- work ruled beyond the destination; closed, never graduates -->

- Building the PoC itself — the destination is the spec; a build session executes it.
- Non-CLI surfaces (web UI, dashboards) — CLI tables per the charting decision.
- Integrating advice into OMP or any harness — the tool advises; it doesn't route.
- Running benchmarks or inference — consumes published ratings only.
- SWE-Atlas-QnA as a ratings source — ruled out in [05 Choose sources](issues/05-choose-sources.md); not part of the destination's source set.
- Provider-level pricing (OpenRouter vs direct) — ruled out in [06 Model identity & pricing](issues/06-model-identity-and-pricing.md): AA free tier carries none and adding a pricing source would redraw the decision-05 set; AA list price is the price.
