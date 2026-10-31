# Add provider-scoped advice and shared selection state

Type: task
Status: ready-for-agent
Blocked by: 35

## What to build

Implement one working advice query and selection-state path for Model table and Provider picks, with creator-scoped Intelligence advice and explicit empty/unavailable recovery. Connect the existing batch Model table consumer to that path and exercise both projections from the real loaded fixture. This is query/state implementation, not a new TUI provider feature or a web scaffold.

Implementation prerequisite: [Implement the eight-role selection policy](35-eight-role-selection-policy.md), which consumes [Preserve index-specific metrics and source provenance](34-preserve-index-metrics-provenance.md). Follow [the spec](../spec.md). [Build the Provider lens web comparison](37-provider-lens-web-comparison.md) adds visible browser controls to this completed shared path; it must not introduce a second scoring policy.

## Binding requirements

### One selection policy, two projections

- Reuse the previous task's selected-index eligibility, objective-selected effort, exact complete ordering keys, capability grades and missing-data reasons. Do not create provider-specific scores, a second ranking pipeline or JavaScript scoring.
- The candidate sequence is: required-data eligibility → one objective-selected measured configuration per model → active selected-index capability display filter → provider constraint. The capability filter does not choose a different effort to make a model pass. Calculate reference populations/independent grades before creator and capability display constraints.
- Preserve the dataset inclusion boundary of at least one DeepSWE or Terminal-Bench rating. Artificial Analysis-only catalog models can make their creator discoverable but cannot become ranked candidates; source-only included models remain reachable as unranked records with reasons. Never fabricate an Artificial Analysis score/cost to fill a pick.
- Model table retains all qualifying distinct models at their selected effort for the active role/objective/provider/filter. For Intelligence, partition selected rows into frontier and dominated sections and apply the complete objective order within each section. For Coding/Agentic, use direct selected-index score order without a cost frontier, replacement, path or cheaper-alternative claim.
- Provider picks groups the qualifying candidates by their Artificial Analysis creator and takes the first two distinct models in direct objective order: Primary, then Runner-up. Do not take the first two frontier-first Model table rows. A dominated Intelligence model can be either pick; Primary does not imply global frontier membership. Runner-up is neither another effort of Primary nor a price-diversity/cheapest-alternative selection.
- All providers produces picks within each creator, not two global picks. Selecting one creator produces only that creator's table/picks and scoped advice. One qualifying model yields one Primary with `No qualifying runner-up` explained; zero yields none. Do not repeat a model at another effort, substitute another creator or relax a constraint.

### Provider membership and comparison scope

- Provider means model creator, not gateway/hosting endpoint or a price dimension. State allows exactly one creator or All providers, not a multiselect. Preserve canonical model identity, source/effort alignment and existing alias joins.
- Expose the fixed curated shortcuts OpenAI, Anthropic, Google, DeepSeek and xAI, independent of source scores, token share, eligible model count, role or filters. A shortcut with no eligible model remains selectable. Full chooser data contains every creator in the loaded catalog, including creators without shortcuts or qualifying picks. Do not remove them based on the current result set.
- For Intelligence, provider selection constrains the full comparison universe for frontier membership, cross-effort frontier path, strict replacements and cheaper-near-equal detail alternatives. It is not only a row filter applied after global advice is computed.
- Build that advisory universe from all included models' measured efforts with valid finite Intelligence score and finite non-negative matching Intelligence task cost within the selected creator scope. It is floor-free and capability-display-filter-free: neither the Lowest qualifying price capability floor nor the active display filter removes advisory points. A model's non-selected effort can therefore remain a valid replacement/path/alternative point.
- Preserve strict dominance (score ≥ target and cost ≤ target with at least one strict), same-effort replacement preference, cross-effort fallback, maximum score gain then maximum saving among replacement candidates. Preserve up to three lower-cost alternatives whose Intelligence score is at least the target score minus 5, price-sorted. All of these comparisons use the same creator scope; All providers restores the global included-model universe.
- Coding/Agentic have no established matching task costs. Do not transfer their scores onto an Intelligence-cost frontier, infer value/price advice, use an Intelligence cost tie or expose misleading empty cost-advice sections. Missing timing cannot change candidates, picks or advice.
- Provider/capability changes do not alter published scores or grades. Selected-index Artificial Analysis capability grades keep all scored configurations across efforts in the refresh; DeepSWE/Terminal-Bench remain independent at their existing reference sets. Existing value/output-speed/price grade populations remain over their valid objective-selected role rows before creator/capability constraints, not creator-relative or newly per-effort bins. OpenRouter share stays display-only and unavailable without verified data; it cannot affect shortcuts or query results.
- The query result must identify provider selection and advisory comparison scope so consumers can distinguish provider-local from global frontier status without inferring it from a color or Primary label.

