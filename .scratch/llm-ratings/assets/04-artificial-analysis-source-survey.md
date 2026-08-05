# Artificial Analysis — source survey (ticket 04)

Surveyed 2026-08-05 from primary sources: official docs, API reference, methodology page, ToS, homepage.

## Source URLs

- Homepage / charts: https://artificialanalysis.ai/
- Data API docs (tiered V2 API): https://artificialanalysis.ai/data-api/docs
- API reference (free API, incl. legacy endpoint): https://artificialanalysis.ai/api-reference
- Data API landing (premium plans): https://artificialanalysis.ai/data-api ; pricing: https://artificialanalysis.ai/pricing
- OpenAPI spec: https://artificialanalysis.ai/api/v2/openapi
- Intelligence Index methodology: https://artificialanalysis.ai/methodology/intelligence-benchmarking
- Terms of Use: https://artificialanalysis.ai/docs/legal/Terms-of-Use.pdf
- Changelog (cadence evidence): https://artificialanalysis.ai/changelog

## What is exposed publicly

### Data API — two documented surfaces (both key-authenticated)

**Tiered V2 API (current docs, base `https://artificialanalysis.ai/api/v2`):**
- `GET /language/models/free` — Free tier. Per-model: headline indices (intelligence index, versioned, currently v4.1), median performance, input/output token pricing, pre-calculated Intelligence-Index eval cost (total + per-task), release date, creator, id/slug/name.
- `GET /language/models` — Pro+. Adds per-benchmark evaluation scores, full pricing incl. blended, performance percentiles/quartiles, context window, parameters, modalities, licensing, `reasoning_model` flag, `openrouter_api_id`, `huggingface_url`.
- `GET /language/models/{slug}` — Pro+. Adds evaluation token counts, omniscience/openness index breakdowns; `providers` array is Commercial-only.
- `GET /language/models/{slug}/performance` — Commercial-only. Per-provider time series of output speed (median tok/s), TTFT, time-to-first-answer-token, end-to-end response time; windows 7d/30d/90d, daily/weekly/monthly granularity.
- `GET /language/providers*` — Commercial-only (provider-level pricing/performance).

**Legacy free API (still documented at /api-reference):**
- `GET /api/v2/data/llms/models` — free; same envelope, includes per-benchmark scores (MMLU-Pro, GPQA, HLE, LiveCodeBench, SciCode, MATH-500, AIME) plus intelligence/coding/math indices, blended 3:1 price, median output tok/s and TTFT. Rated 1,000 req/day on that page.
- Media endpoints (Elo arena ratings): text-to-image, image-editing, text-to-speech, text-to-video — not needed for this PoC.
- CritPt batch-evaluation API — runs CritPt evals; not data access.

### Dimensions published (per model, language models)

- Intelligence Index (composite, v4.1: GDPval-AA v2, τ³-Banking, Terminal-Bench v2.1, SciCode, AA-LCR, AA-Omniscience, HLE, GPQA Diamond, CritPt; categories Agents 34% / Coding 24% / Scientific Reasoning 24% / General 18%) — free tier.
- Area indices: coding index and agentic index (derived subsets of the above), plus math index on the legacy endpoint.
- Per-benchmark scores (MMLU-Pro, GPQA, HLE, LiveCodeBench, SciCode, MATH-500, AIME etc.) — legacy free endpoint; Pro tier on V2.
- Prices: input + output per 1M tokens (free tier); blended 3:1 and full pricing (Pro); cost per Intelligence-Index task pre-computed (free tier includes total + per-task).
- Speed/latency: median output tokens/s, median TTFT, median time-to-first-answer-token (free tier has medians; percentiles/quartiles Pro); end-to-end response time assumes 500 answer tokens. Time series Commercial-only.

## Access method & auth

- API key via `x-api-key` header (no OAuth). Keys are per-organisation; create an account at https://artificialanalysis.ai, generate key in API-key management. Keep server-side.
- Tiers: Free / Pro / Commercial. Rate limits reset daily 00:00 UTC: Free 100 req/day, Pro 500 req/day (docs page), Commercial custom (legacy page states 1,000/day for its free endpoint — see confidence notes). Response headers `X-RateLimit-*`, `Retry-After` on 429.
- Free tier of the V2 API is explicitly "the public language models endpoint with headline indices, median performance, and input/output pricing" — sufficient for the PoC's core columns (rating, price, median speed). Blended price and per-benchmark scores need Pro.
- Pro: $417/month per seat (yearly billing discounts); Commercial provisioned manually (contact team).
- Stable `id` (UUID) recommended as primary key; slugs/names may change. Nulls = "not measured", never zero.

