"""Ticket 16 — interactive TUI contract tests (spec §6–7). Observable
behavior only: key sequences piped into the real CLI in a subprocess with
--interactive, asserted on the rendered frames and exit codes; batch mode
(piped stdin without the flag) is unchanged and pinned here too.

Key protocol for the pipe: whole sequences are written atomically (the
escape parser's 40 ms window only ever sees an arrow key's own bytes), and a
bare Esc must be the last key before EOF — the window can merge a bare Esc
with a key that follows it in the same buffer. Every sequence below ends
with EOF, which quits cleanly.
"""

import json
import os
import pty
import re
import select
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / ".scratch" / "llm-ratings" / "fixtures" / "main"
CLEAR = b"\x1b[2J\x1b[H"
_DATA = re.compile(r"^ {2}(?:\d|—)")


def run_tui(keys, fixtures=FIXTURES):
    """Run the CLI in TUI mode with piped key bytes; returns CompletedProcess."""
    env = dict(os.environ, LLM_RATINGS_AA_API_KEY="dummy")
    return subprocess.run(
        [sys.executable, "-m", "llmratings", "--interactive",
         "--fixtures", str(fixtures)],
        input=keys.encode(), capture_output=True, cwd=REPO, env=env)


def frames(p):
    """Rendered frames, one per key processed (f0 = the initial frame)."""
    return [f.decode() for f in p.stdout.split(CLEAR) if f]


def plain(frame):
    """Frame with the cursor's reverse-video codes stripped."""
    return frame.replace("\x1b[7m", "").replace("\x1b[0m", "")


def data_rows(frame):
    """Table data-row lines (two-space indent, grade cell first)."""
    return [ln for ln in plain(frame).splitlines() if _DATA.match(ln)]


def rev_row(frame):
    """The cursor-marked (reverse-video) row line of a table frame."""
    return next(ln for ln in frame.splitlines() if "\x1b[7m" in ln)


