# 03 SWE-Atlas-QnA source survey

Type: research
Blocked by: —
Status: resolved

## Question

What is SWE-Atlas-QnA, and what does it expose publicly? Confirm its shape (leaderboard vs dataset, what the QnA component measures), which ratings data it has, how it is accessed (public API, CSV export, HTML scrape), model coverage and date range, update cadence, and any licensing/ToS constraints on reuse. Note whether per-effort ratings exist. Deliverable: a markdown survey linked from this ticket.

## Answer

SWE-Atlas-QnA ("Codebase QnA") is Scale AI's first released benchmark in the SWE-Atlas suite, and it is **both a leaderboard and an open dataset** — the ratings live on the leaderboard, the tasks live in the dataset. It measures deep code comprehension: agents answer underspecified technical questions about real repos (124 tasks, 11 repos, Go/Python/C/TS) inside Docker sandboxes, scored by an LLM judge (Claude Opus 4.5) against expert rubrics. The ratings metric is Task Resolve Rate (% tasks passing all rubric items) with ±95% CI, one row per (model, harness, effort) config — ~21 rows as of 2026-08-05, frontier + open-weight models, covering rows tagged NEW since the Mar 2026 launch with irregular, event-driven updates (latest note 2026-07-28). Access: leaderboard is public HTML with data embedded server-side (no API, no CSV — HTML scrape only); the dataset is free on Hugging Face (`ScaleAI/SWE-Atlas-QnA`, parquet) and GitHub (`scaleapi/SWE-Atlas`, Apache-2.0, verified; the HF card itself has no license tag — treat Apache-2.0 as operative). For ticket 05: this source qualifies as leaderboard-sourced ratings via HTML scrape, with an optional downloadable dataset for re-runs; no ToS statement found on scraping the numbers (unverified).

Fog items: **per-effort ratings — partial/no systematic split.** Effort is only an annotation on each row (e.g. `xHigh`), mostly on frontier rows; no effort filter or per-effort breakdown exists, so "on Max effort" comparisons are only incidental. **Latency/throughput — no.** The source publishes resolve rate only; the "fast" axis would have to come from elsewhere (e.g. artificialanalysis.ai's own time/cost-per-task runs of QnA).

Full survey: [assets/03-swe-atlas-qna-source-survey.md](../assets/03-swe-atlas-qna-source-survey.md)

