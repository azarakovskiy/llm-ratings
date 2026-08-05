"""CLI contract tests — tickets 11–14. Observable output only: exit codes and
rendered lines, run through the real CLI in a subprocess against the checked-in
fixtures (no network, no mocks). Ticket 13's TB grades at high/max efforts are
rendered in-process through the same fixture seam (the CLI's one rendered
category is Chores/low, where TB is `—`); the collapse tie-break and the
wholesale row count are asserted on the dataset the tables are built from."""

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))  # in-process `import llmratings` for render tests
FIXTURES = REPO / ".scratch" / "llm-ratings" / "fixtures" / "main"


def run_cli(env_extra, *args):
    env = dict(os.environ)
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "llmratings", *args],
        capture_output=True, text=True, cwd=REPO, env=env)


def run_fixtures(env_extra=None):
    return run_cli(env_extra or {"LLM_RATINGS_AA_API_KEY": "dummy"},
                   "--fixtures", str(FIXTURES))


def _row_after(lines, needle):
    """First table row line containing needle (rows start with two spaces)."""
    return next(ln for ln in lines if needle in ln and ln.startswith("  "))


def _cell_at(row, at, width):
    """Cell of a rendered row at column offset `at`, whitespace-stripped."""
    return row[at:at + width].strip()


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


class ChoresTable(unittest.TestCase):
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
        models = ["Kimi K3", "GPT-5.6 Sol", "GPT-5.5", "Claude Opus 5",
                  "gpt-5-6-terra"]
        idx = [next(i for i, ln in enumerate(self.lines)
                    if m in ln and ln.startswith("  "))
               for m in models]
        self.assertEqual(idx, sorted(idx), "dominated rows not cheapest-first")

    def test_unpriced_row_last_without_ppi(self):
        terra, _ = self.row_after("gpt-5-6-terra")
        # price n/a, Δ columns —, PPI column n/a, Spd —: no "k" magnitude
        # anywhere in the row
        self.assertRegex(terra, r"n/a\s+—\s+—\s+n/a\s+—\s*$")
        self.assertEqual(terra, self.lines[-1],
                         "unpriced row must sort last")

    def test_tb_column_dash(self):
        header = next(ln for ln in self.lines if "DSW" in ln and "TB" in ln)
        self.assertIn("TB", header)
        for model in ["GPT-5.6 Luna", "Kimi K3", "Claude Opus 5"]:
            row, _ = self.row_after(model)
            self.assertIn("—", row)

    def test_grades_per_source(self):
        luna, _ = self.row_after("GPT-5.6 Luna")
        self.assertRegex(luna, r"^\s*1\s+1\s+—\s+GPT-5\.6 Luna")
        terra, _ = self.row_after("gpt-5-6-terra")
        self.assertRegex(terra, r"^\s*2\s+—\s+—\s+gpt-5-6-terra")

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

    def test_unpriced_row_has_no_arrow(self):
        _, arrow = self.row_after("gpt-5-6-terra")
        self.assertIsNone(arrow)


