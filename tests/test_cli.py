"""Behavioral consumers of real saved/temporary rating-source payloads.

The batch CLI, shared selected-index query and independent source evidence use
the same fetch/identity pipeline. Live acquisition tests use a local HTTP origin.
"""

import json
from datetime import datetime, timezone
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # in-process `import llmratings` for render tests
FIXTURES = REPO / ".scratch" / "llm-ratings" / "fixtures" / "main"

from llmratings import evidence, fetch, identity, render  # noqa: E402  (sys.path setup above)
from llmratings.session import Session  # noqa: E402
ROLES = render.load_roles(REPO / "llmratings" / "roles.json")


def run_cli(env_extra, *args):
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "llmratings", *args],
        capture_output=True, text=True, cwd=REPO, env=env)


def run_fixtures(env_extra=None, *args):
    return run_cli(env_extra or {"LLM_RATINGS_AA_API_KEY": "dummy"},
                   "--fixtures", str(FIXTURES), *args)



# Single-effort source template also used by local HTTP acquisition tests.
AA_ROW = ('{{"id": "{i}", "name": "{name} (low)", "slug": "{slug}-low",'
          ' "model_creator": {{"name": "Acme"}},'
          ' "evaluations": {{"artificial_analysis_intelligence_index": {ii}}},'
          ' "artificial_analysis_intelligence_index_cost":'
          ' {{"cost_per_task": {{"total_cost": {cost}}}}},'
          ' "performance": {{"median_output_tokens_per_second": {spd}}}}}')


def _live_handler(srv):
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            srv.serve(self.path, self)

        def log_message(self, *args):
            pass
    return H


class _LiveServer:
    """Local HTTP origin for the live-mode tests (no network leaves the
    machine): serves the fixture payloads in the shapes the live fetchers
    expect — deepswe.json verbatim; aa.json split into page_size=200 pages;
    tb.json's listing with download_urls rewritten to this origin plus one
    JSON per submission; or.json at /api/v1/models. `fail` is a path
    substring whose requests return 500 — the per-source failure contract."""

    PAGE_SIZE = 200

    def __init__(self, fixtures_dir=FIXTURES, fail=None, page_versions=None, page_dates=None):
        self.dir = Path(fixtures_dir)
        self.fail = fail
        self.page_versions = page_versions or {}
        self.page_dates = page_dates or {}
        self.seen = []
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _live_handler(self))
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def url(self, path=""):
        return f"http://127.0.0.1:{self.port}{path}"

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def serve(self, path, h):
        self.seen.append(path)
        if self.fail and self.fail in path:
            h.send_response(500)
            h.end_headers()
            return
        try:
            body = self._body(path)
        except KeyError:
            h.send_response(404)
            h.end_headers()
            return
        h.send_response(200)
        h.send_header("Content-Type", "application/json")
        h.send_header("Content-Length", str(len(body)))
        h.end_headers()
        h.wfile.write(body)

    def _body(self, path):
        if path.startswith("/artifacts/"):
            return (self.dir / "deepswe.json").read_bytes()
        if path.startswith("/api/v2/language/models/free"):
            aa = json.loads((self.dir / "aa.json").read_text())
            page = int(parse_qs(urlsplit(path).query).get("page", ["1"])[0])
            batch = aa["data"][(page - 1) * self.PAGE_SIZE: page * self.PAGE_SIZE]
            if page in self.page_versions:
                aa["intelligence_index_version"] = self.page_versions[page]
            aa.update(self.page_dates.get(page, {}))
            return json.dumps(dict(aa, data=batch)).encode()
        if path.startswith("/api/v1/models"):
            p = self.dir / "or.json"
            if not p.is_file():
                raise KeyError(path)
            return p.read_bytes()
        if path.startswith("/repos/"):
            tb = json.loads((self.dir / "tb.json").read_text())
            listing = []
            for e in tb["listing"]:
                e = dict(e)
                e["download_url"] = self.url("/sub/" + e["name"])
                listing.append(e)
            return json.dumps(listing).encode()
        if path.startswith("/sub/"):
            tb = json.loads((self.dir / "tb.json").read_text())
            return json.dumps(tb["submissions"][path.rsplit("/", 1)[-1]]).encode()
        raise KeyError(path)


class MissingKey(unittest.TestCase):
    def test_error_before_any_output(self):
        # The CLI treats a falsy key as unset, so an empty string forces the
        # missing-key path even when the parent env holds a real key.
        r = run_cli({"LLM_RATINGS_AA_API_KEY": ""}, "--fixtures", str(FIXTURES))
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("LLM_RATINGS_AA_API_KEY", r.stderr)


class FixtureFailure(unittest.TestCase):
    def test_missing_deepswe_names_source(self):
        with tempfile.TemporaryDirectory() as td:
            r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"}, "--fixtures", td)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("DeepSWE", r.stderr)

    def test_missing_aa_names_source(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "deepswe.json").write_text("{}")
            r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"}, "--fixtures", td)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Artificial Analysis", r.stderr)

    def test_missing_tb_names_source(self):
        # Only tb.json absent — the other two sources are intact, so the
        # failure must name Terminal-Bench, not a generic error.
        with tempfile.TemporaryDirectory() as td:
            for f in ("deepswe.json", "aa.json"):
                Path(td, f).write_text(Path(FIXTURES, f).read_text())
            r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"}, "--fixtures", td)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Terminal-Bench", r.stderr)

    def test_corrupt_tb_names_source(self):
        with tempfile.TemporaryDirectory() as td:
            for f in ("deepswe.json", "aa.json"):
                Path(td, f).write_text(Path(FIXTURES, f).read_text())
            Path(td, "tb.json").write_text("{")
            r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"}, "--fixtures", td)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Terminal-Bench", r.stderr)

    def test_missing_or_is_best_effort(self):
        # OpenRouter is enrichment only (ticket 18): a fixture without
        # or.json must render full tables, never fail.
        with tempfile.TemporaryDirectory() as td:
            for f in ("deepswe.json", "aa.json", "tb.json"):
                Path(td, f).write_text(Path(FIXTURES, f).read_text())
            r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"}, "--fixtures", td)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("frontier: ", r.stdout)


def aa_config(key, effort="low", score=50, cost=1, coding=None, agentic=None,
              speed=100, provider="Acme"):
    """A synthetic source-shaped row, with independent index measurements."""
    return {
        "id": f"{key}-{effort}", "name": f"{key} ({effort})",
        "slug": f"{key}-{effort}", "model_creator": {"name": provider},
        "evaluations": {"artificial_analysis_intelligence_index": score,
                        "artificial_analysis_coding_index": coding,
                        "artificial_analysis_agentic_index": agentic},
        "artificial_analysis_intelligence_index_cost":
            {"cost_per_task": {"total_cost": cost}},
        "performance": {"median_output_tokens_per_second": speed},
    }