class Seam(unittest.TestCase):
    """The batch/TUI seam: piped stdin without the flag stays batch; the
    flag forces the TUI off a tty (the pipe drives it)."""

    def test_piped_stdin_without_flag_stays_batch(self):
        env = dict(os.environ, LLM_RATINGS_AA_API_KEY="dummy")
        r = subprocess.run(
            [sys.executable, "-m", "llmratings", "--fixtures", str(FIXTURES)],
            input=b"", capture_output=True, cwd=REPO, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("frontier: ", r.stdout.decode())
        self.assertNotIn("\x1b[2J", r.stdout.decode())

    def test_interactive_flag_renders_frames_off_a_tty(self):
        r = run_tui("q")
        self.assertEqual(r.returncode, 0)
        out = r.stdout.decode()
        self.assertIn("\x1b[2J", out)          # TUI clear-screen per frame
        self.assertIn("artificialanalysis.ai", out)  # attribution in the TUI

    def test_tty_stdin_piped_stdout_stays_batch(self):
        # stdin is a terminal but stdout is redirected: batch output, never
        # ANSI frames (the ticket's batch-unchanged contract).
        env = dict(os.environ, LLM_RATINGS_AA_API_KEY="dummy")
        master, slave = pty.openpty()
        try:
            p = subprocess.run(
                [sys.executable, "-m", "llmratings", "--fixtures",
                 str(FIXTURES)],
                stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=REPO, env=env, timeout=15)
        finally:
            os.close(master)
            os.close(slave)
        self.assertEqual(p.returncode, 0)
        out = p.stdout.decode()
        self.assertIn("frontier: ", out)
        self.assertNotIn("\x1b[2J", out)

    def test_tty_path_runs_termios_tui(self):
        # Both ends a pty: the real termios raw-mode path — keys written to
        # the master drive the session, and q restores the terminal on exit.
        env = dict(os.environ, LLM_RATINGS_AA_API_KEY="dummy")
        master, slave = pty.openpty()
        p = subprocess.Popen(
            [sys.executable, "-m", "llmratings", "--fixtures", str(FIXTURES)],
            stdin=slave, stdout=slave, stderr=slave, cwd=REPO, env=env)
        os.close(slave)
        out = []
        stop = threading.Event()

        def drain():
            while not stop.is_set():
                r, _, _ = select.select([master], [], [], 0.1)
                if not r:
                    continue
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    return
                if not chunk:
                    return
                out.append(chunk)
        t = threading.Thread(target=drain, daemon=True)
        t.start()
        try:
            time.sleep(0.3)
            os.write(master, b"2")
            time.sleep(0.3)
            os.write(master, b"q")
            rc = p.wait(timeout=10)
        finally:
            stop.set()
            os.close(master)
            t.join(timeout=2)
        self.assertEqual(rc, 0)
        text = b"".join(out).decode("utf-8", "replace")
        self.assertIn("LLM RATINGS \u2014 Everyday \u00b7 effort medium (default)", text)
        self.assertNotIn("Traceback", text)


class Navigation(unittest.TestCase):
    def test_category_nav_arrow_and_digits(self):
        # 2 → Everyday; → → Deliberate; ← → Everyday; 5 → Best Value; 1 → Chores.
        r = run_tui("2\x1b[C\x1b[D51")
        self.assertEqual(r.returncode, 0)
        f = frames(r)
        self.assertIn("LLM RATINGS — Everyday · effort medium (default)", f[1])
        self.assertIn("Everyday — medium effort — best PPI first", f[1])
        self.assertIn("LLM RATINGS — Deliberate · effort high (default)", f[2])
        self.assertIn("LLM RATINGS — Everyday · effort medium (default)", f[3])
        self.assertIn("LLM RATINGS — Best Value · effort high (default)", f[4])
        self.assertIn("LLM RATINGS — Chores · effort low (default)", f[5])

    def test_row_nav_up_down(self):
        # Chores display order: Luna, Kimi, Sol, GPT-5.5, Opus, Terra.
        r = run_tui("\x1b[B\x1b[B\x1b[B\x1b[A")
        self.assertEqual(r.returncode, 0)
        f = frames(r)
        self.assertIn("GPT-5.6 Luna", rev_row(f[0]))
        self.assertIn("Kimi K3", rev_row(f[1]))
        self.assertIn("GPT-5.6 Sol", rev_row(f[2]))
        self.assertIn("GPT-5.5", rev_row(f[3]))
        self.assertIn("GPT-5.6 Sol", rev_row(f[4]))

    def test_up_at_top_stays(self):
        r = run_tui("\x1b[A\x1b[A")
        self.assertEqual(r.returncode, 0)
        self.assertIn("GPT-5.6 Luna", rev_row(frames(r)[-1]))


class FiltersAndEffort(unittest.TestCase):
    def test_f_cycles_all_to_cap5_to_cap4(self):
        # Chores low AA grades: Luna 1, Kimi 3, Sol 4, GPT-5.5 2, Opus 5,
        # Terra —. cap=5 keeps Opus only; cap≥4 keeps Sol and Opus.
        r = run_tui("fff")
        self.assertEqual(r.returncode, 0)
        f = frames(r)
        self.assertIn("filter: cap = 5", f[1])
        self.assertEqual(len(data_rows(f[1])), 1)
        self.assertIn("Claude Opus 5", data_rows(f[1])[0])
        self.assertIn("filter: cap ≥ 4", f[2])
        rows = data_rows(f[2])
        self.assertEqual(len(rows), 2)
        self.assertTrue(any("GPT-5.6 Sol" in ln for ln in rows))
        self.assertIn("filter: all", f[3])
        self.assertEqual(len(data_rows(f[3])), 6)

    def test_e_cycles_to_default_and_back(self):
        # low → medium → high → xhigh → max → default(low).
        r = run_tui("eeeeee")
        self.assertEqual(r.returncode, 0)
        f = frames(r)
        self.assertIn("effort low (override)", f[1])
        self.assertIn("effort medium (override)", f[2])
        self.assertIn("Chores — medium effort — cheapest first", f[2])
        self.assertIn("effort high (override)", f[3])
        self.assertIn("effort xhigh (override)", f[4])
        self.assertIn("effort max (override)", f[5])
        self.assertIn("effort low (default)", f[6])

    def test_e_resets_on_category_switch(self):
        # Chores high override → right into Everyday (default medium): the
        # "(default)" suffix proves the stale high override was dropped.
        r = run_tui("eee\x1b[C")
        self.assertEqual(r.returncode, 0)
        f = frames(r)
        self.assertIn("LLM RATINGS — Everyday · effort medium (default)", f[4])
        self.assertNotIn("override", f[4])


class DetailView(unittest.TestCase):
    def _deep_row(self, downs):
        """Open the Deep table (4), move `downs` rows, press Enter."""
        return run_tui("4" + "\x1b[B" * downs + "\r")

    def test_detail_disagreement_on(self):
        # Luna max: DSW grade 1, AA 2, TB 4 → span 3 → flag set.
        r = self._deep_row(1)
        self.assertEqual(r.returncode, 0)
        f = frames(r)[3]
        self.assertIn("LLM RATINGS — detail", f)
        self.assertIn("GPT-5.6 Luna max — OpenAI", f)
        self.assertIn("DeepSWE  grade 1   raw 0.672    rank 5 of 5", f)
        self.assertIn("AA       grade 2   raw 51.2     rank 4 of 4", f)
        self.assertIn("TB       grade 4   raw 0.757    rank 2 of 3", f)
        self.assertIn("PPI      1.1k = 51.2 / $0.047   value grade 5", f)
        self.assertIn("list price  $0.20/$1.20 per M in/out (max variant)", f)
        self.assertIn("price tier 1", f)
        self.assertIn("speed     180.5 t/s   speed tier 5", f)
        self.assertIn("frontier * — no other configuration beats this on rating AND price", f)
        self.assertIn("sources disagree (DeepSWE 1 vs TB 4 at max)", f)

    def test_detail_disagreement_off(self):
        # Sol max: DSW 4, AA 4, TB 5 → span 1 → no flag; dominated arrow.
        r = self._deep_row(2)
        self.assertEqual(r.returncode, 0)
        f = frames(r)[4]
        self.assertIn("GPT-5.6 Sol max — OpenAI", f)
        self.assertIn("DeepSWE  grade 4   raw 0.727    rank 2 of 5", f)
        self.assertIn("AA       grade 4   raw 58.9     rank 2 of 4", f)
        self.assertIn("TB       grade 5   raw 0.769    rank 1 of 3", f)
        self.assertIn("PPI      48 = 58.9 / $1.23   value grade 3", f)
        self.assertIn("dominated — → Claude Opus 5 high: same rating, save $0.0066", f)
        self.assertNotIn("sources disagree", f)

    def test_detail_tb_dash(self):
        # Kimi max: no TB row → the TB line is the honest `—` case.
        r = self._deep_row(3)
        self.assertEqual(r.returncode, 0)
        f = frames(r)[5]
        self.assertIn("Kimi K3 max — Kimi", f)
        self.assertIn("no TB row at max effort", f)
        self.assertIn("PPI      67 = 57.1 / $0.855   value grade 4", f)
        self.assertIn("price tier 2", f)
        self.assertNotIn("sources disagree", f)

    def test_detail_not_ranked_row(self):
        # Terra low is source-only (no AA row): no frontier/dominated
        # position — the detail must still state that status explicitly.
        r = run_tui("\x1b[B" * 5 + "\r")   # Chores, 5 downs → Terra
        self.assertEqual(r.returncode, 0)
        f = frames(r)[6]
        self.assertIn("gpt-5-6-terra low — —", f)
        self.assertIn("not ranked — no AA price, so no frontier/dominated position", f)
        self.assertIn("price tier —", f)
        self.assertIn("PPI      n/a — no AA price at this effort", f)
        self.assertIn("speed     —   no AA speed at this effort", f)

    def test_detail_price_tier_dash_without_cost(self):
        # An AA row with no per-task cost (and no pricing) must render
        # price tier —, never the literal None.
        AA = ('{"id": "u1", "name": "GPT-5.6 Luna (low)",'
              ' "slug": "gpt-5-6-luna-low", "model_creator": {"name": "Acme"},'
              ' "evaluations": {"artificial_analysis_intelligence_index": 33.3}}')
        with tempfile.TemporaryDirectory() as td:
            Path(td, "aa.json").write_text(json.dumps({"data": [json.loads(AA)]}))
            ds = {"rows": [{"model": "gpt-5-6-luna", "reasoning_effort": "low",
                            "pass_at_1": 0.4}]}
            Path(td, "deepswe.json").write_text(json.dumps(ds))
            Path(td, "tb.json").write_text(
                json.dumps({"listing": [], "submissions": {}}))
            r = run_tui("\r", td)
        self.assertEqual(r.returncode, 0)
        f = frames(r)[1]
        self.assertIn("GPT-5.6 Luna low — Acme", f)
        self.assertIn("list price  n/a   price tier —", f)
        self.assertNotIn("price tier None", f)
        self.assertIn("not ranked — no AA price, so no frontier/dominated position", f)

    def test_esc_returns_to_table(self):
        r = run_tui("4\r\x1b")
        self.assertEqual(r.returncode, 0)
        f = frames(r)
        self.assertIn("LLM RATINGS — detail", f[2])
        self.assertIn("LLM RATINGS — Deep · effort max (default)", f[3])
        self.assertIn("★ frontier", f[3])
        self.assertNotIn("LLM RATINGS — detail", f[3])


class Quit(unittest.TestCase):
    def test_q_quits_cleanly_from_table(self):
        r = run_tui("q")
        self.assertEqual(r.returncode, 0)

    def test_q_quits_cleanly_from_detail(self):
        r = run_tui("4\rq")
        self.assertEqual(r.returncode, 0)
        self.assertIn("LLM RATINGS — detail", frames(r)[2])


if __name__ == "__main__":
    unittest.main()
