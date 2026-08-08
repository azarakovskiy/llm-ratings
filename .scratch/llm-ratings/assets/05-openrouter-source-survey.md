# OpenRouter API — source survey

Surveyed 2026-08-08 from live primary sources: the real `GET /api/v1/models` payload, the OpenAPI spec, docs pages, FAQ, and the ToS (scraped via firecrawl).

## Source URLs

- Client SDKs overview: https://openrouter.ai/docs/client-sdks/overview
- API reference overview: https://openrouter.ai/docs/api_reference/overview
- Models endpoint docs: https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties
- Benchmarks endpoint docs: https://openrouter.ai/docs/client-sdks/typescript/sdks/benchmarks/README
- Limits & auth: https://openrouter.ai/docs/api_reference/limits ; https://openrouter.ai/docs/api_reference/authentication
- FAQ (variants, cadence, free tier, rate limits): https://openrouter.ai/docs/faq
- Changelog (cadence): https://openrouter.ai/docs/changelog
- OpenAPI spec: https://openrouter.ai/openapi.json
- Terms of Service (Last Updated Jul 29 2026): https://openrouter.ai/terms
- Live payload: `GET https://openrouter.ai/api/v1/models`

## Overview

OpenRouter is an LLM **aggregator/router** (one API in front of many providers). As a *ratings* source it is a reseller of other people's data rather than a primary bench-lab:

- **Identity, prices, context, architecture, reasoning metadata** — first-class, in the live `GET /models` payload. ✅
- **Benchmark scores** — present as a `benchmarks` block on model rows: the Artificial Analysis Intelligence/Coding/Agentic indices (the *same indices our AA source already consumes*), plus Design Arena Elo/rank/win-rate per category. ✅ (no key needed)
- **Speed (tok/s) + latency** — exposed only at the per-provider **endpoint** level (`/models/{author}/{slug}/endpoints`) as `throughput_last_30m` and `latency_last_30m` (p50/p75/p90/p99), and **only with an authenticated API key**; both are `null` unauthenticated. It is NOT in the `GET /models` list. ⚠️
- **Reasoning effort** — a **request parameter** (`reasoning.effort`, enum `max|xhigh|high|medium|low|minimal|none`) with per-model `supported_efforts`/`default_effort`. NOT separate effort-variant model rows (unlike AA). ⚠️
- **Per-task cost** — not computed by OpenRouter; only per-token (and per-request/image/audio) prices. The benchmarks endpoint has `avg_cost_per_task` *for its own tau-bench/GPQA evals only*. ❌

## Data shape — live `GET https://openrouter.ai/api/v1/models` (no auth needed, HTTP 200)

Envelope: `{ "data": [Model], "links": {"next": null}, "total_count": 400 }`. When `offset`/`limit` are omitted the full list is returned (400 rows, one page, `next: null`).

Verbatim top-level keys of a `Model` row (from the real payload / `components.schemas.Model.properties`):
`id`, `canonical_slug`, `hugging_face_id`, `name`, `created`, `description`, `context_length`, `architecture`, `pricing`, `top_provider`, `per_request_limits`, `supported_parameters`, `default_parameters`, `supported_voices`, `knowledge_cutoff`, `expiration_date`, `links`, `reasoning`, `benchmarks`, `alias_target`.

Key fields (quoted from the live payload):

