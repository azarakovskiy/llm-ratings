"""Interactive TUI (tickets 16, 17, 18) — a thin Textual shell over render.py.

Ticket 16 shipped a hand-rolled ANSI TUI (termios/select, zero deps); on the
user's terminal (cmux, full-width pane) its `"\x1b[2J\x1b[H" + "\n".join()`
frames rendered as a staggered mess, while the identical bytes through a
non-TTY pipe aligned perfectly — the emulator mangles `\n`-only frames with
no cursor addressing. The fix is to stop hand-rolling, not to adjust columns
(ADR 0001). Ticket 17 replaces the I/O shell with Textual: `render.py`
stays the single source of table text (batch and TUI render identical
lines), `Session` keeps the state machine, and the `LlmRatings` App just
draws `Session.frame()` and routes keys into `Session.key()`.

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


class Session:
    """TUI state: role tab, cursor, filter, objective override, open detail
    row.

    `frame()` renders the current state; `key()` applies one key. The two
    stay separate so the Textual shell is just draw → key → redraw.
    """

    def __init__(self, ds, roles, role_name=None):
        self.ds = ds
        self.roles = roles
        self.role_i = (0 if role_name is None else
                       next(i for i, r in enumerate(roles)
                            if r["name"] == role_name))
        self.cursor = 0
        self.filt = 0
        self.obj = None       # objective override; None = role default
        self.detail_row = None    # row dict open in the detail view
        self.quit = False
        self._rows = []           # display-ordered rows of the last table

    @property
    def role(self):
        return self.roles[self.role_i]

    @property
    def objective(self):
        return self.obj or self.role["objective"]

    def frame(self):
        role = self.role
        if self.detail_row is not None:
            return (["LLM RATINGS — detail", ""]
                    + render.detail(self.ds, self.detail_row, role,
                                    self.objective)
                    + ["", "Esc back · q quit", render.ATTRIBUTION])
        lines, self._rows = render.table(
            self.ds, role, objective=self.objective,
            min_grade=FILTERS[self.filt][1])
        sel = [i for i, ln in enumerate(lines)
               if any(ln.startswith(f"  {row['model']} ")
                      for row in self._rows)]
        if sel:
            self.cursor = min(self.cursor, len(sel) - 1)
            at = sel[self.cursor]
            lines[at] = "\x1b[7m" + lines[at] + "\x1b[0m"
        state = "default" if self.obj is None else "override"
        status = (f"LLM RATINGS — {role['name']} · objective "
                  f"{render.OBJECTIVE_LABEL[self.objective]} ({state}) · "
                  f"filter: {FILTERS[self.filt][0]}")
        # render.table already carries the role header + column header lines.
        return [status, ""] + lines + ["", TABLE_FOOTER, render.ATTRIBUTION]

    def key(self, k):
        if self.quit:
            return
        if self.detail_row is not None:
            if k in ("q", "eof"):
                self.quit = True
            elif k == "esc":
                self.detail_row = None
            elif k in ("left", "right"):
                self._switch_role(k)
            return
        if k in ("q", "esc", "eof"):
            self.quit = True
        elif k in ("left", "right") or (
                k.isdigit() and 1 <= int(k) <= len(self.roles)):
            self._switch_role(k)
        elif k == "up":
            self.cursor = max(0, self.cursor - 1)
        elif k == "down":
            self.cursor += 1
        elif k == "f":
            self.filt = (self.filt + 1) % len(FILTERS)
            self.cursor = 0
        elif k == "o":
            # cap → ppi → price → role default (None); resets on role switch.
            i = _LENS.index(self.obj) if self.obj in _LENS else -1
            self.obj = _LENS[i + 1] if i + 1 < len(_LENS) else None
            self.cursor = 0
        elif k == "enter":
            if self._rows:
                self.detail_row = self._rows[self.cursor]

    def _switch_role(self, k):
        """←/→ wrap around; 1–N jump. Spec §6: the objective override resets
        on role switch so a stale lens never carries over."""
        n = len(self.roles)
        if k == "left":
            self.role_i = (self.role_i - 1) % n
        elif k == "right":
            self.role_i = (self.role_i + 1) % n
        else:
            self.role_i = int(k) - 1
        self.obj = None
        self.cursor = 0
        self.detail_row = None


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
