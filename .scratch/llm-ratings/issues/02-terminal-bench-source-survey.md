# 02 Terminal-Bench v2 source survey

Type: research
Blocked by: —
Status: resolved

## Question

What does Terminal-Bench v2 expose publicly? Specifically: which ratings data (leaderboard scores, per-model entries), how it is accessed (public API, CSV export, HTML scrape), model coverage and date range, update cadence, and any licensing/ToS constraints on reuse. Note whether per-effort ratings exist. Deliverable: a markdown survey linked from this ticket.

## Answer

Terminal-Bench v2 is a viable public ratings source, with the per-effort caveat answered: **per-effort ratings exist on v2.1, not v2.0**. Ticket 05 (choose sources) should target **v2.1** — the current active iteration (launched May 2026, homepage leaderboard) — because it is the only one with an Effort axis (max/high/xhigh; `max` entries exist for GPT-5.6 Terra 78.4%, GPT-5.6 Luna 75.7%, Claude Opus 4.7 68.9%, GLM-5.1 58.7%) and per-run Cost. v2.0's 142 rows (Oct 2025–May 2026) carry only accuracy ± CI, no effort, and its submission channel is closed pending a replacement process.

Access: no public JSON/CSV API on tbench.ai (probed → 404); the leaderboards are full server-rendered HTML tables (one page each, no pagination) so HTML scrape works. The cleanest machine-readable path is v2.1's per-row submission JSONs checked into `harbor-framework/terminal-bench-2-1/leaderboard/submissions/*.json` — they include accuracy, stderr, n_trials, pass@k, tokens, cost, and avg trial duration. Rows are agent+model pairs (not model-only), multiple rows per model/agent across dates and efforts; model coverage spans OpenAI/Anthropic/Google/xAI/DeepSeek/Moonshot/Z.ai/MiniMax/Meta/Qwen. Cadence is event-driven (each merged submission PR adds a row), not scheduled. Licensing is Apache-2.0 across repos and the HF submissions dataset; leaderboard data is public by submission policy; no restrictive ToS found. Benchmark tasks carry a training-corpus canary (irrelevant for score display).

Fog notes for ticket 05:
- **Per-effort ratings: YES (v2.1 only)** — Effort is a required submission parameter and leaderboard column; v2.0 has none. Limitation: one effort per row, no per-model effort sweeps.
- **Latency/throughput: NO on leaderboard surfaces** — no latency/throughput columns; v2.1 JSONs expose `avg_trial_duration_sec` and tokens as a partial proxy, and v2.1 shows Cost; v2.0 exposes nothing of the sort.

Full survey: [assets/02-terminal-bench-source-survey.md](../assets/02-terminal-bench-source-survey.md)