class SelectionPolicy(unittest.TestCase):
    """Policy consumers from synthetic temporary source payloads."""

    def dataset(self, configs, included=None, tb=None):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        keys = {identity.aa_base_slug(r["slug"], identity.parse_aa_effort(r["name"]))
                for r in configs}
        included = sorted(keys) if included is None else included
        docs = {
            "aa.json": {"data": configs},
            "deepswe.json": {"rows": [
                {"model": key, "reasoning_effort": "low", "pass_at_1": 0.5}
                for key in included]},
            "tb.json": tb or {"listing": [], "submissions": {}},
        }
        for name, doc in docs.items():
            Path(td.name, name).write_text(json.dumps(doc))
        return identity.build({key: key for key in keys},
                              fetch.fetch_all(td.name))

    def role(self, name="Explorer", **changes):
        profile = next(r for r in ROLES if r["name"] == name)
        if not changes:
            return profile
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name, "roles.json")
        path.write_text(json.dumps([dict(profile, **changes)]))
        return render.load_roles(path)[0]

    def picks(self, result):
        return [(r["key"], r["effort"]) for r in result["rows"]]

    def test_role_selects_its_index_and_one_measured_effort(self):
        ds = self.dataset([
            aa_config("alpha", "low", 40, 1, 10, 80),
            aa_config("alpha", "max", 60, 6, 90, 20),
            aa_config("beta", "medium", 50, 1, 70, 90),
            aa_config("catalog-only", "low", 99, 0.01, 99, 99),
        ], included=["alpha", "beta", "source-only"])
        expected = {
            "Explorer": [("beta", "medium"), ("alpha", "low")],
            "Coder": [("alpha", "max"), ("beta", "medium")],
            "Coordinator": [("beta", "medium"), ("alpha", "low")],
            "Utility": [("beta", "medium"), ("alpha", "low")],
        }
        for name, picks in expected.items():
            with self.subTest(role=name):
                result = render.query(ds, self.role(name))
                self.assertEqual(self.picks(result), picks)
                self.assertEqual(result["status"], "ok")
                self.assertEqual([r["key"] for r in result["unranked"]],
                                 ["dsw:source-only"])
                self.assertIn("Artificial Analysis",
                              result["unranked"][0]["reason"])
                for row in result["rows"]:
                    self.assertEqual(row["configuration"].effort, row["effort"])

    def test_strict_frontier_retains_identical_and_negative_finite_points(self):
        ds = self.dataset([
            aa_config("beta", score=-5, cost=0),
            aa_config("alpha", score=-5, cost=0),
            aa_config("higher", "high", -2, 1),
            aa_config("lower", "max", -6, 0),
            aa_config("invalid", score=500, cost=-1),
            aa_config("catalog-only", score=999, cost=0),
        ], included=["alpha", "beta", "higher", "lower", "invalid"])
        result = render.query(ds, self.role("Planner"))
        self.assertEqual(self.picks(result), [
            ("higher", "high"), ("alpha", "low"), ("beta", "low"), ("lower", "max")])
        rows = {r["key"]: r for r in result["rows"]}
        self.assertTrue(rows["alpha"]["frontier"])
        self.assertTrue(rows["beta"]["frontier"])
        self.assertTrue(rows["higher"]["frontier"])
        self.assertFalse(rows["lower"]["frontier"])
        self.assertEqual(rows["lower"]["dom"][:2], (1, 0))
        self.assertEqual({p[0] for p in result["points"]},
                         {"alpha", "beta", "higher", "lower"})
        self.assertEqual([r["key"] for r in result["unranked"]], ["invalid"])

    def test_highest_capability_uses_score_cost_effort_and_key(self):
        configs = [
            aa_config("score", score=80, cost=100),
            aa_config("cost-choice", "low", 70, 4),
            aa_config("cost-choice", "high", 70, 2),
            aa_config("effort-choice", "max", 70, 2),
            aa_config("effort-choice", "xhigh", 70, 2),
            aa_config("effort-choice", "high", 70, 2),
            aa_config("effort-choice", "medium", 70, 2),
            aa_config("effort-choice", "low", 70, 2),
            aa_config("cheaper", "max", 70, 1),
            aa_config("beta", "medium", 70, 2),
            aa_config("alpha", "medium", 70, 2),
        ]
        expected = [("score", "low"), ("cheaper", "max"),
                    ("effort-choice", "low"), ("alpha", "medium"),
                    ("beta", "medium"), ("cost-choice", "high")]
        for rows in (configs, list(reversed(configs))):
            result = render.query(self.dataset(rows), self.role("Planner"))
            self.assertEqual(self.picks(result), expected)

    def test_best_value_uses_ratio_score_cost_effort_and_key(self):
        configs = [
            aa_config("alpha", "low", 30, 3),
            aa_config("alpha", "high", 40, 4),
            aa_config("alpha", "max", 100, 20),
            aa_config("beta", "high", 40, 4),
            aa_config("beta", "low", 40, 4),
            aa_config("gamma", "medium", 40, 4),
            aa_config("ratio-winner", "max", 40, 2),
            # Equal zero quotients and scores still compare matching cost.
            aa_config("zero-alpha", "low", 0, 2),
            aa_config("zero-alpha", "high", 0, 1),
            aa_config("zero-beta", "low", 0, 2),
            aa_config("zero-gamma", "high", 0, 1),
        ]
        expected = [("ratio-winner", "max"), ("beta", "low"),
                    ("gamma", "medium"), ("alpha", "high"),
                    ("zero-alpha", "high"), ("zero-gamma", "high"),
                    ("zero-beta", "low")]
        for rows in (configs, list(reversed(configs))):
            self.assertEqual(self.picks(render.query(self.dataset(rows), self.role())),
                             expected)

    def test_lowest_price_uses_cost_score_effort_and_key_not_speed(self):
        configs = [
            aa_config("alpha", "low", 10, 2, speed=10000),
            aa_config("alpha", "max", 20, 2, speed=9999),
            aa_config("alpha", "high", 20, 2, speed=None),
            aa_config("beta", "medium", 20, 2),
            aa_config("gamma", "high", 20, 2),
            aa_config("delta", "low", 20, 2),
            aa_config("cheapest", "max", 1, 1),
            aa_config("score-winner", "low", 30, 2),
        ]
        expected = [("cheapest", "max"), ("score-winner", "low"),
                    ("delta", "low"), ("beta", "medium"),
                    ("alpha", "high"), ("gamma", "high")]
        for rows in (configs, list(reversed(configs))):
            result = render.query(self.dataset(rows), self.role("Utility", floor=1))
            self.assertEqual(self.picks(result), expected)

    def test_every_effort_tie_is_in_measurement_order_then_canonical_key(self):
        configs = [aa_config(key, effort, 40, 2, 40, 40)
                   for key, effort in [("a-max", "max"), ("b-xhigh", "xhigh"),
                                       ("c-high", "high"), ("d-medium", "medium"),
                                       ("z-low", "low"), ("y-low", "low")]]
        expected = [("y-low", "low"), ("z-low", "low"), ("d-medium", "medium"),
                    ("c-high", "high"), ("b-xhigh", "xhigh"), ("a-max", "max")]
        ds = self.dataset(configs)
        for name, objective in (("Planner", "cap"), ("Explorer", "ppi"),
                                ("Utility", "price"), ("Coder", "cap"),
                                ("Coordinator", "cap")):
            with self.subTest(role=name):
                self.assertEqual(self.picks(render.query(ds, self.role(name), objective)),
                                 expected)

    def test_area_capability_has_no_cost_tie_or_index_fallback(self):
        ds = self.dataset([
            aa_config("alpha", "low", 1, None, 90, 40),
            aa_config("alpha", "max", 99, 0, 90, 80),
            aa_config("beta", "low", 100, 0, 90, 80),
            aa_config("intel-only", "low", 999, 0.001),
            aa_config("negative", "medium", 99, None, -10, -20),
            aa_config("nonfinite", "low", 100, 1, float("inf"), float("nan")),
        ])
        for name, expected in (
                ("Coder", [("alpha", "low"), ("beta", "low"), ("negative", "medium")]),
                ("Coordinator", [("beta", "low"), ("alpha", "max"),
                                 ("negative", "medium")])):
            with self.subTest(role=name):
                result = render.query(ds, self.role(name))
                self.assertEqual(self.picks(result), expected)
                self.assertEqual(result["points"], [])
                self.assertEqual({r["key"] for r in result["unranked"]},
                                 {"intel-only", "nonfinite"})
                for row in result["rows"]:
                    for field in ("cost", "ppi", "value", "price_tier", "frontier", "dom"):
                        self.assertIsNone(row[field], field)
                lines, display = render.table(ds, self.role(name))
                self.assertEqual([(r["key"], r["effort"]) for r in display], expected)
                self.assertNotIn("Benchmark task cost", "\n".join(lines))
                opened = evidence.model_evidence(ds, result, display[0])
                self.assertEqual(opened["alternatives"], [])
                self.assertEqual(opened["advisory_scope"]["kind"], "unavailable")

    def test_intelligence_required_data_and_usable_quotient(self):
        ds = self.dataset([
            aa_config("valid", score=20, cost=2),
            aa_config("zero", score=100, cost=0),
            aa_config("no-cost", score=999, cost=None),
            aa_config("negative-cost", score=1000, cost=-1),
            aa_config("no-score", score=None, cost=1),
            aa_config("nan-score", score=float("nan"), cost=1),
            aa_config("infinite-score", score=float("inf"), cost=1),
            aa_config("nan-cost", score=2000, cost=float("nan")),
            aa_config("infinite-cost", score=2000, cost=float("inf")),
            aa_config("overflow-ratio", score=1e308, cost=5e-324),
            aa_config("negative-score", score=-10, cost=2),
        ])
        self.assertEqual(self.picks(render.query(ds, self.role("Planner"))), [
            ("overflow-ratio", "low"), ("zero", "low"), ("valid", "low"),
            ("negative-score", "low")])
        self.assertEqual(self.picks(render.query(ds, self.role())), [
            ("valid", "low"), ("negative-score", "low")])
        price = render.query(ds, self.role("Utility", floor=1))
        self.assertEqual(self.picks(price), [
            ("zero", "low"), ("overflow-ratio", "low"), ("valid", "low"),
            ("negative-score", "low")])
        zero = next(r for r in price["rows"] if r["key"] == "zero")
        self.assertEqual(zero["cost"], 0)
        self.assertIsNone(zero["ppi"])
        self.assertIsNone(zero["value"])
        self.assertTrue(all(r["reason"] for r in price["unranked"]))

    def test_capability_population_precedes_cost_inclusion_and_effort_selection(self):
        references = [aa_config(f"reference-{score}", identity.EFFORTS[n % 5],
                                score, None, score, score)
                      for n, score in enumerate(range(0, 100, 10))]
        configs = references + [
            aa_config("alpha", "low", 30, 1, 70, 50),
            aa_config("alpha", "max", 70, 5, 30, 90),
            aa_config("edge", score=20, cost=0.5, coding=20, agentic=20),
            aa_config("equal-edge", score=20, cost=0.6, coding=20, agentic=20),
            aa_config("weak", score=10, cost=0.01, coding=10, agentic=10),
            aa_config("unpriced", "high", 80, None, 80, 80),
        ]
        ds = self.dataset(configs, included=["alpha", "edge", "equal-edge",
                                            "weak", "unpriced"])
        expected = {
            "Planner": {"alpha": ("max", 70, 4), "edge": ("low", 20, 2),
                        "equal-edge": ("low", 20, 2), "weak": ("low", 10, 1)},
            "Coder": {"alpha": ("low", 70, 4), "edge": ("low", 20, 2),
                      "equal-edge": ("low", 20, 2), "weak": ("low", 10, 1),
                      "unpriced": ("high", 80, 5)},
            "Coordinator": {"alpha": ("max", 90, 5), "edge": ("low", 20, 2),
                            "equal-edge": ("low", 20, 2), "weak": ("low", 10, 1),
                            "unpriced": ("high", 80, 5)},
        }
        for name, grades in expected.items():
            result = render.query(ds, self.role(name))
            self.assertEqual({r["key"]: (r["effort"], r["score"], r["grade"])
                              for r in result["rows"]}, grades)
        for name in ("Utility", "Explorer"):
            price = render.query(ds, self.role(name), "price")
            self.assertEqual(self.picks(price), [
                ("edge", "low"), ("equal-edge", "low"), ("alpha", "low")])
            self.assertEqual([r["grade"] for r in price["rows"]], [2, 2, 2])
        self.assertIn(("weak", "low"), self.picks(render.query(ds, self.role())))
        filtered = render.query(ds, self.role("Planner"), min_grade=5)
        self.assertEqual(filtered["status"], "no_qualifying")
        self.assertEqual(filtered["rows"], [])
        self.assertIn("No qualifying configuration", filtered["reason"])
        self.assertIn("Planner", filtered["reason"])
        self.assertIn("grade ≥ 5", filtered["reason"])
        self.assertEqual({r["key"] for r in filtered["excluded"]},
                         {"alpha", "edge", "equal-edge", "weak"})
        self.assertEqual(filtered["points"], render.query(ds, self.role("Planner"))["points"])

    def test_independent_axis_grades_do_not_shrink_under_display_filter(self):
        ds = self.dataset([
            aa_config("alpha", score=10, cost=1, speed=10),
            aa_config("beta", score=20, cost=2, speed=10),
            aa_config("gamma", score=30, cost=3, speed=30),
            aa_config("missing-timing", score=40, cost=4, speed=None),
        ])
        baseline = render.query(ds, self.role())
        rows = {r["key"]: r for r in baseline["rows"]}
        self.assertEqual((rows["alpha"]["spd"], rows["beta"]["spd"],
                          rows["gamma"]["spd"]), (3, 3, 5))
        self.assertIsNone(rows["missing-timing"]["spd"])
        self.assertEqual({r["value"] for r in baseline["rows"]}, {5})
        self.assertEqual([rows[k]["price_tier"] for k in
                          ("alpha", "beta", "gamma", "missing-timing")], [1, 2, 3, 4])
        narrow = render.query(ds, self.role(), min_grade=4)
        for row in narrow["rows"]:
            self.assertEqual(tuple(row[f] for f in ("grade", "value", "spd", "price_tier")),
                             tuple(rows[row["key"]][f]
                                   for f in ("grade", "value", "spd", "price_tier")))
        added = self.dataset([
            aa_config("alpha", score=10, cost=1, speed=10),
            aa_config("beta", score=20, cost=2, speed=20),
            aa_config("gamma", score=30, cost=3, speed=30),
        ])
        before = next(r for r in render.query(added, self.role())["rows"]
                      if r["key"] == "beta")
        after = self.dataset([
            aa_config("alpha", score=10, cost=1, speed=10),
            aa_config("beta", score=20, cost=2, speed=20),
            aa_config("gamma", score=30, cost=3, speed=30),
            aa_config("delta", score=40, cost=4, speed=25),
        ])
        after = next(r for r in render.query(after, self.role())["rows"]
                     if r["key"] == "beta")
        self.assertEqual((before["spd"], after["spd"]), (4, 3))

    def test_timing_and_unverified_share_never_change_selected_policy(self):
        configs = [
            aa_config("alpha", "max", 40, 2, 40, 40, speed=9999),
            aa_config("alpha", "low", 40, 2, 40, 40, speed=None),
            aa_config("beta", "medium", 50, 3, 50, 50),
        ]
        original = self.dataset(configs)
        for config in configs:
            config["performance"] = {
                "median_output_tokens_per_second": 1,
                "median_time_to_first_answer_token_seconds": 99999,
                "median_time_to_first_token_seconds": 0,
                "median_end_to_end_response_time_seconds": None,
            }
        changed = self.dataset(configs)
        for model in changed.models.values():
            model.token_share_30d = 0.99
        for name in ("Planner", "Explorer", "Utility", "Coder", "Coordinator"):
            role = self.role(name)
            def observed(ds):
                result = render.query(ds, role)
                rows = [(r["key"], r["effort"], r["score"], r["grade"],
                         r["dsw"], r["tb"], r["value"], r["price_tier"],
                         r["dom"], r["alternatives"])
                        for r in result["rows"]]
                picks = [(g["provider"], g["primary"]["key"],
                          g["runner_up"]["key"] if g["runner_up"] else None)
                         for g in result["picks"]]
                return rows, picks, result["frontier_path"], result["shortcuts"]
            self.assertEqual(observed(original), observed(changed))

    def test_unsupported_area_objectives_and_empty_results_are_explicit(self):
        ds = self.dataset([aa_config("intel-only", score=100, cost=1)])
        for name in ("Coder", "Coordinator"):
            for objective in ("ppi", "price"):
                result = render.query(ds, self.role(name), objective)
                self.assertEqual(result["status"], "unavailable_objective")
                self.assertEqual(result["objective"], objective)
                self.assertEqual(result["rows"], [])
                self.assertEqual(result["points"], [])
                self.assertIn(render.OBJECTIVE_LABEL[objective], result["reason"])
                self.assertIn("intel-only", result["unranked"][0]["key"])
        no_area = render.query(ds, self.role("Coder"))
        self.assertEqual(no_area["status"], "no_qualifying")
        self.assertIn("No qualifying configuration", no_area["reason"])
        self.assertIn("Coding", no_area["unranked"][0]["reason"])
        no_price = self.dataset([aa_config("unpriced", cost=None)])
        lines, rows = render.table(no_price, self.role("Planner"))
        self.assertEqual(rows, [])
        output = "\n".join(lines)
        self.assertIn("No qualifying configuration", output)
        self.assertIn("Highest capability", output)
        self.assertIn("Unranked included models", output)

    def test_advice_remains_floor_free_and_display_filter_free(self):
        ds = self.dataset([
            aa_config("target", "max", 80, 10),
            aa_config("near-one", score=79, cost=1),
            aa_config("near-two", score=78, cost=2),
            aa_config("near-three", score=77, cost=3),
            aa_config("near-four", score=76, cost=4),
        ])
        broad = render.query(ds, self.role("Utility"))
        strict = render.query(ds, self.role("Utility", floor=5), min_grade=5)
        self.assertEqual(self.picks(strict), [("target", "max")])
        self.assertEqual(strict["points"], broad["points"])
        opened = evidence.model_evidence(ds, strict, strict["rows"][0])
        self.assertEqual(opened["alternatives"], [
            ("near-one", "low", 1, 79), ("near-two", "low", 2, 78),
            ("near-three", "low", 3, 77)])
        self.assertEqual({r["key"] for r in strict["unranked"]},
                         {"near-one", "near-two", "near-three", "near-four"})

    def test_provider_picks_use_direct_order_not_frontier_sections(self):
        ds = self.dataset([
            aa_config("winner", score=100, cost=5),
            aa_config("winner", "high", score=100, cost=6),
            aa_config("second", "max", score=99, cost=10),
            aa_config("cheap", score=80, cost=1),
            aa_config("only", score=90, cost=2, provider="Other"),
            aa_config("catalog-only", score=200, cost=0, provider="Catalog"),
        ], included=["winner", "second", "cheap", "only"])
        result = render.query(ds, self.role("Planner"), view="picks")
        groups = {g["provider"]: g for g in result["picks"]}
        self.assertEqual([(groups["Acme"][slot]["key"],
                           groups["Acme"][slot]["effort"])
                          for slot in ("primary", "runner_up")],
                         [("winner", "low"), ("second", "max")])
        self.assertFalse(groups["Acme"]["runner_up"]["frontier"])
        self.assertEqual([r["key"] for r in result["table_rows"]],
                         ["winner", "only", "cheap", "second"])
        self.assertEqual(groups["Other"]["primary"]["key"], "only")
        self.assertIsNone(groups["Other"]["runner_up"])
        self.assertEqual(groups["Other"]["reason"], "No qualifying runner-up")
        self.assertEqual(result["creators"], ["Acme", "Catalog", "Other"])
        self.assertEqual(result["shortcuts"],
                         ("OpenAI", "Anthropic", "Google", "DeepSeek", "xAI"))
        self.assertEqual([g["provider"] for g in result["providers_without_picks"]],
                         ["Catalog"])
        self.assertIn("inclusion", result["providers_without_picks"][0]["reason"])
        scoped = render.query(ds, self.role("Planner"), provider="Acme", view="picks")
        self.assertEqual([g["provider"] for g in scoped["picks"]], ["Acme"])
        self.assertEqual({r["provider"] for r in scoped["table_rows"]}, {"Acme"})
        empty = render.query(ds, self.role("Planner"), provider="Google")
        self.assertEqual(empty["picks"], [])
        self.assertEqual(empty["status"], "no_qualifying")
        self.assertIn("Google", empty["reason"])
        self.assertEqual(empty["creators"], result["creators"])
        self.assertEqual(empty["shortcuts"], result["shortcuts"])

    def test_creator_scope_keeps_nonselected_filter_and_floor_free_advice(self):
        ds = self.dataset([
            aa_config("target", "max", score=80, cost=10),
            aa_config("peer", "max", score=81, cost=9),
            aa_config("peer", "low", score=100, cost=11),
            aa_config("cross", score=90, cost=1),
            aa_config("near-one", score=79, cost=2),
            aa_config("near-two", "high", score=78, cost=3),
            aa_config("near-three", "medium", score=77, cost=4),
            aa_config("near-four", "max", score=76, cost=5),
            aa_config("too-low", score=74, cost=0.1),
            aa_config("outsider", "max", score=100, cost=0.5, provider="Other"),
            aa_config("catalog-only", score=100, cost=0, provider="Catalog"),
        ], included=["target", "peer", "cross", "near-one", "near-two",
                     "near-three", "near-four", "too-low", "outsider"])
        global_result = render.query(ds, self.role("Planner"))
        local = render.query(ds, self.role("Planner"), provider="Acme")
        global_rows = {r["key"]: r for r in global_result["rows"]}
        rows = {r["key"]: r for r in local["rows"]}
        self.assertEqual(local["advisory_scope"]["kind"], "provider")
        self.assertEqual(local["advisory_scope"]["provider"], "Acme")
        self.assertEqual(global_result["advisory_scope"]["kind"], "global")
        self.assertEqual(rows["peer"]["effort"], "low")
        self.assertTrue(rows["peer"]["frontier"])
        self.assertFalse(global_rows["peer"]["frontier"])
        self.assertEqual(rows["target"]["dom"], (1, 1, "peer", "max", 81, 9))
        self.assertEqual(global_rows["target"]["dom"],
                         (20, 9.5, "outsider", "max", 100, 0.5))
        self.assertEqual(rows["target"]["alternatives"], [
            ("cross", "low", 1, 90), ("near-one", "low", 2, 79),
            ("near-two", "high", 3, 78)])
        self.assertEqual(global_rows["target"]["alternatives"], [
            ("outsider", "max", 0.5, 100), ("cross", "low", 1, 90),
            ("near-one", "low", 2, 79)])
        self.assertEqual(local["frontier_path"], [
            ("too-low", "low", 0.1, 74), ("cross", "low", 1, 90),
            ("peer", "low", 11, 100)])
        self.assertEqual(global_result["frontier_path"],
                         [("too-low", "low", 0.1, 74), ("outsider", "max", 0.5, 100)])
        strict = render.query(ds, self.role("Utility", floor=5),
                              min_grade=5, provider="Acme")
        self.assertEqual(strict["points"], local["points"])
        self.assertEqual(strict["frontier_path"], local["frontier_path"])
        self.assertNotIn("catalog-only", {p[0] for p in local["points"]})
        opened = evidence.model_evidence(ds, local, rows["target"])
        self.assertEqual(opened["advisory_scope"]["label"], "Creator-local comparison — Acme")
        self.assertEqual(opened["dom"], (1, 1, "peer", "max", 81, 9))
        self.assertEqual(opened["alternatives"], [
            ("cross", "low", 1, 90), ("near-one", "low", 2, 79),
            ("near-two", "high", 3, 78)])
        restored = render.query(ds, self.role("Planner"), provider=None)
        self.assertEqual(restored["frontier_path"], global_result["frontier_path"])
        self.assertEqual(restored["rows"], global_result["rows"])

    def test_provider_display_exclusions_keep_selected_effort_and_measurement_reasons(self):
        ds = self.dataset([
            aa_config("cheap-effort", "low", score=10, cost=1),
            aa_config("cheap-effort", "max", score=100, cost=100),
            aa_config("unpriced", score=90, cost=None),
            aa_config("other", score=50, cost=1, provider="Other"),
            aa_config("catalog", score=200, cost=1, provider="Catalog"),
        ], included=["cheap-effort", "unpriced", "other", "source-only"])
        broad = render.query(ds, self.role())
        narrow = render.query(ds, self.role(), provider="Acme", min_grade=5)
        self.assertEqual(narrow["status"], "no_qualifying")
        self.assertEqual(narrow["rows"], [])
        self.assertEqual(narrow["picks"], [])
        self.assertEqual([(r["key"], r["effort"]) for r in narrow["excluded"]],
                         [("cheap-effort", "low")])
        excluded = narrow["excluded"][0]
        self.assertEqual(excluded["configuration"].effort, "low")
        self.assertIn("Capability display", excluded["reason"])
        self.assertEqual([r["key"] for r in narrow["unranked"]], ["unpriced"])
        self.assertIn("task cost", narrow["unranked"][0]["reason"])
        self.assertIsNone(narrow["unranked"][0]["configuration"])
        self.assertIn("dsw:source-only", {r["key"] for r in broad["unranked"]})
        self.assertEqual({r["provider"] for r in narrow["excluded"] + narrow["unranked"]},
                         {"Acme"})
        self.assertIn("Explorer", narrow["reason"])
        self.assertIn("Acme", narrow["reason"])
        self.assertIn("grade ≥ 5", narrow["reason"])
        reasons = narrow["providers_without_picks"][0]
        self.assertIn("Capability display", reasons["reason"])
        self.assertIn("task cost", reasons["reason"])
        self.assertEqual(reasons["excluded"], narrow["excluded"])
        selected = next(r for r in broad["rows"] if r["key"] == "cheap-effort")
        for field in ("configuration", "score", "grade", "dsw", "tb",
                      "value", "spd", "price_tier"):
            self.assertEqual(excluded[field], selected[field])
        self.assertEqual(narrow["creators"], ["Acme", "Catalog", "Other"])
        self.assertEqual(narrow["shortcuts"], broad["shortcuts"])

    def test_scoped_area_picks_never_expose_intelligence_cost_advice(self):
        ds = self.dataset([
            aa_config("alpha", "max", score=100, cost=0, coding=50, agentic=60),
            aa_config("alpha", "low", score=1, cost=100, coding=50, agentic=60),
            aa_config("beta", "low", score=100, cost=0, coding=50, agentic=60),
            aa_config("other", score=100, cost=0, coding=100, agentic=100,
                      provider="Other"),
        ])
        for name in ("Coder", "Coordinator"):
            result = render.query(ds, self.role(name), provider="Acme", view="picks")
            self.assertEqual(self.picks(result), [("alpha", "low"), ("beta", "low")])
            self.assertEqual(result["points"], [])
            self.assertEqual(result["frontier_path"], [])
            self.assertEqual(result["advisory_scope"]["kind"], "unavailable")
            self.assertEqual(result["picks"][0]["primary"]["key"], "alpha")
            self.assertEqual(result["picks"][0]["runner_up"]["key"], "beta")
            for row in result["rows"]:
                self.assertIsNone(row["frontier"])
                self.assertIsNone(row["dom"])
                self.assertIsNone(row["cost"])
                self.assertEqual(row["alternatives"], [])
            for objective in ("ppi", "price"):
                unavailable = render.query(ds, self.role(name), objective,
                                           min_grade=4, provider="Acme", view="picks")
                self.assertEqual(unavailable["status"], "unavailable_objective")
                self.assertEqual(unavailable["objective"], objective)
                self.assertEqual(unavailable["min_grade"], 4)
                self.assertEqual(unavailable["provider"], "Acme")
                self.assertEqual(unavailable["view"], "picks")
                self.assertEqual(unavailable["picks"], [])
                self.assertIn(name, unavailable["reason"])
                self.assertIn("Acme", unavailable["reason"])
                self.assertIn("grade ≥ 4", unavailable["reason"])
                self.assertEqual({r["key"] for r in unavailable["unranked"]},
                                 {"alpha", "beta"})
                self.assertEqual({r["action"] for r in unavailable["recovery_actions"]},
                                 {"all_providers", "clear_capability",
                                  "highest_capability", "role_default"})

    def test_unmeasured_rows_do_not_shape_configuration_grades(self):
        unmeasured = aa_config("unmeasured", score=999, coding=999, agentic=999)
        unmeasured.update(name="unmeasured", slug="unmeasured")
        ds = self.dataset([
            aa_config("alpha", "low", 10, 1, 10, 10),
            aa_config("beta", "max", 20, 2, 20, 20),
            unmeasured,
        ])
        for name in ("Planner", "Coder", "Coordinator"):
            result = render.query(ds, self.role(name))
            self.assertEqual({r["key"]: r["grade"] for r in result["rows"]},
                             {"alpha": 3, "beta": 5})
            self.assertEqual(result["unranked"][0]["key"], "unmeasured")
            self.assertIn("measured", result["unranked"][0]["reason"])


