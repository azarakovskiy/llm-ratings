# Fixtures — main and runtime source contract (tickets 11–18, 34)

Saved copies of the real source payloads, curated to a small subset, served
by the CLI's `--fixtures` mode (the spec's user-confirmed test seam: no
network below the fetch boundary).

These are historical test payloads, not current market measurements. The
recorded snapshot date and Intelligence Index version describe the saved
evidence only. The model set includes fictional names, and the Terminal-Bench
and OpenRouter rows are synthetic; missing creators are not coverage claims.

## Provenance

Fetched live 2026-08-05:

- `deepswe.json` — `https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`
  (no auth; `generated_at` 2026-08-04T01:34:32Z)
- `aa.json` — `https://artificialanalysis.ai/api/v2/language/models/free?page_size=200&page=1..3`
  (free tier, `x-api-key`; `intelligence_index_version` 4.1)
- `tb.json` — **synthesized** (ticket 13) in the shape of the real v2.1
  payloads per the source survey (`assets/02-terminal-bench-source-survey.md`):
  `{"listing": [...]}` mirrors the GitHub contents-API response for
  `harbor-framework/terminal-bench-2-1/leaderboard/submissions`, and
  `submissions` maps each filename to its submission JSON (`source_filter` /
  `metadata` / `metrics` / `disqualified_trials` / `trials`). No live TB
  payloads are saved; the entries are plausible v2.1-shaped rows for the
  fixture models (efforts high/xhigh/max only, accuracy ± stderr, cost USD,
  avg trial duration, tokens). Live shapes land in ticket 15.
- `or.json` — **synthesized** (ticket 18) in the shape of the real OpenRouter
  `GET /api/v1/models` response per the source survey
  (`assets/05-openrouter-source-survey.md`): `{"data": [...]}` rows with a
  vendor-prefixed `id`, `context_length`, and `architecture.modalities`
  (input/output modality lists). Real OR data (400 rows) was fetched live
  2026-08-08 to validate the shape, but the fixture models are fictional, so
  the rows are hand-written in the real shape like `tb.json`. Kimi K3 is
  deliberately omitted — the "no OpenRouter row" detail case.

Rows are verbatim from the payloads (TB: synthesized); only the row selection
is curated.

`provenance.json` records the historical snapshot dates from this README for
DeepSWE/Artificial Analysis and marks Terminal-Bench/OpenRouter as synthetic.
Their synthetic snapshot dates are unknown. A run's actual UTC fetch timestamp
is separate: reading these files today does not make their measurements current.

## Model set (7)

| Model | AA rows in fixture | Role |
|---|---|---|
| GPT-5.6 Luna (OpenAI, closed) | all efforts | cheapest config; the frontier anchor; near-tie Δ story |
| GPT-5.6 Sol (OpenAI, closed) | all efforts | frontier at medium/high/xhigh; dominated at low |
| GPT-5.5 (OpenAI, closed) | all efforts | same-effort dominated at low — the replacement-preference case |
| Claude Opus 5 (Anthropic, closed) | all efforts | top of the frontier path at max |
| Kimi K3 (Moonshot, open-weights) | low, max | open-weight model; AA-only config at low (DSW `—`) |
| GPT-5.6 Terra (OpenAI, closed) | **deliberately excluded** | source-only at low: AA `—`, price n/a, no PPI |
| Qwen3.8 Max (Alibaba) | none in reality | model-level no-AA-row case; source-only identity (DSW xhigh only, renders at xhigh tables in later tickets) |

Curation notes:

- GPT-5.6 Terra's AA rows exist in the real payload but are excluded so the
  fixture spans "with and without AA rows" per ticket 11 — a real model
  rendering source-only at low effort. The checked-in alias table still maps
  `gpt-5-6-terra`; the join degrades to source-only when the AA row is absent,
  and ticket 15's live payloads restore it.
- `gpt-5-5-instant-*` / `gpt-5-5-pro` AA rows are separate models, not
  GPT-5.5 variants — excluded.
