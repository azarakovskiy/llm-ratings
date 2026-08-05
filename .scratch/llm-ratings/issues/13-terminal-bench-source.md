# 13 Terminal-Bench v2.1 source with best-agent collapse

Type: task
Status: resolved
Blocked by: 11

## What to build

Terminal-Bench v2.1 as a third rating source, wired through the existing seams. Fixture mode gains the TB payloads: the submissions listing plus the per-entry JSONs (each carrying accuracy ± CI, effort, cost USD, trial duration, tokens; v2.1 offers only high/xhigh/max efforts). Rows are agent × model pairs; tables must show one rating per (model × source × effort), so agent rows collapse to the best-scoring agent per (model × effort), ties broken by recency. The TB grade column joins the table (quintile-binned over TB's own valid set at that effort) and shows `—` at efforts TB doesn't cover (Chores/Everyday). Alias table gains the TB model strings for the fixture models.

## Acceptance criteria

- [ ] TB grade column populated at high/xhigh/max, `—` at low/medium
- [ ] Agent × model rows collapsed to best agent per (model × effort); tie broken by most recent
- [ ] TB rows attach wholesale (nothing discarded) and join onto canonical model identity
- [ ] Fixture fetch failure for TB → clear error naming the source, nonzero exit

## Answer

Shipped in worktree `llm-ratings-t13`, branch `t13-terminal-bench`, commit `9c2c021` (worktree clean). Terminal-Bench v2.1 wired as a third source: `fetch.py` gains `tb` in SOURCES/FILES with error name "Terminal-Bench"; `identity.py` gains `agent`/`date` on Rating, `TB_EFFORTS = (high, xhigh, max)`, the `best_tb()` best-agent collapse (per model × effort, ties broken by most recent date), a TB parse branch, and a shared `_join()` alias-or-source-only helper; `render.py` gains the TB grade column (per-source quintiles over the collapsed set, `—` at low/medium) via `_source_grades()`; `aliases.json` gains the four TB model strings. New fixture `.scratch/llm-ratings/fixtures/main/tb.json`: 11 synthesized v2.1-shaped submissions (source_filter/metadata/metrics/disqualified_trials/trials, filenames `<date>-<org>-<model>-<effort>-<agent>.json`) for Luna (incl. a recency tie at max), Sol, GPT-5.5, Claude Opus 5; provenance documented in the fixtures README.

Tests: 27/27 green. Coverage: grades at high/max, `—` at low/medium, collapse, recency tie-break, wholesale attach (11/11), canonical join (no `tb:` source-only key), xhigh collapse at dataset level, missing/corrupt tb.json → nonzero exit with "Terminal-Bench" on stderr. /code-review against 3d25727: 1 P2 (tests bypass the subprocess seam for high/max — deliberate and documented: this branch's CLI renders only Chores/low, so TB grades at high/max aren't argv-observable until ticket 12's category selection; subprocess style kept wherever behavior IS contract-visible) and 2 P3 duplications fixed (identity `_join`, render `_source_grades`). All four acceptance criteria met.