class RolesFile(unittest.TestCase):
    def test_approved_catalog_order_and_cli_names(self):
        expected = [
            ("Explorer", "intelligence", "ppi"), ("Researcher", "intelligence", "ppi"),
            ("Planner", "intelligence", "cap"), ("Coder", "coding", "cap"),
            ("Reviewer", "coding", "cap"), ("Coordinator", "agentic", "cap"),
            ("Generalist", "intelligence", "ppi"), ("Utility", "intelligence", "price")]
        self.assertEqual([(r["name"], r["index"], r["objective"]) for r in ROLES], expected)
        self.assertEqual({r["floor"] for r in ROLES}, {2})
        for name in ("bogus", "Chores", "Generic", "Orchestrator"):
            result = run_fixtures(None, "--role", name)
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid choice", result.stderr)
            self.assertIn("Coordinator", result.stderr)

    def run_profile(self, profile, *args):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        path = Path(td.name, "roles.json")
        path.write_text(json.dumps(profile))
        return run_fixtures({"LLM_RATINGS_AA_API_KEY": "dummy",
                             "LLM_RATINGS_ROLES": str(path)}, *args)

    def test_edited_catalog_changes_selected_index_objective_and_default(self):
        custom = dict(ROLES[0], name="Mail Sorter", index="coding", objective="cap")
        custom.pop("floor")
        result = self.run_profile([custom, ROLES[0]])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Mail Sorter — Coding — Highest capability", result.stdout)
        self.assertIn("GPT-5.6 Sol", result.stdout)
        self.assertIn("Extra high", result.stdout)
        self.assertIn("78.3", result.stdout)
        self.assertNotIn("frontier:", result.stdout)
        explicit = self.run_profile([ROLES[0], custom], "--role", "Mail Sorter")
        self.assertEqual(explicit.stdout, result.stdout)
        changed = self.run_profile([dict(custom, index="agentic")])
        self.assertIn("Mail Sorter — Agentic — Highest capability", changed.stdout)
        self.assertIn("55.3", changed.stdout)

    def test_recognized_unsupported_profile_stays_selected(self):
        result = self.run_profile([dict(ROLES[3], objective="ppi")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Coder — Coding — Best value", result.stdout)
        self.assertIn("Unavailable objective", result.stdout)
        self.assertNotIn("Direct Coding score order", result.stdout)

    def test_malformed_profiles_fail_with_actionable_startup_errors(self):
        malformed = [
            ({"name": "not a list"}, "non-empty list"), ([], "non-empty list"),
            ([None], "not an object"), ([dict(ROLES[0], name=" ")], "name"),
            ([dict(ROLES[0], description=None)], "description"),
            ([dict(ROLES[0], capacity="")], "capacity"),
            ([dict(ROLES[0], index="vision")], "index"),
            ([dict(ROLES[0], index=[])], "index"),
            ([dict(ROLES[0], objective="speed")], "objective"),
            ([dict(ROLES[0], objective={})], "objective"),
            ([dict(ROLES[0], floor=True)], "floor"),
            ([dict(ROLES[0], floor=0)], "floor"),
            ([ROLES[0], ROLES[0]], "repeats role name"),
        ]
        for profiles, error in malformed:
            with self.subTest(profiles=profiles):
                result = self.run_profile(profiles)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(error, result.stderr)



class SavedPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = identity.build(
            identity.load_aliases(REPO / "llmratings" / "aliases.json"),
            fetch.fetch_all(FIXTURES))
        cls.roles = {r["name"]: r for r in ROLES}

    def test_all_shipped_roles_have_hand_computed_direct_order_and_efforts(self):
        value = [("gpt-5-6-luna", "low"), ("gpt-5-6-sol", "low"),
                 ("kimi-k3", "low"), ("gpt-5-5", "low"), ("claude-opus-5", "low")]
        capability = [("claude-opus-5", "max"), ("gpt-5-6-sol", "max"),
                      ("kimi-k3", "max"), ("gpt-5-5", "xhigh"), ("gpt-5-6-luna", "max")]
        coding = [("gpt-5-6-sol", "xhigh"), ("claude-opus-5", "max"),
                  ("kimi-k3", "max"), ("gpt-5-5", "xhigh"), ("gpt-5-6-luna", "max")]
        agentic = [("claude-opus-5", "max"), ("gpt-5-6-sol", "max"),
                   ("kimi-k3", "max"), ("gpt-5-6-luna", "max"), ("gpt-5-5", "xhigh")]
        price = [("gpt-5-6-luna", "xhigh"), ("kimi-k3", "low"),
                 ("gpt-5-6-sol", "low"), ("claude-opus-5", "low"), ("gpt-5-5", "medium")]
        expected = {"Explorer": value, "Researcher": value, "Planner": capability,
                    "Coder": coding, "Reviewer": coding, "Coordinator": agentic,
                    "Generalist": value, "Utility": price}
        for name, picks in expected.items():
            with self.subTest(role=name):
                result = render.query(self.ds, self.roles[name])
                self.assertEqual([(r["key"], r["effort"]) for r in result["rows"]], picks)

    def test_batch_defaults_and_source_only_evidence_are_reachable(self):
        result = run_fixtures()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Explorer — Intelligence — Best value", result.stdout)
        self.assertIn(render.ATTRIBUTION, result.stdout)
        self.assertIn("Unranked included models", result.stdout)
        query = render.query(self.ds, self.roles["Explorer"])
        self.assertTrue(query["unranked"])
        self.assertTrue(all(r["measurements"] and r["configuration"] is None
                            for r in query["unranked"]))

    def test_model_table_sections_do_not_replace_direct_objective_order(self):
        role = self.roles["Planner"]
        direct = render.query(self.ds, role)["rows"]
        _, visible = render.table(self.ds, role)
        self.assertEqual([r["model"] for r in visible], [
            "Claude Opus 5", "GPT-5.6 Luna", "GPT-5.6 Sol", "Kimi K3", "GPT-5.5"])
        self.assertNotEqual([r["key"] for r in direct], [r["key"] for r in visible])
        for section in ([r for r in visible if r["frontier"]],
                        [r for r in visible if not r["frontier"]]):
            self.assertIsNone(section[0]["score_change"])
            self.assertIsNone(section[0]["cost_change"])
        sol, kimi, gpt = visible[2:]
        self.assertAlmostEqual(kimi["score_change"], -1.8)
        self.assertAlmostEqual(kimi["cost_change"], -0.3773)
        self.assertAlmostEqual(gpt["score_change"], -2.3)
        self.assertIsNone(sol["score_change"])

    def test_real_shared_session_projections_and_batch_keep_scope_and_grades(self):
        state = Session(self.ds, ROLES)
        table = state.query()
        self.assertEqual(table["role"]["name"], "Explorer")
        self.assertEqual(table["view"], "table")
        self.assertEqual(table["provider_label"], "All providers")
        self.assertEqual([(r["key"], r["effort"]) for r in table["table_rows"]][:1],
                         [("gpt-5-6-luna", "low")])
        picks = state.set_view("picks")
        openai = next(g for g in picks["picks"] if g["provider"] == "OpenAI")
        self.assertEqual([(openai[slot]["key"], openai[slot]["effort"])
                          for slot in ("primary", "runner_up")],
                         [("gpt-5-6-luna", "low"), ("gpt-5-6-sol", "low")])
        self.assertEqual({g["provider"] for g in picks["picks"]},
                         {"OpenAI", "Anthropic", "Kimi"})
        self.assertEqual({r["key"] for r in picks["unranked"]},
                         {"dsw:qwen3-8-max", "dsw:gpt-5-6-terra"})
        state.set_role("Planner")
        broad = state.query()
        baseline = {r["key"]: r for r in broad["rows"]}
        narrow = state.set_provider("OpenAI")
        self.assertEqual(narrow["advisory_scope"]["kind"], "provider")
        self.assertEqual(narrow["view"], "picks")
        openai = narrow["picks"][0]
        self.assertEqual([(openai[slot]["key"], openai[slot]["effort"])
                          for slot in ("primary", "runner_up")],
                         [("gpt-5-6-sol", "max"), ("gpt-5-5", "xhigh")])
        filtered = state.set_min_grade(5)
        for row in filtered["rows"] + filtered["excluded"]:
            for field in ("configuration", "score", "grade", "dsw", "tb",
                          "value", "spd", "price_tier"):
                self.assertEqual(row[field], baseline[row["key"]][field])
        self.assertEqual(filtered["creators"], broad["creators"])
        self.assertEqual(filtered["shortcuts"], broad["shortcuts"])
        lines, displayed = render.table(self.ds, state.role, result=filtered)
        self.assertEqual(displayed, filtered["table_rows"])
        self.assertIn("Provider selection: OpenAI", "\n".join(lines))
        state.set_min_grade(None)
        restored = state.recover("all_providers")
        self.assertEqual(restored["frontier_path"], broad["frontier_path"])
        self.assertEqual(restored["rows"], broad["rows"])
        self.assertIs(state.ds, self.ds)
        batch = run_fixtures(None, "--role", "Explorer")
        self.assertEqual(batch.returncode, 0, batch.stderr)
        self.assertIn("Provider selection: All providers", batch.stdout)
        self.assertIn("Global comparison — All providers", batch.stdout)

    def test_same_effort_replacement_precedes_greater_cross_effort_gain(self):
        rows = {r["key"]: r for r in render.query(
            self.ds, self.roles["Explorer"])["rows"]}
        gpt = rows["gpt-5-5"]["dom"]
        self.assertEqual(gpt[2:4], ("gpt-5-6-sol", "low"))
        self.assertAlmostEqual(gpt[0], 5.9)
        self.assertAlmostEqual(gpt[1], 0.015)
        # Luna Maximum has a larger score gain, but is not same-effort.
        fallback = rows["kimi-k3"]["dom"]
        self.assertEqual(fallback[2:4], ("gpt-5-6-luna", "max"))
        self.assertAlmostEqual(fallback[0], 4.6)
        self.assertAlmostEqual(fallback[1], 0.1956)


class TerminalBench(unittest.TestCase):
    """Independent effort reference sets after best-agent collapse."""

    TB_MODELS = {"gpt-5-6-luna", "gpt-5-6-sol", "gpt-5-5", "claude-opus-5"}

    @classmethod
    def setUpClass(cls):
        from llmratings import fetch, identity
        raw = fetch.fetch_all(FIXTURES)
        aliases = identity.load_aliases(REPO / "llmratings" / "aliases.json")
        cls.ds = identity.build(aliases, raw)
        by_name = {r["name"]: r for r in ROLES}
        cls.results = {name: render.query(cls.ds, by_name[name])
                       for name in ("Explorer", "Planner", "Coder")}

    def test_default_selected_low_rows_have_no_terminal_bench_measurement(self):
        rows = self.results["Explorer"]["rows"]
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(r["effort"] == "low" for r in rows))
        self.assertTrue(all(r["tb"] is None and r["ratings"]["tb"] is None
                            for r in rows))

    def test_source_grades_stay_in_their_independent_effort_populations(self):
        rows = {r["model"]: r for r in self.results["Planner"]["rows"]}
        expected = {"Claude Opus 5": (5, 2), "GPT-5.6 Sol": (4, 5),
                    "GPT-5.6 Luna": (1, 4), "Kimi K3": (2, None),
                    "GPT-5.5": (4, None)}
        self.assertEqual({name: (r["dsw"], r["tb"]) for name, r in rows.items()},
                         expected)
        self.assertEqual(rows["GPT-5.6 Luna"]["ratings"]["tb"].score, 0.757)
        self.assertIsNone(rows["GPT-5.5"]["ratings"]["tb"])

    def test_collapse_best_agent(self):
        from llmratings import identity
        # GPT-5.5 high has two agents: codex .664 and warp .671 — the better
        # one wins, and the table shows a single GPT-5.5 row.
        best = identity.best_tb(self.ds.ratings, "high")
        self.assertEqual(best["gpt-5-5"].score, 0.671)
        self.assertEqual(best["gpt-5-5"].agent, "warp")
        rows = [r for r in self.results["Explorer"]["rows"] if r["key"] == "gpt-5-5"]
        self.assertEqual(len(rows), 1)

    def test_tie_broken_by_recency(self):
        from llmratings import identity
        # Luna max has two agents at .757 — the more recent submission
        # (2026-07-11, codex) wins over 2026-07-01 (junie).
        best = identity.best_tb(self.ds.ratings, "max")
        self.assertEqual(best["gpt-5-6-luna"].score, 0.757)
        self.assertEqual(best["gpt-5-6-luna"].date, "2026-07-11")
        self.assertEqual(best["gpt-5-6-luna"].agent, "codex-cli")

    def test_xhigh_rows_attach_and_collapse(self):
        from llmratings import identity
        # GPT-5.5's cap row sits at xhigh; the xhigh leg of the acceptance
        # criteria is asserted at the dataset level: both xhigh rows attach
        # and collapse to one rating per model — the same code path the
        # max columns render.
        xhigh = [r for r in self.ds.ratings
                 if r.source == "tb" and r.effort == "xhigh"]
        self.assertEqual(len(xhigh), 2)
        best = identity.best_tb(self.ds.ratings, "xhigh")
        self.assertEqual({k: r.score for k, r in best.items()},
                         {"gpt-5-6-luna": 0.733, "gpt-5-6-sol": 0.745})

    def test_rows_attach_wholesale_and_join_canonical(self):
        # All 11 fixture submissions attach; each joins onto its canonical AA
        # base slug — no TB source-only identity leaks into the tables.
        tb = [r for r in self.ds.ratings if r.source == "tb"]
        self.assertEqual(len(tb), 11)
        for r in tb:
            self.assertIn(r.model_key, self.TB_MODELS)
        self.assertNotIn("tb:", {r.model_key for r in tb})


class LiveAcquisition(unittest.TestCase):
    """Ticket 15 — live HTTP acquisition replaces the fixture backend. These
    tests exercise the live fetch code paths with no network leaving the
    machine: a local stdlib HTTP server serves the checked-in fixture payloads
    in the shapes the live fetchers expect (the LLM_RATINGS_HTTP_BASE seam),
    and can 500 any single path to exercise the per-source failure contract.
    The alias-seed extension degrades an unknown model to source-only
    identity through the fixture seam; ticket 18's OpenRouter enrichment is
    best-effort (a 500 degrades to a full table, the context join is
    dataset-level)."""

    KEY = {"LLM_RATINGS_AA_API_KEY": "dummy"}

    def live_run(self, srv, *args):
        env = dict(self.KEY)
        env["LLM_RATINGS_HTTP_BASE"] = srv.url()
        return run_cli(env, *args)

    def test_live_missing_key_setup_error(self):
        # No --fixtures: the default is now live. A missing key must hit the
        # ticket-11 setup error before any fetch.
        r = run_cli({"LLM_RATINGS_AA_API_KEY": ""})
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("LLM_RATINGS_AA_API_KEY", r.stderr)

    def test_live_deepswe_failure_names_source(self):
        srv = _LiveServer(fail="/artifacts/")
        self.addCleanup(srv.stop)
        r = self.live_run(srv)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "", "no partial tables on source failure")
        self.assertIn("DeepSWE", r.stderr)

    def test_live_aa_failure_names_source(self):
        srv = _LiveServer(fail="/api/v2/language/models/free")
        self.addCleanup(srv.stop)
        r = self.live_run(srv)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("Artificial Analysis", r.stderr)

    def test_live_tb_listing_failure_names_source(self):
        srv = _LiveServer(fail="/repos/harbor-framework")
        self.addCleanup(srv.stop)
        r = self.live_run(srv)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("Terminal-Bench", r.stderr)

    def test_live_tb_submission_failure_names_source(self):
        # The listing serves fine; one per-entry raw JSON 500s — the whole
        # TB source fails naming Terminal-Bench (no partial TB tables).
        srv = _LiveServer(fail="/sub/")
        self.addCleanup(srv.stop)
        r = self.live_run(srv)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertIn("Terminal-Bench", r.stderr)

    def test_live_or_failure_is_best_effort(self):
        # OpenRouter 500s: the run must still render full tables (ticket 18
        # — enrichment never joins the hard-fail contract), and the fetch
        # must have been attempted.
        srv = _LiveServer(fail="/api/v1/models")
        self.addCleanup(srv.stop)
        r = self.live_run(srv)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("frontier: ", r.stdout)
        self.assertIn("GPT-5.6 Luna", r.stdout)
        self.assertTrue(any("/api/v1/models" in p for p in srv.seen),
                        "OR fetch must be attempted on every live run")

    def test_live_renders_same_tables_as_fixture_mode(self):
        srv = _LiveServer()
        self.addCleanup(srv.stop)
        live = self.live_run(srv)
        self.assertEqual(live.returncode, 0, live.stderr)
        self.assertEqual(live.stdout, run_fixtures().stdout)

    def test_live_aa_paginates_until_short_page(self):
        # 250 AA rows served as 200 + 50. Kimi K3 (rated by DeepSWE) sits at
        # index 200 — the start of page 2 — so a fetcher that stops after
        # page 1 loses its AA row and the parity assertion below fails: the
        # merge is observable from output alone. The request log then pins
        # the rest of the contract (a second page was requested, no third).
        # Researcher is a floor-free Intelligence Best value consumer, so
        # catalog-only reference rows cannot hide the page-two recommendation.
        dummy = [json.loads(AA_ROW.format(
                     i=f"u{n}", name=f"Model {n}", slug=f"model-{n}",
                     ii=10 + n, cost=0.01 * n, spd=100 + n))
                 for n in range(1, 247)]
        rows = [json.loads(AA_ROW.format(
                    i="u1", name="GPT-5.6 Luna", slug="gpt-5-6-luna",
                    ii=40, cost=0.1, spd=100)),
                json.loads(AA_ROW.format(
                    i="u2", name="GPT-5.6 Sol", slug="gpt-5-6-sol",
                    ii=50, cost=0.2, spd=200)),
                json.loads(AA_ROW.format(
                    i="u3", name="GPT-5.5", slug="gpt-5-5",
                    ii=60, cost=0.3, spd=300)),
                json.loads(AA_ROW.format(
                    i="u4", name="Claude Opus 5", slug="claude-opus-5",
                    ii=70, cost=0.4, spd=400))] + dummy
        rows[200] = json.loads(AA_ROW.format(
                        i="u5", name="Kimi K3", slug="kimi-k3",
                        ii=30, cost=0.05, spd=150))
        with tempfile.TemporaryDirectory() as td:
            Path(td, "aa.json").write_text(json.dumps({"data": rows}))
            Path(td, "deepswe.json").write_text(json.dumps({"rows": [
                {"model": s, "reasoning_effort": "low", "pass_at_1": p}
                for s, p in [("gpt-5-6-luna", 0.4), ("gpt-5-6-sol", 0.5),
                             ("gpt-5-5", 0.6), ("claude-opus-5", 0.7),
                             ("kimi-k3", 0.35)]]}))
            Path(td, "tb.json").write_text(
                json.dumps({"listing": [], "submissions": {}}))
            srv = _LiveServer(td)
            self.addCleanup(srv.stop)
            live = self.live_run(srv, "--role", "Researcher")
            fix = run_cli(self.KEY, "--fixtures", td, "--role", "Researcher")
        self.assertEqual(live.returncode, 0, live.stderr)
        self.assertEqual(fix.returncode, 0, fix.stderr)
        self.assertEqual(live.stdout, fix.stdout)
        self.assertIn("GPT-5.6 Luna", live.stdout)
        self.assertIn("Kimi K3", live.stdout)
        self.assertTrue(any("page=2" in p for p in srv.seen),
                        "AA fetcher must page past a full 200-row page")
        self.assertFalse(any("page=3" in p for p in srv.seen),
                         "AA fetcher must stop on the short page")

    def test_live_or_context_joins_onto_models(self):
        # Dataset-level assertion of the live OpenRouter join (fixture-loaded
        # evidence cases are in test_evidence): ids resolve through the alias table
        # ("openai/gpt-5.6-luna") or a vendor-prefix strip ("anthropic/
        # claude-opus-5"); models without an OR row keep context None.
        from llmratings import fetch, identity
        srv = _LiveServer()
        self.addCleanup(srv.stop)
        os.environ["LLM_RATINGS_HTTP_BASE"] = srv.url()
        os.environ["LLM_RATINGS_AA_API_KEY"] = "dummy"
        try:
            raw = fetch.fetch_all(None)
        finally:
            del os.environ["LLM_RATINGS_HTTP_BASE"]
            del os.environ["LLM_RATINGS_AA_API_KEY"]
        aliases = identity.load_aliases(REPO / "llmratings" / "aliases.json")
        ds = identity.build(aliases, raw)
        self.assertEqual(ds.models["claude-opus-5"].context_length, 200000)
        self.assertEqual(ds.models["claude-opus-5"].modalities,
                         "in: text, image, file; out: text")
        self.assertEqual(ds.models["gpt-5-6-luna"].context_length, 200000)
        self.assertIsNone(ds.models["kimi-k3"].context_length,
                          "models without an OR row keep context None")

    def test_unknown_model_is_unranked_with_a_source_only_reason(self):
        # Source-only evidence stays reachable, outside ranked recommendations.
        with tempfile.TemporaryDirectory() as td:
            for f in ("aa.json", "tb.json"):
                Path(td, f).write_text(Path(FIXTURES, f).read_text())
            ds = json.loads(Path(FIXTURES, "deepswe.json").read_text())
            ds["rows"].append({"model": "brand-new-model-9000",
                               "reasoning_effort": "low", "pass_at_1": 0.5})
            Path(td, "deepswe.json").write_text(json.dumps(ds))
            r = run_cli(self.KEY, "--fixtures", td)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("- brand-new-model-9000 [dsw:brand-new-model-9000]: "
                      "No measured Artificial Analysis configuration", r.stdout)
        self.assertFalse(any(ln.startswith("  brand-new-model-9000 ")
                             for ln in r.stdout.splitlines()))


