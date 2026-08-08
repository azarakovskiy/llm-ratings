"""CLI contract tests — tickets 11–18. Observable output only: exit codes and
rendered lines, run through the real CLI in a subprocess against the
checked-in fixtures or a local stdlib HTTP origin (no external network, no
mocks). Ticket 13's TB grades are rendered in-process through the same
fixture seam (the batch CLI's default role is Chores/price, where most rows
sit at low — the Researcher role's max/xhigh rows carry the TB column);
the collapse tie-break and the wholesale row count are asserted on the
dataset the tables are built from. Ticket 15's live fetchers run against
the local origin via the LLM_RATINGS_HTTP_BASE seam: live output must match
fixture-mode output, and each source's failure path must name the source
and exit nonzero with no output. Ticket 18: roles come from roles.json
(LLM_RATINGS_ROLES swaps the file — a test seam), objectives select each
model's effort, the price-lens floor drops below-floor models, OpenRouter
enrichment is best-effort (live 500 degrades to a full table)."""

import json
import os
import re
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

from llmratings import render  # noqa: E402  (sys.path setup above)
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


def _row_after(lines, needle):
    """First table row line containing needle (rows start with two spaces)."""
    return next(ln for ln in lines if needle in ln and ln.startswith("  "))


def _cell_at(row, at, width):
    """Cell of a rendered row at column offset `at`, whitespace-stripped."""
    return row[at:at + width].strip()


# AA row template shared by the hand-built fixtures (TierBinning, EdgeFixture,
# LiveAcquisition): one low-effort config per model.
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

    def __init__(self, fixtures_dir=FIXTURES, fail=None):
        self.dir = Path(fixtures_dir)
        self.fail = fail
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


