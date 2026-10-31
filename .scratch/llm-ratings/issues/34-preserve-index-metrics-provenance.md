# Preserve index-specific metrics and source provenance

Type: task
Status: resolved
Blocked by: none

## What to build

Extend the existing source-fetch and identity contract so downstream advice can read each measured configuration's Intelligence, Coding and Agentic scores, matched Intelligence task cost, distinct published timing and auditable provenance. Deliver a working dataset consumer through the real fixture seam; do not change recommendation policy in this task.

This is an implementation task under [the spec](../spec.md), not another decision or a prototype merge. It has no implementation prerequisite. [Implement the eight-role selection policy](35-eight-role-selection-policy.md) consumes this data contract next.

## Binding requirements

### Acquisition and identity

- Reuse `llmratings/fetch.py:fetch_all` and `llmratings/identity.py:build`, their live/fixture boundary and existing aliases. Do not add a parallel acquisition pipeline, scraping, vendored production dataset, scheduler or cache.
- DeepSWE v1.1, Artificial Analysis and Terminal-Bench v2.1 are the three rating sources. A missing key fails before advice; a fetch/parse failure in any rating source names that source, exits nonzero and produces no partial advice. OpenRouter metadata remains best-effort; its absence or malformed optional data must not fail otherwise valid ratings.
- Canonical model key remains the Artificial Analysis base slug, not its per-effort UUID. Provider means the Artificial Analysis creator, not an API gateway. Preserve measured-effort identity, alias joins, source-only identities, wholesale source rows and Terminal-Bench best-agent/recency behavior. Never copy metrics between effort variants or infer equivalent budgets across creators from equal effort labels.
- Preserve the inclusion boundary: ranked/advisory models must have at least one DeepSWE or Terminal-Bench rating. An Artificial Analysis-only catalog row does not become a recommendation. Keep source-only models reachable as unranked data without manufactured scores or prices. Normalizing additional metrics does not widen this boundary.

### Metrics and provenance

For each Artificial Analysis measured effort, retain independent nullable values from these exact published paths relative to `data[]`:

| Meaning | Published path |
| --- | --- |
| Intelligence score | `evaluations.artificial_analysis_intelligence_index` |
| Coding score | `evaluations.artificial_analysis_coding_index` |
| Agentic score | `evaluations.artificial_analysis_agentic_index` |
| Matching Intelligence benchmark task cost | `artificial_analysis_intelligence_index_cost.cost_per_task.total_cost` |
| Time to first answer token, seconds, including thinking | `performance.median_time_to_first_answer_token_seconds` |
| Output tokens per second | `performance.median_output_tokens_per_second` |
| Time to first token, seconds | `performance.median_time_to_first_token_seconds` |
| Estimated response time for 500 answer tokens, seconds | `performance.median_end_to_end_response_time_seconds` |

- Preserve input/output and available cache-read/cache-write token list prices under `pricing` as separate explanatory USD-per-million-token figures. Neither these prices nor the outer Intelligence suite `total_cost` is the matching task cost. DeepSWE/Terminal-Bench run expenditure is a different basis.
- Missing, null, nonnumeric or non-finite metrics remain explicitly unavailable, never zero-filled. Preserve a genuinely published zero as zero; the next policy task decides which objectives can use it. Do not synthesize missing timing from other medians, substitute first-token for first-answer time, or use another effort's score/cost. Retain raw source rows even when a normalized optional metric is unusable.
- Keep all three indexes distinct and retain the response's reported `intelligence_index_version` when supplied. Do not substitute the separate Coding Agent Index, claim a verified complete current Coding/Agentic formula, or invent an area-index task-cost field.
- Dataset consumers must have source URLs, the actual run fetch date and available snapshot/source dates, the original row, and the configuration identity needed to audit a value. Preserve Terminal-Bench individual submission URLs and date, not just its listing URL. Exclude secrets and request headers from provenance. Fixture acquisition must remain visibly distinguishable from a live-source fetch: a run today does not make its historical saved rows current measurements.
- Timing is explanatory only. First-answer time includes thinking; first-token time may stop at a reasoning token; output rate is throughput; the 500-answer-token value is a published synthetic estimate, not whole-agent task duration. The Free route's exact prompt preset and provider aggregation are not established. Do not describe its figures as the performance of the selected creator's particular serving endpoint.

### OpenRouter enrichment and evidence boundary

