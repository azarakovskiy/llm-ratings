"""Interactive TUI (tickets 16, 17, 18) — a thin Textual shell over render.py.

Ticket 16 shipped a hand-rolled ANSI TUI (termios/select, zero deps); on the
user's terminal (cmux, full-width pane) its `"\x1b[2J\x1b[H" + "\n".join()`
frames rendered as a staggered mess, while the identical bytes through a
non-TTY pipe aligned perfectly — the emulator mangles `\n`-only frames with
no cursor addressing. The fix is to stop hand-rolling, not to adjust columns
(ADR 0001). Ticket 17 replaces the I/O shell with Textual: `render.py`
stays the single source of table text. The shared `session.Session` owns
advice choices; this adapter adds terminal navigation and `frame()`/`key()`.
The `LlmRatings` App only draws frames and routes keys.

Keymap (spec §6): ←/→ or 1–N role nav (N = roles.json length), ↑/↓ row nav,
`f` capability filter (all → grade = 5 → grade ≥ 4 on the selected index), `o`
objective override (Highest capability → Best value → Lowest qualifying price
→ role default, reset on role switch —
ticket 18 deletes the `e` effort override: efforts now come from the active
objective), Enter detail view, Esc back, q quit; Ctrl-C quits too. Textual
owns cursor addressing, resize and scrolling; batch mode (non-tty stdin
without the old `--interactive` flag) is untouched in __main__.
"""

from __future__ import annotations

import os
import sys

from . import render
from .session import Session as SelectionSession

try:
    from rich.text import Text
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import VerticalScroll
    from textual.drivers.linux_driver import LinuxDriver
    from textual.widgets import Static
    _TEXTUAL = True
except ImportError:   # batch mode must keep working without textual
    _TEXTUAL = False

FILTERS = [("all", None), ("grade = 5", 5), ("grade ≥ 4", 4)]

TABLE_FOOTER = ("←/→ or 1–N role · ↑/↓ move · f filter · o objective · "
                "Enter detail · Esc/q quit")

# The `o` cycle walks render.OBJECTIVES (cap → ppi → price) then back to
# the role default (None). Roles load from roles.json in file order
# (ticket 18).
_LENS = render.OBJECTIVES


class Session(SelectionSession):
    """Terminal navigation and frames over the UI-independent advice state."""

    def __init__(self, ds, roles, role_name=None):
        super().__init__(ds, roles, role_name)
        self.cursor = 0
        self.quit = False

    def frame(self):
        result = self.query()
        if result["details"] is not None:
            return (["LLM RATINGS — detail", ""]
                    + render.detail(self.ds, result["details"], self.role,
                                    self.objective)
                    + ["", "Esc back · q quit", render.ATTRIBUTION])
        lines, rows = render.table(self.ds, self.role, result=result)
        self.cursor = next((i for i, row in enumerate(rows)
                            if row["key"] == self.selected_key), 0)
        if rows:
            at = next(i for i, line in enumerate(lines)
                      if line.startswith(f"  {rows[self.cursor]['model']} "))
            lines[at] = "\x1b[7m" + lines[at] + "\x1b[0m"
        state = "default" if self.objective_override is None else "override"
        filter_label = next(label for label, grade in FILTERS
                            if grade == self.min_grade)
        status = (f"LLM RATINGS — {self.role['name']} · objective "
                  f"{render.OBJECTIVE_LABEL[self.objective]} ({state}) · "
                  f"filter: {filter_label}")
        return [status, ""] + lines + ["", TABLE_FOOTER, render.ATTRIBUTION]

    def key(self, k):
        if self.quit:
            return
        if self.detail_key is not None:
            if k in ("q", "eof"):
                self.quit = True
            elif k == "esc":
                self.close_details()
            elif k in ("left", "right"):
                self._switch_role(k)
            return
        if k in ("q", "esc", "eof"):
            self.quit = True
        elif k in ("left", "right") or (
                k.isdigit() and 1 <= int(k) <= len(self.roles)):
            self._switch_role(k)
        elif k == "f":
            i = next(i for i, (_, grade) in enumerate(FILTERS)
                     if grade == self.min_grade)
            self.set_min_grade(FILTERS[(i + 1) % len(FILTERS)][1])
        elif k == "o":
            i = (_LENS.index(self.objective_override)
                 if self.objective_override in _LENS else -1)
            self.set_objective(_LENS[i + 1] if i + 1 < len(_LENS) else None)
        elif k in ("up", "down", "enter"):
            rows = self.query()["table_rows"]
            if not rows:
                return
            self.cursor = next((i for i, row in enumerate(rows)
                                if row["key"] == self.selected_key), 0)
            if k == "enter":
                self.request_details(rows[self.cursor]["key"])
            else:
                self.cursor = max(0, min(len(rows) - 1,
                                        self.cursor + (1 if k == "down" else -1)))
                self.select_model(rows[self.cursor]["key"])

    def _switch_role(self, k):
        i = self.roles.index(self.role)
        if k == "left":
            i = (i - 1) % len(self.roles)
        elif k == "right":
            i = (i + 1) % len(self.roles)
        else:
            i = int(k) - 1
        self.set_role(self.roles[i]["name"])