class ChoresTable(unittest.TestCase):
    """The default role (Chores, price lens with floor 2): each model at its
    cheapest above-floor configuration — Luna's low config grades 1 and
    drops out, so Luna enters at medium; the rest at low."""

    @classmethod
    def setUpClass(cls):
        cls.r = run_fixtures()
        assert cls.r.returncode == 0, cls.r.stderr
        cls.lines = [ln.rstrip() for ln in cls.r.stdout.splitlines()]

    def row_after(self, needle):
        """(row, arrow-or-None) for the first table row containing needle."""
        idx = next(i for i, ln in enumerate(self.lines) if needle in ln
                   and ln.startswith("  "))
        return (self.lines[idx],
                self.lines[idx + 1] if idx + 1 < len(self.lines) else None)

    def test_exit_zero_and_attribution(self):
        self.assertEqual(self.r.returncode, 0)
        self.assertIn("artificialanalysis.ai", self.r.stdout)

    def test_role_header_with_capacity(self):
        self.assertIn("Chores — objective price — cheapest first · floor 2",
                      self.r.stdout)
        self.assertIn("Chores: Light, repetitive agent tasks", self.r.stdout)
        self.assertIn("capacity: Speed first, then price", self.r.stdout)

    def test_sections_and_star(self):
        joined = "\n".join(self.lines)
        self.assertIn("★ frontier", joined)
        self.assertIn("✗ dominated", joined)
        luna, _ = self.row_after("GPT-5.6 Luna")
        self.assertTrue(luna.endswith("*"))

    def test_path_line(self):
        path = next(ln for ln in self.lines if ln.startswith("frontier: "))
        self.assertTrue(path.startswith(
            "frontier: GPT-5.6 Luna low 33 @ $0.0088 →"))
        self.assertTrue(path.endswith("→ Claude Opus 5 max 61 @ $2.34"))

    def test_cheapest_first_order(self):
        models = ["Kimi K3", "GPT-5.6 Sol", "GPT-5.5", "Claude Opus 5"]
        idx = [next(i for i, ln in enumerate(self.lines)
                    if m in ln and ln.startswith("  "))
               for m in models]
        self.assertEqual(idx, sorted(idx), "dominated rows not cheapest-first")

    def test_luna_enters_at_medium(self):
        # Luna low grades 1 (below the floor 2), so the price lens moves it
        # to medium — the Effort column must say so.
        luna, _ = self.row_after("GPT-5.6 Luna")
        self.assertIn("medium", luna)

    def test_tb_column_dash(self):
        header = next(ln for ln in self.lines if "DSW" in ln and "TB" in ln)
        self.assertIn("TB", header)
        for model in ["GPT-5.6 Luna", "Kimi K3", "GPT-5.6 Sol", "GPT-5.5",
                      "Claude Opus 5"]:
            row, _ = self.row_after(model)
            self.assertIn("—", row)

    def test_grades_per_source(self):
        # Luna medium: DSW grade 1 (its .113 score is the low end of the
        # medium set), AA grade 2 (38.1 in a 4-model set). Kimi low: DSW has
        # no low row → `—`, AA grade 3.
        luna, _ = self.row_after("GPT-5.6 Luna")
        self.assertRegex(luna, r"^\s*1\s+2\s+—\s+GPT-5\.6 Luna")
        kimi, _ = self.row_after("Kimi K3")
        self.assertRegex(kimi, r"^\s*—\s+3\s+—\s+Kimi K3")

    def test_delta_columns(self):
        sol, _ = self.row_after("GPT-5.6 Sol")
        self.assertIn("+2.8", sol)
        self.assertIn("+$0.0021", sol)
        gpt55, _ = self.row_after("GPT-5.5")
        self.assertIn("-5.9", gpt55)
        self.assertIn("+$0.015", gpt55)
        opus, _ = self.row_after("Claude Opus 5")
        self.assertIn("+7.1", opus)
        self.assertIn("+$0.166", opus)

    def test_same_effort_arrow_preferred(self):
        # Cross-effort Luna max gives +7.7 pts; the arrow must still pick the
        # same-effort Sol low (+5.9) — the observable proof of the preference.
        _, arrow = self.row_after("GPT-5.5")
        self.assertEqual(arrow.strip(), "→ GPT-5.6 Sol low: +5.9 pts, save $0.015")

    def test_cross_effort_arrows(self):
        _, arrow = self.row_after("Kimi K3")
        self.assertEqual(arrow.strip(), "→ GPT-5.6 Luna max: +4.6 pts, save $0.196")
        _, arrow = self.row_after("GPT-5.6 Sol")
        self.assertEqual(arrow.strip(), "→ GPT-5.6 Luna max: +1.8 pts, save $0.198")
        _, arrow = self.row_after("Claude Opus 5")
        self.assertEqual(arrow.strip(), "→ GPT-5.6 Sol medium: +3 pts, save $0.036")

    def test_source_only_model_absent(self):
        # Terra has no AA row, so no objective-selected configuration: it
        # never enters a role table (spec §3/§4 — absent from ranked tables).
        self.assertNotIn("gpt-5-6-terra", self.r.stdout)