- **id**: `"id": "meta/muse-spark-1.2"` — stable routing slug (`org/model`, optionally with variant suffix). Also `canonical_slug` (`"meta/muse-spark-1.2-20260805"`) — the dated, version-pinned slug (what a `:latest` alias resolves to). `created` is a Unix epoch int.
- **name**: `"name": "Meta: Muse Spark 1.2"`.
- **context_length**: `"context_length": 1048576` (int, tokens). `top_provider.context_length` / `max_completion_tokens` / `is_moderated` give the top provider's variant.
- **pricing** — units are **USD per single token** (NOT per 1M). Live: `"prompt": "0.00000125"`, `"completion": "0.00000425"` (a $1.25/$4.25-per-1M model). Optional keys: `input_cache_read`, `input_cache_write`, `web_search`, `request`, `image`, `image_output`, `audio`, `audio_output`, `input_audio_cache`, `image_token`, `discount` (fractional), and `overrides[]` (tiered pricing by `min_prompt_tokens`). OpenAPI confirms: `"Price in USD per token for completion (output) generation"`. To get $/1M multiply by 1e6.
- **architecture**: `{"modality":"text+image+video->text", "input_modalities":[...], "output_modalities":[...], "tokenizer":"Qwen", "instruct_type":null}`.
- **supported_parameters**: array e.g. `["...","reasoning","reasoning_effort","temperature","tools",...]` — per-model capability list (not ratings).
- **top_provider**: `{"context_length":..., "max_completion_tokens":..., "is_moderated":...}` — does NOT carry provider name in the list row (that's in the per-endpoint detail).
- **benchmarks** (present in live payload; OpenAPI: "Omitted when no benchmark data is available"):
  - `artificial_analysis`: `{"intelligence_index":58.1, "coding_index":71.8, "agentic_index":58.4}` (154 of 400 models).
  - `design_arena`: array of `{"arena":"models", "category":"website", "elo":1350, "win_rate":63, "rank":5}` (217 of 400 models).
- **reasoning**: `{"mandatory":true, "default_enabled":true, "supported_efforts":["xhigh","high","medium","low","minimal"], "default_effort":"medium", "supports_max_tokens":...}`.
- **alias_target**: only on `~org/model-latest` aliases, e.g. `{"name":"DeepSeek: DeepSeek V4 Flash 0731", "slug":"deepseek/deepseek-v4-flash-0731"}`.

**Fields that DO NOT exist in `GET /models`:** NO speed/throughput (tok/s), NO latency/TTFT, NO quality/intelligence column beyond the `benchmarks` block, NO per-task cost, NO reasoning-effort sub-rows. Sort query params (`sort=throughput-high-to-low`, `latency-low-to-high`, `intelligence-high-to-low`, …) and filter params (`min_intelligence_index`, …) exist but only reorder/filter; the list row itself carries no throughput/latency number.

## Reasoning effort

**Effort variants are NOT separate model ids.** The live payload models reasoning as a per-request parameter: `supported_parameters` includes `reasoning` and `reasoning_effort`; the `reasoning` object enumerates `supported_efforts` (enum `max|xhigh|high|medium|low|minimal|none`, descending order per OpenAPI) and a `default_effort`. You rank "on effort X" by calling the same `id` with `reasoning: {effort: "xhigh"}`.

The suffix variants `:free`, `:batch`, `:thinking`, `:nitro`, `:extended` are **routing/behavior variants, not effort levels** (FAQ "What are model variants?"). In the live list only `:free` (14) and `:batch` (60) appear as separate rows plus one `:thinking` row (`qwen/qwen-plus-2025-07-28:thinking` = "reasoning by default" pricing variant). `:nitro` (sort by throughput) and `:extended` never appear as ids — they are dynamic request-time modifiers. Contrast with AA, where each effort is its own model row.

## Other rating/benchmark endpoints

- **`GET /api/v1/benchmarks`** — unified benchmark endpoint aggregating Artificial Analysis, Design Arena, and OpenRouter's own **tau-bench (verified airline)** and **GPQA Diamond** evals (accuracy, accuracy_stddev, avg_cost_per_task, total_tasks, last_run_timestamp). **Requires an API key** (unauthenticated → `401 {"error":{"message":"No cookie auth credentials found","code":401}}`); `source` filter enum `artificial-analysis|design-arena|openrouter`. Rate-limited 30 req/min, 500 req/day per docs. Response `meta.version: "v1"`.
- **`GET /models/{author}/{slug}/endpoints`** — per-provider endpoint detail; the only place speed/latency numbers live.
- **`GET /model/{author}/{slug}`** — single-model detail. `GET /models/count` → `{"data":{"count":400}}`.
- No leaderboard/Elo-aggregate endpoint in the API; the Design Arena Elo data is inline in each model's `benchmarks`.

## Speed / latency

Only at the **per-provider endpoint** level: `GET /api/v1/models/{author}/{slug}/endpoints` returns per-endpoint `throughput_last_30m` and `latency_last_30m`, each a `PercentileStats {p50,p75,p90,p99}` object. OpenAPI: throughput = "tokens per second over the last 30 minutes…output"; latency = "time to first token" ms. **Both are `null` for unauthenticated requests** (verified live) — the schema says they are "Only visible when authenticated with an API key or cookie." So a speed column is obtainable but (a) requires an API key and (b) is provider-specific (one model may have many provider endpoints), not a single per-model figure. It is not in `GET /models`.

## Per-task cost

OpenRouter does **not** compute a general per-task cost. Pricing is strictly per-token (+ per-request/image/audio/`web_search` fields). The only per-task figure anywhere is `avg_cost_per_task` on its own tau-bench/GPQA eval entries in `GET /benchmarks` (an eval cost, not a ratings-column cost). A "cost per effort variant per task" (what AA precomputes) has no OpenRouter equivalent — you'd derive it yourself from price × your own token counts.

## Auth / free tier / rate limits

- `GET /models` (and `/models/count`, `/model/{author}/{slug}`, and the non-speed fields of `/models/{author}/{slug}/endpoints`) work **unauthenticated** — verified 200 with no key.
- `GET /benchmarks` and the speed/latency fields on endpoints **require a valid API key** (Bearer token).
- Free tier: OpenRouter gives new users a small free credit allowance plus free models; free models are rate-limited to 50 req/day without credits, 1000 req/day once you hold ≥10 credits. Credit/rate-limit check endpoint `GET /api/v1/key`.
- No documented dedicated rate limit for `GET /models`; benchmarks endpoint is 30/min + 500/day per docs.

## ToS / attribution

- **No attribution requirement** in the ToS for displaying OpenRouter data. `HTTP-Referer` / `X-OpenRouter-Title` headers are *optional* and are for app discoverability/rankings, not legal attribution.
- **Redistribution is restricted.** ToS §7 prohibited conduct: (04) "access the Site or Service for purposes of reselling API access to Models or otherwise developing a competing service"; (05) "scrape or copy any information on the Site or the Services"; (13) "sell or otherwise transfer … any Materials … or any right or ability to view, access, or use any Material." §12 reserves all rights to "Materials" (incl. "information, data") to OpenRouter. So consuming the API to *display/derive* rankings is fine, but **shipping the catalog/prices/benchmarks onward as a product dataset** is not expressly licensed — the same safe posture as AA (consume + derive, don't redistribute wholesale).
- **AI-content disclosure:** no AI-disclosure requirement found in the ToS for data surfaced by the API.
- Scraping the *site* to get data the API exposes is prohibited; use the API.

## Scale / cadence

- **400 models** live (`total_count: 400`, `/models/count` = 400), all in one unauthenticated page.
- **Both open- and closed-weights:** 298 of 400 carry a non-null `hugging_face_id` (open weights); the rest are proprietary/closed.
- **Cadence:** continuous, no fixed schedule — "we work on adding models as quickly as we can," often day-of-release via lab partnerships. The changelog shows near-daily API releases (Jul 24–29 2026 all present). `canonical_slug` version-pinning (`-20260805`) lets you track which dated snapshot a `latest` alias points to.
- Note: model ids with `:batch` (60) and `:free` (14) inflate the raw count vs. unique base models.

## Gaps vs our five needs

1. **Identity (stable id+name+provider)** — ✅ strong: `id` slug, `canonical_slug`, `name`, `alias_target`; `hugging_face_id`. (Provider name is only at the endpoints level, but model id/name is solid.)
2. **Prices** — ✅ per-token prompt/completion (+ cache/request/image/audio, tiered `overrides`); multiply by 1e6 for $/1M. No key needed.
3. **Speed tok/s** — ⚠️ exists but only per-provider endpoint and **requires an API key**; `null` unauthenticated; not a single per-model value.
4. **Ratings/intelligence scores** — ✅ the AA Intelligence/Coding/Agentic indices are in the unauthenticated `GET /models` payload (same indices our AA source uses), plus Design Arena Elo. No benchmark coverage for ~246/400 models.
5. **Reasoning-effort variants** — ⚠️ **NOT separate model rows**; effort is a request param (`reasoning.effort`) with per-model `supported_efforts`. A CLI that lists "rank on effort X" would need to run/estimate per effort rather than read a pre-scored effort row (unlike AA).

## Verdict table

| # | Need | Satisfied by OpenRouter? | Evidence |
|---|------|--------------------------|----------|
| 1 | Model identity: stable id + name + provider | ✅ Yes (id/name fully; provider via endpoints detail) | `id`, `canonical_slug`, `name`, `alias_target`, `hugging_face_id` in live `GET /models`; `GET /models/{author}/{slug}/endpoints` has `name`/`model_name`. |
| 2 | Prices | ✅ Yes — per-token prompt/completion (+cache/request/image/audio, tiered overrides); $/1M = ×1e6 | Live `pricing.prompt/completion`; OpenAPI "Price in USD per token"; FAQ "price per million tokens." |
| 3 | Speed (tok/s) | ⚠️ Partial — per-provider endpoint only, **needs API key**, `null` unauthenticated, not per-model | `throughput_last_30m` (p50–p99) on `PublicEndpoint`; verified `null` without auth; schema: "Only visible when authenticated…" |
| 4 | Ratings/intelligence scores | ✅ Yes — AA Intelligence/Coding/Agentic indices + Design Arena Elo, unauthenticated | `benchmarks.artificial_analysis.intelligence_index` etc. live (154/400); `benchmarks.design_arena` (217/400); unified `GET /benchmarks` (key required) |
| 5 | Reasoning-effort variants | ⚠️ No as separate rows — effort is a request param, not pre-scored model rows | `reasoning.supported_efforts` + `reasoning_effort` in `supported_parameters`; ReasoningEffort enum; FAQ `:thinking`/`:nitro` are routing variants, not effort rows |

**Bottom line:** OpenRouter is a good *supplementary* identity + price + index source (it literally re-serves AA's indices, so it overlaps AA rather than replacing it, and needs a key for the speed axis). It does **not** satisfy needs 3 (speed needs key + is provider-scoped) and 5 (effort variants are parameters, not scored rows) out of the box. It cannot replace the AA/DeepSWE/Terminal-Bench effort-per-variant ratings.