- Preserve context length and modalities and the recorded join contract: resolve a rankings permaslug through catalog `canonical_slug` to catalog `id`, then through the existing alias/model join. A permaslug is variant-free and must not be manufactured from `id`. Existing ID/alias enrichment must continue to work.
- The recorded display-only 30-day OpenRouter token-share intent is not proof of an available feed. No authenticated rankings payload or complete 30-day top-50 coverage is verified by the recorded evidence. Do not invent an endpoint schema, credential, successful fetch, market-share value or zero for unknown share. Absence from a top-50 result is not zero usage.
- Keep share explicitly unavailable unless actual verified data supports it. A positive display value requires verified 30-day coverage, a denominator including `other`, and one canonical-model aggregation across variants, dated snapshots and days without counting a row twice; there is no effort split. Isolated illustrative totals are not sufficient evidence. Do not require new authentication to use the existing tool.
- Share, when supported, is display-only: it cannot affect inclusion, eligibility, effort selection, grades, objectives, ties or provider shortcuts. Retain this as an evidence/access limit, not a new product exclusion or a claim that the intended feed is impossible.

## Implementation seams

- Extend `llmratings/identity.py` (`Model`, `Rating`, `Dataset`, `build`) and `llmratings/fetch.py` only as needed to carry normalized metrics and provenance through the existing path. Retain raw rows and adapt existing callers if the data shape changes; no compatibility-only duplicate metric stores.
- Reuse `.scratch/llm-ratings/fixtures/main/{aa,deepswe,tb,or}.json`, `tests/test_cli.py` and its local HTTP-origin seam (`LLM_RATINGS_HTTP_BASE`). The historical fixture already has distinct timing and area-score fields; its date/version and synthesized Terminal-Bench rows are evidence limits, not current market claims.
- Update relevant runtime source-contract documentation to explain added available fields and unavailable states, without claiming external verification. Do not implement ranking or browser controls here.

## Acceptance criteria

- [x] A real `fetch_all(fixture_path)` followed by `identity.build(aliases, raw)` yields separate Intelligence/Coding/Agentic scores and all four timing values at the correct measured effort, with matching Intelligence task cost, separate list prices, original rows, source URLs and date/version provenance.
- [x] A historical fixture example with unequal first-token, first-answer and estimated-response times retains three unequal values. Removing any one optional metric leaves only that metric unavailable; the other metrics and configuration remain intact. Null cost object, null `cost_per_task`, missing values and non-finite values do not crash normalization or turn into zeros.
- [x] The same loaded canonical model retains each effort's own score/cost/timing. UUID differences do not split the model; aliases attach source rows; best-agent/recency collapse is unchanged. Source-only rows remain auditable and the Artificial Analysis-only tail is not promoted into ranked/advisory inclusion.
- [x] Failure regressions name each failed rating source and produce no partial advice; absent/malformed OpenRouter metadata still yields the rating dataset. Source URLs and persisted provenance contain no API key.
- [x] Catalog join cases where `canonical_slug` differs from `id` reach the correct model through the recorded hop. Unknown or unverified share stays unavailable, including top-50 absence; neither missing enrichment nor display-only metadata changes rating values.
- [x] Existing batch fixture consumption remains runnable; this task does not change objective selection, tie-breaks, grades or frontier policy. Runtime source documentation states the metric bases and factual access/coverage limits.

## Verification

Run these after implementation, not during ticket drafting:

1. Extend existing consumer regression coverage in `tests/test_cli.py` for metric-basis/effort alignment, missing/non-finite fields, distinct canonical-slug/ID joins and source-only/Artificial Analysis-only cases. Use real temporary source payloads through `fetch_all` and `identity.build`, not mocked datasets, source-text assertions or checks of attribute existence. Run the affected unittest cases after implementation.
2. Separately run a throwaway Python consumer that loads the saved fixture through real `fetch_all`/`identity.build` and prints/asserts concrete, source-checked per-effort index scores, matching task cost, unequal timing values and source/date provenance. This exercises the changed data contract outside the test runner. Then run `LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --fixtures .scratch/llm-ratings/fixtures/main` with non-TTY input/output and observe the attributed batch result through the unchanged pipeline. Reuse the existing local HTTP origin for pagination and named-source failure checks without external network or real keys.
3. Run `make test` and `make lint` once after all changes land. Update assertions for actual dataset/output behavior, not source-text searches or tests that simply repeat a constructor's input.

## Non-goals and authority

No ranking-policy change, role catalog change, provider chooser, browser UI, new benchmark, source replacement, gateway pricing, retry service, harness routing or config export. Authentication/access gaps remain explicit unavailable data, not fabricated implementation prerequisites.

