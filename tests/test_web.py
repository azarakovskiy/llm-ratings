"""Public HTTP and CLI consumers of the real source/identity/session path."""

import http.client
import json
import os
import select
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

from test_cli import FIXTURES, REPO, ROLES, _LiveServer, aa_config, run_cli
from llmratings import fetch, identity, web
from llmratings.session import Session


class Document(HTMLParser):
    """Read visible text and selected native controls, not HTML layout."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.text = []
        self.tags = []
        self.selected = []
        self.tables = []
        self.current_table = None
        self.deltas = {}
        self.current_model = None
        self.current_delta = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == "table":
            self.current_table = []
            self.tables.append(self.current_table)
        if tag == "tr":
            self.current_model = attrs.get("data-model")
        if tag == "td" and self.current_model:
            for kind in ("score", "cost"):
                if f"data-{kind}-change" in attrs:
                    self.current_delta = self.deltas.setdefault(self.current_model, {}).setdefault(kind, [])
        if tag == "option" and "selected" in attrs:
            self.selected.append(attrs.get("value", ""))
        if tag == "button" and (attrs.get("aria-pressed") == "true"
                                or attrs.get("aria-current") in ("true", "page")):
            self.selected.append(attrs.get("value", ""))

    def handle_data(self, data):
        self.text.append(data)
        if self.current_table is not None:
            self.current_table.append(data)
        if self.current_delta is not None:
            self.current_delta.append(data)

    def handle_endtag(self, tag):
        if tag == "table":
            self.current_table = None
        if tag == "tr":
            self.current_model = None
        if tag == "td":
            self.current_delta = None

    @property
    def visible(self):
        return " ".join(" ".join(self.text).split())

    def delta(self, model, kind):
        value = "".join(self.deltas[model][kind]).strip()
        if value == "No previous row":
            return None
        return float(value.replace("$", "").replace("−", "-").replace(",", ""))


class WebAdvice(unittest.TestCase):
    def setUp(self):
        ds = identity.build(
            identity.load_aliases(REPO / "llmratings" / "aliases.json"),
            fetch.fetch_all(FIXTURES))
        self.start_dataset(ds)

    def start_dataset(self, ds):
        self.server = web.create_server(Session(ds, ROLES))
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.stop, self.server, thread)

    @staticmethod
    def stop(server, thread):
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    def request(self, method="GET", path="/", body=None, headers=None):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read().decode()
        finally:
            connection.close()

    def action(self, action, value):
        status, _, body = self.request(
            "POST", body=urlencode({"action": action, "value": value}),
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 200, body)
        return Document(body)

    def test_serves_fixture_advice_and_both_real_comparison_views(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.assertGreater(self.server.server_address[1], 0)
        status, _, body = self.request()
        self.assertEqual(status, 200)
        doc = Document(body)
        self.assertTrue(any(attrs.get("id") == "app" for _, attrs in doc.tags))
        for text in ("Explorer", "Best value", "Intelligence score", "GPT-5.6 Luna",
                     "GPT-5.6 Sol", "33.3", "Low", "Artificial Analysis",
                     "DeepSWE", "Terminal-Bench", "2026-08-05"):
            self.assertIn(text, doc.visible)
        self.assertIn("snapshot", doc.visible.lower())
        self.assertTrue(any(tag == "a" and attrs.get("href", "").startswith(
            "https://artificialanalysis.ai") for tag, attrs in doc.tags))
        picks = self.action("view", "picks")
        for text in ("Primary", "Runner-up", "GPT-5.6 Luna", "GPT-5.6 Sol",
                     "No qualifying runner-up", "Kimi"):
            self.assertIn(text, picks.visible)
        self.assertIn("Details", picks.visible)
        table = self.action("view", "table")
        self.assertIn("Intelligence score", table.visible)
        self.assertIn("GPT-5.6 Luna", table.visible)


    @staticmethod
    def open_evidence(doc):
        return [attrs for _, attrs in doc.tags
                if "model-evidence" in attrs.get("class", "").split()
                and "hidden" not in attrs]

    def test_explicit_inline_evidence_in_both_views_and_source_only_records(self):
        _, _, body = self.request()
        initial = Document(body)
        self.assertFalse(self.open_evidence(initial))
        for label in ("Time to first answer token", "including thinking",
                      "Output tokens per second", "How picks work"):
            self.assertIn(label, initial.visible)
        self.action("provider", "OpenAI")
        self.action("objective", "cap")
        opened = self.action("details", "gpt-5-6-sol")
        self.assertEqual(len(self.open_evidence(opened)), 1)
        for label in ("GPT-5.6 Sol", "Maximum", "Measured configurations",
                      "Why this configuration", "Capability per dollar",
                      "Published timing and token list prices", "USD per million input tokens",
                      "Time to first token", "Estimated response time for 500 answer tokens",
                      "OpenRouter", "30-day token share", "Unavailable",
                      "DeepSWE", "Terminal-Bench", "2026-08-05"):
            self.assertIn(label, opened.visible)
        control = next(attrs for tag, attrs in opened.tags
                       if tag == "button" and attrs.get("aria-expanded") == "true")
        self.assertTrue(any(attrs.get("id") == control["aria-controls"]
                            for _, attrs in opened.tags))
        source_links = [attrs["href"] for tag, attrs in opened.tags if tag == "a"]
        self.assertTrue(any("leaderboard-live.json" in url for url in source_links))
        self.assertTrue(any("terminal-bench-2-1" in url for url in source_links))
        closed = self.action("close_details", "")
        self.assertFalse(self.open_evidence(closed))
        self.assert_choices(closed, "Explorer", "cap", "OpenAI", "", "table")
        picks = self.action("view", "picks")
        self.assertFalse(self.open_evidence(picks))
        for key in ("gpt-5-6-sol", "gpt-5-5"):
            opened = self.action("details", key)
            self.assertEqual(len(self.open_evidence(opened)), 1)
            self.assertIn("Why this configuration", opened.visible)
        self.action("recover", "all_providers")
        opened = self.action("details", "dsw:gpt-5-6-terra")
        self.assertEqual(len(self.open_evidence(opened)), 1)
        self.assertIn("No measured Artificial Analysis configuration", opened.visible)
        self.assertIn("DeepSWE", opened.visible)
        self.assertIn("Unranked", opened.visible)

    def test_details_clear_on_result_changes_and_area_cost_advice_stays_unavailable(self):
        transitions = (("objective", "cap"), ("capability", "4"),
                       ("provider", "OpenAI"), ("view", "picks"), ("role", "Coder"))
        for action, value in transitions:
            self.action("details", "gpt-5-6-sol")
            changed = self.action(action, value)
            self.assertFalse(self.open_evidence(changed), (action, value))
        opened = self.action("details", "gpt-5-6-sol")
        self.assertIn("Coding", opened.visible)
        self.assertIn("no matching Coding benchmark task cost", opened.visible)
        self.assertIn("Intelligence benchmark task cost", opened.visible)
        unavailable = self.action("objective", "ppi")
        self.assertFalse(self.open_evidence(unavailable))
        opened = self.action("details", "gpt-5-6-sol")
        self.assertEqual(len(self.open_evidence(opened)), 1)
        self.assertIn("Unavailable objective", opened.visible)
        self.assert_choices(opened, "Coder", "ppi", "OpenAI", "4", "picks")
        status, _, _ = self.request("POST", body="action=details&value=unknown-model",
                                    headers={"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 400)

    def test_unranked_negative_cost_is_not_relabelled_positive_and_missing_metrics_stay_missing(self):
        with tempfile.TemporaryDirectory() as td:
            docs = {
                "aa.json": {"data": [aa_config("invalid-cost", score=50, cost=-4, speed=None)]},
                "deepswe.json": {"rows": [
                    {"model": "invalid-cost", "reasoning_effort": "low", "pass_at_1": .5}]},
                "tb.json": {"listing": [], "submissions": {}},
            }
            for name, payload in docs.items():
                Path(td, name).write_text(json.dumps(payload))
            ds = identity.build({"invalid-cost": "invalid-cost"}, fetch.fetch_all(td))
        self.start_dataset(ds)
        doc = self.action("details", "invalid-cost")
        self.assertEqual(len(self.open_evidence(doc)), 1)
        self.assertIn("−$4", doc.visible)
        self.assertIn("No finite non-negative matching Intelligence benchmark task cost", doc.visible)
        self.assertIn("— means unavailable", doc.visible)
        self.assertIn("Time to first answer token, including thinking", doc.visible)
        self.assertIn("Context length", doc.visible)
        self.assertIn("30-day token share Unavailable", doc.visible)

    def assert_choices(self, doc, role, objective, provider, capability, view):
        for value in (role, objective, provider, capability, view):
            self.assertIn(value, doc.selected, doc.visible)

    def test_manual_objective_override_keeps_role_default_label_truthful(self):
        doc = self.action("objective", "cap")
        self.assertIn("cap", doc.selected)
        self.assertIn("Role default: Best value", doc.visible)
        self.assertIn("override active", doc.visible.lower())
        self.assertNotIn("Objective override: Best value", doc.visible)

    def test_transitions_and_named_recovery_retain_unrelated_constraints(self):
        self.action("provider", "Anthropic")
        self.action("capability", "5")
        self.action("objective", "price")
        doc = self.action("view", "picks")
        self.assert_choices(doc, "Explorer", "price", "Anthropic", "5", "picks")
        doc = self.action("role", "Coder")
        self.assert_choices(doc, "Coder", "cap", "Anthropic", "5", "picks")
        self.assertIn("Coding score", doc.visible)
        doc = self.action("objective", "ppi")
        self.assert_choices(doc, "Coder", "ppi", "Anthropic", "5", "picks")
        self.assertIn("unavailable", doc.visible.lower())
        self.assertIn("task cost", doc.visible.lower())
        doc = self.action("recover", "highest_capability")
        self.assert_choices(doc, "Coder", "cap", "Anthropic", "5", "picks")
        doc = self.action("role", "Coordinator")
        self.assert_choices(doc, "Coordinator", "cap", "Anthropic", "5", "picks")
        self.assertIn("Agentic score", doc.visible)
        doc = self.action("objective", "price")
        self.assert_choices(doc, "Coordinator", "price", "Anthropic", "5", "picks")
        self.assertIn("unavailable", doc.visible.lower())
        self.action("role", "Explorer")
        self.action("objective", "cap")
        doc = self.action("recover", "role_default")
        self.assert_choices(doc, "Explorer", "ppi", "Anthropic", "5", "picks")
        doc = self.action("recover", "all_providers")
        self.assert_choices(doc, "Explorer", "ppi", "", "5", "picks")
        self.action("provider", "xAI")
        doc = self.action("capability", "4")
        self.assert_choices(doc, "Explorer", "ppi", "xAI", "4", "picks")
        self.assertIn("No qualifying configuration", doc.visible)
        doc = self.action("recover", "clear_capability")
        self.assert_choices(doc, "Explorer", "ppi", "xAI", "", "picks")
        self.assertIn("No qualifying configuration", doc.visible)

    def test_static_allowlist_security_headers_and_no_file_escape(self):
        for path, content_type in (("/", "text/html"), ("/web.css", "text/css"),
                                   ("/web.js", "text/javascript")):
            with self.subTest(path=path):
                status, headers, body = self.request(path=path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
                self.assertTrue(headers["Content-Type"].startswith(content_type))
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(headers["Referrer-Policy"], "no-referrer")
                csp = headers["Content-Security-Policy"]
                for directive in ("default-src 'none'", "script-src 'self'",
                                  "style-src 'self'", "frame-ancestors 'none'",
                                  "base-uri 'none'", "form-action 'self'"):
                    self.assertIn(directive, csp)
                self.assertNotIn("unsafe-inline", csp)
        for path in ("/aliases.json", "/roles.json", "/../aliases.json",
                     "/%2e%2e/aliases.json", "/web.css/../../aliases.json",
                     "//web.js", "/web.js?file=aliases.json", "/api",
                     "/.scratch/llm-ratings/fixtures/main/aa.json"):
            with self.subTest(path=path):
                status, _, body = self.request(path=path)
                self.assertEqual(status, 404)
                self.assertNotIn("gpt-5", body.lower())
                self.assertNotIn(path, body)

    def test_rejects_foreign_mutations_and_invalid_forms_without_changing_state(self):
        self.action("provider", "OpenAI")
        self.action("objective", "cap")
        valid = urlencode({"action": "provider", "value": "Anthropic"})
        origin = f"http://127.0.0.1:{self.server.server_port}"
        invalid = [
            (valid, {"Origin": "https://example.com"}, 403),
            (valid, {"Origin": "null"}, 403),
            (valid, {"Origin": origin + ".example.com"}, 403),
            (valid, {"Referer": "https://example.com/"}, 403),
            (valid, {"Sec-Fetch-Site": "cross-site"}, 403),
            (valid, {"Sec-Fetch-Site": "same-site"}, 403),
            (valid, {"Host": "attacker.example"}, 403),
            (valid, {"Content-Type": "application/json"}, 415),
            ("x" * 4097, {}, 413),
            (valid, {"Content-Length": "-1"}, 400),
            (valid, {"Content-Length": "9" * 5000}, 413),
            (valid, {"Content-Encoding": "gzip"}, 415),
            (valid, {"Transfer-Encoding": "chunked"}, 411),
            ("action=provider&value=OpenAI&value=Anthropic", {}, 400),
            ("action=provider&value=OpenAI&extra=bad", {}, 400),
            ("action=provider", {}, 400),
            ("action=provider&value=%FF", {}, 400),
            ("action=unknown&value=private-user-input", {}, 400),
            ("action=role&value=private-user-input", {}, 400),
            ("action=objective&value=private-user-input", {}, 400),
            ("action=capability&value=3", {}, 400),
            ("action=view&value=private-user-input", {}, 400),
            ("action=recover&value=private-user-input", {}, 400),
            ("action=details&value=private-user-input", {}, 400),
            ("action=close_details&value=private-user-input", {}, 400),
        ]
        for body, extra_headers, expected in invalid:
            with self.subTest(body=body[:60], headers=extra_headers):
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                headers.update(extra_headers)
                status, _, response = self.request("POST", body=body, headers=headers)
                self.assertEqual(status, expected, response)
                self.assertNotIn("private-user-input", response)
        status, _, body = self.request()
        self.assertEqual(status, 200)
        self.assert_choices(Document(body), "Explorer", "cap", "OpenAI", "", "table")
        status, _, body = self.request(
            "POST", body=valid, headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": origin, "Referer": origin + "/", "Sec-Fetch-Site": "same-origin"})
        self.assertEqual(status, 200)
        self.assertIn("Anthropic", Document(body).selected)

    def test_source_shaped_edge_cases_escape_content_without_serializing_raw_rows(self):
        provider = "Synthetic <script>bad()</script>"
        configs = [aa_config("alpha", score=100, cost=10, provider=provider),
                   aa_config("beta", score=99, cost=11, provider=provider),
                   aa_config("delta", score=90, cost=20, provider=provider),
                   aa_config("gamma", score=80, cost=5, provider=provider),
                   aa_config("solo", score=70, cost=4, provider="Synthetic Solo"),
                   aa_config("catalog-only", score=60, cost=3, provider="Synthetic Empty")]
        configs[0]["name"] = "Synthetic <img src=x onerror=bad()> (low)"
        configs[0]["private_fixture_row"] = "raw-row-must-not-reach-browser"
        with tempfile.TemporaryDirectory() as td:
            docs = {"aa.json": {"data": configs}, "tb.json": {"listing": [], "submissions": {}},
                    "deepswe.json": {"rows": [
                        {"model": key, "reasoning_effort": "low", "pass_at_1": .5}
                        for key in ("alpha", "beta", "delta", "gamma", "solo", "orphan")]}}
            for name, payload in docs.items():
                Path(td, name).write_text(json.dumps(payload))
            ds = identity.build(
                {key: key for key in ("alpha", "beta", "delta", "gamma", "solo", "catalog-only")},
                fetch.fetch_all(td))
        self.start_dataset(ds)
        self.action("objective", "cap")
        doc = self.action("view", "picks")
        picks = next(" ".join(table) for table in doc.tables
                     if "Primary" in " ".join(table) and "Runner-up" in " ".join(table))
        self.assertIn("Synthetic <img src=x onerror=bad()>", picks)
        self.assertIn("beta", picks)
        self.assertLess(picks.index("Synthetic <img"), picks.index("beta"))
        self.assertNotIn("gamma", picks)
        self.assertIn("No qualifying runner-up", doc.visible)
        self.assertIn("Creators without qualifying models", doc.visible)
        status, _, body = self.request()
        self.assertEqual(status, 200)
        self.assertNotIn("raw-row-must-not-reach-browser", body)
        self.assertNotIn(td, body)
        self.assertFalse(any(tag == "img" or tag == "script" and not attrs.get("src")
                             for tag, attrs in Document(body).tags))
        doc = self.action("provider", "Synthetic Empty")
        self.assertIn("Synthetic Empty", doc.selected)
        self.assertIn("No qualifying configuration", doc.visible)
        self.action("recover", "all_providers")
        doc = self.action("view", "table")
        self.assertIn("orphan", doc.visible)
        self.assertIn("unranked", doc.visible.lower())
        self.action("provider", provider)
        doc = self.action("objective", "ppi")
        self.assertEqual((doc.delta("gamma", "score"), doc.delta("gamma", "cost")), (None, None))
        self.assertEqual((doc.delta("alpha", "score"), doc.delta("alpha", "cost")), (20, 5))
        self.assertEqual((doc.delta("beta", "score"), doc.delta("beta", "cost")), (None, None))
        self.assertEqual((doc.delta("delta", "score"), doc.delta("delta", "cost")), (-9, 9))
        doc = self.action("capability", "5")
        self.assertIn("beta", doc.visible)
        self.assertIn("gamma", doc.visible)
        self.assertIn("filter", doc.visible.lower())
        self.assertEqual((doc.delta("alpha", "score"), doc.delta("alpha", "cost")), (None, None))
        self.assertEqual((doc.delta("beta", "score"), doc.delta("beta", "cost")), (None, None))
        self.assertNotIn("gamma", doc.deltas)
        self.assertNotIn("delta", doc.deltas)


class WebLaunch(unittest.TestCase):
    def start_cli(self, *args, **env_extra):
        env = dict(os.environ, LLM_RATINGS_AA_API_KEY="web-test-secret")
        env.update(env_extra)
        process = subprocess.Popen(
            [sys.executable, "-m", "llmratings", "--web", *args],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, cwd=REPO, env=env)
        self.addCleanup(self.stop_cli, process)
        ready, _, _ = select.select([process.stdout], [], [], 15)
        self.assertTrue(ready, "web launch did not print a URL")
        url = process.stdout.readline().strip()
        self.assertRegex(url, r"^http://127\.0\.0\.1:[1-9][0-9]*/$")
        return process, url

    def stop_cli(self, process):
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
        try:
            out, err = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            self.fail("web server did not stop on Ctrl-C")
        self.assertEqual(process.returncode, 0, out + err)

    def test_non_tty_web_honors_role_and_stops_cleanly(self):
        process, url = self.start_cli("--fixtures", str(FIXTURES), "--role", "Coder")
        connection = http.client.HTTPConnection(url.split("/")[2], timeout=5)
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read().decode()
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        doc = Document(body)
        self.assertIn("Coder", doc.selected)
        self.assertIn("Coding score", doc.visible)
        self.assertIn("Highest capability", doc.visible)
        self.assertNotIn("web-test-secret", body)
        process.send_signal(signal.SIGINT)
        process.wait(timeout=10)
        self.assertEqual(process.returncode, 0)

    def test_web_default_role_follows_role_file_order(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name, "roles.json")
        path.write_text(json.dumps([ROLES[-1], *ROLES[:-1]]))
        _, url = self.start_cli("--fixtures", str(FIXTURES),
                                LLM_RATINGS_ROLES=str(path))
        connection = http.client.HTTPConnection(url.split("/")[2], timeout=5)
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read().decode()
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        self.assertIn("Utility", Document(body).selected)
        self.assertIn("price", Document(body).selected)
        self.assertNotIn(str(path), body)

    def test_live_startup_fetches_once_and_controls_reuse_loaded_sources(self):
        source = _LiveServer()
        self.addCleanup(source.stop)
        _, url = self.start_cli(LLM_RATINGS_HTTP_BASE=source.url())
        acquired = list(source.seen)
        self.assertEqual(len(acquired), len(set(acquired)))
        self.assertTrue(any("/artifacts/" in path for path in acquired))
        self.assertTrue(any("/api/v2/language/models/free" in path for path in acquired))
        self.assertTrue(any("/repos/" in path for path in acquired))
        for action, value in (("provider", "OpenAI"), ("objective", "cap"),
                              ("capability", "4"), ("view", "picks"),
                              ("role", "Coder"), ("objective", "ppi"),
                              ("recover", "highest_capability"),
                              ("recover", "all_providers"), ("view", "table"),
                              ("details", "gpt-5-6-sol"), ("close_details", "")):
            with self.subTest(action=action, value=value):
                connection = http.client.HTTPConnection(url.split("/")[2], timeout=5)
                try:
                    connection.request(
                        "POST", "/", urlencode({"action": action, "value": value}),
                        {"Content-Type": "application/x-www-form-urlencoded"})
                    response = connection.getresponse()
                    body = response.read().decode()
                finally:
                    connection.close()
                self.assertEqual(response.status, 200, body)
                self.assertNotIn("web-test-secret", body)
        self.assertEqual(source.seen, acquired)

    def test_optional_enrichment_failure_still_serves_loaded_advice(self):
        source = _LiveServer(fail="/api/v1/models")
        self.addCleanup(source.stop)
        _, url = self.start_cli(LLM_RATINGS_HTTP_BASE=source.url())
        connection = http.client.HTTPConnection(url.split("/")[2], timeout=5)
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            body = response.read().decode()
        finally:
            connection.close()
        self.assertEqual(response.status, 200)
        self.assertIn("GPT-5.6 Luna", Document(body).visible)

    def test_setup_and_required_source_failures_do_not_start_a_server(self):
        missing = run_cli({"LLM_RATINGS_AA_API_KEY": ""}, "--web",
                          "--fixtures", str(FIXTURES))
        self.assertNotEqual(missing.returncode, 0)
        self.assertEqual(missing.stdout, "")
        self.assertIn("LLM_RATINGS_AA_API_KEY", missing.stderr)
        for path, name in (("/artifacts/", "DeepSWE"),
                           ("/api/v2/language/models/free", "Artificial Analysis"),
                           ("/repos/", "Terminal-Bench")):
            with self.subTest(source=name):
                source = _LiveServer(fail=path)
                try:
                    result = run_cli(
                        {"LLM_RATINGS_AA_API_KEY": "web-test-secret",
                         "LLM_RATINGS_HTTP_BASE": source.url()}, "--web")
                finally:
                    source.stop()
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertIn(name, result.stderr)
                self.assertNotIn("web-test-secret", result.stderr)


if __name__ == "__main__":
    unittest.main()
