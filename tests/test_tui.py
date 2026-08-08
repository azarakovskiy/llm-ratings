"""Tickets 16–18 — Textual TUI contract tests (spec §6–7). Observable
behavior only: the real app driven through Textual's `run_test()` harness —
key presses via the Pilot, assertions on the displayed frame's plain text
and its reverse-video selection span. Batch mode (piped stdin, no TTY) is
unchanged and pinned here too. The ticket-16 pipe-key seam (`--interactive`
+ hand-rolled ANSI frame parsing) is gone with the plain-ANSI TUI (ADR
0001); the pty test below still drives the real terminal driver path.
Ticket 18: roles come from roles.json (tab order = file order, `LLM_RATINGS_
ROLES` swaps the file), the `o` key cycles the objective override (the `e`
effort override is gone — efforts come from the active objective), and the
detail view gains the alternatives band and the OpenRouter context line.
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

from llmratings import fetch, identity, render
from llmratings.tui import LlmRatings

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / ".scratch" / "llm-ratings" / "fixtures" / "main"
_DATA = re.compile(r"^ {2}(?:\d|—)")
ROLES = render.load_roles(REPO / "llmratings" / "roles.json")


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
            self.assertTrue(wait_for("LLM RATINGS \u2014 Generic"),
                            "key '2' did not switch the role")
            os.write(master, b"q")
            rc = p.wait(timeout=10)
        finally:
            stop.set()
            os.close(master)
            t.join(timeout=2)
        self.assertEqual(rc, 0)
        text_out = b"".join(out).decode("utf-8", "replace")
        self.assertIn("LLM RATINGS \u2014 Generic \u00b7 objective ppi (default)",
                      text_out)
        self.assertNotIn("Traceback", text_out)


class Navigation(unittest.IsolatedAsyncioTestCase):
    async def test_role_nav_arrow_and_digits(self):
        # 2 → Generic; → → Researcher; ← → Generic; 5 → Orchestrator;
        # 1 → Chores. Each role shows its objective as the default lens.
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("2")
            self.assertIn("LLM RATINGS — Generic · objective ppi (default)", text(app))
            self.assertIn("Generic — objective ppi — best PPI first", text(app))
            await pilot.press("right")
            self.assertIn("LLM RATINGS — Researcher · objective cap (default)", text(app))
            await pilot.press("left")
            self.assertIn("LLM RATINGS — Generic · objective ppi (default)", text(app))
            await pilot.press("5")
            self.assertIn("LLM RATINGS — Orchestrator · objective ppi (default)", text(app))
            await pilot.press("1")
            self.assertIn("LLM RATINGS — Chores · objective price (default)", text(app))

    async def test_row_nav_up_down(self):
        # Chores display order: Luna (medium), Kimi, Sol, GPT-5.5, Opus —
        # Terra is source-only and absent from every role table.
        app = LlmRatings(DS, ROLES)
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
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("up", "up")
            self.assertIn("GPT-5.6 Luna", rev_row(app))

    async def test_footer_drops_e_effort_key(self):
        # Ticket 18: the `e` effort override is gone — the footer advertises
        # `o objective`, never an effort key.
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            self.assertIn("o objective", text(app))
            self.assertNotIn("e effort", text(app))


class FiltersAndEffort(unittest.IsolatedAsyncioTestCase):
    async def test_f_cycles_all_to_cap5_to_cap4(self):
        # Chores AA grades at the objective-selected efforts: Luna medium 2,
        # Kimi low 3, Sol low 4, GPT-5.5 low 2, Opus low 5. cap=5 keeps
        # Opus only; cap≥4 keeps Sol and Opus; all → 5 rows (Terra is
        # source-only, so the old 6th row is gone).
        app = LlmRatings(DS, ROLES)
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
            self.assertEqual(len(data_rows(text(app))), 5)

    async def test_o_cycles_to_default_and_back(self):
        # Chores default IS price: cap → ppi → price → default(price).
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("o")
            self.assertIn("objective cap (override)", text(app))
            self.assertIn("Chores — objective cap — best capability first", text(app))
            await pilot.press("o")
            self.assertIn("objective ppi (override)", text(app))
            await pilot.press("o")
            self.assertIn("objective price (override)", text(app))
            await pilot.press("o")
            self.assertIn("objective price (default)", text(app))

    async def test_o_resets_on_role_switch(self):
        # Chores cap override → right into Generic (default ppi): the
        # "(default)" suffix proves the stale override was dropped.
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("o", "right")
            self.assertIn("LLM RATINGS — Generic · objective ppi (default)", text(app))
            self.assertNotIn("override", text(app))


class DetailView(unittest.IsolatedAsyncioTestCase):
    async def test_detail_disagreement_on(self):
        # Researcher (cap): row 1 = Luna max. DSW grade 1, AA 2, TB 4 →
        # span 3 → flag set.
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("3", "down", "enter")
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
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("3", "down", "down", "enter")
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
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("3", "down", "down", "down", "enter")
            f = text(app)
            self.assertIn("Kimi K3 max — Kimi", f)
            self.assertIn("no TB row at max effort", f)
            self.assertIn("PPI      67 = 57.1 / $0.855   value grade 4", f)
            self.assertIn("price tier 2", f)
            self.assertNotIn("sources disagree", f)

    async def test_detail_price_tier_dash_without_cost(self):
        # An AA row with no per-task cost (and no pricing) must render
        # price tier —, never the literal None. The cap lens (Researcher)
        # selects the costless config — the price lens would drop it.
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
        app = LlmRatings(d, ROLES, "Researcher")
        async with app.run_test() as pilot:
            await pilot.press("enter")
            f = text(app)
            self.assertIn("GPT-5.6 Luna low — Acme", f)
            self.assertIn("list price  n/a   price tier —", f)
            self.assertNotIn("price tier None", f)
            self.assertIn("not ranked — no AA price, so no frontier/dominated position", f)

    async def test_detail_alternatives(self):
        # Researcher, Opus max (row 0): cheaper configs within 5 AA pts,
        # price-sorted, top 3 — ΔAA vs the row's own index.
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("3", "enter")
            f = text(app)
            self.assertIn("alternatives — cheaper, within 5 AA pts, price-sorted:", f)
            self.assertIn("  GPT-5.6 Sol high — $0.549, ΔAA -4.8", f)
            self.assertIn("  Claude Opus 5 medium — $0.722, ΔAA -4.4", f)
            self.assertIn("  GPT-5.6 Sol xhigh — $0.833, ΔAA -3.0", f)

    async def test_detail_context_from_or(self):
        # OR rows join context + modalities onto models; models without an
        # OR row (Kimi K3 — the deliberate fixture omission) say so.
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("3", "enter")
            self.assertIn("context   200k tokens   in: text, image, file; out: text",
                          text(app))
            await pilot.press("escape", "down", "down", "down", "enter")
            self.assertIn("context   n/a — no OpenRouter row for this model",
                          text(app))

    async def test_esc_returns_to_table(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("3", "enter")
            self.assertIn("LLM RATINGS — detail", text(app))
            await pilot.press("escape")
            f = text(app)
            self.assertIn("LLM RATINGS — Researcher · objective cap (default)", f)
            self.assertIn("★ frontier", f)
            self.assertNotIn("LLM RATINGS — detail", f)


class RolesFile(unittest.IsolatedAsyncioTestCase):
    """Ticket 18: roles.json drives the tab keymap — a role added to the
    file extends the digit bindings without a code change."""

    SIX = [
        {"name": "Mail Sorter", "description": "Triage an inbox.",
         "capacity": "Fast and cheap; speed matters.", "objective": "price"},
        {"name": "Chores", "description": "Light, repetitive agent tasks.",
         "capacity": "Speed first, then price.", "objective": "price",
         "floor": 2},
        {"name": "Generic", "description": "Mixed everyday work.",
         "capacity": "Best PPI.", "objective": "ppi", "floor": 2},
        {"name": "Researcher", "description": "Deep-dive questions.",
         "capacity": "Peak reasoning.", "objective": "cap", "floor": 2},
        {"name": "Coder", "description": "Implementation work.",
         "capacity": "Peak reasoning.", "objective": "cap", "floor": 2},
        {"name": "Orchestrator", "description": "Plans and delegates.",
         "capacity": "Best PPI.", "objective": "ppi", "floor": 2},
    ]

    async def test_roles_file_drives_number_keys(self):
        # A 6-role file extends the digit keymap: 6 reaches the file's 6th
        # role (a key the default 5-role file cannot reach), and 1 reaches
        # Mail Sorter — the role added at the head of the file. Roles flow
        # through the same loader as production (floor defaults to 2), not
        # as hand-built dicts.
        with tempfile.TemporaryDirectory() as td:
            Path(td, "roles.json").write_text(json.dumps(self.SIX))
            roles = render.load_roles(Path(td, "roles.json"))
        app = LlmRatings(DS, roles, "Chores")
        async with app.run_test() as pilot:
            await pilot.press("6")
            self.assertIn("LLM RATINGS — Orchestrator · objective ppi (default)",
                          text(app))
            await pilot.press("1")
            self.assertIn("LLM RATINGS — Mail Sorter · objective price (default)",
                          text(app))


class Quit(unittest.IsolatedAsyncioTestCase):
    async def test_q_quits_cleanly_from_table(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("q")
            self.assertFalse(app.is_running)

    async def test_q_quits_cleanly_from_detail(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("3", "enter")
            self.assertIn("LLM RATINGS — detail", text(app))
            await pilot.press("q")
            self.assertFalse(app.is_running)

    async def test_ctrl_c_quits_cleanly(self):
        # Textual 8 no longer quits on ctrl+c by default (it shows a "use
        # ctrl+q" notice); the TUI rebinds it to quit — the contract is a
        # clean exit, not a notification.
        app = LlmRatings(DS, ROLES)
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
