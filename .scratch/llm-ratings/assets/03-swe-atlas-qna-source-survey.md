# Source survey: SWE-Atlas-QnA (Scale AI)

Surveyed 2026-08-05 from primary sources: Scale Labs leaderboard, scale.com blog, arXiv paper, GitHub repo, Hugging Face dataset card; corroborated by artificialanalysis.ai.

## What it is

SWE Atlas is Scale AI's benchmark suite for evaluating AI coding agents across professional software-engineering workflows, composed of three leaderboards: **Codebase QnA** (released), Test Writing, and Refactoring. Announced 2026-03-04 (scale.com blog); paper: arXiv:2605.08366 (2026-05-08).

**SWE-Atlas-QnA** ("Codebase QnA") is the first released benchmark in the suite. It measures **deep code comprehension**: the agent gets a real open-source repository inside a Docker container and must answer intentionally underspecified technical questions (tracing execution paths, explaining architecture, root-cause analysis) using runtime analysis and multi-file reasoning. It is **both a leaderboard and an open dataset** — the distinction ticket 05 needs: the *ratings* live only on the leaderboard; the *dataset* (tasks + rubrics, no scores) is freely downloadable.

- **Size/coverage:** 124 tasks across 11 production repos in Go, Python, C, TypeScript (kitty, k6, maddy, Scapy, TruffleHog, etc.), pinned to commits. Repos drawn from SWE-Bench Pro; strong-copyleft (GPL) by design for contamination resistance.
- **Metric:** Task Resolve Rate — % of tasks where the agent's answer passes *every* rubric criterion (score 1.0), graded by an LLM judge (Claude Opus 4.5) against expert-written rubrics (avg 12.3 criteria/task). Leaderboard also shows ±95% CI per row and rank (UB).
- **Task categories:** architecture & system design 35%, root-cause analysis 30%, code onboarding 23%, security 9%, API/library integration 3%.

## Ratings data on the leaderboard

- Shape: one row per (model, harness, reasoning-effort) configuration — e.g. "Opus 5 (Claude Code) xHigh", "GPT 5.4 (Codex) xHigh", "DeepSeek V4 Pro (Mini-SWE-Agent)". ~21 rows as of 2026-08-05: top = Opus 5 (Claude Code) xHigh 63.17±5.01, Opus 4.8 xHigh 57.26, GLM 5.2 (MSA) 48.12, GPT-5.6-Sol (Codex) xHigh 46.00, GPT 5.5 (Codex) xHigh 45.43, Muse Spark 1.1 xHigh 42.20, GPT 5.4 (Codex) xHigh 40.80, Opus 4.7 (Claude Code) 40.32, Fable-5 xHigh 39.00, GPT 5.4 xHigh (MSA) 36.30, Opus 4.6 (Claude Code) 33.30, GPT 5.3 (Codex) xHigh 32.60, Sonnet 4.6 (Claude Code) 31.20, Opus 4.6 (MSA) 30.00, DeepSeek V4 Pro (MSA) 27.15, Muse Spark 24.20, GLM 5 (MSA) 20.50, Gemini 3.1 Pro (MSA) 13.50, Kimi K2.5 (MSA) 13.10, MiniMax M2.5 (MSA) 10.30, Gemini 3 Flash (MSA) 8.20.
- Harness matters: models run both on the standard Mini-SWE-Agent harness and on native scaffolds (Claude Code, Codex CLI); native scaffolds score higher (per blog).
- Model coverage: frontier closed (Anthropic Opus/Sonnet, OpenAI GPT-5.x, Google Gemini, Moonshot Kimi, MiniMax, GLM) and open-weight (DeepSeek V4 Pro, GLM-5/5.2, Muse Spark, Fable-5). Date range: evaluations since launch (Feb–Mar 2026) onward; rows tagged NEW as added.
- Full per-task data (prompts, reference answers, rubrics) is in the dataset, so any model can be re-run on all 124 tasks — but the leaderboard itself only publishes aggregate pass rates.

## Access method

- **Leaderboard (ratings):** https://labs.scale.com/leaderboard/sweatlas-qna (also scale.com/leaderboard/sweatlas-qna). Public HTML; the table is embedded server-side in the Next.js RSC payload — **no public API and no CSV/export found** (checked page source for api/json/csv/export endpoints). Acquisition = HTML scrape of the rendered page (stable structure, includes score, ±CI, harness, effort, rank).
- **Dataset (tasks, no ratings):** Hugging Face `ScaleAI/SWE-Atlas-QnA` (124-row `test` split, parquet; usable via HF viewer/datasets API) and full harbor-format task data (Docker envs, run configs) in GitHub `scaleapi/SWE-Atlas` (`data/qa/`, 124 task dirs).
- **Methodology/results tables:** arXiv:2605.08366 (HTML/PDF).

## Update cadence

Irregular, event-driven — models are added as Scale evaluates them; the page carries dated change notes (e.g. "Update July 28, 2026" raising mini-swe-agent step count to 500). No fixed schedule; refresh = re-scrape on demand.

## Licensing / ToS

- GitHub repo `scaleapi/SWE-Atlas`: **Apache-2.0** (verified via GitHub license API) — covers the benchmark data, prompts, and harness configs.
- HF dataset page: **no license tag** (cardData.license = None, no license tag in metadata) — flag: reuse of the HF copy is license-ambiguous on paper; the canonical GitHub source is Apache-2.0, so treat that as the operative license and note the gap.
- Leaderboard *numbers*: no explicit reuse terms found; standard site ToS applies, no statement found permitting/forbidding scraping — flag as unverified.
- Note: tasks are built inside strong-copyleft (GPL) repos; that governs the repo code itself (and is Scale's anti-contamination choice), not the QnA prompts/answers.

## Fog items (decision-relevant)

- **Per-effort ratings: partial / no systematic breakdown.** Each leaderboard row carries an effort annotation (e.g. `xHigh`) and the paper compares "same reasoning effort" across scaffolds, but there is **no per-effort split** — each model appears once at one effort setting, and the leaderboard offers no effort filter. "On Max effort" comparisons are only *incidentally* available for the (mostly frontier) rows that happen to be run at xHigh; most open-weight rows have no effort label. → Not a per-effort source; treat rows as (model, harness, effort) configurations, mostly xHigh for frontier, unspecified otherwise.
- **Latency/throughput: no.** The leaderboard and paper publish only resolve rate (±CI) plus analysis of answer length/tool-use; no wall-time, tokens, or cost. (Adjacent: artificialanalysis.ai runs SWE-Atlas-QnA as one-third of its Coding Agent Index and measures its own time-per-task and cost-per-task on its own harness — a candidate for the "fast" axis, but from AA, not Scale.)

## Sources

- Leaderboard: https://labs.scale.com/leaderboard/sweatlas-qna
- Blog: https://scale.com/blog/swe-atlas
- Paper: https://arxiv.org/abs/2605.08366
- GitHub: https://github.com/scaleapi/SWE-Atlas (Apache-2.0)
- HF dataset: https://huggingface.co/datasets/ScaleAI/SWE-Atlas-QnA
- Corroboration: https://artificialanalysis.ai/agents/coding-agents (QnA = "Technical Q&A, 124 tasks, By Scale AI", 1/3 of AA Coding Agent Index)