class FiveRoles(unittest.TestCase):
    """Ticket 18: --role selects any of the roles from roles.json; each
    renders every model at its objective-selected configuration, sorted by
    the objective's value so the Δ columns read the ladder."""

    OBJECTIVE = {"Chores": "price", "Generic": "ppi", "Researcher": "cap",
                 "Coder": "cap", "Orchestrator": "ppi"}
    # Combined table order (★ frontier section first, then ✗ dominated),
    # each section on its objective's value. Hand-computed from the
    # checked-in fixtures.
    ORDER = {
        "Chores": ["GPT-5.6 Luna", "Kimi K3", "GPT-5.6 Sol", "GPT-5.5",
                   "Claude Opus 5"],
        "Generic": ["GPT-5.6 Luna", "GPT-5.6 Sol", "Kimi K3", "GPT-5.5",
                    "Claude Opus 5"],
        "Researcher": ["Claude Opus 5", "GPT-5.6 Luna", "GPT-5.6 Sol",
                       "Kimi K3", "GPT-5.5"],
        "Coder": ["Claude Opus 5", "GPT-5.6 Luna", "GPT-5.6 Sol",
                  "Kimi K3", "GPT-5.5"],
        "Orchestrator": ["GPT-5.6 Luna", "GPT-5.6 Sol", "Kimi K3",
                         "GPT-5.5", "Claude Opus 5"],
    }

    @classmethod
    def role_lines(cls, name):
        r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"},
                    "--fixtures", str(FIXTURES), "--role", name)
        assert r.returncode == 0, r.stderr
        return [ln.rstrip() for ln in r.stdout.splitlines()]

    @classmethod
    def setUpClass(cls):
        cls.lines = {name: cls.role_lines(name) for name in cls.OBJECTIVE}

    def row_after(self, name, needle):
        idx = next(i for i, ln in enumerate(self.lines[name]) if needle in ln
                   and ln.startswith("  "))
        return self.lines[name][idx]

    def test_each_role_renders_its_objective(self):
        for name, objective in self.OBJECTIVE.items():
            first = next(ln for ln in self.lines[name]
                         if ln.startswith(f"{name} — objective "))
            self.assertTrue(first.startswith(
                f"{name} — objective {objective} —"), f"{name}: {first}")

    def test_floor_shown_under_price_lens_only(self):
        chores = next(ln for ln in self.lines["Chores"]
                      if ln.startswith("Chores — "))
        self.assertIn("· floor 2", chores)
        for name in ("Generic", "Researcher", "Coder", "Orchestrator"):
            head = next(ln for ln in self.lines[name]
                        if ln.startswith(f"{name} — "))
            self.assertNotIn("floor", head)

    def test_league_axis_order(self):
        for name, models in self.ORDER.items():
            lines = self.lines[name]
            idx = [next(i for i, ln in enumerate(lines)
                        if m in ln and ln.startswith("  "))
                   for m in models]
            self.assertEqual(idx, sorted(idx),
                             f"{name} rows not on their objective's order")

    def test_mixed_efforts_per_row(self):
        # cap (Researcher/Coder): GPT-5.5 has no max variant → its row sits
        # at xhigh while the others sit at max.
        for name in ("Researcher", "Coder"):
            gpt55 = self.row_after(name, "GPT-5.5")
            self.assertIn("xhigh", gpt55)
            opus = self.row_after(name, "Claude Opus 5")
            self.assertIn("max", opus)

    def test_deltas_read_the_ladder(self):
        # Chores (price): Kimi opens the dominated section, Sol +2.8 pts
        # from it, Opus +7.1 from GPT-5.5 — near-tie deltas on the price
        # ladder.
        chores = self.lines["Chores"]
        sol = self.row_after("Chores", "GPT-5.6 Sol")
        self.assertIn("+2.8", sol)
        self.assertIn("+$0.0021", sol)
        opus = self.row_after("Chores", "Claude Opus 5")
        self.assertIn("+7.1", opus)
        self.assertIn("+$0.166", opus)
        # Generic (ppi): Luna is the only frontier row; Sol opens the
        # dominated section; Kimi -2.8 pts from Sol — a near-tie visible as
        # a small number, not swallowed.
        generic = self.lines["Generic"]
        kimi = self.row_after("Generic", "Kimi K3")
        self.assertIn("-2.8", kimi)
        self.assertIn("-$0.0021", kimi)
        opus = self.row_after("Generic", "Claude Opus 5")
        self.assertIn("+7.1", opus)
        self.assertIn("+$0.166", opus)
        # Researcher (cap): Luna -9.5 from the frontier Opus; the dominated
        # section's Sol opens, Kimi -1.8 from Sol, GPT-5.5 -2.3 from Kimi.
        res = self.lines["Researcher"]
        luna = self.row_after("Researcher", "GPT-5.6 Luna")
        self.assertIn("-9.5", luna)
        self.assertIn("-$2.29", luna)
        kimi = self.row_after("Researcher", "Kimi K3")
        self.assertIn("-1.8", kimi)
        self.assertIn("-$0.377", kimi)
        gpt55 = self.row_after("Researcher", "GPT-5.5")
        self.assertIn("-2.3", gpt55)
        self.assertIn("+$0.32", gpt55)

    def test_dash_where_no_row_at_effort(self):
        # Kimi has no DSW low row → its Chores row shows `—` in the DSW
        # cell while AA/TB grade from its config.
        self.assertRegex(self.row_after("Chores", "Kimi K3"),
                         r"^\s*—\s+3\s+—\s+Kimi K3")

    def test_unknown_role_errors(self):
        r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"},
                    "--fixtures", str(FIXTURES), "--role", "bogus")
        self.assertEqual(r.returncode, 2)
        self.assertIn("invalid choice", r.stderr)
        self.assertIn("Orchestrator", r.stderr)


