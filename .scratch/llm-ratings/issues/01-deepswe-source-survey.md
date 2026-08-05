# 01 DeepSWE source survey

Type: research
Blocked by: —
Status: resolved

## Question

What does DeepSWE expose publicly? Specifically: which ratings data (leaderboard scores, per-model entries), how it is accessed (public API, CSV export, HTML scrape), model coverage and date range, update cadence, and any licensing/ToS constraints on reuse. Note whether per-effort ratings exist. Deliverable: a markdown survey linked from this ticket.

## Answer

DeepSWE (by Datacurve) is a solid source for the ratings PoC: its leaderboard is the
per-model×per-effort pass rate on 113 held-out, contamination-controlled software tasks,
run on one harness (mini-swe-agent) for comparability. All scores are **public static JSON
at `https://deepswe.datacurve.ai/artifacts/<version>/<name>.json`** (no auth, no API key,
no documented API — the SPA reads the same files), refreshed continuously as models are
added ("as they're released"; v1.1 stable since 2026-06-14, snapshot generated 2026-08-04).
19 models, 51 config rows, each with pass@1, pass@4, CI, mean/median cost USD, output/input
tokens, duration seconds, and agent steps. Trial-level (per task × config) data is also
downloadable (38 MB trials.json). Licensing: benchmark repo is Apache-2.0; HF task dataset
is gated (held-out eval data); site carries a training-corpora canary and robots.txt blocks
AI-training crawlers — none of which bars consuming the published scores. Ticket 05 should
choose DeepSWE as a per-effort capability + cost source; fetch `leaderboard-live.json` for
v1.1 and pick rows by `reasoning_effort`.

Fog items:
- **Per-effort ratings: YES** — `reasoning_effort` is a first-class column
  (low/medium/high/xhigh/max); 9 models have a `max` row, so "compare on Max effort"
  is directly queryable.
- **Latency/throughput: PARTIAL** — no latency axis in the UI, but the JSON carries
  mean/median `duration_seconds` and `agent_steps` per config (crude speed proxy;
  no tokens/sec).

Full survey: [assets/01-deepswe-source-survey.md](../assets/01-deepswe-source-survey.md)