- Rows with no effort setting (non-reasoning AA rows) are kept verbatim; the
  parser ignores them for configs.

## What the subset exercises

- Frontier membership and `*` markers (Luna low is the only frontier config at
  low effort).
- Replacement arrows: same-effort preferred (GPT-5.5 low → Sol low: +5.9 pts,
  save $0.015 — a cross-effort Luna max arrow has strictly higher gain, so the
  preference is observable); cross-effort fallback (Kimi low → Luna max; Sol
  low → Luna max; Opus 5 low → Sol medium).
- ΔAA/Δ$ near-ties (Sol low sits $0.002 above Kimi low) and cheapest-first
  sort with the unpriced row last.
- Frontier path line: 12 configs spanning low → max (Luna low … Opus 5 max).
- DSW/AA grade columns, TB `—`, effort per row, open and closed weights,
  price n/a / no PPI on the source-only row.

## TB set (ticket 13) — 11 submissions, 4 models

| File (abridged) | Agent | Model | Effort | Acc ± CI | Date | Role |
|---|---|---|---|---|---|---|
| …-gpt-5-6-luna-max-codex-cli | codex-cli | GPT-5.6 Luna | max | .757 ± .021 | 07-11 | the recency tie-break winner |
| …-gpt-5-6-luna-max-junie-cli | junie-cli | GPT-5.6 Luna | max | .757 ± .024 | 07-01 | same score, older — loses the tie |
| …-gpt-5-6-luna-xhigh-codex-cli | codex-cli | GPT-5.6 Luna | xhigh | .733 ± .021 | 07-05 | xhigh coverage (no table renders xhigh yet) |
| …-gpt-5-6-luna-high-codex-cli | codex-cli | GPT-5.6 Luna | high | .701 ± .022 | 06-20 | TB grade 4 at high |
| …-gpt-5-6-sol-max-codex-cli | codex-cli | GPT-5.6 Sol | max | .769 ± .020 | 07-10 | best TB score at max → grade 5 |
| …-gpt-5-6-sol-xhigh-codex-cli | codex-cli | GPT-5.6 Sol | xhigh | .745 ± .022 | 07-08 | xhigh coverage |
| …-gpt-5-6-sol-high-codex-cli | codex-cli | GPT-5.6 Sol | high | .712 ± .023 | 06-25 | TB grade 5 at high |
| …-gpt-5-5-high-warp | warp | GPT-5.5 | high | .671 ± .025 | 07-02 | best-agent collapse winner (.671 > .664) |
| …-gpt-5-5-high-codex-cli | codex-cli | GPT-5.5 | high | .664 ± .024 | 06-15 | loses the collapse; no TB max row → `—` at Deep |
| …-claude-opus-5-max-claude-code | claude-code | Claude Opus 5 | max | .689 ± .019 | 07-09 | TB grade 2 at max |
| …-claude-opus-5-max-terminus-2 | terminus-2 | Claude Opus 5 | max | .661 ± .020 | 07-03 | loses the collapse |

Notes:

- Model strings (`model_name`) are the TB v2.1 display style ("GPT-5.6 Luna",
  "GPT-5.5", "Claude Opus 5") and map to AA base slugs via the alias table;
  every TB row joins onto a canonical model — none degrades to `tb:` identity.
