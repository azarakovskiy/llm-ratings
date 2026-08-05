# 11 Tracer bullet: fixture-fed pipeline end to end (Chores table)

Type: task
Status: resolved
Blocked by: None — can start immediately

## What to build

The whole pipeline working end to end for one category, fed from saved fixtures instead of the network. Running the CLI in fixture mode prints the Chores table — the smallest complete answer the spec defines:

- ★ frontier section on top: configurations nothing beats on AA Intelligence Index at equal-or-lower per-task cost (one side strict), marked `*`; ✗ dominated section below, every row annotated with its best strict replacement ("→ X: +N pts, save $Y"), same-effort replacements preferred, cross-effort fallback when no same-effort replacement exists.
- Frontier path line across efforts at the top (the cross-effort ladder of frontier configurations).
- Columns `DSW | AA | Model | Effort | Provider | $/task | ΔAA | Δ$ | PPI | *`; TB column rendered `—` (source not wired yet); ΔAA/Δ$ against the row above within the section; sort cheapest-first (Chores league axis); `Effort` per row so mixed-effort comparisons stay legible.
- Missing `LLM_RATINGS_AA_API_KEY` → clear setup error and nonzero exit before any output. Any source fetch failure → clear error naming the source and nonzero exit. Attribution line visible in every run.

This ticket also lays the seams everything else rides on: the CLI entry point, the fixture mode (saved source payloads served instead of HTTP — the spec's user-confirmed test seam), the normalized row model (source, model, effort, score, CI, agent where TB, cost; nothing discarded — rows attach wholesale), the checked-in alias table for the fixture models (canonical model = an AA row; a rated model with no AA row keeps a source-only identity: price n/a, no PPI), and per-source capability tiering (quintile-binned 1–5 over the models that source rates at that effort; equal values never split across bins).

Fixture set: a small curated subset of the real payloads (~6 models spanning frontier/dominated, open/closed, with and without AA rows, across efforts so the frontier path line and cross-effort arrows are exercised), under the feature's scratch dir per the spec's fixture strategy.

## Acceptance criteria

- [ ] Fixture mode renders the Chores table: ★ frontier and ✗ dominated sections, `*` on frontier rows
- [ ] Replacement arrows: same-effort replacement preferred over cross-effort; arrow text reads "+N pts, save $Y"
- [ ] ΔAA/Δ$ values correct against the row above; rows sorted cheapest-first
- [ ] Frontier path line renders across efforts; `Effort` column present
- [ ] DSW and AA grade columns show per-source capability tiers; TB column shows `—`
- [ ] Model with no AA row shows price n/a and no PPI; open- and closed-weight models both present
- [ ] Missing AA API key → clear error, nonzero exit, no output
- [ ] Fixture fetch failure → clear error naming the source, nonzero exit
- [ ] Attribution line present in output

## Answer

Shipped: `llmratings/` package (fetch, identity, tier, rank, render, `__main__`, `aliases.json`), the curated main fixture under `fixtures/main/` (deepswe.json + aa.json, verbatim rows), and `tests/test_cli.py` — 14 tests, all passing (`python3 -m unittest discover -s tests`), all asserting observable CLI output through the real `python -m llmratings --fixtures` seam with a dummy key. All acceptance criteria verified against the smoke run: ★/✗ sections with `*`, same-effort arrow preference (GPT-5.5 low → Sol low +5.9, not the higher-gain cross-effort Luna max), ΔAA/Δ$ near-ties, 12-step frontier path line, DSW/AA quintile grades, TB `—`, Terra source-only (n/a price, no PPI), missing-key and missing-fixture errors with nonzero exit and empty stdout, attribution line.

Interpretations (deviations from the spec text, deliberate):

- **Model key = AA base slug, not the stable UUID.** The free API issues a fresh UUID per reasoning-effort variant (e.g. `gpt-5-6-luna-low` and `gpt-5-6-luna` carry different ids), so the UUID is not stable across a model's variants. The base slug (variant slug minus `-low|medium|high|xhigh|max`) is stable and human-readable; source-only models key `dsw:<name>`. Ticket 15 can revisit if the Pro API exposes a true stable id.
- **Fixture row count: 21, not the planned 24** — GPT-5.5 has no `max` variant in the real payload (low/medium/high/xhigh only); all other models span all five efforts, Kimi K3 low+max.
- **Terra curation** per plan: Terra's AA rows exist in the payload but are excluded so a real model renders source-only at low (AA `—`, price n/a, no PPI); the checked-in alias table still maps it, so ticket 15's live payloads restore the AA join. Qwen3.8 Max is the model-level no-AA-row case (DSW xhigh only, renders in later tickets' xhigh tables).
- **Inclusion rule**: model included iff ≥1 DeepSWE/TB rating anywhere; a row renders at effort E iff the included model has ≥1 rating at E from any source (Kimi K3 at low is AA-only and renders with `—` in DSW). AA-only long-tail models never enter.
- **Envelope**: single JSON document; `pagination` normalized to one page (page 1, total_pages 1, has_more false) since the fixture is the whole curated set.

Fixture provenance: fetched live 2026-08-05 (DeepSWE `leaderboard-live.json`, AA free tier pages 1–3 with the user's key); curation documented in `fixtures/main/README.md`.
