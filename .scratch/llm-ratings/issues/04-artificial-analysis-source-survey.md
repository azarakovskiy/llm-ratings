# 04 Artificial Analysis source survey

Type: research
Blocked by: —
Status: resolved

## Question

What does artificialanalysis.ai expose publicly? Specifically: endpoints and auth (public API vs API key), which dimensions are published (Intelligence Index, area indices, prices, output speed), model coverage, update cadence, and any licensing/ToS constraints on reuse. Note whether per-effort ratings exist. This source is the likely anchor for price and breadth. Deliverable: a markdown survey linked from this ticket.

## Answer

Artificial Analysis is the strongest candidate for the price-and-breadth anchor, and it is machine-accessible: a key-authenticated Data API (`x-api-key` header, no OAuth) at `https://artificialanalysis.ai/api/v2`. The free tier (`GET /language/models/free`, 100 req/day) already returns the PoC's core columns per model — the versioned Intelligence Index (v4.1, built from 9 evaluations including Terminal-Bench v2.1), median output speed and TTFT, and input/output token prices — across ~591 models (homepage pagination, 2026-08-05). Pro ($417/mo/seat) adds blended/full pricing, per-benchmark scores, performance percentiles, context window and licensing; Commercial adds provider-level data and 7/30/90-day performance time series. Coverage is current-moment and continuously updated (multiple new model evaluations per week per the changelog; no fixed schedule).

For ticket 05, the key decisions: (1) the free tier suffices for rating + price + median-speed columns, but blended price (needed for price-per-intelligence) and per-benchmark scores are Pro-gated — budget for one Pro seat or accept input/output-only pricing; (2) licensing is attribution-required on all tiers, redistribution needs bespoke terms, and the site ToS prohibits scraping — so consume via the API with a visible attribution line, don't scrape; (3) the API returns a stable UUID `id` per model plus `openrouter_api_id` (Pro), which helps join to other sources for model identity.

**Fog notes:** Per-effort ratings: YES — but as separate model rows, not a breakdown field: each effort setting (e.g. Claude Opus 5 Low/Medium/High/Xhigh/Max Effort, DeepSeek V4 Flash "Reasoning, Max Effort") is its own model entry with its own score and price, so "Max effort" rankings mean filtering to the max-effort variant rows. Latency/throughput: YES — median output tokens/s, median TTFT and time-to-first-answer-token are on the free tier (percentiles/quartiles Pro, time series Commercial), so the "fast" axis is data-backed.

Full survey: [assets/04-artificial-analysis-source-survey.md](../assets/04-artificial-analysis-source-survey.md)
