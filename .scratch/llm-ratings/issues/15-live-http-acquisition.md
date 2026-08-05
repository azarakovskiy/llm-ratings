# 15 Live HTTP acquisition for all three sources

Type: task
Status: ready-for-agent
Blocked by: 11, 13

## What to build

Real acquisition replaces the fixture backend: every run fetches current data, no vendored snapshot, no cache, no daemon. DeepSWE leaderboard JSON (no auth); Artificial Analysis paginated API (page_size 200, `x-api-key` from `LLM_RATINGS_AA_API_KEY`, ~3 pages at current model count — API only, never scrape); Terminal-Bench submissions enumeration via the GitHub API plus per-entry raw JSON. Any source failure → clear error naming the source and nonzero exit, no silent partial tables. The alias seed is extended to the current DeepSWE/TB model strings (~25–30 models) so the live tables join cleanly; a model without an alias degrades to source-only identity rather than blocking the run. Fixture mode stays for tests — the seam is untouched below the fetch boundary.

## Acceptance criteria

- [ ] Live run fetches DeepSWE + AA + TB and renders the same tables fixture mode renders
- [ ] AA pagination handled (multiple pages, key from env); key missing → the 11 setup error path
- [ ] Any single source failure → clear error naming the source, nonzero exit, no partial output
- [ ] Alias seed covers the current source model strings; unknown model degrades to source-only identity, run still completes
- [ ] Fixture mode still works unchanged
