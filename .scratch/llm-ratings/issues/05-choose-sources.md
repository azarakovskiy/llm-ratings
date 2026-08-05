# 05 Choose sources

Type: grilling
Blocked by: 01, 02, 03, 04
Status: resolved

## Question

Given the four source surveys (01–04), which sources does the PoC ingest, and how (API key, CSV snapshot, scrape)? The answer records the decision plus the acquisition facts later tickets depend on: URLs, key location, row counts, expected update cadence.

## Answer

**Decision:** ingest DeepSWE (v1.1 live JSON) + Terminal-Bench v2.1 (GitHub submission JSONs) + Artificial Analysis (free-tier API). SWE-Atlas-QnA dropped. Rationale: the three sources share some data but each carries unique coverage; a model may rate differently per source, and that disagreement is information (different meaning per model per tier — feeds 07/08), not noise to average away.

**Acquisition facts (all verified 2026-08-05):**

- **DeepSWE** — `GET https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`, no auth. 51 rows (19 models × reasoning-effort configs incl. max), 113 tasks; `generated_at` 2026-08-04T01:34Z. Rolling, event-driven updates as frontier models land.
- **Terminal-Bench v2.1** — enumerate `GET https://api.github.com/repos/harbor-framework/terminal-bench-2-1/contents/leaderboard/submissions` (unauthenticated GitHub API; 21 entries incl. .gitkeep → 20 submission JSONs), then fetch each via `raw.githubusercontent.com`. Files named `<date>-<org>-<model>-<effort>-<agent>.json`; each carries accuracy ± CI, effort, cost USD, avg trial duration, token counts. Apache-2.0. Event-driven: one row per merged submission PR.
- **Artificial Analysis** — `GET https://artificialanalysis.ai/api/v2/language/models/free?page_size=200` with `x-api-key` header; free tier, 100 req/day, page_size capped at 200 → 3 pages ≈ 591 models (verified: key valid, `tier: free`, II v4.1). Per-row: stable UUID `id`, slug, name, creator, release date, II score + version, median speed/TTFT, in/out prices, cost per II task. Continuous updates (multiple evaluations/week). **Key location:** env var `LLM_RATINGS_AA_API_KEY`, user-held, never stored in the repo. **Attribution required on all tiers** — CLI output carries a visible attribution line; consume via API only, never scrape (ToS).

**Posture:** live fetch per run — no vendored snapshot, no caching in v1. Missing AA key → clear setup error and exit (AA is the price/speed anchor; silent degradation would produce broken tables).

**Notes for later tickets:** AA pricing is list prices; DeepSWE cost/task is Datacurve's measured Modal pricing, TB cost is per-run — don't mix as if same basis (06). Model identity join across sources is ticket 06's problem (AA stable `id`/`slug` vs source model strings).