class RolesFile(unittest.TestCase):
    """Ticket 18: roles.json is the config surface — a role added to the
    file creates a tab (LLM_RATINGS_ROLES swaps the file; the seam mirrors
    LLM_RATINGS_HTTP_BASE)."""

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

    def test_added_role_renders_and_defaults_follow_file_order(self):
        # Mail Sorter sits FIRST in the file → it becomes the default tab
        # (file order is authoritative), and its omitted floor defaults to 2.
        with tempfile.TemporaryDirectory() as td:
            Path(td, "roles.json").write_text(json.dumps(self.SIX))
            env = {"LLM_RATINGS_AA_API_KEY": "dummy",
                   "LLM_RATINGS_ROLES": str(Path(td, "roles.json"))}
            r = run_cli(env, "--fixtures", str(FIXTURES))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Mail Sorter — objective price — cheapest first · floor 2",
                      r.stdout)
        self.assertNotIn("Chores — objective", r.stdout)

    def test_added_role_selectable_by_name(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "roles.json").write_text(json.dumps(self.SIX))
            env = {"LLM_RATINGS_AA_API_KEY": "dummy",
                   "LLM_RATINGS_ROLES": str(Path(td, "roles.json"))}
            r = run_cli(env, "--fixtures", str(FIXTURES), "--role", "Mail Sorter")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Mail Sorter — objective price", r.stdout)

    def test_corrupt_roles_file_errors_cleanly(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, "roles.json").write_text('{"name": "not a list"}')
            r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy",
                         "LLM_RATINGS_ROLES": str(Path(td, "roles.json"))},
                        "--fixtures", str(FIXTURES))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("roles", r.stderr.lower())