- No TB rows at low/medium (v2.1 doesn't offer them) — the `—` at
  Chores/Everyday is the honest absence of data, not a dropped row.
- Kimi K3, Terra and Qwen3.8 Max have no TB rows: Kimi/Terra show `—` in the
  TB column at every effort; nothing-discarded is asserted on the 11 rows.

## Runtime normalized source contract

`fetch.fetch_all(directory)` reads the saved responses without network;
`fetch.fetch_all(None)` uses the existing live endpoints. Both return the
source payloads plus `_provenance`. `identity.build(aliases, raw)` carries that
record into `Dataset.provenance` and preserves each original row in
`Rating.raw`. No second acquisition path or production snapshot is introduced.

For Artificial Analysis, each measured effort has these independent nullable
fields. Published paths below are relative to `data[]`:

| Rating field | Published path and basis |
|---|---|
| `score` | `evaluations.artificial_analysis_intelligence_index` — Intelligence only |
| `coding_score` | `evaluations.artificial_analysis_coding_index` |
| `agentic_score` | `evaluations.artificial_analysis_agentic_index` |
| `cost` | `artificial_analysis_intelligence_index_cost.cost_per_task.total_cost` — matching Intelligence benchmark USD/task |
| `first_answer_seconds` | `performance.median_time_to_first_answer_token_seconds` — includes thinking |
| `speed` | `performance.median_output_tokens_per_second` — output throughput |
| `first_token_seconds` | `performance.median_time_to_first_token_seconds` — may stop at a reasoning token |
| `response_500_tokens_seconds` | `performance.median_end_to_end_response_time_seconds` — published synthetic estimate for 500 answer tokens |
| `pricing` | `pricing.price_1m_input_tokens`, `price_1m_output_tokens`, `price_1m_cache_hit_tokens`, `price_1m_cache_write_tokens` — separate USD per million tokens |

An absent, null, nonnumeric or non-finite optional number becomes `None`;
zero remains zero. A malformed optional object leaves its metrics unavailable
without dropping the configuration or its raw row. No timing, score or cost is
copied from another effort. The outer Intelligence suite `total_cost`, token
list prices, and DeepSWE/Terminal-Bench run expenditures are different bases.
There is no established matching Coding/Agentic task cost. The separate Coding
Agent Index is not a substitute for these scores, and the complete current
Coding/Agentic formulas remain a source gap.

`Dataset.provenance` exposes `mode` (`fixture` or `live`), actual UTC
`fetched_at`, and per-source `urls`, `snapshot_date`, `synthetic`, and labelled
`source_dates` when published. Unknown history stays null/empty. Live
Artificial Analysis pagination also retains page URLs, row ranges, reported
index versions and dates; each rating gets its page's
`intelligence_index_version` and `source_url`. Terminal-Bench ratings retain
individual listing `download_url` values in `source_url`, plus submission
`date`, agent and wholesale raw evidence. Source URLs omit credentials,
headers, fragments and non-pagination query parameters.

The canonical model key is still the Artificial Analysis base slug; UUIDs
remain per-effort evidence. Existing aliases and Terminal-Bench best-agent,
then recency collapse are unchanged. Source-only models remain auditable in
the dataset with no manufactured Artificial Analysis values. Artificial
Analysis-only catalog models do not enter ranked/advisory inclusion. This
source slice does not change objective selection, ties, grades or frontiers.

OpenRouter catalog enrichment remains best effort. Context and input/output
modalities are optional; malformed or missing catalog data does not fail
ratings. Original joined rows remain in `Model.catalog_rows`.
`Dataset.openrouter_models` maps a supplied catalog `canonical_slug` (the
rankings permaslug) through that row's `id`, then the existing ID/alias join,
to the canonical model key. A permaslug is never derived from an `id`.
Existing ID-only and vendor-prefix joins still work.

`Model.token_share_30d` remains explicitly `None`, not zero. No authenticated
rankings payload, complete 30-day coverage or top-50 presence has been verified
by the recorded evidence. Catalog fields or illustrative totals do not prove
share; top-50 absence is not zero usage. A future positive display value needs
verified window/coverage, source/date, a denominator including `other`, and
one canonical-model aggregation across variants, dated snapshots and days
without double-counting or effort splits. This is an evidence/access limit,
not a claim that the intended feed is impossible. Share cannot affect policy.

Timing is explanatory, not whole-agent task duration or evidence about a
creator's particular serving endpoint. The Free route's exact prompt preset
and provider aggregation remain unestablished. This implementation and its
offline checks do not claim a newly inspected authenticated live response.

