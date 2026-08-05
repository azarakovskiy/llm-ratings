"""Interactive TUI (ticket 16) — plain ANSI, zero dependencies (spec §1
allows it; the repo is stdlib-only). Spec §6 keymap: category nav ←/→ or
1–5, ↑/↓ row nav, `f` capability filter (all → cap = 5 → cap ≥ 4, banding
key = AA grade), `e` effort override (low → medium → high → xhigh → max →
default, reset on category switch), Enter detail view, Esc back, q quit.

The session is a small state machine (`Session`: state + key → state) over a
thin termios/select I/O shell, so the whole keymap is pipeable in tests:
`--interactive` forces TUI mode off a tty, and EOF quits cleanly. Batch mode
(non-tty stdin without the flag) is untouched in __main__.
"""

import os
import select
import sys
import time

from . import render
from .identity import EFFORTS

FILTERS = [("all", None), ("cap = 5", 5), ("cap ≥ 4", 4)]

_ARROWS = {b"\x1b[A": "up", b"\x1b[B": "down", b"\x1b[C": "right",
           b"\x1b[D": "left", b"\x1bOA": "up", b"\x1bOB": "down",
           b"\x1bOC": "right", b"\x1bOD": "left"}

# Disambiguation window: arrow keys arrive as ESC + 2 continuation bytes;
# a bare Esc with nothing after it inside the window stays an Esc. Pipe
# tests write whole sequences atomically, so the window only ever sees a
# sequence's own bytes — a bare Esc must be the last key written before EOF.
ESC_WINDOW = 0.04

TABLE_FOOTER = ("←/→ or 1–5 category · ↑/↓ move · f filter · e effort · "
                "Enter detail · Esc/q quit")


class Session:
    """TUI state: category, cursor, filter, effort override, open detail row.

    `frame()` renders the current state; `key()` applies one key. The two
    stay separate so the CLI loop is just draw → read → apply.
    """

    def __init__(self, ds, category="Chores"):
        self.ds = ds
        self.cat = next(i for i, c in enumerate(render.CATEGORIES)
                        if c[0] == category)
        self.cursor = 0
        self.filt = 0
        self.override = None      # effort override; None = category default
        self.detail_row = None    # row dict open in the detail view
        self.quit = False
        self._rows = []           # display-ordered rows of the last table

    @property
    def category(self):
        return render.CATEGORIES[self.cat]

    @property
    def effort(self):
        return self.override or self.category[1]

    def frame(self):
        name = self.category[0]
        if self.detail_row is not None:
            return (["LLM RATINGS — detail", ""]
                    + render.detail(self.ds, self.detail_row, name)
                    + ["", "Esc back · q quit", render.ATTRIBUTION])
        effort = self.effort
        lines, self._rows = render.table(self.ds, name, effort,
                                         FILTERS[self.filt][1])
        sel = [i for i, ln in enumerate(lines)
               if ln.startswith("  ") and not ln.startswith("    ")]
        if sel:
            self.cursor = min(self.cursor, len(sel) - 1)
            at = sel[self.cursor]
            lines[at] = "\x1b[7m" + lines[at] + "\x1b[0m"
        label = (f"effort {effort} (default)" if self.override is None
                 else f"effort {effort} (override)")
        status = (f"LLM RATINGS — {name} · {label} · "
                  f"league: {render.AXIS_LABEL[self.category[2]]} · "
                  f"filter: {FILTERS[self.filt][0]}")
        # render.table already carries the column header in its lines.
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
                self._switch_category(k)
            return
        if k in ("q", "esc", "eof"):
            self.quit = True
        elif k in ("left", "right", "1", "2", "3", "4", "5"):
            self._switch_category(k)
        elif k == "up":
            self.cursor = max(0, self.cursor - 1)
        elif k == "down":
            self.cursor += 1
        elif k == "f":
            self.filt = (self.filt + 1) % len(FILTERS)
            self.cursor = 0
        elif k == "e":
            if self.override is None:
                self.override = EFFORTS[0]
            else:
                i = EFFORTS.index(self.override) + 1
                self.override = EFFORTS[i] if i < len(EFFORTS) else None
            self.cursor = 0
        elif k == "enter":
            if self._rows:
                self.detail_row = self._rows[self.cursor]

    def _switch_category(self, k):
        """←/→ wrap around; 1–5 jump. Spec §6: the effort override resets
        on category switch so a stale effort never carries over."""
        n = len(render.CATEGORIES)
        if k == "left":
            self.cat = (self.cat - 1) % n
        elif k == "right":
            self.cat = (self.cat + 1) % n
        else:
            self.cat = int(k) - 1
        self.override = None
        self.cursor = 0
        self.detail_row = None


def _esc_tail(stdin):
    """Continuation bytes after ESC within the disambiguation window. Reads
    one byte at a time so a key that follows an arrow key in the pipe is
    never swallowed (a bare Esc stays alone)."""
    fd = stdin.fileno()
    tail = b""
    end = time.monotonic() + ESC_WINDOW
    while time.monotonic() < end and len(tail) < 2:
        r, _, _ = select.select([stdin], [], [], 0.01)
        if not r:
            break
        chunk = os.read(fd, 1)
        if not chunk:
            break
        tail += chunk
    return tail


def read_key(stdin):
    """One key from stdin: "up"/"down"/"left"/"right"/"esc"/"enter"/"eof",
    a digit 1–5, or a letter (f, e, q — Ctrl-C maps to q)."""
    fd = stdin.fileno()
    b = os.read(fd, 1)
    if not b:
        return "eof"
    if b == b"\x1b":
        seq = b + _esc_tail(stdin)
        return _ARROWS.get(seq, "esc")
    if b in (b"\n", b"\r"):
        return "enter"
    if b == b"\x03":          # Ctrl-C — raw mode swallows SIGINT
        return "q"
    return b.decode("ascii", "replace").lower()


def _emit(lines):
    sys.stdout.write("\x1b[2J\x1b[H" + "\n".join(lines) + "\n")
    sys.stdout.flush()


def run(ds, category="Chores"):
    """Interactive session: draw → read → apply until q/Esc/EOF. Returns 0 —
    every mode has an exit key, and EOF (a closed pipe) also quits cleanly."""
    stdin = sys.stdin
    fd = stdin.fileno()
    saved = None
    if stdin.isatty():
        import termios
        import tty
        saved = termios.tcgetattr(fd)
        tty.setraw(fd)
    try:
        sess = Session(ds, category)
        while not sess.quit:
            _emit(sess.frame())
            sess.key(read_key(stdin))
    finally:
        if saved is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, saved)
    return 0