class PriceFloor(unittest.TestCase):
    """Ticket 18: under the price lens, a model whose configurations all
    grade below the role's floor does not appear; under cap it still does —
    the floor is a price-lens filter, not an inclusion rule."""

    @staticmethod
    def aa_row(i, name, slug, ii, cost, spd, effort):
        return {"id": i, "name": f"{name} ({effort})",
                "slug": f"{slug}-{effort}",
                "model_creator": {"name": "Acme"},
                "evaluations": {"artificial_analysis_intelligence_index": ii},
                "artificial_analysis_intelligence_index_cost":
                    {"cost_per_task": {"total_cost": cost}},
                "performance": {"median_output_tokens_per_second": spd}}

    @classmethod
    def setUpClass(cls):
        # Low scores {10, 20, 30, 50, 60} → grades 1,2,3,4,5; max scores
        # {30, 35, 40, 55, 70} → 1,2,3,4,5. Luna grades 1 at both efforts →
        # below floor 2 everywhere; Kimi and Sol qualify at low. The two
        # filler models are AA-only (no DSW/TB rating) so they shape the
        # grade bins without ever entering the tables.
        cls.td = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.td.cleanup)
        aa = {"data": [
            cls.aa_row("u1", "GPT-5.6 Luna", "gpt-5-6-luna", 10, 0.1, 100, "low"),
            cls.aa_row("u2", "GPT-5.6 Luna", "gpt-5-6-luna", 30, 0.2, 110, "max"),
            cls.aa_row("u3", "Kimi K3", "kimi-k3", 50, 0.3, 120, "low"),
            cls.aa_row("u4", "Kimi K3", "kimi-k3", 55, 0.6, 130, "max"),
            cls.aa_row("u5", "GPT-5.6 Sol", "gpt-5-6-sol", 60, 0.5, 140, "low"),
            cls.aa_row("u6", "GPT-5.6 Sol", "gpt-5-6-sol", 70, 1.0, 150, "max"),
            cls.aa_row("u7", "GPT-5.4", "gpt-5-4", 20, 9.9, 160, "low"),
            cls.aa_row("u8", "GPT-5.4", "gpt-5-4", 35, 9.9, 170, "max"),
            cls.aa_row("u9", "GPT-5.3", "gpt-5-3", 30, 9.9, 180, "low"),
            cls.aa_row("uA", "GPT-5.3", "gpt-5-3", 40, 9.9, 190, "max"),
        ]}
        Path(cls.td.name, "aa.json").write_text(json.dumps(aa))
        ds = {"rows": [
            {"model": "gpt-5-6-luna", "reasoning_effort": "low", "pass_at_1": 0.2},
            {"model": "kimi-k3", "reasoning_effort": "low", "pass_at_1": 0.5},
            {"model": "gpt-5-6-sol", "reasoning_effort": "low", "pass_at_1": 0.6},
        ]}
        Path(cls.td.name, "deepswe.json").write_text(json.dumps(ds))
        Path(cls.td.name, "tb.json").write_text(
            json.dumps({"listing": [], "submissions": {}}))

    def lines_for(self, role):
        r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"},
                    "--fixtures", self.td.name, "--role", role)
        self.assertEqual(r.returncode, 0, r.stderr)
        return [ln.rstrip() for ln in r.stdout.splitlines()]

    def test_below_floor_model_absent_under_price(self):
        # Luna's configs are on the frontier path (the envelope is
        # cross-effort and floor-free), but no table ROW may carry it: the
        # floor filter is per-model row selection.
        lines = self.lines_for("Chores")
        rows = [ln for ln in lines if ln.startswith("  ")]
        self.assertFalse(any("GPT-5.6 Luna" in ln for ln in rows),
                         "below-floor model must not appear as a row")
        self.assertTrue(any("Kimi K3" in ln for ln in rows))
        self.assertTrue(any("GPT-5.6 Sol" in ln for ln in rows))

    def test_same_model_present_under_cap(self):
        # The floor only applies under the price lens: cap selects Luna's
        # max configuration (30 > 20) and it renders at max effort.
        lines = self.lines_for("Researcher")
        luna = next(ln for ln in lines if "GPT-5.6 Luna" in ln
                    and ln.startswith("  "))
        self.assertIn("max", luna)


class TierColumns(unittest.TestCase):
    """Ticket 14: the Spd column renders the speed tier (AA median output
    tokens/s at the row's effort, 5 = fastest); a row without AA speed
    shows a dash. Benchmark-run durations never enter this axis."""

    @classmethod
    def setUpClass(cls):
        cls.r = run_fixtures()
        assert cls.r.returncode == 0, cls.r.stderr
        cls.lines = [ln.rstrip() for ln in cls.r.stdout.splitlines()]
        header = next(ln for ln in cls.lines if ln.startswith("DSW"))
        cls.spd_at = header.index("Spd")

    def row_after(self, needle):
        return _row_after(self.lines, needle)

    def spd_of(self, row):
        return _cell_at(row, self.spd_at, 4)

    def test_spd_renders_speed_tier(self):
        # Chores speeds: Luna medium 156.1, GPT-5.5 low 71.8, Sol low 62.1,
        # Opus low 53.8, Kimi low 35.0 -> five distinct values -> tiers
        # 5,4,3,2,1 (5 = fastest).
        for model, expected in [("GPT-5.6 Luna", "5"), ("GPT-5.5", "4"),
                                ("GPT-5.6 Sol", "3"), ("Claude Opus 5", "2"),
                                ("Kimi K3", "1")]:
            self.assertEqual(self.spd_of(self.row_after(model)), expected, model)


