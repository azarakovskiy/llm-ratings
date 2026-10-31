"""Shared advice state and TUI behavior through real loaded source fixtures.

UI-independent transitions retain active constraints and explicit evidence;
the terminal shell adds navigation without a second selection policy.
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
from unittest.mock import patch

from llmratings import fetch, identity, render
from llmratings.session import Session
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


class SharedSession(unittest.TestCase):
    """UI-independent transitions consume the same loaded policy as batch."""

    def test_defaults_explicit_role_and_both_real_fixture_projections(self):
        session = Session(DS, ROLES)
        result = session.query()
        self.assertIs(session.ds, DS)
        self.assertIs(session.role, ROLES[0])
        self.assertEqual(session.objective, "ppi")
        self.assertEqual((session.objective_override, session.min_grade,
                          session.provider, session.view,
                          session.selected_key, session.detail_key),
                         (None, None, None, "table", None, None))
        self.assertIs(result["role"], ROLES[0])
        self.assertEqual((result["index"], result["objective"],
                          result["objective_override"], result["min_grade"],
                          result["provider"], result["view"]),
                         ("intelligence", "ppi", None, None, None, "table"))
        self.assertIsNone(result["selected"])
        self.assertIsNone(result["details"])
        session = Session(DS, ROLES, "Planner")
        result = session.query()
        self.assertEqual([(r["key"], r["effort"]) for r in result["table_rows"]], [
            ("claude-opus-5", "max"), ("gpt-5-6-luna", "max"),
            ("gpt-5-6-sol", "max"), ("kimi-k3", "max"), ("gpt-5-5", "xhigh")])
        result = session.set_view("picks")
        groups = {g["provider"]: g for g in result["picks"]}
        self.assertEqual((groups["OpenAI"]["primary"]["key"],
                          groups["OpenAI"]["primary"]["effort"],
                          groups["OpenAI"]["runner_up"]["key"],
                          groups["OpenAI"]["runner_up"]["effort"]),
                         ("gpt-5-6-sol", "max", "gpt-5-5", "xhigh"))
        self.assertEqual(groups["Anthropic"]["primary"]["key"], "claude-opus-5")
        self.assertIsNone(groups["Anthropic"]["runner_up"])
        self.assertEqual(groups["Kimi"]["primary"]["key"], "kimi-k3")
        self.assertIsNone(groups["Kimi"]["runner_up"])
        self.assertEqual(result["view"], "picks")
        self.assertEqual(result["advisory_scope"]["kind"], "global")

    def choices(self, session):
        return (session.role["name"], session.objective_override, session.objective,
                session.min_grade, session.provider, session.view)

    def configured(self):
        session = Session(DS, ROLES, "Planner")
        session.set_objective("cap")
        session.set_min_grade(4)
        session.set_provider("OpenAI")
        session.set_view("picks")
        session.select_model("gpt-5-6-sol")
        session.request_details("gpt-5-6-sol")
        return session

    def test_each_transition_preserves_other_choices_and_clears_stale_evidence(self):
        cases = (
            ("set_role", "Explorer", ("Explorer", None, "ppi", 4, "OpenAI", "picks")),
            ("set_role", "Coder", ("Coder", None, "cap", 4, "OpenAI", "picks")),
            ("set_role", "Coordinator",
             ("Coordinator", None, "cap", 4, "OpenAI", "picks")),
            ("set_objective", "ppi", ("Planner", "ppi", "ppi", 4, "OpenAI", "picks")),
            ("set_objective", "price",
             ("Planner", "price", "price", 4, "OpenAI", "picks")),
            ("set_objective", None, ("Planner", None, "cap", 4, "OpenAI", "picks")),
            ("set_min_grade", 5, ("Planner", "cap", "cap", 5, "OpenAI", "picks")),
            ("set_min_grade", None,
             ("Planner", "cap", "cap", None, "OpenAI", "picks")),
            ("set_provider", "Anthropic",
             ("Planner", "cap", "cap", 4, "Anthropic", "picks")),
            ("set_provider", None, ("Planner", "cap", "cap", 4, None, "picks")),
            ("set_view", "table", ("Planner", "cap", "cap", 4, "OpenAI", "table")),
        )
        for method, value, expected in cases:
            with self.subTest(action=method, value=value):
                session = self.configured()
                result = getattr(session, method)(value)
                self.assertEqual(self.choices(session), expected)
                self.assertEqual((result["role"]["name"], result["objective_override"],
                                  result["objective"], result["min_grade"],
                                  result["provider"], result["view"]), expected)
                self.assertIsNone(session.selected_key)
                self.assertIsNone(session.detail_key)
                self.assertIsNone(result["selected"])
                self.assertIsNone(result["details"])
                self.assertIs(session.ds, DS)

    def test_passive_selection_never_opens_or_closes_explicit_details(self):
        session = Session(DS, ROLES, "Planner")
        result = session.select_model("gpt-5-6-sol")
        self.assertEqual(result["selected"]["effort"], "max")
        self.assertIsNone(result["details"])
        session.request_details("gpt-5-6-sol")
        result = session.select_model("gpt-5-6-luna")
        self.assertEqual(result["selected"]["key"], "gpt-5-6-luna")
        self.assertEqual(result["details"]["key"], "gpt-5-6-sol")
        result = session.select_model(None)
        self.assertIsNone(result["selected"])
        self.assertEqual(result["details"]["key"], "gpt-5-6-sol")
        result = session.close_details()
        self.assertIsNone(result["details"])
        self.assertIsNone(session.detail_key)
        self.assertIsNone(session.selected_key)
        session.request_details("gpt-5-6-luna")
        self.assertEqual(session.query()["details"]["key"], "gpt-5-6-luna")
        result = session.set_objective("ppi")
        self.assertIsNone(result["selected"])
        self.assertIsNone(result["details"])
        result = session.select_model("gpt-5-6-luna")
        self.assertEqual(result["selected"]["effort"], "low")
        self.assertIsNone(result["details"])
        result = session.request_details("gpt-5-6-luna")
        self.assertEqual(result["details"]["effort"], "low")
        self.assertIs(result["selected"]["configuration"], result["details"]["configuration"])

    def test_secondary_requests_keep_scoped_excluded_and_unranked_evidence(self):
        session = Session(DS, ROLES)
        session.set_provider("OpenAI")
        session.set_min_grade(5)
        result = session.request_details("gpt-5-6-luna")
        excluded = next(r for r in result["excluded"] if r["key"] == "gpt-5-6-luna")
        self.assertIs(result["details"], excluded)
        self.assertEqual((excluded["effort"], excluded["score"], excluded["grade"]),
                         ("low", 33.3, 1))
        self.assertIn("display", excluded["reason"].lower())
        self.assertIsNotNone(excluded["configuration"])
        self.assertNotIn(excluded["key"], {r["key"] for r in result["unranked"]})
        result = session.select_model("gpt-5-6-luna")
        self.assertEqual(result["selected"]["effort"], "low")
        session.set_provider("Anthropic")
        with self.assertRaises(ValueError):
            session.request_details("gpt-5-6-luna")
        session.set_provider(None)
        result = session.request_details("dsw:gpt-5-6-terra")
        self.assertIsNone(result["details"]["configuration"])
        self.assertTrue(result["details"]["measurements"])
        self.assertIn("measured", result["details"]["reason"].lower())
        self.assertIn(result["details"], result["unranked"])
        session.set_provider("OpenAI")
        with self.assertRaises(ValueError):
            session.select_model("dsw:gpt-5-6-terra")

    def test_each_named_recovery_changes_only_its_choice(self):
        cases = (
            ("all_providers", ("Coder", "ppi", "ppi", 4, None, "picks")),
            ("clear_capability", ("Coder", "ppi", "ppi", None, "OpenAI", "picks")),
            ("highest_capability", ("Coder", "cap", "cap", 4, "OpenAI", "picks")),
            ("role_default", ("Coder", None, "cap", 4, "OpenAI", "picks")),
        )
        for action, expected in cases:
            with self.subTest(action=action):
                session = Session(DS, ROLES, "Coder")
                session.set_objective("ppi")
                session.set_min_grade(4)
                session.set_provider("OpenAI")
                session.set_view("picks")
                session.select_model("gpt-5-6-sol")
                session.request_details("gpt-5-6-sol")
                result = session.recover(action)
                self.assertEqual(self.choices(session), expected)
                self.assertIsNone(session.selected_key)
                self.assertIsNone(session.detail_key)
                self.assertIsNone(result["selected"])
                self.assertIsNone(result["details"])
                self.assertEqual(result["status"],
                                 "unavailable_objective" if expected[2] == "ppi" else "ok")

    def test_unsupported_area_overrides_remain_explicit_until_objective_recovery(self):
        for name, index in (("Coder", "coding"), ("Coordinator", "agentic")):
            for objective in ("ppi", "price"):
                with self.subTest(role=name, objective=objective):
                    session = Session(DS, ROLES, name)
                    session.set_provider("OpenAI")
                    session.set_min_grade(4)
                    session.set_view("picks")
                    result = session.set_objective(objective)
                    self.assertEqual(self.choices(session),
                                     (name, objective, objective, 4, "OpenAI", "picks"))
                    self.assertEqual(result["index"], index)
                    self.assertEqual(result["status"], "unavailable_objective")
                    for field in ("rows", "table_rows", "picks", "points", "frontier_path"):
                        self.assertEqual(result[field], [])
                    self.assertEqual(result["advisory_scope"]["kind"], "unavailable")
                    self.assertTrue(result["unranked"])
                    self.assertIn("highest_capability",
                                  {a["action"] for a in result["recovery_actions"]})
                    result = session.recover("highest_capability")
                    self.assertEqual(self.choices(session),
                                     (name, "cap", "cap", 4, "OpenAI", "picks"))
                    self.assertEqual(result["status"], "ok")
                    self.assertTrue(result["picks"])

    def test_empty_intersection_keeps_constraints_until_named_recovery(self):
        session = Session(DS, ROLES)
        session.set_provider("Google")
        session.set_min_grade(5)
        result = session.set_view("picks")
        self.assertEqual(result["status"], "no_qualifying")
        self.assertEqual(self.choices(session),
                         ("Explorer", None, "ppi", 5, "Google", "picks"))
        self.assertIn("No qualifying configuration", result["reason"])
        for constraint in ("Explorer", "Google", "Best value", "5"):
            self.assertIn(constraint, result["reason"])
        self.assertEqual(result["picks"], [])
        self.assertIn("all_providers", {a["action"] for a in result["recovery_actions"]})
        session.recover("all_providers")
        self.assertEqual(self.choices(session),
                         ("Explorer", None, "ppi", 5, None, "picks"))
        result = session.recover("clear_capability")
        self.assertEqual(self.choices(session),
                         ("Explorer", None, "ppi", None, None, "picks"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["rows"]), 5)

    def test_catalog_names_and_absent_shortcuts_stay_selectable(self):
        session = Session(DS, ROLES)
        for provider in ("Kimi", "OpenAI", "Anthropic", "Google", "DeepSeek", "xAI"):
            with self.subTest(provider=provider):
                result = session.set_provider(provider)
                self.assertEqual(session.provider, provider)
                self.assertEqual(result["provider"], provider)
                self.assertEqual(result["creators"], ["Anthropic", "Kimi", "OpenAI"])
                self.assertEqual(result["shortcuts"],
                                 ("OpenAI", "Anthropic", "Google", "DeepSeek", "xAI"))
                self.assertEqual(result["advisory_scope"]["kind"], "provider")
                self.assertEqual(result["advisory_scope"]["provider"], provider)
                if provider in ("Google", "DeepSeek", "xAI"):
                    self.assertEqual(result["status"], "no_qualifying")

    def test_invalid_requests_leave_choices_and_requested_evidence_unchanged(self):
        with self.assertRaises(ValueError):
            Session(DS, [])
        with self.assertRaises(ValueError):
            Session(DS, ROLES, "Missing role")
        session = self.configured()
        expected = self.choices(session)
        invalid = {
            "set_role": (None, "", "Missing role", []),
            "set_objective": ("", "speed", [], 1),
            "set_min_grade": (0, 3, True, 5.0, "5"),
            "set_provider": ("", "Unknown creator", "All providers", "—", []),
            "set_view": (None, "providers", []),
            "select_model": ("missing", "claude-opus-5", []),
            "request_details": (None, "missing", "claude-opus-5", []),
            "recover": (None, "reset", "provider", []),
        }
        for method, values in invalid.items():
            for value in values:
                with self.subTest(action=method, value=value):
                    with self.assertRaises(ValueError):
                        getattr(session, method)(value)
                    self.assertEqual(self.choices(session), expected)
                    self.assertEqual(session.selected_key, "gpt-5-6-sol")
                    self.assertEqual(session.detail_key, "gpt-5-6-sol")

    def test_every_action_reuses_loaded_dataset_and_rating_objects_without_fetching(self):
        session = Session(DS, ROLES)
        with patch.object(fetch, "fetch_all",
                          side_effect=AssertionError("state must not acquire sources")):
            session.set_role("Planner")
            session.set_objective("cap")
            session.set_min_grade(4)
            session.set_provider("OpenAI")
            session.set_view("picks")
            session.select_model("gpt-5-6-sol")
            result = session.request_details("gpt-5-6-sol")
            rating = next(r for r in DS.ratings if r.source == "aa"
                          and r.model_key == "gpt-5-6-sol" and r.effort == "max")
            self.assertIs(result["details"]["configuration"], rating)
            session.close_details()
            for action in ("all_providers", "clear_capability",
                           "highest_capability", "role_default"):
                result = session.recover(action)
                row = next(r for r in result["rows"] if r["key"] == "gpt-5-6-sol")
                self.assertIs(row["configuration"], rating)
                self.assertIs(session.ds, DS)


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
                self.assertIsNone(app.sess.detail_key)
                self.assertNotIn("LLM RATINGS — detail", text(app))
                if i:
                    self.assertEqual(app.sess.selected_key, row["key"])
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
            self.assertIsNone(app.sess.objective_override)
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
                    self.assertIsNone(app.sess.objective_override)
                    self.assertIn("Highest capability (default)", text(app))
                    self.assertTrue(data_rows(text(app)))

    async def test_role_switch_resets_objective_in_table_and_detail(self):
        app = LlmRatings(DS, ROLES)
        async with app.run_test() as pilot:
            await pilot.press("o", "right")
            self.assertEqual(app.sess.role["name"], "Researcher")
            self.assertIsNone(app.sess.objective_override)
            self.assertIn("Best value (default)", text(app))
            await pilot.press("o", "enter", "right")
            self.assertEqual(app.sess.role["name"], "Planner")
            self.assertIsNone(app.sess.objective_override)
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
            selected_key = app.sess.selected_key
            self.assertEqual(app.sess.detail_key, selected_key)
            await pilot.press("escape")
            self.assertIn("Highest capability (default)", text(app))
            self.assertNotIn("LLM RATINGS — detail", text(app))
            self.assertEqual(rev_row(app), selected)
            self.assertEqual(app.sess.selected_key, selected_key)
            self.assertIsNone(app.sess.detail_key)


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
