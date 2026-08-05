# 13 Terminal-Bench v2.1 source with best-agent collapse

Type: task
Status: ready-for-agent
Blocked by: 11

## What to build

Terminal-Bench v2.1 as a third rating source, wired through the existing seams. Fixture mode gains the TB payloads: the submissions listing plus the per-entry JSONs (each carrying accuracy ± CI, effort, cost USD, trial duration, tokens; v2.1 offers only high/xhigh/max efforts). Rows are agent × model pairs; tables must show one rating per (model × source × effort), so agent rows collapse to the best-scoring agent per (model × effort), ties broken by recency. The TB grade column joins the table (quintile-binned over TB's own valid set at that effort) and shows `—` at efforts TB doesn't cover (Chores/Everyday). Alias table gains the TB model strings for the fixture models.

## Acceptance criteria

- [ ] TB grade column populated at high/xhigh/max, `—` at low/medium
- [ ] Agent × model rows collapsed to best agent per (model × effort); tie broken by most recent
- [ ] TB rows attach wholesale (nothing discarded) and join onto canonical model identity
- [ ] Fixture fetch failure for TB → clear error naming the source, nonzero exit