class TierBinning(unittest.TestCase):
    """Ticket 14 binning over small sets, observed through the Spd column:
    fewer than five populated tiers, equal values never split across bins,
    tiers recompute from the data of the run, and no AA price -> no PPI."""

    AA = AA_ROW

    MODELS = [("gpt-5-6-luna", "GPT-5.6 Luna"), ("gpt-5-6-sol", "GPT-5.6 Sol"),
              ("claude-opus-5", "Claude Opus 5"), ("gpt-5-5", "GPT-5.5")]

    def lines_for(self, speeds, costs=None, role="Chores"):
        """Run the CLI on a hand-built fixture: one low-effort config per
        model, AA rows carrying the given speeds. Returns stdout lines."""
        models = self.MODELS[:len(speeds)]
        costs = costs or [0.1 + 0.1 * n for n in range(1, len(speeds) + 1)]
        with tempfile.TemporaryDirectory() as td:
            aa = {"data": [json.loads(self.AA.format(
                i=f"u{n}", name=name, slug=slug,
                ii=30 + n, cost=costs[n - 1], spd=s))
                for n, ((slug, name), s) in enumerate(zip(models, speeds), 1)]}
            Path(td, "aa.json").write_text(json.dumps(aa))
            ds = {"rows": [{"model": slug, "reasoning_effort": "low",
                            "pass_at_1": 0.1 * n}
                           for n, (slug, _) in enumerate(models, 1)]}
            Path(td, "deepswe.json").write_text(json.dumps(ds))
            # Empty TB set — this fixture is about the tier bins, not the
            # TB source; the merged CLI still requires the file (ticket 13).
            Path(td, "tb.json").write_text(
                json.dumps({"listing": [], "submissions": {}}))
            r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"},
                        "--fixtures", td, "--role", role)
            self.assertEqual(r.returncode, 0, r.stderr)
            lines = [ln.rstrip() for ln in r.stdout.splitlines()]
            header = next(ln for ln in lines if ln.startswith("DSW"))
            self.spd_at = header.index("Spd")
            return lines

    def spd_of(self, lines, model):
        return _cell_at(_row_after(lines, model), self.spd_at, 4)

    def test_equal_speeds_share_a_bin(self):
        # Three models, two distinct speeds: the equal pair keeps one tier and
        # only two of the five tiers are populated.
        lines = self.lines_for([10, 10, 30])
        self.assertEqual(self.spd_of(lines, "GPT-5.6 Luna"),
                         self.spd_of(lines, "GPT-5.6 Sol"))
        self.assertEqual({self.spd_of(lines, name) for _, name in self.MODELS[:3]},
                         {"5", "3"})

    def test_tiers_recompute_from_run_data(self):
        # Same model set plus one more speed: Model 2's bin changes because
        # the set changed — tiers come from the data of the run, not a table.
        a = self.lines_for([10, 20, 30])
        b = self.lines_for([10, 20, 30, 25])
        self.assertEqual(self.spd_of(a, "GPT-5.6 Sol"), "4")
        self.assertEqual(self.spd_of(b, "GPT-5.6 Sol"), "3")

    def test_no_price_no_ppi_but_speed_renders(self):
        # Luna has an AA row with no per-task cost: PPI n/a (no value tier),
        # while the speed tier still grades from tokens/s. The price lens
        # cannot select an unpriced config, so the cap lens (Researcher) is
        # the view that renders it.
        lines = self.lines_for([100, 50], costs=["null", 0.5], role="Researcher")
        header = next(ln for ln in lines if ln.startswith("DSW"))
        ppi_at = header.index("PPI")
        luna = _row_after(lines, "GPT-5.6 Luna")
        self.assertEqual(_cell_at(luna, ppi_at, 5), "n/a")
        self.assertEqual(self.spd_of(lines, "GPT-5.6 Luna"), "5")


