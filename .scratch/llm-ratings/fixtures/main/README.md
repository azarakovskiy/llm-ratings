# Fixtures — main (ticket 11)

Saved copies of the real source payloads, curated to a small subset, served
by the CLI's `--fixtures` mode (the spec's user-confirmed test seam: no
network below the fetch boundary).

## Provenance

Fetched live 2026-08-05:

- `deepswe.json` — `https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`
  (no auth; `generated_at` 2026-08-04T01:34:32Z)
- `aa.json` — `https://artificialanalysis.ai/api/v2/language/models/free?page_size=200&page=1..3`
  (free tier, `x-api-key`; `intelligence_index_version` 4.1)

Rows are verbatim from the payloads; only the row selection is curated.

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
