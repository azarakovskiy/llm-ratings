"""Ticket 17 — Textual TUI contract tests (spec §6–7). Observable behavior
only: the real app driven through Textual's `run_test()` harness — key
presses via the Pilot, assertions on the displayed frame's plain text and
its reverse-video selection span. Batch mode (piped stdin, no TTY) is
unchanged and pinned here too. The ticket-16 pipe-key seam (`--interactive`
+ hand-rolled ANSI frame parsing) is gone with the plain-ANSI TUI (ADR
0001); the pty test below still drives the real terminal driver path.
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

from llmratings import fetch, identity
from llmratings.tui import LlmRatings

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / ".scratch" / "llm-ratings" / "fixtures" / "main"
_DATA = re.compile(r"^ {2}(?:\d|—)")


def build_ds(fixtures=FIXTURES):
    """The fixture-fed Dataset the CLI builds for --fixtures runs."""
    raw = fetch.fetch_all(str(fixtures))
    aliases = identity.load_aliases(REPO / "llmratings" / "aliases.json")
    return identity.build(aliases, raw)


DS = build_ds()


def text(app):
    """Plain text of the displayed frame (styles stripped)."""
    return str(app.query_one("#table").content)


def data_rows(frame):
    """Table data-row lines (two-space indent, grade cell first)."""
    return [ln for ln in frame.splitlines() if _DATA.match(ln)]


def rev_row(app):
    """The cursor-marked (reverse-video) row line of the current frame."""
    t = app.query_one("#table").content
    for span in t.spans:
        if span.style.reverse:
            return t.plain[span.start:span.end]
    raise AssertionError("no reverse-video row in the frame")


class Seam(unittest.TestCase):
    """The batch/TUI seam: piped stdin stays batch, and a real TTY drives
    the Textual terminal path."""

    def test_piped_stdin_without_flag_stays_batch(self):
        env = dict(os.environ, LLM_RATINGS_AA_API_KEY="dummy")
        r = subprocess.run(
            [sys.executable, "-m", "llmratings", "--fixtures", str(FIXTURES)],
            input=b"", capture_output=True, cwd=REPO, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("frontier: ", r.stdout.decode())
        self.assertNotIn("\x1b[2J", r.stdout.decode())

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

    def test_tty_path_runs_textual_tui(self):
        # Both ends a pty: the real Textual terminal driver — wait for the
        # first frame, then drive and quit, and assert a clean exit.
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

        def wait_for(needle, timeout=15):
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if needle in b"".join(out).decode("utf-8", "replace"):
                    return True
                if p.poll() is not None:
                    return False
                time.sleep(0.1)
            return False

        try:
            self.assertTrue(wait_for("LLM RATINGS \u2014 Chores"),
                            "no initial TUI frame from the Textual driver")
            os.write(master, b"2")
            self.assertTrue(wait_for("LLM RATINGS \u2014 Everyday"),
                            "key '2' did not switch the category")
            os.write(master, b"q")
            rc = p.wait(timeout=10)
        finally:
            stop.set()
            os.close(master)
            t.join(timeout=2)
        self.assertEqual(rc, 0)
        text_out = b"".join(out).decode("utf-8", "replace")
        self.assertIn("LLM RATINGS \u2014 Everyday \u00b7 effort medium (default)", text_out)
        self.assertNotIn("Traceback", text_out)


class Navigation(unittest.IsolatedAsyncioTestCase):
    async def test_category_nav_arrow_and_digits(self):
        # 2 → Everyday; → → Deliberate; ← → Everyday; 5 → Best Value; 1 → Chores.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("2")
            self.assertIn("LLM RATINGS — Everyday · effort medium (default)", text(app))
            self.assertIn("Everyday — medium effort — best PPI first", text(app))
            await pilot.press("right")
            self.assertIn("LLM RATINGS — Deliberate · effort high (default)", text(app))
            await pilot.press("left")
            self.assertIn("LLM RATINGS — Everyday · effort medium (default)", text(app))
            await pilot.press("5")
            self.assertIn("LLM RATINGS — Best Value · effort high (default)", text(app))
            await pilot.press("1")
            self.assertIn("LLM RATINGS — Chores · effort low (default)", text(app))

    async def test_row_nav_up_down(self):
        # Chores display order: Luna, Kimi, Sol, GPT-5.5, Opus, Terra.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            self.assertIn("GPT-5.6 Luna", rev_row(app))
            await pilot.press("down")
            self.assertIn("Kimi K3", rev_row(app))
            await pilot.press("down")
            self.assertIn("GPT-5.6 Sol", rev_row(app))
            await pilot.press("down")
            self.assertIn("GPT-5.5", rev_row(app))
            await pilot.press("up")
            self.assertIn("GPT-5.6 Sol", rev_row(app))

    async def test_up_at_top_stays(self):
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("up", "up")
            self.assertIn("GPT-5.6 Luna", rev_row(app))


class FiltersAndEffort(unittest.IsolatedAsyncioTestCase):
    async def test_f_cycles_all_to_cap5_to_cap4(self):
        # Chores low AA grades: Luna 1, Kimi 3, Sol 4, GPT-5.5 2, Opus 5,
        # Terra —. cap=5 keeps Opus only; cap≥4 keeps Sol and Opus.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("f")
            self.assertIn("filter: cap = 5", text(app))
            self.assertEqual(len(data_rows(text(app))), 1)
            self.assertIn("Claude Opus 5", data_rows(text(app))[0])
            await pilot.press("f")
            self.assertIn("filter: cap ≥ 4", text(app))
            rows = data_rows(text(app))
            self.assertEqual(len(rows), 2)
            self.assertTrue(any("GPT-5.6 Sol" in ln for ln in rows))
            await pilot.press("f")
            self.assertIn("filter: all", text(app))
            self.assertEqual(len(data_rows(text(app))), 6)

    async def test_e_cycles_to_default_and_back(self):
        # low → medium → high → xhigh → max → default(low).
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("e")
            self.assertIn("effort low (override)", text(app))
            await pilot.press("e")
            self.assertIn("effort medium (override)", text(app))
            self.assertIn("Chores — medium effort — cheapest first", text(app))
            await pilot.press("e")
            self.assertIn("effort high (override)", text(app))
            await pilot.press("e")
            self.assertIn("effort xhigh (override)", text(app))
            await pilot.press("e")
            self.assertIn("effort max (override)", text(app))
            await pilot.press("e")
            self.assertIn("effort low (default)", text(app))

    async def test_e_resets_on_category_switch(self):
        # Chores high override → right into Everyday (default medium): the
        # "(default)" suffix proves the stale high override was dropped.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("e", "e", "e", "right")
            self.assertIn("LLM RATINGS — Everyday · effort medium (default)", text(app))
            self.assertNotIn("override", text(app))


class DetailView(unittest.IsolatedAsyncioTestCase):
    async def test_detail_disagreement_on(self):
        # Luna max: DSW grade 1, AA 2, TB 4 → span 3 → flag set.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("4", "down", "enter")
            f = text(app)
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

    async def test_detail_disagreement_off(self):
        # Sol max: DSW 4, AA 4, TB 5 → span 1 → no flag; dominated arrow.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("4", "down", "down", "enter")
            f = text(app)
            self.assertIn("GPT-5.6 Sol max — OpenAI", f)
            self.assertIn("DeepSWE  grade 4   raw 0.727    rank 2 of 5", f)
            self.assertIn("AA       grade 4   raw 58.9     rank 2 of 4", f)
            self.assertIn("TB       grade 5   raw 0.769    rank 1 of 3", f)
            self.assertIn("PPI      48 = 58.9 / $1.23   value grade 3", f)
            self.assertIn("dominated — → Claude Opus 5 high: same rating, save $0.0066", f)
            self.assertNotIn("sources disagree", f)

    async def test_detail_tb_dash(self):
        # Kimi max: no TB row → the TB line is the honest `—` case.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("4", "down", "down", "down", "enter")
            f = text(app)
            self.assertIn("Kimi K3 max — Kimi", f)
            self.assertIn("no TB row at max effort", f)
            self.assertIn("PPI      67 = 57.1 / $0.855   value grade 4", f)
            self.assertIn("price tier 2", f)
            self.assertNotIn("sources disagree", f)

    async def test_detail_not_ranked_row(self):
        # Terra low is source-only (no AA row): no frontier/dominated
        # position — the detail must still state that status explicitly.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("down", "down", "down", "down", "down", "enter")
            f = text(app)
            self.assertIn("gpt-5-6-terra low — —", f)
            self.assertIn("not ranked — no AA price, so no frontier/dominated position", f)
            self.assertIn("price tier —", f)
            self.assertIn("PPI      n/a — no AA price at this effort", f)
            self.assertIn("speed     —   no AA speed at this effort", f)

    async def test_detail_price_tier_dash_without_cost(self):
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
            d = build_ds(td)
        app = LlmRatings(d)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            f = text(app)
            self.assertIn("GPT-5.6 Luna low — Acme", f)
            self.assertIn("list price  n/a   price tier —", f)
            self.assertNotIn("price tier None", f)
            self.assertIn("not ranked — no AA price, so no frontier/dominated position", f)

    async def test_esc_returns_to_table(self):
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("4", "enter")
            self.assertIn("LLM RATINGS — detail", text(app))
            await pilot.press("escape")
            f = text(app)
            self.assertIn("LLM RATINGS — Deep · effort max (default)", f)
            self.assertIn("★ frontier", f)
            self.assertNotIn("LLM RATINGS — detail", f)


class Quit(unittest.IsolatedAsyncioTestCase):
    async def test_q_quits_cleanly_from_table(self):
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("q")
            self.assertFalse(app.is_running)

    async def test_q_quits_cleanly_from_detail(self):
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("4", "enter")
            self.assertIn("LLM RATINGS — detail", text(app))
            await pilot.press("q")
            self.assertFalse(app.is_running)

    async def test_ctrl_c_quits_cleanly(self):
        # Textual 8 no longer quits on ctrl+c by default (it shows a "use
        # ctrl+q" notice); the TUI rebinds it to quit — the contract is a
        # clean exit, not a notification.
        app = LlmRatings(DS)
        async with app.run_test() as pilot:
            await pilot.press("ctrl+c")
            self.assertFalse(app.is_running)

    def test_stdin_eof_quits_cleanly(self):
        # Ticket 16's "EOF quits cleanly" contract: closing the terminal
        # (stdin EOF) must exit the real driver, not leave a zombie
        # spinning on the closed fd (_EofDriver).
        env = dict(os.environ, LLM_RATINGS_AA_API_KEY="dummy")
        master, slave = pty.openpty()
        p = subprocess.Popen(
            [sys.executable, "-m", "llmratings", "--fixtures",
             str(FIXTURES)],
            stdin=slave, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, cwd=REPO, env=env)
        os.close(slave)
        os.close(master)          # terminal gone → stdin EOF
        try:
            rc = p.wait(timeout=10)
        finally:
            if p.poll() is None:
                p.kill()
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