if _TEXTUAL:

    class _EofDriver(LinuxDriver):
        """LinuxDriver whose input thread quits the app when stdin hits
        EOF. The stock driver's read loop spins forever on a closed stdin
        (the EOF state stays readable, `os.read` keeps returning b''), which
        would lose ticket 16's "EOF quits cleanly" contract — a closed
        terminal must not leave a zombie process.

        ponytail: mirror of LinuxDriver.run_input_thread with one change on
        EOF; drop this subclass when upstream handles EOF itself.
        """

        def run_input_thread(self) -> None:
            import selectors
            from codecs import getincrementaldecoder

            from textual._loop import loop_last
            from textual._parser import ParseError
            from textual._xterm_parser import XTermParser

            selector = selectors.SelectSelector()
            selector.register(self.fileno, selectors.EVENT_READ)
            fileno = self.fileno
            EVENT_READ = selectors.EVENT_READ
            parser = XTermParser(self._debug)
            feed = parser.feed
            tick = parser.tick
            utf8_decoder = getincrementaldecoder("utf-8")().decode
            decode = utf8_decoder
            read = os.read

            def process_selector_events(selector_events, final=False):
                for last, (_selector_key, mask) in loop_last(selector_events):
                    if mask & EVENT_READ:
                        unicode_data = decode(read(fileno, 1024 * 4),
                                              final=final and last)
                        if not unicode_data:
                            # stdin hit EOF — quit instead of spinning.
                            self.exit_event.set()
                            self._app.call_from_thread(self._app.exit)
                            return
                        for event in feed(unicode_data):
                            self.process_message(event)
                for event in tick():
                    self.process_message(event)

            try:
                while not self.exit_event.is_set():
                    process_selector_events(selector.select(0.1))
                selector.unregister(self.fileno)
                process_selector_events(selector.select(0.1), final=True)
            finally:
                selector.close()
                try:
                    for event in feed(""):
                        pass
                except (EOFError, ParseError):
                    pass

    class LlmRatings(App):
        """Textual shell over a Session: one full-frame Static; the
        ticket-16 keymap as priority bindings (the scroll container would
        otherwise consume ↑/↓/←/→ once the table outgrows the viewport, and
        Textual 8 binds ctrl+c to copy on the Screen — the priority pass
        beats both). Digits 1–9 are bound; Session ignores any beyond the
        roles.json count, so a role added to the file extends the keymap
        without a code change."""

        BINDINGS = [
            Binding("left", "press('left')", show=False, priority=True),
            Binding("right", "press('right')", show=False, priority=True),
            Binding("up", "press('up')", show=False, priority=True),
            Binding("down", "press('down')", show=False, priority=True),
            Binding("f", "press('f')", show=False, priority=True),
            Binding("o", "press('o')", show=False, priority=True),
            Binding("enter", "press('enter')", show=False, priority=True),
            Binding("escape", "press('esc')", show=False, priority=True),
            Binding("q", "press('q')", show=False, priority=True),
            Binding("ctrl+c", "press('q')", show=False, priority=True),
            Binding("1", "press('1')", show=False, priority=True),
            Binding("2", "press('2')", show=False, priority=True),
            Binding("3", "press('3')", show=False, priority=True),
            Binding("4", "press('4')", show=False, priority=True),
            Binding("5", "press('5')", show=False, priority=True),
            Binding("6", "press('6')", show=False, priority=True),
            Binding("7", "press('7')", show=False, priority=True),
            Binding("8", "press('8')", show=False, priority=True),
            Binding("9", "press('9')", show=False, priority=True),
        ]

        def __init__(self, ds, roles, role_name=None):
            super().__init__(driver_class=_EofDriver)
            self.sess = Session(ds, roles, role_name)

        def compose(self) -> ComposeResult:
            with VerticalScroll(id="view"):
                yield Static("", id="table", markup=False)

        def on_mount(self) -> None:
            self._redraw()

        def action_press(self, key: str) -> None:
            """One keymap key → Session.key; quits on q (every key routes
            through here, so this is the single exit point)."""
            self.sess.key(key)
            if self.sess.quit:
                self.exit()
            else:
                self._redraw()

        def _redraw(self) -> None:
            """Draw the current frame; keep the selected row visible (the
            cursor's reverse-video line is the frame's one ANSI span)."""
            lines = self.sess.frame()
            self.query_one("#table", Static).update(
                Text.from_ansi("\n".join(lines)))
            sel = next((i for i, ln in enumerate(lines) if "\x1b[7m" in ln),
                       0)
            view = self.query_one("#view", VerticalScroll)
            if not view.size.height:   # not laid out yet — the initial view
                return                 # starts at the top; no anchor to set
            top, bottom = view.scroll_offset.y, view.scroll_offset.y + view.size.height
            if not (top <= sel < bottom):
                view.scroll_to(y=sel, animate=False)


def available() -> bool:
    """True when the Textual dependency is importable. Batch mode runs
    without it; the interactive path refuses to start with a clear setup
    error (checked before the fetch, so a missing dep is reported
    immediately rather than after a network round-trip)."""
    return _TEXTUAL


def run(ds, roles, role_name) -> int:
    """Run the interactive session; returns 0 — every mode has an exit key,
    and EOF/Ctrl-C quit cleanly. A missing textual dependency fails with a
    clear setup error instead of a traceback."""
    if not _TEXTUAL:
        print("error: textual is not installed — run `make deps`",
              file=sys.stderr)
        return 1
    LlmRatings(ds, roles, role_name).run()
    return 0