### Shared state and transitions

Use the smallest UI-independent state that owns the active role, optional objective override, capability filter, provider selection, active view and requested model details/selection. Reuse existing role/session semantics where they still apply; do not add a state-machine framework or bind the shared query to Textual.

| State/action | Required behavior |
| --- | --- |
| Initial session | First role in file order (Explorer for shipped profiles), its default objective, all capability grades, All providers, Model table, no requested details. An explicit supported `--role` chooses that initial role. |
| Change role | Use the new role's index/default objective; clear objective override; retain provider, capability filter and current view. Clear stale row/details. |
| Change view | Switch Model table/Provider picks; retain role, objective override, provider and capability filter. Clear stale row/details. |
| Change provider | Change only provider selection, then recompute candidates/advisory scope. Retain role, objective and capability filter/view. Clear stale row/details. |
| Change capability filter | Change only the display filter (all, grade 5, grade ≥ 4), not the selected effort or grade population. Retain other choices; clear stale row/details. |
| Change objective | Retain role/index, provider, capability filter and view. Re-select one configuration per model under the requested objective or retain an explicit unavailable-objective state. Clear stale row/details. |
| All providers recovery | Clear only the provider constraint. Preserve the active role, objective, capability filter and view; clear stale row/details as for a provider change. |
| Capability recovery | Clear only that capability display filter. Do not switch creator, role, objective or view. Clear stale row/details. |
| Supported-objective recovery | Change only the objective to the supported requested choice (Highest capability for area roles). Preserve role/index, provider, capability filter and view; clear stale row/details. |
| Use role default recovery | Clear only the objective override so the active role's default applies. Preserve role/index, provider, capability filter and view; clear stale row/details. |
| Request/close model details | Details open only by explicit model request and close explicitly. Passive row/focus selection is not a detail request. A result-set change must not leave evidence for an old model/configuration attached to a new row. |

- No saved preferences or implicit persistence. Do not silently reset unsupported area Best value/Lowest qualifying price overrides, switch index, select another creator, clear a filter or revert to a default as an empty-state shortcut.
- Expose an explicit unavailable-objective result for those unsupported combinations, separate from a supported objective with no eligible configuration. Every empty result names the selected role, provider and active constraints; use `No qualifying configuration` for supported all-unqualified results. Preserve unranked reasons and creators-without-picks reasons for later secondary disclosure and recovery.
- Query both projections from the same loaded refresh/state. State changes reuse the already loaded dataset; they do not fetch sources, recompute a new market snapshot, call a model or alter reference sets. No native visible provider controls or dead Details button are required in this task; later web tasks own those surfaces.

## Implementation seams

- Reuse the shared policy built from `llmratings/render.py:objective_rows`, `_select`, `_league_key` and `table`; migrate table consumption to the shared query rather than copy the policy. Keep noninteractive fixture output useful and compatible with the new eight-role/index behavior.
- Extend existing Intelligence helpers in `llmratings/rank.py` and the point/alternative callers currently in `llmratings/render.py` so the query passes the right creator-scoped included-model points. Avoid a second frontier implementation.
- `llmratings/tui.py:Session` currently owns role/objective/filter/cursor/detail state. Extract/reuse necessary semantics for the UI-independent state, with explicit transition operations usable by the web consumer. Keep existing terminal callers runnable until final web cutover, but do not add terminal provider hotkeys or a second provider state path. Remove any shared-policy duplication made obsolete by the extraction.
- Use existing fixture loading and `tests/test_cli.py` consumer tests; adapted state behavior tests may reuse `tests/test_tui.py` patterns without asserting Textual implementation details. Update runtime advice/state documentation to explain creator scope, independent grades and named-only recovery.

## Acceptance criteria

