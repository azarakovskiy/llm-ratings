# Textual for the interactive TUI

**Status: superseded by [ticket 38](../../.scratch/llm-ratings/issues/38-inline-evidence-web-cutover.md).**
The supported interactive surface is now the local web application, launched
with `make run` or `python3 -m llmratings --web`. Module invocation without
`--web` always produces batch output, including in a terminal. The terminal
adapter, TTY dispatch, Textual dependency, dependency-install target and
terminal-only tests have been removed. UI-independent state coverage now lives
in `tests/test_session.py`; structured evidence and web consumers retain the
valid model/source behavior. The runtime uses only the Python standard library.
See the [runtime README](../../README.md) for current setup and usage.

## Historical decision

The reasoning and implementation consequences below describe the earlier TUI,
not current installation instructions.

The interactive TUI renders as a staggered mess of text on the user's
terminal (cmux, full-width pane): the ticket-16 session hand-rolled ANSI
frames — `"\x1b[2J\x1b[H" + "\n".join(lines)` — with `\n`-only line endings
and no cursor addressing, which the terminal emulator mangles while a
non-TTY pipe renders the same bytes perfectly aligned. We replace the
hand-rolled ANSI layer with **Textual** (the spec §1 preferred dependency
for the TUI) instead of adjusting columns.

The spec required the build session to confirm the TUI dependency before
starting; the ticket-16 session picked plain ANSI without confirming — this
ADR closes that gap. The alternatives were: plain ANSI (shipped, broken
under cmux; no test harness either), curses (stdlib, but we'd hand-build
layout, scrolling and a test seam that Textual provides, for a dependency
count of zero either way), and Textual (mature widget framework with cursor
addressing, resize handling and an `app.run_test()` harness that replaced
the pipe-key seam in `tests/test_tui.py`). We picked Textual: `render.py`
stays the single source of table text — the App is a thin shell that draws
`render.table()`/`render.detail()` lines and routes keys into the `Session`
state machine — so the batch path is untouched and the dependency is
contained to `llmratings/tui.py`.

Consequences: `textual` becomes the repo's first dependency
(`requirements.txt`, installed via `make deps`); the TUI now requires a
terminal that Textual supports. Batch mode (non-tty stdin) never imports
the Textual code path and keeps working without it. Textual 8's Linux
driver spins forever on stdin EOF (closed terminal), so the shell subclasses
it (`_EofDriver` in `llmratings/tui.py`) to exit cleanly — ticket 16's
"EOF/Ctrl-C clean exit" contract.
