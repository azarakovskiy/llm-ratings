# Fixtures — main (tickets 11–18)

Saved copies of the real source payloads, curated to a small subset, served
by the CLI's `--fixtures` mode (the spec's user-confirmed test seam: no
network below the fetch boundary).

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