- [ ] Loading the real fixture through `fetch_all`, `identity.build` and `load_roles`, then querying one shared state yields complete Model table and Provider picks projections. The batch Model table uses that same path; tests do not exercise an unused parallel policy.
- [ ] Hand-computable edge fixtures prove direct objective-order Primary/Runner-up selection, including a dominated pick that frontier-first order would incorrectly replace. Models with multiple efforts appear only once, at the objective-selected effort; filter failure does not trigger another-effort substitution. Zero/one/two-model cases return exactly zero/one/two picks per creator.
- [ ] Selecting a creator changes Intelligence frontier/path/replacements/top-three cheaper-within-five alternatives to that creator. All providers restores global comparisons. A valid non-selected effort and points below the display filter or price floor remain in the advisory universe. Same-effort replacement remains preferred when cross-effort advice is also available.
- [ ] Scores and all existing grades for the same configurations are unchanged when creator/capability constraints change. Artificial Analysis-only models do not enter candidates/advice; source-only models remain unranked with reasons; full catalog creators and the five fixed shortcuts remain reachable even with no qualifying picks.
- [ ] Query results retain included models excluded by the active capability display filter, with their objective-selected configurations and an explicit display-filter exclusion reason, separately from models lacking qualifying measurements. Keep those filtered records available to secondary disclosures in the selected provider scope; do not relabel them as unranked measurement failures or select another effort to pass the filter.
- [ ] All state transitions in the table above preserve unrelated choices and clear stale row/detail selection. Role switches reset only the objective override in addition to stale selection; view switches preserve it. Explicit requests, not passive selection, control requested details.
- [ ] Empty intersections retain the selected state and expose named-only recovery. Unsupported Coding/Agentic objective overrides stay explicit and selected until objective recovery. Area views have no cost-frontier/replacement/cheaper-alternative claims or price-based tie.
- [ ] Query results expose selected role/index/objective/provider/filter/view and advisory scope, plus unavailable/unranked reasons. No filter/state action performs a new source acquisition. Runtime documentation and batch behavior use full visible objective/source/index labels.

## Verification

Run after implementation:

1. Update existing consumer/state behavior coverage and add focused boundary regressions where needed for direct-objective versus frontier-first picks, distinct-model/short results, creator-scoped floor/filter-free advice, grade invariance, unsupported objectives and named-only recovery. Include a model with a qualifying objective-selected configuration excluded only by the capability display filter; verify its retained configuration and filter reason are distinct from an unranked model lacking required measurements. Load real saved/temporary source payloads through fetch/identity/role loading and consume the actual shared query/state, not embedded prototype rows, dummy state objects or mocked projections. Run affected unittest cases after implementation.
2. Separately run a throwaway Python consumer that loads `.scratch/llm-ratings/fixtures/main` through the real pipeline, creates the actual shared state and prints/asserts concrete Model table rows and ordered Primary/Runner-up identities/efforts. Change provider, role, objective, filter and view; observe scoped replacement/alternative evidence, invariant grades, preserved unrelated state, cleared stale details and explicit empty/unsupported recovery. Use small labelled source-payload variations for cases the main snapshot cannot produce. This is runnable query/state proof outside the test runner; it must reach the batch-connected policy, not an unused parallel implementation.
3. Run `LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --fixtures .scratch/llm-ratings/fixtures/main --role Explorer` noninteractively to confirm the real batch table still consumes the integrated path, with attribution and no fabricated missing-data recommendation. Run `make test` and `make lint` once after all changes. Browser rendering is verified by the next task, not claimed here.

## Non-goals and authority

No browser implementation, new terminal provider controls, saved settings, extra role/objective, market-share computation, benchmark execution, new acquisition service, gateway routing, provider-level pricing, harness mapping or configuration writing. The web surface supersedes historical `p`/`v` terminal-control proposals; preserve their workflow meaning, not an obsolete shortcut requirement.

- [Spec](../spec.md)
- [Define quick selection by major model provider — approved Answer](29-provider-quick-selection.md#answer)
- [Choose AA signals and objectives for the agreed roles — approved Answer](30-role-advice-criteria.md#answer)
- [Choose human-readable cross-harness role stereotypes — approved Answer](28-name-human-readable-roles.md#answer)
- [Verify AA index cost bases and latency semantics — resolved Answer](32-aa-role-metric-bases.md#answer) and [immutable metric findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md)
- [Archived provider-workflow source](https://github.com/azarakovskiy/llm-ratings/blob/29beda7bb4872c8640d19c4b15e4d01405d134c3/.scratch/llm-ratings/assets/29-provider-quick-selection.prototype.html): workflow evidence only; its visual design and temporary role/index policy are not the product specification.
- [Redesign the provider-selection prototype for readable model advice — live Provider lens approval](33-redesign-provider-selection-prototype.md#answer), with approved [Model table](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-desktop.png) and [Provider picks](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-provider-picks.png) evidence. The captured synthesized fixture is not real provider coverage or live market advice; no prototype fixture, variant switcher or Preview-state control is an implementation source.