class EdgeFixture(unittest.TestCase):
    """Hand-built edge fixture (spec §Test strategy): equal-cost tie on the
    frontier and an AA-only model that must stay out of the envelope."""

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.td.cleanup)
        aa = {"data": [
            json.loads(AA_ROW.format(i="u1", name="GPT-5.6 Luna",
                                     slug="gpt-5-6-luna", ii=50, cost=1.0,
                                     spd=1000)),
            json.loads(AA_ROW.format(i="u2", name="GPT-5.6 Sol",
                                     slug="gpt-5-6-sol", ii=60, cost=1.0,
                                     spd=1000)),
            json.loads(AA_ROW.format(i="u3", name="Kimi K3",
                                     slug="kimi-k3", ii=90, cost=0.5,
                                     spd=1000)),
        ], "intelligence_index_version": 4.1, "tier": "free",
            "pagination": {"page": 1, "page_size": 200, "total_pages": 1,
                           "has_more": False}}
        Path(cls.td.name, "aa.json").write_text(json.dumps(aa))
        ds = {"rows": [
            {"model": "gpt-5-6-luna", "reasoning_effort": "low",
             "pass_at_1": 50},
            {"model": "gpt-5-6-sol", "reasoning_effort": "low",
             "pass_at_1": 60},
        ]}
        Path(cls.td.name, "deepswe.json").write_text(json.dumps(ds))
        # Empty TB set — this fixture is about the frontier, not the TB source.
        Path(cls.td.name, "tb.json").write_text(
            json.dumps({"listing": [], "submissions": {}}))
        cls.r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"},
                        "--fixtures", cls.td.name)
        assert cls.r.returncode == 0, cls.r.stderr
        cls.lines = [ln.rstrip() for ln in cls.r.stdout.splitlines()]

    def test_equal_cost_keeps_only_higher_index(self):
        # Both configs cost $1.00; the 60-index one must dominate the 50.
        path = next(ln for ln in self.lines if ln.startswith("frontier: "))
        self.assertEqual(path, "frontier: GPT-5.6 Sol low 60 @ $1.00")
        star = next(ln for ln in self.lines
                    if ln.startswith("  ") and ln.endswith("*"))
        self.assertIn("GPT-5.6 Sol", star)
        self.assertNotIn("GPT-5.6 Luna", star)

    def test_aa_only_model_never_enters(self):
        # Kimi K3 (90 @ $0.50, the cheapest AND best) has no DSW/TB rating:
        # spec §3 keeps it out of the path line, sections, and arrows.
        self.assertNotIn("Kimi", self.r.stdout)

    def test_dominated_row_arrow_without_saving(self):
        luna = next(i for i, ln in enumerate(self.lines)
                    if "GPT-5.6 Luna" in ln)
        self.assertEqual(self.lines[luna + 1].strip(),
                         "→ GPT-5.6 Sol low: +10 pts")


