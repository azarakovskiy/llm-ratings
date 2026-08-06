# 17 Replace plain-ANSI TUI with Textual

Type: task
Status: resolved
Blocked by: none

## What to build

The ticket-16 TUI renders as a staggered mess of text on the user's terminal
(cmux, full-width pane): it emits hand-rolled ANSI frames —
`"\x1b[2J\x1b[H" + "\n".join(lines)` — with `\n`-only line endings and no
cursor addressing. The identical bytes piped through a non-TTY render a
perfectly aligned table; cmux's emulation mangles them. Fix is to stop
hand-rolling, not to adjust columns. The batch path is NOT broken
(`make run | cat` = aligned table).

User approved (grilling, 5 decisions) replacing the TUI layer with Textual.
The spec §1 names Textual as the preferred TUI dependency and requires the
build session to confirm before starting; the ticket-16 session picked plain
ANSI without confirming — that gap is why this ADR exists.

## Decisions (user-confirmed, binding)

1. Framework: Textual.
2. Scope: thin Textual shell over `render.py` — `render.py` stays the
   single source of table text; the app draws those lines, handles keys,
   keeps `Session` state semantics. No DataTable widget.
3. Tests: Textual `app.run_test()` harness — replaces the pipe-key seam in
   `tests/test_tui.py`; same observable contracts. Delete the `--interactive`
   CLI flag and the pipe seam. Batch detection stays `isatty`;
   `tests/test_cli.py` untouched.
4. Deps: `requirements.txt` + `make deps` — first dependency in the repo.
   Clear "run `make deps`" error when `textual` is missing.
5. ADR: `docs/adr/0001-textual-for-interactive-tui.md` (repo has no
   `docs/adr/` yet).

## Acceptance criteria

- [ ] `make test` green (rewritten TUI tests + untouched batch tests)
- [ ] `make run` in the user's cmux session renders an aligned, readable
      table (user confirms; reproduce the bug first to prove the fix)
- [ ] Batch unchanged: `make run | cat` output byte-identical to today
- [ ] `make deps` installs and a missing-textual run prints a clear error
- [ ] ADR written and committed

## Notes

- Contract to preserve (spec §6–7 + ticket 16): keymap ←/→ + 1–5 category
  nav, ↑/↓ rows, `f` all → cap 5 → cap ≥4, `e` effort cycle with reset on
  category switch, Enter detail, Esc back, q quit; Ctrl-C clean exit.
- Detail view fields and table lines come from `render.detail()` /
  `render.table()` — reuse, don't rebuild.
- Python 3.14.6 (Homebrew, PEP 668 — `make deps` needs
  `--break-system-packages`); textual 8.2.8; no venv in this repo.
- Makefile is untracked (`?? Makefile`); commit it with this ticket.

## Answer

Shipped `17bb0f1` on `t17-textual-tui` (worktree `llm-ratings-t17`, base
`3cb8f6e`), merged `743bfdf`, 64/64 tests green, reviewed (standards + spec,
both P2 findings fixed). Textual 8.2.8 thin shell over `render.py`:
`llmratings/tui.py` keeps the ticket-16 `Session` state machine unchanged
and adds a `LlmRatings` App that draws `Session.frame()` (ANSI parsed via
rich `Text.from_ansi`, reverse-video cursor span preserved) and routes the
full keymap through priority bindings (the scroll container would otherwise
steal ↑/↓/←/→ once the table outgrows the viewport; Textual 8 binds ctrl+c
to copy on the Screen — the priority pass beats both). Scroll-follow only
when the selected row leaves the viewport; missing-textual run prints
"error: textual is not installed — run `make deps`" (preflighted before the
fetch, so no network round-trip for a setup error). `--interactive` and the
pipe-key seam deleted; batch detection stays `isatty`. EOF contract: Textual
8's Linux driver spins forever on stdin EOF, so the shell subclasses it
(`_EofDriver`) to exit cleanly — covered by a new pty test that closes the
master. Tests rewritten on `app.run_test()` with the Pilot (same observable
contracts: frames, reverse-video selection, detail fields, quit paths) plus
the two batch-seam pty tests and a new EOF-exit test. `requirements.txt`
(textual>=8.2.8) + `make deps` (`--break-system-packages`, Homebrew PEP
668); Makefile tracked for the first time. ADR
`docs/adr/0001-textual-for-interactive-tui.md` (why Textual over plain ANSI
— cmux fragility, spec's named choice, run_test harness — and over curses;
the "spec said confirm, build session didn't" gap). Batch output verified
byte-identical to master. Review fixes: shadowed `_redraw` (P3), EOF exit
(P2), missing-textual preflight before fetch (P2). Open item: acceptance
criterion 2 — user confirms the cmux rendering (implementer verified the
pty-driven frame is aligned; the user's cmux session is the final check).
