"""Structured model evidence through real saved and temporary source payloads."""

import json
import tempfile
import unittest
from pathlib import Path

from llmratings import evidence, fetch, identity, render

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / ".scratch" / "llm-ratings" / "fixtures" / "main"
ROLES = render.load_roles(REPO / "llmratings" / "roles.json")


def build_ds(fixtures=FIXTURES):
    return identity.build(
        identity.load_aliases(REPO / "llmratings" / "aliases.json"),
        fetch.fetch_all(fixtures))


class ModelEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = build_ds()

    def opened(self, key, role="Planner", *, ds=None, **constraints):
        ds = self.ds if ds is None else ds
        profile = next(r for r in ROLES if r["name"] == role)
        result = render.query(ds, profile, **constraints)
        record = next(r for group in ("rows", "excluded", "unranked")
                      for r in result[group] if r["key"] == key)
        return evidence.model_evidence(ds, result, record)

    def configuration(self, opened, effort):
        return next(c for c in opened["configurations"] if c["effort"] == effort)

    def sources(self, opened, effort):
        return {s["source"]: s for s in self.configuration(opened, effort)["sources"]}

    def docs(self):
        return {source: json.loads((FIXTURES / name).read_text())
                for source, name in {**fetch.FILES, "or": "or.json"}.items()}

    def load(self, docs):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        for source, name in {**fetch.FILES, "or": "or.json"}.items():
            if source in docs:
                Path(td.name, name).write_text(json.dumps(docs[source]))
        return build_ds(td.name)

    def test_independent_source_scores_ranks_and_disagreement(self):
        opened = self.opened("gpt-5-6-luna")
        self.assertEqual((opened["model"], opened["provider"], opened["effort"]),
                         ("GPT-5.6 Luna", "OpenAI", "max"))
        self.assertEqual([c["effort"] for c in opened["configurations"]],
                         ["low", "medium", "high", "xhigh", "max"])
        self.assertEqual([c["effort"] for c in opened["configurations"] if c["selected"]],
                         ["max"])
        sources = self.sources(opened, "max")
        self.assertEqual({key: (s["index"], s["score"], s["grade"], s["rank"],
                                s["population_size"])
                          for key, s in sources.items()}, {
            "aa": ("Intelligence", 51.2, 3, 12, 21),
            "deepswe": ("pass@1", 0.671875, 1, 5, 5),
            "tb": ("accuracy", 0.757, 4, 2, 3),
        })
        self.assertIn("across measured efforts", sources["aa"]["population_label"])
        self.assertIn("Maximum", sources["deepswe"]["population_label"])
        self.assertIn("best agent per model", sources["tb"]["population_label"])
        disagreement = self.configuration(opened, "max")["disagreement"]
        self.assertEqual([(s["name"], s["grade"]) for s in disagreement],
                         [("Artificial Analysis", 3), ("DeepSWE", 1),
                          ("Terminal-Bench", 4)])
        self.assertEqual(sources["tb"]["rating"].agent, "codex-cli")
        self.assertEqual(sources["tb"]["rating"].date, "2026-07-11")
        self.assertTrue(sources["tb"]["source_url"].endswith(
            "20260711-openai-gpt-5-6-luna-max-codex-cli.json"))
        self.assertEqual(sources["aa"]["rating"].intelligence_index_version, 4.1)
        self.assertIn("Highest capability", opened["rationale"])
        self.assertIn("Maximum", opened["rationale"])
        self.assertIn("no fixed effort", opened["rationale"])

    def test_dominated_configuration_keeps_replacement_without_false_disagreement(self):
        opened = self.opened("gpt-5-6-sol")
        sources = self.sources(opened, "max")
        self.assertEqual((sources["aa"]["score"], sources["aa"]["grade"],
                          sources["aa"]["rank"]), (58.9, 5, 3))
        self.assertEqual((sources["deepswe"]["score"], sources["deepswe"]["grade"],
                          sources["deepswe"]["rank"], sources["deepswe"]["population_size"]),
                         (0.7266666666666667, 4, 2, 5))
        self.assertEqual((sources["tb"]["score"], sources["tb"]["grade"],
                          sources["tb"]["rank"], sources["tb"]["population_size"]),
                         (0.769, 5, 1, 3))
        self.assertEqual(self.configuration(opened, "max")["disagreement"], [])
        self.assertFalse(opened["frontier"])
        gain, saving, key, effort, score, cost = opened["dom"]
        self.assertEqual((gain, key, effort, score, cost),
                         (0, "claude-opus-5", "high", 58.9, 1.2259))
        self.assertAlmostEqual(saving, 0.0066)

    def test_missing_source_does_not_borrow_a_score_or_hide_available_disagreement(self):
        opened = self.opened("kimi-k3")
        self.assertEqual([c["effort"] for c in opened["configurations"]], ["low", "max"])
        sources = self.sources(opened, "max")
        self.assertEqual((sources["aa"]["score"], sources["aa"]["grade"],
                          sources["aa"]["rank"], sources["aa"]["population_size"]),
                         (57.1, 4, 6, 21))
        self.assertEqual((sources["deepswe"]["grade"], sources["deepswe"]["rank"],
                          sources["deepswe"]["population_size"]), (2, 4, 5))
        self.assertIsNone(sources["tb"]["rating"])
        self.assertIsNone(sources["tb"]["score"])
        self.assertIsNone(sources["tb"]["grade"])
        self.assertIsNone(sources["tb"]["rank"])
        self.assertIn("No Terminal-Bench row at Maximum effort", sources["tb"]["reason"])
        self.assertEqual([s["source"] for s in
                          self.configuration(opened, "max")["disagreement"]],
                         ["aa", "deepswe"])
        low = self.sources(opened, "low")
        self.assertIsNone(low["deepswe"]["score"])
        self.assertIn("Low effort", low["deepswe"]["reason"])
        self.assertEqual(self.configuration(opened, "low")["disagreement"], [])

    def test_costless_intelligence_is_unranked_but_coding_keeps_its_actual_evidence(self):
        ds = self.load({
            "aa": {"data": [{
                "id": "u1", "name": "GPT-5.6 Luna (low)", "slug": "gpt-5-6-luna-low",
                "model_creator": {"name": "Acme"},
                "evaluations": {"artificial_analysis_intelligence_index": 33.3,
                                "artificial_analysis_coding_index": 44.2}}]},
            "deepswe": {"rows": [{"model": "gpt-5-6-luna",
                                   "reasoning_effort": "low", "pass_at_1": 0.4}]},
            "tb": {"listing": [], "submissions": {}},
        })
        intelligence = self.opened("gpt-5-6-luna", ds=ds)
        self.assertIsNone(intelligence["configuration"])
        self.assertIsNone(intelligence["effort"])
        self.assertIn("matching Intelligence benchmark task cost", intelligence["reason"])
        config = self.configuration(intelligence, "low")
        self.assertFalse(config["selected"])
        self.assertIn("matching Intelligence benchmark task cost", config["eligibility_reason"])
        self.assertEqual(self.sources(intelligence, "low")["aa"]["score"], 33.3)
        coding = self.opened("gpt-5-6-luna", "Coder", ds=ds)
        self.assertEqual(coding["effort"], "low")
        self.assertEqual(self.sources(coding, "low")["aa"]["score"], 44.2)
        self.assertIsNone(coding["configuration"].cost)
        self.assertIsNone(coding["frontier"])
        self.assertIsNone(coding["dom"])
        self.assertEqual(coding["alternatives"], [])
        self.assertEqual(coding["advisory_scope"]["kind"], "unavailable")

    def test_coding_uses_selected_coding_effort_and_never_intelligence_cost_advice(self):
        opened = self.opened("gpt-5-6-sol", "Coder")
        self.assertEqual(opened["effort"], "xhigh")
        aa = self.sources(opened, "xhigh")["aa"]
        self.assertEqual((aa["index"], aa["score"], aa["grade"], aa["rank"],
                          aa["population_size"]), ("Coding", 78.3, 5, 1, 21))
        self.assertEqual(opened["configuration"].score, 57.7)
        self.assertEqual(opened["configuration"].cost, 0.8325)
        self.assertIsNone(opened["frontier"])
        self.assertIsNone(opened["dom"])
        self.assertEqual(opened["alternatives"], [])
        self.assertIn("Cost-based advice unavailable for Coding",
                      opened["advisory_scope"]["label"])
        self.assertIn("Coding score descending", opened["rationale"])
        self.assertNotIn("task cost ascending", opened["rationale"])
        self.assertEqual([c["effort"] for c in opened["configurations"] if c["selected"]],
                         ["xhigh"])

    def test_intelligence_alternatives_keep_efforts_matching_prices_and_score_changes(self):
        opened = self.opened("claude-opus-5")
        self.assertEqual(opened["alternatives"], [
            ("gpt-5-6-sol", "high", 0.5486, 55.9),
            ("claude-opus-5", "medium", 0.7224, 56.3),
            ("gpt-5-6-sol", "xhigh", 0.8325, 57.7)])
        for point, delta in zip(opened["alternatives"], (-4.8, -4.4, -3.0)):
            self.assertAlmostEqual(point[3] - opened["configuration"].score, delta)

    def test_catalog_context_and_missing_metadata_remain_honest(self):
        opus = self.opened("claude-opus-5")
        catalog = self.ds.models[opus["key"]]
        self.assertEqual(catalog.context_length, 200000)
        self.assertEqual(catalog.modalities, "in: text, image, file; out: text")
        self.assertEqual(catalog.catalog_rows[0]["id"], "anthropic/claude-opus-5")
        kimi = self.opened("kimi-k3")
        missing = self.ds.models[kimi["key"]]
        self.assertIsNone(missing.context_length)
        self.assertIsNone(missing.modalities)
        self.assertEqual(missing.catalog_rows, [])
        self.assertIsNone(missing.token_share_30d)
        self.assertIsNotNone(kimi["configuration"])

    def test_matching_task_prices_are_not_token_prices_or_other_source_run_costs(self):
        opened = self.opened("gpt-5-6-luna")
        selected = opened["configuration"]
        self.assertEqual(selected.cost, 0.0473)
        self.assertEqual((selected.pricing["price_1m_input_tokens"],
                          selected.pricing["price_1m_output_tokens"]), (0.2, 1.2))
        low = self.configuration(opened, "low")["configuration"]
        self.assertEqual(low.cost, 0.0088)
        self.assertNotEqual(low.raw["id"], selected.raw["id"])
        tb = self.sources(opened, "max")["tb"]["rating"]
        self.assertEqual(tb.raw["metrics"]["total_cost_usd"], 4.2)
        self.assertIsNone(tb.cost)
        self.assertEqual((selected.first_answer_seconds, selected.first_token_seconds,
                          selected.response_500_tokens_seconds, selected.speed),
                         (139.23, 139.23, 142, 180.51))
        kimi = self.configuration(self.opened("kimi-k3"), "low")["configuration"]
        self.assertEqual((kimi.first_answer_seconds, kimi.first_token_seconds,
                          kimi.response_500_tokens_seconds, kimi.speed),
                         (60.66, 3.45, 74.96, 34.96))

    def test_missing_timing_price_and_catalog_do_not_change_selection_or_fill_each_other(self):
        docs = self.docs()
        row = next(r for r in docs["aa"]["data"] if r["name"] == "GPT-5.6 Luna (max)")
        row["performance"]["median_time_to_first_answer_token_seconds"] = None
        row["pricing"]["price_1m_input_tokens"] = None
        docs.pop("or")
        opened = self.opened("gpt-5-6-luna", ds=self.load(docs))
        baseline = self.opened("gpt-5-6-luna")
        self.assertEqual((opened["effort"], opened["configuration"].cost,
                          opened["frontier"], opened["dom"], opened["alternatives"]),
                         (baseline["effort"], baseline["configuration"].cost,
                          baseline["frontier"], baseline["dom"], baseline["alternatives"]))
        selected = opened["configuration"]
        self.assertIsNone(selected.first_answer_seconds)
        self.assertEqual((selected.first_token_seconds, selected.response_500_tokens_seconds,
                          selected.speed), (139.23, 142, 180.51))
        self.assertIsNone(selected.pricing["price_1m_input_tokens"])
        self.assertEqual(selected.pricing["price_1m_output_tokens"], 1.2)
        self.assertEqual(self.sources(opened, "max")["aa"]["grade"], 3)

    def test_unsupported_objectives_keep_sources_without_selecting_any_configuration(self):
        for role in ("Coder", "Coordinator"):
            for objective in ("ppi", "price"):
                with self.subTest(role=role, objective=objective):
                    opened = self.opened("gpt-5-6-sol", role, objective=objective)
                    self.assertIsNone(opened["configuration"])
                    self.assertIsNone(opened["effort"])
                    self.assertIn("Unavailable objective", opened["reason"])
                    self.assertIn("No configuration selected", opened["rationale"])
                    self.assertNotIn("Within each model", opened["rationale"])
                    self.assertFalse(any(c["selected"] for c in opened["configurations"]))
                    self.assertTrue(all("Unavailable objective" in c["eligibility_reason"]
                                        for c in opened["configurations"]))
                    maximum = self.sources(opened, "max")
                    self.assertEqual(maximum["deepswe"]["rank"], 2)
                    self.assertEqual(maximum["tb"]["rank"], 1)
                    self.assertEqual(opened["alternatives"], [])

    def test_all_scored_efforts_include_aa_only_long_tail_and_competition_ties(self):
        docs = self.docs()
        docs["aa"]["data"].extend([
            {"id": "catalog-high", "name": "Catalog High (low)", "slug": "catalog-high-low",
             "evaluations": {"artificial_analysis_intelligence_index": 999}},
            {"id": "catalog-tie", "name": "Catalog Tie (low)", "slug": "catalog-tie-low",
             "evaluations": {"artificial_analysis_intelligence_index": 58.9,
                             "artificial_analysis_coding_index": 78.3}},
        ])
        ds = self.load(docs)
        intelligence = self.sources(self.opened("gpt-5-6-sol", ds=ds), "max")["aa"]
        self.assertEqual((intelligence["index"], intelligence["score"], intelligence["grade"],
                          intelligence["rank"], intelligence["population_size"]),
                         ("Intelligence", 58.9, 5, 4, 23))
        coding = self.sources(self.opened("gpt-5-6-sol", "Coder", ds=ds), "xhigh")["aa"]
        self.assertEqual((coding["index"], coding["score"], coding["grade"],
                          coding["rank"], coding["population_size"]),
                         ("Coding", 78.3, 5, 1, 22))
        after_tied_first = self.sources(
            self.opened("claude-opus-5", "Coder", ds=ds), "max")["aa"]
        self.assertEqual(after_tied_first["rank"], 3)
        result = render.query(ds, next(r for r in ROLES if r["name"] == "Planner"))
        self.assertFalse({"catalog-high", "catalog-tie"} & {r["key"] for r in result["rows"]})

    def test_source_only_efforts_keep_their_actual_independent_grades(self):
        opened = self.opened("dsw:gpt-5-6-terra")
        self.assertIsNone(opened["configuration"])
        self.assertIsNone(opened["effort"])
        self.assertEqual(opened["provider"], "—")
        self.assertIn("No measured Artificial Analysis configuration", opened["reason"])
        self.assertEqual([c["effort"] for c in opened["configurations"]],
                         ["low", "medium", "high", "xhigh", "max"])
        self.assertTrue(all(c["configuration"] is None and not c["selected"]
                            for c in opened["configurations"]))
        sources = self.sources(opened, "max")
        self.assertEqual((sources["deepswe"]["score"], sources["deepswe"]["grade"],
                          sources["deepswe"]["rank"], sources["deepswe"]["population_size"]),
                         (0.6962305986696231, 3, 3, 5))
        self.assertIsNone(sources["aa"]["score"])
        self.assertIsNone(sources["aa"]["grade"])
        self.assertIsNone(sources["tb"]["score"])
        self.assertEqual(self.configuration(opened, "max")["disagreement"], [])

    def test_unmeasured_source_efforts_are_retained_last_not_invented_as_configurations(self):
        docs = self.docs()
        docs["deepswe"]["rows"].extend([
            {"model": "gpt-5-6-luna", "pass_at_1": 0.7},
            {"model": "no-effort-peer", "pass_at_1": 0.8},
        ])
        docs["tb"]["submissions"].update({
            "unmeasured-luna.json": {
                "source_filter": {"model_name": "GPT-5.6 Luna", "reasoning_effort": "low"},
                "metrics": {"accuracy": 0.5}},
            "unmeasured-peer.json": {
                "source_filter": {"model_name": "no-effort-peer"},
                "metrics": {"accuracy": 0.6}},
        })
        ds = self.load(docs)
        opened = self.opened("gpt-5-6-luna", ds=ds)
        self.assertEqual(opened["effort"], "max")
        self.assertEqual([c["effort"] for c in opened["configurations"]],
                         ["low", "medium", "high", "xhigh", "max", None])
        config = self.configuration(opened, None)
        self.assertIsNone(config["configuration"])
        self.assertFalse(config["selected"])
        self.assertIn("No measured reasoning effort", config["eligibility_reason"])
        sources = self.sources(opened, None)
        self.assertIsNone(sources["aa"]["score"])
        self.assertEqual((sources["deepswe"]["score"], sources["deepswe"]["grade"],
                          sources["deepswe"]["rank"], sources["deepswe"]["population_size"]),
                         (0.7, 3, 2, 2))
        self.assertEqual((sources["tb"]["score"], sources["tb"]["grade"],
                          sources["tb"]["rank"], sources["tb"]["population_size"]),
                         (0.5, 3, 2, 2))
        self.assertEqual(sources["tb"]["rating"].raw["source_filter"]["reasoning_effort"],
                         "low")
        self.assertIn("no measured reasoning effort", sources["tb"]["population_label"])
        source_only = self.opened("dsw:no-effort-peer", ds=ds)
        self.assertIsNone(source_only["configuration"])
        self.assertEqual([c["effort"] for c in source_only["configurations"]], [None])
        self.assertEqual(self.sources(source_only, None)["deepswe"]["rank"], 1)

    def test_missing_selected_index_stays_unranked_without_source_or_index_substitution(self):
        docs = self.docs()
        for row in docs["aa"]["data"]:
            if row["slug"].startswith("gpt-5-6-luna"):
                row["evaluations"]["artificial_analysis_agentic_index"] = None
        opened = self.opened("gpt-5-6-luna", "Coordinator", ds=self.load(docs))
        self.assertIsNone(opened["configuration"])
        self.assertIsNone(opened["effort"])
        self.assertIn("No finite Agentic score", opened["reason"])
        sources = self.sources(opened, "max")
        self.assertEqual(sources["aa"]["index"], "Agentic")
        self.assertIsNotNone(sources["aa"]["rating"])
        self.assertEqual(sources["aa"]["rating"].score, 51.2)
        self.assertIsNone(sources["aa"]["score"])
        self.assertIsNone(sources["aa"]["rank"])
        self.assertIn("No finite Artificial Analysis Agentic score", sources["aa"]["reason"])
        self.assertEqual([s["source"] for s in
                          self.configuration(opened, "max")["disagreement"]],
                         ["deepswe", "tb"])

    def test_objective_and_display_exclusion_never_reselect_an_explored_effort(self):
        capability = self.opened("gpt-5-6-luna")
        value = self.opened("gpt-5-6-luna", "Explorer", min_grade=5)
        price = self.opened("gpt-5-6-luna", "Utility")
        self.assertEqual((capability["effort"], value["effort"], price["effort"]),
                         ("max", "low", "xhigh"))
        self.assertIn("Capability display", value["reason"])
        self.assertIsNone(self.configuration(value, "low")["eligibility_reason"])
        self.assertEqual([c["effort"] for c in value["configurations"] if c["selected"]],
                         ["low"])
        self.assertIn("Chosen measured effort: Low", value["rationale"])
        self.assertIn("Capability per dollar descending", value["rationale"])
        self.assertIn("Capability grade ≥ 2", price["rationale"])
        self.assertIn("inclusively", price["rationale"])
        for effort in ("low", "medium", "high"):
            self.assertIn("capability grade ≥ 2",
                          self.configuration(price, effort)["eligibility_reason"])
        self.assertIsNone(self.configuration(price, "xhigh")["eligibility_reason"])
        self.assertEqual(self.sources(price, "xhigh")["aa"]["grade"], 2)
        self.assertIsNone(self.configuration(price, "max")["eligibility_reason"])

    def test_provider_scope_changes_advice_not_any_source_reference_population(self):
        global_evidence = self.opened("gpt-5-6-sol")
        local = self.opened("gpt-5-6-sol", provider="OpenAI")
        self.assertEqual(local["effort"], global_evidence["effort"])
        self.assertEqual(self.sources(local, "max"), self.sources(global_evidence, "max"))
        self.assertEqual(local["advisory_scope"]["kind"], "provider")
        self.assertEqual(local["advisory_scope"]["provider"], "OpenAI")
        self.assertTrue(local["frontier"])
        self.assertIsNone(local["dom"])
        self.assertFalse(global_evidence["frontier"])
        self.assertEqual(global_evidence["dom"][2:4], ("claude-opus-5", "high"))
        self.assertEqual(local["alternatives"], [
            ("gpt-5-6-sol", "high", 0.5486, 55.9),
            ("gpt-5-6-sol", "xhigh", 0.8325, 57.7),
            ("gpt-5-5", "xhigh", 1.1748, 54.8)])
        self.assertEqual(global_evidence["alternatives"], [
            ("gpt-5-6-sol", "high", 0.5486, 55.9),
            ("claude-opus-5", "medium", 0.7224, 56.3),
            ("gpt-5-6-sol", "xhigh", 0.8325, 57.7)])