class FiveCategories(unittest.TestCase):
    """Ticket 12: --category selects any of the five; each renders at its
    fixed effort, sorted by its league axis so the Δ columns read the ladder."""

    EFFORT = {"Chores": "low", "Everyday": "medium", "Deliberate": "high",
              "Deep": "max", "Best Value": "high"}
    # Combined table order (★ frontier section first, then ✗ dominated),
    # each section on its league axis: cheapest first / PPI desc /
    # capability (AA) desc. Hand-computed from the checked-in fixtures.
    ORDER = {
        "Chores": ["GPT-5.6 Luna", "Kimi K3", "GPT-5.6 Sol", "GPT-5.5",
                   "Claude Opus 5", "gpt-5-6-terra"],
        "Everyday": ["GPT-5.6 Luna", "GPT-5.6 Sol", "Claude Opus 5",
                     "GPT-5.5", "gpt-5-6-terra"],
        "Deliberate": ["Claude Opus 5", "GPT-5.6 Sol", "GPT-5.6 Luna",
                       "GPT-5.5", "gpt-5-6-terra"],
        "Deep": ["Claude Opus 5", "GPT-5.6 Luna", "GPT-5.6 Sol", "Kimi K3",
                 "gpt-5-6-terra"],
        "Best Value": ["GPT-5.6 Luna", "GPT-5.6 Sol", "Claude Opus 5",
                       "GPT-5.5", "gpt-5-6-terra"],
    }

    @classmethod
    def category_lines(cls, name):
        r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"},
                    "--fixtures", str(FIXTURES), "--category", name)
        assert r.returncode == 0, r.stderr
        return [ln.rstrip() for ln in r.stdout.splitlines()]

    @classmethod
    def setUpClass(cls):
        cls.lines = {name: cls.category_lines(name) for name in cls.EFFORT}

    def row_after(self, name, needle):
        idx = next(i for i, ln in enumerate(self.lines[name]) if needle in ln
                   and ln.startswith("  "))
        return self.lines[name][idx]

    def test_each_category_renders_at_its_fixed_effort(self):
        for name, effort in self.EFFORT.items():
            first = next(ln for ln in self.lines[name]
                         if ln.startswith(f"{name} — "))
            self.assertTrue(first.startswith(f"{name} — {effort} effort —"),
                            f"{name}: {first}")

    def test_league_axis_order(self):
        for name, models in self.ORDER.items():
            lines = self.lines[name]
            idx = [next(i for i, ln in enumerate(lines)
                        if m in ln and ln.startswith("  "))
                   for m in models]
            self.assertEqual(idx, sorted(idx),
                             f"{name} rows not on their league axis")

    def test_deltas_read_the_ladder(self):
        # Chores (cheapest first): Sol +2.8 pts from the frontier Luna,
        # Opus +7.1 from GPT-5.5 — small near-tie deltas on the price ladder.
        chores = self.lines["Chores"]
        sol = self.row_after("Chores", "GPT-5.6 Sol")
        self.assertIn("+2.8", sol)
        self.assertIn("+$0.0021", sol)
        opus = self.row_after("Chores", "Claude Opus 5")
        self.assertIn("+7.1", opus)
        self.assertIn("+$0.166", opus)
        # Everyday (PPI desc): Sol +15.5 pts from Luna, Opus +2.7 from Sol —
        # near-ties visible as small numbers, not swallowed.
        ev = self.lines["Everyday"]
        sol = self.row_after("Everyday", "GPT-5.6 Sol")
        self.assertIn("+15.5", sol)
        self.assertIn("+$0.379", sol)
        opus = self.row_after("Everyday", "Claude Opus 5")
        self.assertIn("+2.7", opus)
        self.assertIn("+$0.332", opus)
        # Deliberate (capability desc): Sol is 3.0 pts under Opus.
        de = self.lines["Deliberate"]
        sol = self.row_after("Deliberate", "GPT-5.6 Sol")
        self.assertIn("-3.0", sol)
        self.assertIn("-$0.677", sol)
        # Deep dominated: Kimi 1.8 pts under Sol max — a near-tie.
        deep = self.lines["Deep"]
        kimi = self.row_after("Deep", "Kimi K3")
        self.assertIn("-1.8", kimi)
        # Best Value (PPI desc): Sol +9.8 pts from Luna, Opus +3.0 from Sol.
        bv = self.lines["Best Value"]
        sol = self.row_after("Best Value", "GPT-5.6 Sol")
        self.assertIn("+9.8", sol)
        self.assertIn("+$0.527", sol)
        opus = self.row_after("Best Value", "Claude Opus 5")
        self.assertIn("+3.0", opus)
        self.assertIn("+$0.677", opus)

    def test_dash_where_no_row_at_effort(self):
        # Terra has no AA row at any effort: AA and TB cells are — at medium,
        # no PPI. Kimi K3 has no medium row at all → absent from Everyday;
        # GPT-5.5 has no max row → absent from Deep.
        ev = self.lines["Everyday"]
        terra = self.row_after("Everyday", "gpt-5-6-terra")
        self.assertRegex(terra, r"\d\s+—\s+—\s+gpt-5-6-terra")
        self.assertNotIn("Kimi", ev)
        de = self.lines["Deliberate"]
        self.assertNotIn("Kimi", de)
        deep = self.lines["Deep"]
        self.assertNotIn("GPT-5.5", deep)

    def test_unknown_category_errors(self):
        r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"},
                    "--fixtures", str(FIXTURES), "--category", "bogus")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("invalid choice", r.stderr)
        self.assertIn("Best Value", r.stderr)
