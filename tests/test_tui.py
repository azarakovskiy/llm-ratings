"""TUI behavior through real source fixtures, the shared policy and Textual.

The terminal shell keeps navigation, objective overrides and evidence views;
it does not implement a second selection policy or depend on table padding.
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
_DATA = re.compile(r"^ {2}(?!Model\s)\S")
ROLES = render.load_roles(REPO / "llmratings" / "roles.json")


def build_ds(fixtures=FIXTURES):
    """The fixture-fed Dataset the CLI builds for --fixtures runs."""
    raw = fetch.fetch_all(str(fixtures))
    aliases = identity.load_aliases(REPO / "llmratings" / "aliases.json")
    return identity.build(aliases, raw)


DS = build_ds()


def role(name):
    return next(r for r in ROLES if r["name"] == name)


def text(app):
    """Plain text of the displayed frame (styles stripped)."""
    return str(app.query_one("#table").content)


def plain(app):
    """Evidence text without terminal alignment whitespace."""
    return " ".join(text(app).split())


def data_rows(frame):
    """Selectable table lines start with two spaces and a model name."""
    return [ln for ln in frame.splitlines() if _DATA.match(ln)]


def rev_row(app):
    """The cursor-marked (reverse-video) row line of the current frame."""
    t = app.query_one("#table").content
    for span in t.spans:
        if span.style.reverse:
            return t.plain[span.start:span.end]
    raise AssertionError("no reverse-video row in the frame")


async def open_model(app, pilot, name):
    """Open evidence by navigating the displayed rows, not policy internals."""
    at = next(i for i, line in enumerate(data_rows(text(app)))
              if line.startswith(f"  {name} "))
    if at:
        await pilot.press(*(["down"] * at))
    await pilot.press("enter")


class Seam(unittest.TestCase):
    """Piped input/output stays batch; a real terminal uses Textual."""

    def test_piped_stdin_without_flag_stays_batch(self):
        env = dict(os.environ, LLM_RATINGS_AA_API_KEY="dummy")
        r = subprocess.run(
            [sys.executable, "-m", "llmratings", "--fixtures", str(FIXTURES)],
            input=b"", capture_output=True, cwd=REPO, env=env)
        self.assertEqual(r.returncode, 0)
        out = r.stdout.decode()
        self.assertIn("Explorer", out)
        self.assertIn("Best value", out)
        self.assertIn(render.ATTRIBUTION, out)
        self.assertNotIn("\x1b[2J", out)

    def test_tty_stdin_piped_stdout_stays_batch(self):
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
        self.assertIn("Explorer", out)
        self.assertIn("Best value", out)
        self.assertNotIn("\x1b[2J", out)

    def test_tty_path_runs_textual_tui(self):
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
            self.assertTrue(wait_for("LLM RATINGS — Explorer"),
                            "no initial TUI frame from the Textual driver")
            os.write(master, b"2")
            self.assertTrue(wait_for("LLM RATINGS — Researcher"),
                            "key '2' did not switch the role")
            os.write(master, b"q")
            rc = p.wait(timeout=10)
        finally:
            if p.poll() is None:
                p.kill()
                p.wait(timeout=10)
            stop.set()
            t.join(timeout=2)
            os.close(master)
        self.assertEqual(rc, 0)
        text_out = b"".join(out).decode("utf-8", "replace")
        self.assertIn("Best value (default)", text_out)
        self.assertNotIn("Traceback", text_out)


class Navigation(unittest.IsolatedAsyncioTestCase):
    async def test_first_loaded_role_is_the_default(self):
        self.assertEqual([r["name"] for r in ROLES], [
            "Explorer", "Researcher", "Planner", "Coder", "Reviewer",
            "Coordinator", "Generalist", "Utility"])
        app = LlmRatings(DS, ROLES)
        async with app.run_test():
            self.assertEqual(app.sess.role["name"], "Explorer")
            self.assertEqual(app.sess.objective, "ppi")
            self.assertIn("Best value (default)", text(app))

    async def test_role_nav_arrow_and_digits(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            for key, name, objective in (
                    ("2", "Researcher", "Best value"),
                    ("right", "Planner", "Highest capability"),
                    ("left", "Researcher", "Best value"),
                    ("4", "Coder", "Highest capability"),
                    ("5", "Reviewer", "Highest capability"),
                    ("6", "Coordinator", "Highest capability"),
                    ("7", "Generalist", "Best value"),
                    ("8", "Utility", "Lowest qualifying price"),
                    ("right", "Explorer", "Best value"),
                    ("left", "Utility", "Lowest qualifying price"),
                    ("1", "Explorer", "Best value")):
                await pilot.press(key)
                self.assertEqual(app.sess.role["name"], name)
                self.assertIn(f"{objective} (default)", text(app))

    async def test_row_nav_follows_display_order_and_skips_secondary_records(self):
        app = LlmRatings(DS, ROLES)
        _, expected = render.table(DS, role("Explorer"))
        self.assertGreater(len(expected), 2)
        self.assertTrue(render.query(DS, role("Explorer"))["unranked"])
        async with app.run_test() as pilot:
            self.assertEqual(len(data_rows(text(app))), len(expected))
            for i, row in enumerate(expected):
                if i:
                    await pilot.press("down")
                self.assertTrue(rev_row(app).startswith(f"  {row['model']} "))
            await pilot.press("down", "down")
            self.assertIn(expected[-1]["model"], rev_row(app))
            await pilot.press("up")
            self.assertIn(expected[-2]["model"], rev_row(app))
            await pilot.press("enter")
            self.assertIn(expected[-2]["model"], text(app))
            self.assertIn("LLM RATINGS — detail", text(app))

    async def test_up_at_top_stays(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            first = rev_row(app)
            await pilot.press("up", "up")
            self.assertEqual(rev_row(app), first)


class FiltersAndEffort(unittest.IsolatedAsyncioTestCase):
    async def test_f_cycles_selected_index_grades_without_reselecting_effort(self):
        selected = render.query(DS, role("Coder"))["rows"]
        self.assertEqual(selected[0]["model"], "GPT-5.6 Sol")
        self.assertEqual(selected[0]["effort"], "xhigh")
        app = LlmRatings(DS, ROLES, "Coder")
        async with app.run_test() as pilot:
            for label, minimum in (("grade = 5", 5), ("grade ≥ 4", 4),
                                   ("all", None)):
                await pilot.press("f")
                expected = [r for r in selected
                            if minimum is None or r["grade"] >= minimum]
                actual = data_rows(text(app))
                self.assertIn(f"filter: {label}", text(app))
                self.assertEqual(len(actual), len(expected))
                for line, row in zip(actual, expected):
                    self.assertTrue(line.startswith(f"  {row['model']} "))
                    self.assertIn(render.EFFORT_LABEL[row["effort"]], line)

    async def test_filter_does_not_promote_another_effort(self):
        selected = render.query(DS, role("Explorer"))["rows"]
        luna = next(r for r in selected if r["model"] == "GPT-5.6 Luna")
        self.assertEqual(luna["effort"], "low")
        self.assertEqual(luna["grade"], 1)
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("f")
            self.assertFalse(any("GPT-5.6 Luna" in line
                                 for line in data_rows(text(app))))
            await pilot.press("f", "f")
            await open_model(app, pilot, "GPT-5.6 Luna")
            self.assertIn("GPT-5.6 Luna Low", plain(app))
            self.assertIn("33.3", plain(app))

    async def test_o_cycles_to_default_and_back(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            for objective, label in (("cap", "Highest capability"),
                                     ("ppi", "Best value"),
                                     ("price", "Lowest qualifying price")):
                await pilot.press("o")
                self.assertEqual(app.sess.objective, objective)
                self.assertIn(f"{label} (override)", text(app))
            await pilot.press("o")
            self.assertIsNone(app.sess.obj)
            self.assertIn("Best value (default)", text(app))

    async def test_unsupported_area_objectives_stay_selected_without_fallback(self):
        for name, index in (("Coder", "coding"), ("Coordinator", "agentic")):
            with self.subTest(role=name):
                app = LlmRatings(DS, ROLES, name)
                async with app.run_test() as pilot:
                    await pilot.press("o")
                    self.assertIn("Highest capability (override)", text(app))
                    self.assertTrue(data_rows(text(app)))
                    for objective, label in (("ppi", "Best value"),
                                             ("price", "Lowest qualifying price")):
                        await pilot.press("o")
                        self.assertEqual(app.sess.objective, objective)
                        result = render.query(DS, role(name), objective)
                        self.assertEqual(result["index"], index)
                        self.assertEqual(result["status"], "unavailable_objective")
                        self.assertIn(f"{label} (override)", text(app))
                        self.assertIn("unavailable", text(app).lower())
                        self.assertEqual(data_rows(text(app)), [])
                        await pilot.press("enter")
                        self.assertNotIn("LLM RATINGS — detail", text(app))
                    await pilot.press("o")
                    self.assertIsNone(app.sess.obj)
                    self.assertIn("Highest capability (default)", text(app))
                    self.assertTrue(data_rows(text(app)))

    async def test_role_switch_resets_objective_in_table_and_detail(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("o", "right")
            self.assertEqual(app.sess.role["name"], "Researcher")
            self.assertIsNone(app.sess.obj)
            self.assertIn("Best value (default)", text(app))
            await pilot.press("o", "enter", "right")
            self.assertEqual(app.sess.role["name"], "Planner")
            self.assertIsNone(app.sess.obj)
            self.assertIn("Highest capability (default)", text(app))
            self.assertNotIn("LLM RATINGS — detail", text(app))


class DetailView(unittest.IsolatedAsyncioTestCase):
    async def test_detail_preserves_independent_source_evidence_and_disagreement(self):
        app = LlmRatings(DS, ROLES, "Planner")
        async with app.run_test() as pilot:
            await open_model(app, pilot, "GPT-5.6 Luna")
            f = plain(app)
            self.assertIn("GPT-5.6 Luna Maximum", f)
            self.assertRegex(f, r"DeepSWE grade 1\b.*?raw 0\.671875\b")
            self.assertRegex(f, r"Terminal-Bench grade 4\b.*?raw 0\.757\b")
            self.assertIn("Artificial Analysis", f)
            self.assertIn("51.2", f)
            self.assertIn("Capability per dollar", f)
            self.assertIn("$0.20/$1.20", f)
            self.assertIn("Output tokens per second: 180.51 tokens/s", f)
            self.assertIn("sources disagree", f)
            self.assertIn(render.ATTRIBUTION, text(app))

    async def test_detail_keeps_dominated_advice_without_false_disagreement(self):
        app = LlmRatings(DS, ROLES, "Planner")
        async with app.run_test() as pilot:
            await open_model(app, pilot, "GPT-5.6 Sol")
            f = plain(app)
            self.assertIn("GPT-5.6 Sol Maximum", f)
            self.assertRegex(f, r"DeepSWE grade 4\b.*?raw 0\.72666\d*\b")
            self.assertRegex(f, r"Terminal-Bench grade 5\b.*?raw 0\.769\b")
            self.assertIn("58.9", f)
            self.assertIn("Dominated", f)
            self.assertIn("Claude Opus 5 High", f)
            self.assertIn("$0.0066", f)
            self.assertNotIn("sources disagree", f)

    async def test_missing_source_does_not_borrow_another_effort(self):
        app = LlmRatings(DS, ROLES, "Planner")
        async with app.run_test() as pilot:
            await open_model(app, pilot, "Kimi K3")
            f = plain(app)
            self.assertIn("Kimi K3 Maximum", f)
            self.assertIn("no Terminal-Bench row at Maximum effort", f)
            self.assertIn("57.1", f)
            # The cross-effort Intelligence grade is 4; DeepSWE stays 2 in
            # its independent Maximum-effort population, even without TB.
            self.assertIn("DeepSWE grade 2", f)
            self.assertIn("Artificial Analysis Intelligence score grade 4", f)
            self.assertIn("sources disagree", f)

    async def test_costless_intelligence_is_unranked_but_coding_can_open_evidence(self):
        aa = {"id": "u1", "name": "GPT-5.6 Luna (low)",
              "slug": "gpt-5-6-luna-low", "model_creator": {"name": "Acme"},
              "evaluations": {"artificial_analysis_intelligence_index": 33.3,
                              "artificial_analysis_coding_index": 44.2}}
        with tempfile.TemporaryDirectory() as td:
            Path(td, "aa.json").write_text(json.dumps({"data": [aa]}))
            Path(td, "deepswe.json").write_text(json.dumps({"rows": [
                {"model": "gpt-5-6-luna", "reasoning_effort": "low",
                 "pass_at_1": 0.4}]}))
            Path(td, "tb.json").write_text(
                json.dumps({"listing": [], "submissions": {}}))
            ds = build_ds(td)
        app = LlmRatings(ds, ROLES, "Planner")
        async with app.run_test() as pilot:
            self.assertIn("No qualifying configuration", text(app))
            self.assertEqual(data_rows(text(app)), [])
            self.assertIn("GPT-5.6 Luna", text(app))
            await pilot.press("enter")
            self.assertNotIn("LLM RATINGS — detail", text(app))
            await pilot.press("right", "enter")
            f = plain(app)
            self.assertIn("LLM RATINGS — detail", f)
            self.assertIn("GPT-5.6 Luna Low", f)
            self.assertIn("Coding score", f)
            self.assertIn("44.2", f)
            self.assertNotIn("price tier None", f)
            self.assertIn("Cost-based advice unavailable", f)
            self.assertNotIn("Cheaper alternatives", f)
            self.assertNotIn("Frontier ·", f)
            self.assertNotIn("Dominated ·", f)

    async def test_coding_detail_uses_selected_coding_effort_and_no_cost_advice(self):
        selected = render.query(DS, role("Coder"))["rows"][0]
        self.assertEqual((selected["model"], selected["effort"], selected["score"]),
                         ("GPT-5.6 Sol", "xhigh", 78.3))
        app = LlmRatings(DS, ROLES, "Coder")
        async with app.run_test() as pilot:
            await pilot.press("enter")
            f = plain(app)
            self.assertIn("GPT-5.6 Sol Extra high", f)
            self.assertIn("Coding score", f)
            self.assertIn("78.3", f)
            self.assertIn("Cost-based advice unavailable", f)
            self.assertNotIn("Frontier ·", f)
            self.assertNotIn("Dominated ·", f)
            self.assertNotIn("Cheaper alternatives", f)

    async def test_detail_intelligence_alternatives_keep_efforts_and_price_order(self):
        app = LlmRatings(DS, ROLES, "Planner")
        async with app.run_test() as pilot:
            await open_model(app, pilot, "Claude Opus 5")
            f = plain(app)
            alternatives = ("GPT-5.6 Sol High", "Claude Opus 5 Medium",
                            "GPT-5.6 Sol Extra high")
            self.assertIn("alternatives", f)
            positions = [f.index(name) for name in alternatives]
            self.assertEqual(positions, sorted(positions))
            for value in ("$0.549", "$0.722", "$0.833", "-4.8", "-4.4", "-3.0"):
                self.assertIn(value, f)

    async def test_detail_context_from_openrouter_and_honest_missing_metadata(self):
        app = LlmRatings(DS, ROLES, "Planner")
        async with app.run_test() as pilot:
            await open_model(app, pilot, "Claude Opus 5")
            f = plain(app)
            self.assertIn("Context: 200000 tokens", f)
            self.assertIn("in: text, image, file; out: text", f)
            await pilot.press("escape")
            # Returning preserves the cursor; move back to the first row.
            await pilot.press(*(["up"] * len(data_rows(text(app)))))
            await open_model(app, pilot, "Kimi K3")
            self.assertIn("no OpenRouter context evidence", plain(app))

    async def test_esc_returns_to_same_table_and_cursor(self):
        app = LlmRatings(DS, ROLES, "Planner")
        async with app.run_test() as pilot:
            await pilot.press("down")
            selected = rev_row(app)
            await pilot.press("enter")
            self.assertIn("LLM RATINGS — detail", text(app))
            await pilot.press("escape")
            self.assertIn("Highest capability (default)", text(app))
            self.assertNotIn("LLM RATINGS — detail", text(app))
            self.assertEqual(rev_row(app), selected)


class RolesFile(unittest.IsolatedAsyncioTestCase):
    async def test_edited_file_order_drives_default_and_number_keys(self):
        custom = {"name": "Mail Sorter", "description": "Triage an inbox.",
                  "capacity": "Short context; modest reasoning; speed is useful.",
                  "index": "intelligence", "objective": "price"}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td, "roles.json")
            path.write_text(json.dumps([custom] + list(reversed(ROLES))))
            roles = render.load_roles(path)
        self.assertEqual(roles[0]["floor"], 2)
        app = LlmRatings(DS, roles)
        async with app.run_test() as pilot:
            self.assertEqual(app.sess.role["name"], "Mail Sorter")
            self.assertIn("Lowest qualifying price (default)", text(app))
            await pilot.press("9")
            self.assertEqual(app.sess.role["name"], "Explorer")
            self.assertIn("Best value (default)", text(app))
            await pilot.press("2")
            self.assertEqual(app.sess.role["name"], "Utility")
            await pilot.press("1")
            self.assertEqual(app.sess.role["name"], "Mail Sorter")

    async def test_edited_unsupported_default_is_retained(self):
        custom = dict(role("Coder"), objective="ppi")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td, "roles.json")
            path.write_text(json.dumps([custom]))
            roles = render.load_roles(path)
        app = LlmRatings(DS, roles)
        async with app.run_test():
            self.assertEqual(app.sess.objective, "ppi")
            self.assertIn("Best value (default)", text(app))
            self.assertIn("unavailable", text(app).lower())
            self.assertEqual(data_rows(text(app)), [])


class Quit(unittest.IsolatedAsyncioTestCase):
    async def test_q_quits_cleanly_from_table(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("q")
            self.assertFalse(app.is_running)

    async def test_q_quits_cleanly_from_detail(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("enter")
            self.assertIn("LLM RATINGS — detail", text(app))
            await pilot.press("q")
            self.assertFalse(app.is_running)

    async def test_ctrl_c_quits_cleanly(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("ctrl+c")
            self.assertFalse(app.is_running)

    def test_stdin_eof_quits_cleanly(self):
        env = dict(os.environ, LLM_RATINGS_AA_API_KEY="dummy")
        master, slave = pty.openpty()
        p = subprocess.Popen(
            [sys.executable, "-m", "llmratings", "--fixtures", str(FIXTURES)],
            stdin=slave, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, cwd=REPO, env=env)
        os.close(slave)
        os.close(master)
        try:
            rc = p.wait(timeout=10)
        finally:
            if p.poll() is None:
                p.kill()
                p.wait(timeout=10)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
