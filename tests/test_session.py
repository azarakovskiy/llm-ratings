"""Shared advice state through real loaded source fixtures, without a UI."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from llmratings import fetch, identity, render
from llmratings.session import Session

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / ".scratch" / "llm-ratings" / "fixtures" / "main"
ROLES = render.load_roles(REPO / "llmratings" / "roles.json")


def build_ds(fixtures=FIXTURES):
    """The fixture-fed Dataset used by both web and batch consumers."""
    raw = fetch.fetch_all(str(fixtures))
    aliases = identity.load_aliases(REPO / "llmratings" / "aliases.json")
    return identity.build(aliases, raw)


DS = build_ds()


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

    def test_details_require_a_target_rendered_in_the_active_view(self):
        session = Session(DS, ROLES)
        session.request_details("gpt-5-5")
        result = session.set_view("picks")
        self.assertIsNone(result["details"])
        with self.assertRaises(ValueError):
            session.request_details("gpt-5-5")
        self.assertIsNone(session.query()["details"])
        opened = session.request_details("gpt-5-6-luna")
        self.assertEqual(opened["details"]["key"], "gpt-5-6-luna")
        session.set_min_grade(5)
        excluded = session.request_details("gpt-5-6-luna")
        self.assertIn(excluded["details"], excluded["excluded"])
        unranked = session.request_details("dsw:gpt-5-6-terra")
        self.assertIn(unranked["details"], unranked["unranked"])
        session.set_view("table")
        self.assertEqual(session.request_details("gpt-5-5")["details"]["key"], "gpt-5-5")

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


class RolesFile(unittest.TestCase):
    def test_edited_file_order_drives_default_and_named_role_selection(self):
        custom = {"name": "Mail Sorter", "description": "Triage an inbox.",
                  "capacity": "Short context; modest reasoning; speed is useful.",
                  "index": "intelligence", "objective": "price"}
        with tempfile.TemporaryDirectory() as td:
            path = Path(td, "roles.json")
            path.write_text(json.dumps([custom] + list(reversed(ROLES))))
            roles = render.load_roles(path)
        self.assertEqual(roles[0]["floor"], 2)
        session = Session(DS, roles)
        self.assertEqual(session.role["name"], "Mail Sorter")
        self.assertEqual(session.query()["objective"], "price")
        for name, objective in (("Explorer", "ppi"), ("Utility", "price"),
                                ("Mail Sorter", "price")):
            result = session.set_role(name)
            self.assertEqual(result["role"]["name"], name)
            self.assertEqual(result["objective"], objective)
            self.assertIsNone(result["objective_override"])

    def test_edited_unsupported_default_is_retained(self):
        custom = dict(next(r for r in ROLES if r["name"] == "Coder"),
                      objective="ppi")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td, "roles.json")
            path.write_text(json.dumps([custom]))
            roles = render.load_roles(path)
        session = Session(DS, roles)
        result = session.query()
        self.assertEqual(session.objective, "ppi")
        self.assertIsNone(session.objective_override)
        self.assertEqual(result["role"]["name"], "Coder")
        self.assertEqual(result["index"], "coding")
        self.assertEqual(result["status"], "unavailable_objective")
        self.assertEqual(result["table_rows"], [])


if __name__ == "__main__":
    unittest.main()
