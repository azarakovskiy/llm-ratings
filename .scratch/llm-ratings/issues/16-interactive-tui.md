# 16 Interactive TUI: navigation, filters, effort override, detail view

Type: task
Status: ready-for-agent
Blocked by: 12, 13, 14

## What to build

The batch table becomes an interactive session with the spec's full keymap:

- Category nav ←/→ and 1–5; row nav ↑/↓; Esc goes back, q quits.
- `f` capability filter cycles all → cap 5 → cap ≥4 (banding key = AA grade); the table cuts to the top capability bands.
- `e` effort override cycles low → medium → high → xhigh → max → default for the current category, and **resets when the category switches** so a stale effort never carries over.
- Enter on a row opens the detail view: per-source raw grades and ranks, the PPI division (rating ÷ cost), list price, price tier, speed, frontier/dominated status, and a source-disagreement flag (sources telling different stories about a model). TB grade appears where a TB row exists (`—` otherwise).

Navigation never traps the user: every mode has an exit key. Language choice is confirmed by the build session before starting (Python recommended by the spec — prototype and TUI plan are Python).

## Acceptance criteria

- [ ] Category nav ←/→ and 1–5 switches tables; row nav ↑/↓ moves through rows
- [ ] `f` cycles all → cap 5 → cap ≥4 and back
- [ ] `e` cycles low→medium→high→xhigh→max→default; override resets on category switch
- [ ] Enter opens the detail view with all fields; Esc returns to the table
- [ ] Source-disagreement flag set when sources disagree, absent when they agree
- [ ] q quits with clean exit