class TerminalBench(unittest.TestCase):
    """Ticket 13 — Terminal-Bench v2.1 as a third source. The batch CLI's
    default role (Chores) renders low/medium rows, where TB is `—`; the
    cap-lens tables (Researcher/Coder) carry max/xhigh rows, so the TB
    grade column is observable end to end through the same fixture seam
    (fetch → identity → tier → render)."""

    TB_MODELS = {"gpt-5-6-luna", "gpt-5-6-sol", "gpt-5-5", "claude-opus-5"}

    @classmethod
    def setUpClass(cls):
        from llmratings import fetch, identity
        raw = fetch.fetch_all(FIXTURES)
        aliases = identity.load_aliases(REPO / "llmratings" / "aliases.json")
        cls.ds = identity.build(aliases, raw)
        by_name = {r["name"]: r for r in ROLES}
        cls.lines = {name: [ln.rstrip() for ln in render.render(cls.ds, by_name[name])]
                     for name in ("Researcher", "Coder", "Generic")}

    def row(self, cat, prefix, model):
        """First table row in cat whose line matches prefix + contains model —
        a prefix match skips arrow lines ("    → …") that mention the model."""
        return next(ln for ln in self.lines[cat]
                    if re.match(prefix, ln) and model in ln)

    def test_tb_dash_at_chores_low(self):
        # Every Chores row sits at low/medium where v2.1 has no submissions
        # — the TB cell is `—` even for Kimi, whose DSW cell is `—` too.
        r = run_fixtures()
        self.assertEqual(r.returncode, 0)
        lines = [ln.rstrip() for ln in r.stdout.splitlines()]
        header = next(ln for ln in lines if ln.startswith("DSW"))
        tb_at = header.index("TB")
        for model in ("GPT-5.6 Luna", "GPT-5.6 Sol", "GPT-5.5",
                      "Claude Opus 5", "Kimi K3"):
            ln = _row_after(lines, model)
            self.assertEqual(_cell_at(ln, tb_at, 3), "—", model)

    def test_tb_dash_at_generic_low(self):
        # TB covers high/xhigh/max only — every Generic (ppi → low) row
        # shows `—`. Data rows start with the right-aligned DSW cell (≤2
        # spaces, then a digit or —); titles/header/sections/arrows don't
        # match.
        rows = [ln for ln in self.lines["Generic"]
                if re.match(r"^ {0,2}(?:\d|—)", ln)]
        self.assertTrue(rows)
        for ln in rows:
            self.assertRegex(ln, r"^\s*\S+\s+\S+\s+—\s")

    def test_tb_grades_on_researcher(self):
        # cap rows: Opus/Sol/Luna/Kimi at max, GPT-5.5 at xhigh (no max
        # variant). Max TB scores: Sol .769, Luna .757, Opus .689 → grades
        # 5/4/2 over the collapsed set; Kimi has no TB max row → `—`.
        # GPT-5.5 xhigh has no TB xhigh row → `—`.
        for model, prefix in [
            ("Claude Opus 5", r"^\s*5\s+5\s+2\s+"),
            ("GPT-5.6 Sol", r"^\s*4\s+4\s+5\s+"),
            ("GPT-5.6 Luna", r"^\s*1\s+2\s+4\s+"),
            ("Kimi K3", r"^\s*2\s+3\s+—\s+"),
            ("GPT-5.5", r"^\s*4\s+3\s+—\s+")]:
            self.assertRegex(self.row("Researcher", prefix, model),
                             prefix + model)

    def test_collapse_best_agent(self):
        from llmratings import identity
        # GPT-5.5 high has two agents: codex .664 and warp .671 — the better
        # one wins, and the table shows a single GPT-5.5 row.
        best = identity.best_tb(self.ds.ratings, "high")
        self.assertEqual(best["gpt-5-5"].score, 0.671)
        self.assertEqual(best["gpt-5-5"].agent, "warp")
        rows = [ln for ln in self.lines["Generic"]
                if "GPT-5.5" in ln and ln.startswith("  ")]
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
        # The Researcher role (cap lens) renders every model; the default
        # price lens would drop Kimi (its low grade is 1 — below floor 2).
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
        # Dataset-level assertion of the live OR join (the rendered context
        # line is pinned in test_tui): ids resolve through the alias table
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

    def test_unknown_model_absent_from_ranked_tables(self):
        # A DeepSWE model with no alias entry joins to a source-only identity
        # (no AA row → no objective-selected configuration): the run
        # completes and the model is absent from the ranked tables (spec
        # §3/§4, ticket 18).
        with tempfile.TemporaryDirectory() as td:
            for f in ("aa.json", "tb.json"):
                Path(td, f).write_text(Path(FIXTURES, f).read_text())
            ds = json.loads(Path(FIXTURES, "deepswe.json").read_text())
            ds["rows"].append({"model": "brand-new-model-9000",
                               "reasoning_effort": "low", "pass_at_1": 0.5})
            Path(td, "deepswe.json").write_text(json.dumps(ds))
            r = run_cli(self.KEY, "--fixtures", td)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("brand-new-model-9000", r.stdout)


if __name__ == "__main__":
    unittest.main()
