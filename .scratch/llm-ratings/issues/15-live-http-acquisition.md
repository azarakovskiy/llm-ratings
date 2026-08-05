# 15 Live HTTP acquisition for all three sources

Type: task
Status: resolved
Blocked by: 11, 13

## What to build

Real acquisition replaces the fixture backend: every run fetches current data, no vendored snapshot, no cache, no daemon. DeepSWE leaderboard JSON (no auth); Artificial Analysis paginated API (page_size 200, `x-api-key` from `LLM_RATINGS_AA_API_KEY`, ~3 pages at current model count — API only, never scrape); Terminal-Bench submissions enumeration via the GitHub API plus per-entry raw JSON. Any source failure → clear error naming the source and nonzero exit, no silent partial tables. The alias seed is extended to the current DeepSWE/TB model strings (~25–30 models) so the live tables join cleanly; a model without an alias degrades to source-only identity rather than blocking the run. Fixture mode stays for tests — the seam is untouched below the fetch boundary.

## Acceptance criteria

- [ ] Live run fetches DeepSWE + AA + TB and renders the same tables fixture mode renders
- [ ] AA pagination handled (multiple pages, key from env); key missing → the 11 setup error path
- [ ] Any single source failure → clear error naming the source, nonzero exit, no partial output
- [ ] Alias seed covers the current source model strings; unknown model degrades to source-only identity, run still completes
- [ ] Fixture mode still works unchanged

## Answer

Shipped `7131d14` on `t15-live-http` (worktree `llm-ratings-t15`, base `t12-14-merge`), 45/45 tests green, reviewed (standards + spec). Live acquisition replaces the fixture backend: DeepSWE leaderboard JSON (no auth); AA free API with `x-api-key` from `LLM_RATINGS_AA_API_KEY`, page_size 200 with pagination until a short page; TB submissions via GitHub contents API + each entry's `download_url` raw JSON (reconstructing `<date>-<org>-…` paths dropped — GitHub's own raw URL field, same host). `LLM_RATINGS_HTTP_BASE` env override reroots every live URL — the offline test seam (local stdlib HTTP server, no network in tests). Any source failure → `SourceError` naming the source, nonzero exit, empty stdout; malformed payloads (non-dict AA pages, missing `data`, non-dict TB listing entries) harden into the same named errors. Alias seed extended to 38 entries / 22 models covering all 19 DeepSWE slug strings + all 15 live TB `model_name` strings (org-qualified and dotted); unknown model degrades to source-only identity. Live smoke run (network open, key from `.env`): exit 0, 51 DSW rows, 592 AA rows over 3 pages, 20 TB submissions; 2/546 models source-only (genuinely absent from AA). Fixture mode unchanged — all 37 pre-existing tests untouched.