- [Choose AA signals and objectives for the agreed roles — approved Answer](30-role-advice-criteria.md#answer)
- [Verify AA index cost bases and latency semantics — resolved Answer](32-aa-role-metric-bases.md#answer)
- [Immutable AA index, cost and latency findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md): schema paths, timing distinctions, source dates and explicit statement that no authenticated live API response was inspected.
- [Historical OpenRouter display intent and permaslug evidence limits](../map.md#decisions-so-far), specifically the settled display-only intent and canonical-slug join entries. These are historical summaries with an unavailable original source ticket, not newly verified feed coverage.
- [Define quick selection by major model provider — approved Answer](29-provider-quick-selection.md#answer)
- [Redesign the provider-selection prototype for readable model advice — live Provider lens approval](33-redesign-provider-selection-prototype.md#answer); the approved visual layout is implemented by later tasks, not copied into this source slice.

## Answer

Resolved 2026-10-31 on `implement/t34`. The existing fetch/identity pipeline now
retains separate measured-effort index scores, matching Intelligence task cost,
four distinct timing values and normalized input/output/cache list prices.
Unavailable optional values stay `None`; published zeros and wholesale raw rows
are preserved. No recommendation policy, role or browser controls changed.

### Downstream contract

- `Rating.score` remains Intelligence for Artificial Analysis. New
  `coding_score`, `agentic_score`, `first_answer_seconds`,
  `first_token_seconds`, `response_500_tokens_seconds` and `pricing` complement
  existing matching `cost` and output-throughput `speed`; there is no duplicate
  compatibility metric store. Detail consumes normalized list prices.
- `fetch_all` adds `_provenance`; `Dataset.provenance` exposes fixture/live mode,
  actual UTC fetch time, source URLs, available labelled source dates and
  historical fixture snapshot/synthetic evidence. Artificial Analysis pages
  retain row ranges, URLs and reported versions; each rating carries its own
  `source_url` and `intelligence_index_version`. Terminal-Bench keeps individual
  submission URLs, agent and recency date.
- `Dataset.openrouter_models` resolves a supplied catalog `canonical_slug`
  through that row's `id` and the existing alias/model join. Joined original
  catalog rows stay on `Model.catalog_rows`; malformed optional catalog data
  cannot invalidate ratings. `Model.token_share_30d` stays explicitly unavailable,
  including isolated illustrative totals and catalog/top-50 absence.
- [Runtime source contract](../fixtures/main/README.md#runtime-normalized-source-contract)
  documents fields, units, timing distinctions, source/date limits and the
  unverified OpenRouter feed/coverage boundary. `provenance.json` records only
  the fixture history already documented there, not new live-source evidence.

### Exercised verification

- `PYTHONPATH=tests python3 -m unittest test_cli.SourceContract test_cli.TerminalBench test_cli.LiveAcquisition test_cli.FixtureFailure test_cli.MissingKey`:
  **34 tests passed**. This includes 11 new source-contract cases, real temporary
  payloads, independent missing/non-finite/zero metrics, source-only and
  Artificial Analysis-only identities, distinct permaslug/ID joins, malformed
  optional enrichment, named source parsing/fetch failures without partial
  advice, and the existing local HTTP origin's pagination. The new paginated
  consumer retained separate page-reported versions and URLs without persisting
  the API key or headers.
- A separate throwaway Python process used real saved-fixture
  `fetch_all`/`identity.build` outside unittest: **passed**. Luna Low retained
  Intelligence/Coding/Agentic **33.3/44.2/25.4**, task cost **$0.0088** and
  throughput **146.91**; Maximum retained **51.2/71.4/45.6**, **$0.0473** and
  **180.51**. Kimi Low retained first-token/first-answer/estimated-response
  **3.45/60.66/74.96 seconds**, task cost **$0.2429**, not suite expenditure
  **$283.30**. It printed the original IDs, source URLs, version **4.1**,
  historical snapshot **2026-08-05**, actual fetch timestamp
  **2026-10-31T15:52:16.303687+00:00**, DeepSWE generated date and the synthetic
  Terminal-Bench submission's **2026-07-11** date and individual URL.
- `LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --fixtures .scratch/llm-ratings/fixtures/main`
  with non-TTY input/output: **exit 0**, Artificial Analysis attribution and the
  unchanged Chores/price table and frontier path observed.
- `make test`: **87 tests passed**. `make lint`: **exit 0**. Each repository
  command ran once after implementation. The integration prerequisite merge
  returned **Already up to date**.

All acquisition checks were offline fixtures or the local HTTP origin. No new
authenticated external response, current market measurement, area-index cost
basis or verified OpenRouter 30-day share is claimed.