class SourceContract(unittest.TestCase):
    """Real saved-source acquisition and identity consumers (ticket 34)."""

    def docs(self):
        return {source: json.loads((FIXTURES / name).read_text())
                for source, name in {**fetch.FILES, "or": "or.json"}.items()}

    def load(self, docs):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        for source, name in {**fetch.FILES, "or": "or.json"}.items():
            if source in docs:
                Path(td.name, name).write_text(json.dumps(docs[source]))
        raw = fetch.fetch_all(td.name)
        aliases = identity.load_aliases(REPO / "llmratings" / "aliases.json")
        return identity.build(aliases, raw)

    def test_separate_indexes_cost_timing_and_prices_at_each_effort(self):
        ds = self.load(self.docs())
        luna = {r.effort: r for r in ds.ratings
                if r.source == "aa" and r.model_key == "gpt-5-6-luna"}
        low, maximum = luna["low"], luna["max"]
        self.assertEqual((low.score, low.coding_score, low.agentic_score),
                         (33.3, 44.2, 25.4))
        self.assertEqual((maximum.score, maximum.coding_score,
                          maximum.agentic_score), (51.2, 71.4, 45.6))
        self.assertEqual((low.cost, maximum.cost), (0.0088, 0.0473))
        self.assertEqual((low.first_answer_seconds, low.first_token_seconds,
                          low.response_500_tokens_seconds, low.speed),
                         (1.96, 1.96, 5.36, 146.91))
        self.assertEqual((maximum.first_answer_seconds, maximum.first_token_seconds,
                          maximum.response_500_tokens_seconds, maximum.speed),
                         (139.23, 139.23, 142, 180.51))
        self.assertEqual(low.pricing, {
            "price_1m_input_tokens": 0.2, "price_1m_output_tokens": 1.2,
            "price_1m_cache_hit_tokens": 0.02, "price_1m_cache_write_tokens": 0.25})
        self.assertNotEqual(low.raw["id"], maximum.raw["id"])
        self.assertEqual(low.intelligence_index_version, 4.1)
        self.assertEqual(ds.models["gpt-5-6-luna"].provider, "OpenAI")
        kimi = next(r for r in ds.ratings if r.source == "aa"
                    and r.model_key == "kimi-k3" and r.effort == "low")
        self.assertEqual((kimi.first_token_seconds, kimi.first_answer_seconds,
                          kimi.response_500_tokens_seconds), (3.45, 60.66, 74.96))
        self.assertEqual(kimi.raw["artificial_analysis_intelligence_index_cost"]
                         ["total_cost"], 283.3)
        self.assertEqual(kimi.cost, 0.2429)
        self.assertIsNone(kimi.pricing["price_1m_cache_write_tokens"])


    def test_optional_metrics_are_independently_unavailable(self):
        fields = [
            ("evaluations", "artificial_analysis_intelligence_index", "score", 33.3),
            ("evaluations", "artificial_analysis_coding_index", "coding_score", 44.2),
            ("evaluations", "artificial_analysis_agentic_index", "agentic_score", 25.4),
            ("performance", "median_output_tokens_per_second", "speed", 146.91),
            ("performance", "median_time_to_first_token_seconds",
             "first_token_seconds", 1.96),
            ("performance", "median_time_to_first_answer_token_seconds",
             "first_answer_seconds", 1.96),
            ("performance", "median_end_to_end_response_time_seconds",
             "response_500_tokens_seconds", 5.36),
        ]
        for section, key, field, _ in fields:
            for value in ("missing", None, "not numeric", True, float("nan"),
                          float("inf"), -float("inf"), 0):
                with self.subTest(metric=field, value=value):
                    docs = self.docs()
                    row = docs["aa"]["data"][0]
                    if value == "missing":
                        row[section].pop(key)
                    else:
                        row[section][key] = value
                    ds = self.load(docs)
                    low = next(r for r in ds.ratings if r.source == "aa"
                               and r.model_key == "gpt-5-6-luna" and r.effort == "low")
                    # Only the changed field is unavailable; zero is not missing.
                    expected = [((0 if value == 0 else None) if attr == field
                                 else original) for _, _, attr, original in fields]
                    self.assertEqual([getattr(low, attr) for _, _, attr, _ in fields],
                                     expected)
                    self.assertEqual((low.cost, low.model_key, low.effort),
                                     (0.0088, "gpt-5-6-luna", "low"))
                    if value != "missing":
                        self.assertIn(key, low.raw[section])

    def test_null_malformed_and_nonfinite_costs_and_prices(self):
        for cost in ("missing", None, [], {"cost_per_task": None}, {"cost_per_task": []},
                     {"cost_per_task": {}}, {"cost_per_task": {"total_cost": "bad"}},
                     {"cost_per_task": {"total_cost": float("nan")}},
                     {"cost_per_task": {"total_cost": float("inf")}},
                     {"cost_per_task": {"total_cost": -float("inf")}},
                     {"cost_per_task": {"total_cost": True}},
                     {"cost_per_task": {"total_cost": 0}}):
            with self.subTest(cost=cost):
                docs = self.docs()
                row = docs["aa"]["data"][0]
                if cost == "missing":
                    row.pop("artificial_analysis_intelligence_index_cost")
                else:
                    row["artificial_analysis_intelligence_index_cost"] = cost
                row["pricing"] = {"price_1m_input_tokens": float("inf"),
                                  "price_1m_output_tokens": "bad",
                                  "price_1m_cache_hit_tokens": 0}
                ds = self.load(docs)
                low = next(r for r in ds.ratings if r.source == "aa"
                           and r.model_key == "gpt-5-6-luna" and r.effort == "low")
                self.assertEqual(low.cost, 0 if cost == {
                    "cost_per_task": {"total_cost": 0}} else None)
                self.assertEqual(low.pricing, {
                    "price_1m_input_tokens": None, "price_1m_output_tokens": None,
                    "price_1m_cache_hit_tokens": 0, "price_1m_cache_write_tokens": None})
                self.assertEqual((low.score, low.coding_score, low.first_answer_seconds),
                                 (33.3, 44.2, 1.96))
        for section in ("evaluations", "performance", "pricing"):
            for malformed in (None, [], "bad", 3):
                with self.subTest(section=section, malformed=malformed):
                    docs = self.docs()
                    docs["aa"]["data"][0][section] = malformed
                    ds = self.load(docs)
                    low = next(r for r in ds.ratings if r.source == "aa"
                               and r.model_key == "gpt-5-6-luna" and r.effort == "low")
                    self.assertEqual(low.cost, 0.0088)
                    self.assertEqual(low.raw[section], malformed)

    def test_historical_source_provenance_and_tb_submission_url(self):
        before = datetime.now(timezone.utc)
        raw = fetch.fetch_all(FIXTURES)
        after = datetime.now(timezone.utc)
        ds = identity.build(identity.load_aliases(REPO / "llmratings" / "aliases.json"),
                            raw)
        self.assertEqual(ds.provenance["mode"], "fixture")
        self.assertLessEqual(before, datetime.fromisoformat(ds.provenance["fetched_at"]))
        self.assertLessEqual(datetime.fromisoformat(ds.provenance["fetched_at"]), after)
        aa = ds.provenance["sources"]["aa"]
        self.assertEqual(aa["snapshot_date"], "2026-08-05")
        self.assertFalse(aa["synthetic"])
        self.assertTrue(ds.provenance["sources"]["tb"]["synthetic"])
        self.assertTrue(ds.provenance["sources"]["or"]["synthetic"])
        self.assertEqual(ds.provenance["sources"]["deepswe"]["source_dates"]
                         ["generated_at"], "2026-08-04T01:34:32.908483+00:00")
        tb = identity.best_tb(ds.ratings, "max")["gpt-5-6-luna"]
        self.assertEqual(tb.date, "2026-07-11")
        self.assertEqual(tb.source_url,
                         "https://raw.githubusercontent.com/harbor-framework/"
                         "terminal-bench-2-1/main/leaderboard/submissions/"
                         "20260711-openai-gpt-5-6-luna-max-codex-cli.json")
        self.assertEqual(tb.raw["metrics"]["accuracy"], 0.757)
        self.assertEqual(len([r for r in ds.ratings if r.source == "tb"]), 11)
        self.assertEqual({r.source_url for r in ds.ratings if r.source == "aa"},
                         {"https://artificialanalysis.ai/api/v2/language/models/free"
                          "?page_size=200"})

    def test_catalog_permaslug_uses_id_then_alias_and_share_stays_unknown(self):
        docs = self.docs()
        docs["or"] = {"data": [
            {"canonical_slug": "unrelated/published-permaslug-20260805",
             "id": "openai/gpt-5.6-luna", "context_length": 321000,
             "architecture": {"input_modalities": ["text", None, 5, "image"],
                              "output_modalities": ["text"]},
             "token_share_30d": 0.9},
            {"id": "anthropic/claude-opus-5", "context_length": 200000},
        ], "rankings": [{"permaslug": "unrelated/published-permaslug-20260805",
                         "tokens": 999}], "other": 1}
        ds = self.load(docs)
        key = ds.openrouter_models["unrelated/published-permaslug-20260805"]
        self.assertEqual(key, "gpt-5-6-luna")
        self.assertEqual(ds.models[key].context_length, 321000)
        self.assertEqual(ds.models[key].modalities, "in: text, image; out: text")
        self.assertEqual(ds.models[key].catalog_rows[0]["id"], "openai/gpt-5.6-luna")
        self.assertEqual(ds.models["claude-opus-5"].context_length, 200000)
        self.assertIsNone(ds.models[key].token_share_30d)
        self.assertIsNone(ds.models["kimi-k3"].token_share_30d)
        self.assertNotIn("anthropic/claude-opus-5", ds.openrouter_models,
                         "No permaslug is inferred from id")
        self.assertEqual([(r.score, r.cost) for r in ds.ratings],
                         [(r.score, r.cost) for r in self.load(self.docs()).ratings])

    def test_malformed_optional_catalog_never_invalidates_ratings(self):
        baseline = self.load(self.docs())
        for malformed in (None, [], {"data": None}, {"data": [
                None, {"id": []}, {"id": "openai/gpt-5.6-luna",
                                  "canonical_slug": [], "context_length": True,
                                  "architecture": {"input_modalities": [None, {}],
                                                   "output_modalities": "text"}}]}):
            with self.subTest(catalog=malformed):
                docs = self.docs()
                docs["or"] = malformed
                ds = self.load(docs)
                self.assertEqual([(r.score, r.cost, r.speed) for r in ds.ratings],
                                 [(r.score, r.cost, r.speed) for r in baseline.ratings])
                self.assertIsNone(ds.models["gpt-5-6-luna"].context_length)
                self.assertIsNone(ds.models["gpt-5-6-luna"].modalities)

    def test_source_only_and_aa_only_rows_stay_auditable_not_advice(self):
        docs = self.docs()
        docs["aa"]["data"].append(json.loads(AA_ROW.format(
            i="catalog-only", name="Catalog Only", slug="catalog-only",
            ii=999, cost=0.0001, spd=9999)))
        docs["deepswe"]["rows"].append({"model": "source-only",
                                       "reasoning_effort": "low", "pass_at_1": 0.9})
        ds = self.load(docs)
        source = next(r for r in ds.ratings if r.model_key == "dsw:source-only")
        self.assertEqual((source.score, source.cost, source.raw["model"]),
                         (0.9, None, "source-only"))
        self.assertEqual(source.source_url,
                         "https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json")
        result = render.query(ds, ROLES[2], "cap")
        keys = {r["key"] for r in result["rows"]}
        self.assertNotIn("catalog-only", keys)
        self.assertNotIn("dsw:source-only", keys)
        self.assertIn("dsw:source-only", {r["key"] for r in result["unranked"]})
        self.assertIn("catalog-only", ds.models)
        self.assertIn("dsw:source-only", ds.models)
        self.assertTrue(any(r.raw.get("id") == "catalog-only" for r in ds.ratings))

    def test_named_parse_failures_produce_no_partial_advice(self):
        for source, label in fetch.SOURCES.items():
            with self.subTest(source=source):
                docs = self.docs()
                docs[source] = {"aa": {"data": [None]},
                                "deepswe": {"rows": [None]},
                                "tb": {"submissions": {"bad.json":
                                       {"source_filter": []}}}}[source]
                with tempfile.TemporaryDirectory() as td:
                    for src, name in fetch.FILES.items():
                        Path(td, name).write_text(json.dumps(docs[src]))
                    result = run_cli({"LLM_RATINGS_AA_API_KEY": "secret-test-key"},
                                     "--fixtures", td)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(label, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertNotIn("secret-test-key", result.stderr)


    def test_live_page_versions_fetch_date_and_safe_source_urls(self):
        docs = self.docs()
        low = next(row for row in docs["aa"]["data"]
                   if row["slug"] == "gpt-5-6-luna-low")
        maximum = next(row for row in docs["aa"]["data"]
                       if row["name"] == "GPT-5.6 Luna (max)")
        docs["aa"]["data"] = [low] * 200 + [maximum]
        with tempfile.TemporaryDirectory() as td:
            for source, name in {**fetch.FILES, "or": "or.json"}.items():
                Path(td, name).write_text(json.dumps(docs[source]))
            srv = _LiveServer(td, page_versions={1: 4.1, 2: "v5-test"},
                              page_dates={1: {"updated_at": "2026-09-01"},
                                          2: {"updated_at": "2026-09-02"}})
            self.addCleanup(srv.stop)
            previous = os.environ.copy()
            try:
                os.environ.update(LLM_RATINGS_HTTP_BASE=srv.url(),
                                  LLM_RATINGS_AA_API_KEY="do-not-persist-secret")
                raw = fetch.fetch_all(None)
            finally:
                os.environ.clear()
                os.environ.update(previous)
        ds = identity.build(identity.load_aliases(REPO / "llmratings" / "aliases.json"),
                            raw)
        ratings = [r for r in ds.ratings if r.source == "aa"]
        self.assertEqual(len(ratings), 201)
        self.assertEqual({r.intelligence_index_version for r in ratings[:-1]}, {4.1})
        self.assertEqual(ratings[-1].intelligence_index_version, "v5-test")
        self.assertEqual((ratings[-1].effort, ratings[-1].score, ratings[-1].cost),
                         ("max", 51.2, 0.0473))
        self.assertEqual(ratings[0].source_url,
                         srv.url("/api/v2/language/models/free?page_size=200&page=1"))
        self.assertEqual(ratings[-1].source_url,
                         srv.url("/api/v2/language/models/free?page_size=200&page=2"))
        self.assertEqual(ratings[0].source_dates, {"updated_at": "2026-09-01"})
        self.assertEqual(ratings[-1].source_dates, {"updated_at": "2026-09-02"})
        self.assertFalse(ds.provenance["sources"]["aa"].get("source_dates"))
        self.assertEqual(ds.provenance["mode"], "live")
        self.assertIsNone(ds.provenance["sources"]["aa"]["snapshot_date"])
        self.assertEqual(len(ds.provenance["sources"]["aa"]["pages"]), 2)
        self.assertNotIn("do-not-persist-secret", json.dumps(ds.provenance))
        self.assertNotIn("x-api-key", json.dumps(ds.provenance))
        self.assertTrue(all(r.source_url.startswith(srv.url("/sub/"))
                            for r in ds.ratings if r.source == "tb"))
        self.assertFalse(any("page=3" in path for path in srv.seen))

    def test_submission_provenance_drops_url_credentials_and_secret_query(self):
        docs = self.docs()
        docs["tb"]["listing"][0]["download_url"] = (
            "https://user:secret-test-key@example.test/submission.json"
            "?api_key=secret-test-key&token=secret-test-key#secret-test-key")
        ds = self.load(docs)
        tb = identity.best_tb(ds.ratings, "max")["gpt-5-6-luna"]
        self.assertEqual(tb.source_url, "https://example.test/submission.json")
        self.assertIn("https://example.test/submission.json",
                      ds.provenance["sources"]["tb"]["urls"])
        self.assertNotIn("secret-test-key", json.dumps(ds.provenance))

    def test_invalid_catalog_json_is_best_effort(self):
        with tempfile.TemporaryDirectory() as td:
            for source, name in fetch.FILES.items():
                Path(td, name).write_text(json.dumps(self.docs()[source]))
            Path(td, "or.json").write_text("{")
            raw = fetch.fetch_all(td)
            ds = identity.build(
                identity.load_aliases(REPO / "llmratings" / "aliases.json"), raw)
        self.assertIsNone(raw["or"])
        self.assertTrue(render.query(ds, ROLES[2], "cap")["rows"])
        self.assertIsNone(ds.models["gpt-5-6-luna"].context_length)


if __name__ == "__main__":
    unittest.main()