## Coverage & date range

- ~591 models listed in the homepage intelligence chart as of 2026-08-05 ("25 of 591 models" pagination); API returns the full list paginated (page/page_size/total_pages/has_more). Includes proprietary, open-weights, and commercial-use-restricted models; per-provider offerings wider (provider endpoints).
- Coverage is current-moment: point-in-time scores per model with a versioned index; performance-over-time series available to 90 days (Commercial).
- Each reasoning-effort variant is its own model row (see per-effort below), so e.g. Claude Opus 5 appears as 5+ rows.

## Update cadence

- Continuous, no fixed schedule. Changelog shows multiple new model evaluations per week (e.g. 3 Aug, 31 Jul ×2, 30 Jul ×2, 24 Jul ×5, 22 Jul ×2) plus methodology/price updates.
- Performance is measured continuously per provider (time-series endpoint, daily/weekly buckets over 7/30/90-day windows).
- Index itself is versioned (currently v4.1); major bumps change interpretation, minor bumps may change scores.

## Licensing / ToS constraints

- API use requires attribution on ALL tiers: visible byline/footer link to https://artificialanalysis.ai (docs "Attribution and licensing"; free-API page: "Attribution is required for all use of our free API").
- Site Terms of Use (v1.0, Apr 28 2024): site license is personal, noncommercial; no commercial exploitation, no derivative works, no copying/redistribution of site content; acceptable-use policy prohibits scraping/mining the site with automated agents (public search engines carve-out only). So: use the API, don't scrape the site.
- Data API docs frame API use for "your own products, research, analysis, and monitoring systems" with paid commercial tiers, so commercial consumption via the API is the sanctioned path; wholesale redistribution of the data requires bespoke terms — "For redistribution rights or bespoke contract terms, contact the team."
- Practical read for this PoC: consuming via API with attribution = fine; shipping the raw AA dataset onward as part of a product would need their sign-off; derived rankings with attribution are the low-risk shape. Flag in spec: attribution line required in CLI output.

## Per-effort ratings — YES (as separate model rows)

- AA publishes each reasoning-effort setting as its OWN model entry: distinct slug, name ("Claude Opus 5 (Adaptive Reasoning, Low/Medium/High/Xhigh/Max Effort)"), score, and pricing — e.g. /models/claude-opus-5-low … /models/claude-opus-5 (max), "DeepSeek V4 Flash 0731 (Reasoning, Max Effort)", "Kimi K3 (low)". Confirmed on homepage changelog (24–31 Jul 2026 entries) and model URLs.
- There is NO per-effort breakdown field within a single model record; the API returns each variant as a row (`reasoning_model` flag, per-variant slug). Ranking "on Max effort" = filter to the max-effort variant rows.
- Evaluation protocol: one standardized setting per model (temp 0 non-reasoning / 0.6 reasoning; reasoning models at their disclosed max output tokens), not a sweep across effort levels within one score.

## Latency/throughput ("fast" axis) — YES

- Free tier: median output tokens/s, median TTFT, median time-to-first-answer-token per model. Prompt-type presets (medium 1k / long 10k default / 100k / vision / coding / parallel) control measurement.
- Pro: percentiles/quartiles. Commercial: per-provider time series (7/30/90d).
- The "fast" axis is therefore data-backed from the free tier; the homepage "Speed" chart (output tokens per second) uses the same medians.

## Confidence notes

- HIGH (directly read from primary sources): endpoint paths, auth, tiers/limits, fields, index composition v4.1, attribution requirement, model count (~591, homepage pagination 2026-08-05), per-effort variant entries (homepage changelog), latency/throughput fields.
- MEDIUM: the legacy free endpoint (`/api/v2/data/llms/models`, 1,000 req/day) vs the newer tiered V2 (`/language/models/free`, 100 req/day) are two documented generations; the tiered docs read as current, the /api-reference page as retained legacy. [INFERENCE] Both may work; plan against the tiered V2 free endpoint and treat the legacy one as a fallback that may be deprecated.
- MEDIUM: ToS PDF is dated Apr 2024 and its "personal, noncommercial" site-license language sits uneasily beside the API docs' commercial tiers; API-specific terms take precedence for API use but the mismatch is worth a note in the spec (attribution + no redistribution is the safe posture). [INFERENCE]
- MEDIUM: exact per-model price-update timing is not documented; prices refresh continuously with provider changes (cost-per-task methodology was updated 30 Jul 2026).
- NOT VERIFIED: whether any single request returns the full ~591-row list without pagination (pagination exists; page_size value not stated on the free endpoint docs).