class TierColumns(unittest.TestCase):
    """Ticket 14: the Spd column renders the speed tier (AA median output
    tokens/s at the category's effort, 5 = fastest); a model with no AA row
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
        # Low-effort speeds: Luna 146.9, GPT-5.5 71.8, Sol 62.1, Opus 53.8,
        # Kimi 35.0 -> five distinct values -> tiers 5,4,3,2,1 (5 = fastest).
        for model, expected in [("GPT-5.6 Luna", "5"), ("GPT-5.5", "4"),
                                ("GPT-5.6 Sol", "3"), ("Claude Opus 5", "2"),
                                ("Kimi K3", "1")]:
            self.assertEqual(self.spd_of(self.row_after(model)), expected, model)

    def test_spd_dash_without_aa_row(self):
        # Terra has no AA row at all -> no speed -> dash, like its other
        # source-only columns. DeepSWE's duration/task never grades it.
        self.assertEqual(self.spd_of(self.row_after("gpt-5-6-terra")), "—")


class TierBinning(unittest.TestCase):
    """Ticket 14 binning over small sets, observed through the Spd column:
    fewer than five populated tiers, equal values never split across bins,
    tiers recompute from the data of the run, and no AA price -> no PPI."""

    AA = ('{{"id": "{i}", "name": "{name} (low)", "slug": "{slug}-low",'
          ' "model_creator": {{"name": "Acme"}},'
          ' "evaluations": {{"artificial_analysis_intelligence_index": {ii}}},'
          ' "artificial_analysis_intelligence_index_cost":'
          ' {{"cost_per_task": {{"total_cost": {cost}}}}},'
          ' "performance": {{"median_output_tokens_per_second": {spd}}}}}')

    MODELS = [("gpt-5-6-luna", "GPT-5.6 Luna"), ("gpt-5-6-sol", "GPT-5.6 Sol"),
              ("claude-opus-5", "Claude Opus 5"), ("gpt-5-5", "GPT-5.5")]

    def lines_for(self, speeds, costs=None):
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
            r = run_cli({"LLM_RATINGS_AA_API_KEY": "dummy"}, "--fixtures", td)
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
        # while the speed tier still grades from tokens/s.
        lines = self.lines_for([100, 50], costs=["null", 0.5])
        header = next(ln for ln in lines if ln.startswith("DSW"))
        ppi_at = header.index("PPI")
        luna = _row_after(lines, "GPT-5.6 Luna")
        self.assertEqual(_cell_at(luna, ppi_at, 5), "n/a")
        self.assertEqual(self.spd_of(lines, "GPT-5.6 Luna"), "5")


class EdgeFixture(unittest.TestCase):
    """Hand-built edge fixture (spec §Test strategy): equal-cost tie on the
    frontier and an AA-only model that must stay out of the envelope."""

    AA_ROW = ('{{"id": "{i}", "name": "{name} (low)", "slug": "{slug}-low",'
              ' "model_creator": {{"name": "Acme"}},'
              ' "evaluations": {{"artificial_analysis_intelligence_index": {ii}}},'
              ' "artificial_analysis_intelligence_index_cost":'
              ' {{"cost_per_task": {{"total_cost": {cost}}}}},'
              ' "performance": {{"median_output_tokens_per_second": 1000}}}}')

    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.td.cleanup)
        aa = {"data": [
            json.loads(cls.AA_ROW.format(i="u1", name="GPT-5.6 Luna",
                                         slug="gpt-5-6-luna", ii=50, cost=1.0)),
            json.loads(cls.AA_ROW.format(i="u2", name="GPT-5.6 Sol",
                                         slug="gpt-5-6-sol", ii=60, cost=1.0)),
            json.loads(cls.AA_ROW.format(i="u3", name="Kimi K3",
                                         slug="kimi-k3", ii=90, cost=0.5)),
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
    """Ticket 13 — Terminal-Bench v2.1 as a third source. The CLI's rendered
    category (Chores) is low effort, where TB is `—`; the high/max tables are
    rendered in-process through the same fixture seam (fetch → identity →
    tier → render), so the TB grade column is observable end to end."""

    TB_MODELS = {"gpt-5-6-luna", "gpt-5-6-sol", "gpt-5-5", "claude-opus-5"}

    @classmethod
    def setUpClass(cls):
        from llmratings import fetch, identity, render
        raw = fetch.fetch_all(FIXTURES)
        aliases = identity.load_aliases(REPO / "llmratings" / "aliases.json")
        cls.ds = identity.build(aliases, raw)
        cls.lines = {cat: [ln.rstrip() for ln in render.render(cls.ds, cat)]
                     for cat in ("Deliberate", "Deep", "Everyday")}

    def row(self, cat, prefix, model):
        """First table row in cat whose line matches prefix + contains model —
        a prefix match skips arrow lines ("    → …") that mention the model."""
        return next(ln for ln in self.lines[cat]
                    if re.match(prefix, ln) and model in ln)

    def test_tb_dash_at_chores_low(self):
        r = run_fixtures()
        self.assertEqual(r.returncode, 0)
        lines = [ln.rstrip() for ln in r.stdout.splitlines()]
        for model in ("GPT-5.6 Luna", "GPT-5.6 Sol", "GPT-5.5",
                      "Claude Opus 5"):
            ln = next(ln for ln in lines
                      if re.match(r"^\s*\d+\s+\d+\s+—\s+", ln)
                      and model in ln)
            self.assertRegex(ln, rf"^\s*\d+\s+\d+\s+—\s+{model}")

    def test_tb_dash_at_everyday_medium(self):
        # TB covers high/xhigh/max only — every medium row shows `—`.
        # Data rows start with the right-aligned DSW cell (≤2 spaces, then a
        # digit or —); titles/header/sections/arrows don't match.
        rows = [ln for ln in self.lines["Everyday"]
                if re.match(r"^ {0,2}(?:\d|—)", ln)]
        self.assertTrue(rows)
        for ln in rows:
            self.assertRegex(ln, r"^\s*\S+\s+\S+\s+—\s")

    def test_tb_grades_at_high(self):
        # Deliberate = high. Collapsed TB scores: Sol .712, Luna .701,
        # GPT-5.5 .671 → quintile grades 5/4/2 over TB's own set; Opus 5 has
        # no TB high row → `—`.
        for model, prefix in [
            ("GPT-5.6 Sol", r"^\s*4\s+4\s+5\s+"),
            ("GPT-5.6 Luna", r"^\s*1\s+2\s+4\s+"),
            ("GPT-5.5", r"^\s*3\s+3\s+2\s+"),
            ("Claude Opus 5", r"^\s*5\s+5\s+—\s+")]:
            self.assertRegex(self.row("Deliberate", prefix, model),
                             prefix + model)

    def test_tb_grades_at_max(self):
        # Deep = max. Collapsed TB scores: Sol .769, Luna .757, Opus 5 .689
        # → grades 5/4/2; Kimi and Terra have no TB rows → `—`.
        for model, prefix in [
            ("GPT-5.6 Sol", r"^\s*4\s+4\s+5\s+"),
            ("GPT-5.6 Luna", r"^\s*1\s+2\s+4\s+"),
            ("Claude Opus 5", r"^\s*5\s+5\s+2\s+"),
            ("Kimi K3", r"^\s*2\s+3\s+—\s+"),
            ("gpt-5-6-terra", r"^\s*3\s+—\s+—\s+")]:
            self.assertRegex(self.row("Deep", prefix, model), prefix + model)

    def test_collapse_best_agent(self):
        from llmratings import identity
        # GPT-5.5 high has two agents: codex .664 and warp .671 — the better
        # one wins, and the table shows a single GPT-5.5 row.
        best = identity.best_tb(self.ds.ratings, "high")
        self.assertEqual(best["gpt-5-5"].score, 0.671)
        self.assertEqual(best["gpt-5-5"].agent, "warp")
        rows = [ln for ln in self.lines["Deliberate"]
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
        # No category fixes xhigh effort yet (the `e` override is ticket 16),
        # so the xhigh leg of the acceptance criteria is asserted at the
        # dataset level: both xhigh rows attach and collapse to one rating per
        # model — the same code path the high/max columns render.
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


if __name__ == "__main__":
    unittest.main()
