# Implement the eight-role selection policy

Type: task
Status: resolved
Blocked by: 34

## What to build

Replace the five shipped role profiles and Intelligence-only row selection with the approved eight-role, selected-index policy. Deliver actual batch-consumer behavior through the existing source/identity pipeline, not an unused policy module. The same policy will feed both web comparison views.

Implementation prerequisite: [Preserve index-specific metrics and source provenance](34-preserve-index-metrics-provenance.md). Follow [the spec](../spec.md) and the resolved Answers linked below. [Add provider-scoped advice and shared selection state](36-provider-scoped-advice-state.md) consumes this policy next.

## Binding requirements

### Role profiles

Keep the editable `llmratings/roles.json` and `render.load_roles` pattern. File order is presentation order; Explorer is first and the default unless `--role` requests another profile. Preserve descriptions, prose capacity guidance including speed/context/reasoning needs, objective and floor, and add a validated selected-index field. Internal objective keys `cap`, `ppi` and `price` need not change. Capacity prose guides the user; it is not an input to weights, hidden timing rules or automatic capability filtering.

| Role, in file order | Selected index | Default objective | Task-purpose boundary |
| --- | --- | --- | --- |
| Explorer | Intelligence | Best value | Find and explain existing code/repository behavior; choosing an approach belongs to Planner. |
| Researcher | Intelligence | Best value | Verify external facts and produce sourced findings; not local repository discovery. |
| Planner | Intelligence | Highest capability | Choose an approach, decisions and actionable plan; not implementation or worker management. |
| Coder | Coding | Highest capability | Make and verify changes, including fault diagnosis, UI design, tests and documentation. |
| Reviewer | Coding | Highest capability | Independently assess changes/proposals, including security and second-opinion critique; implementing fixes is separate. |
| Coordinator | Agentic | Highest capability | Divide/delegate work, manage dependencies and combine results; not each worker's implementation. |
| Generalist | Intelligence | Best value | Mixed end-to-end work when no specialist fits; not a synonym for every narrower role. |
| Utility | Intelligence | Lowest qualifying price | Bounded auxiliary outputs such as titles, commit messages, classification and straightforward transformations. Small output does not imply low capability; faithful summarization/memory extraction are not automatically trivial. |

- Roles describe purpose, not cheap/fast/thorough preferences, fixed effort, context or vision. Do not add Debugger, Designer, Security Reviewer, Test Writer, Documentation Writer, Advisor or other specialist roles.
- Keep user-edited role profiles supported through the existing one-file seam; validate unknown indexes/objectives and malformed profiles with an actionable startup error. A recognized but unsupported index/objective combination is an unavailable-objective result, not a malformed-profile fallback.
- `--role` uses the new names and unknown names exit 2. Migrate existing callers/defaults/tests; do not retain the old Chores/Generic/Orchestrator names as compatibility aliases.

### Required data and objective support

- Choose one measured effort per model from that role's selected Artificial Analysis index. Never fix effort by role, choose another index for missing data, or mix one effort's score with another effort's cost.
- Intelligence eligibility requires a finite selected Intelligence score and finite non-negative matching Intelligence benchmark task cost at that effort, even for Highest capability. Best value additionally requires a strictly positive matching cost and a usable finite quotient. A published zero cost can qualify for Highest capability or Lowest qualifying price, but never provides a Best value ratio. Missing/non-finite required values do not qualify.
- Coding and Agentic support Highest capability only, requiring a finite selected-index score and no cost. Neither Intelligence task cost nor token list prices, blended prices, benchmark-run costs or an invented token mix supply matching area-index cost. Area selection has no price tie, value/price objective, cost frontier, replacement, cheaper alternative or cross-workload value claim.
- All three objective choices remain inspectable by later consumers. A Coding/Agentic Best value or Lowest qualifying price override is retained and returns an explicit unavailable-objective state; never revert it, switch index, relax constraints or fabricate a denominator.
- Preserve the inclusion boundary of at least one DeepSWE or Terminal-Bench rating. Extra normalized Artificial Analysis rows do not admit its unrated long tail as recommendations. Keep source-only and other included models with no qualifying configuration reachable as unranked records with a specific reason, rather than silently discarding them or recommending fabricated data.
- If no model qualifies, the consumer shows `No qualifying configuration` with the role and active constraints (and provider when provider selection is added). Missing timing is not an eligibility failure.

### Exact objective comparisons

Use these same complete keys both to select a model's effort and to order the selected models. Do not rely on fixture order, incidental sort stability or frontier section order for a tie.

| Index/objective | Keys, in order |
| --- | --- |
| Intelligence / Highest capability | Intelligence score descending; matching Intelligence task cost ascending; lower effort; canonical model key |
| Intelligence / Best value | Intelligence score / matching Intelligence task cost descending; Intelligence score descending; matching Intelligence task cost ascending; lower effort; canonical model key |
| Intelligence / Lowest qualifying price | Qualifying matching Intelligence task cost ascending; Intelligence score descending; lower effort; canonical model key |
| Coding / Highest capability | Coding score descending; lower effort; canonical model key |
| Agentic / Highest capability | Agentic score descending; lower effort; canonical model key |

Effort order is the existing `low < medium < high < xhigh < max`. Display full effort labels, including Extra high and Maximum. Timing never filters, weights, orders or breaks ties. Delete the former speed-grade tie-break for Lowest qualifying price and any helper made obsolete by its removal. Different Artificial Analysis indexes and independent DeepSWE/Terminal-Bench ratings must never be averaged into one score.

### Grades, floor and advisory boundaries

- Artificial Analysis capability grades use every finite scored model × measured-effort configuration for the selected index in the refresh, across efforts. Compute this reference population before objective eligibility, per-model selection, provider constraints or capability display filtering; do not require a price to contribute a score. Do not shrink the reference set to ranked/included models or re-bin per effort/creator. A missing selected-index score does not borrow another index's grade.
- Reuse `tier.grades` and its distinct-value method: equal values never split; small sets may populate fewer than five grades. DeepSWE and Terminal-Bench capability grades remain source-independent, at their existing effort reference sets; Terminal-Bench first collapses best agent per model × effort with the existing recency tie-break.
- Apply inclusive capability grade ≥ 2 only for Lowest qualifying price, including a manual override on any Intelligence role, not just Utility. Highest capability and Best value are floor-free. Preserve the role floor field/default pattern; the shipped approved profiles use 2. The capability display filter (all, grade 5, grade ≥ 4) is a separate later step using the selected index's grade, not a reason to choose a different effort.
- Preserve the existing independent value/speed/price grade populations over their valid selected-row axes before provider or capability display constraints. Do not change these into creator-relative bins, mix source-run costs into price, or use area-score/Intelligence-cost quotients. Their available Intelligence-derived evidence remains distinct from area capability.
- Intelligence advisory comparisons remain over all included models' valid scored/priced efforts, independent of the price floor and capability display filter. Preserve frontier, same-effort-first strict replacement with cross-effort fallback, and up-to-three cheaper alternatives within 5 Intelligence points sorted by price. Cost-based advice is unavailable, not reconstructed from Coding/Agentic scores, for area roles.
- OpenRouter token share is display-only and cannot change any score, grade, eligibility, objective or tie. Missing or unverified share stays unavailable. Published timing is explanatory only and remains unavailable independently when missing.

### Consumer result and labels

- Expose selected configuration, selected-index raw score/grade, objective metric where supported, source-specific ratings and reasons for unranked/unavailable results through the actual shared row policy used by `render.py`. Keep noninteractive batch output working while the later web tasks are built; do not add new TUI features.
- Full visible labels are Highest capability, Best value, Lowest qualifying price, Artificial Analysis, Intelligence score, Coding score, Agentic score, Benchmark task cost and Capability per dollar. Do not expose `AA`, `cap` or `ppi` as interface labels. A capability-per-dollar number is Intelligence points per matching benchmark-task USD, not predicted production-task return.
- Explain profile indexes as published-score proxies: Coding is not measured review accuracy; Agentic is not proof of multi-agent coordination; Intelligence is not universal task success. Preserve the factual uncertainty about current complete Coding/Agentic formulas. Do not substitute the separate Coding Agent Index.

## Implementation seams

- Extend `llmratings/roles.json` and `llmratings/render.py:load_roles`, `_select`, `objective_rows` and `_league_key` or their replacement shared functions. Reuse `llmratings/identity.py` measured efforts/data contract, `llmratings/tier.py:grades` and `llmratings/rank.py` Intelligence machinery.
- Migrate batch and existing session callers to the one policy result; do not create one ranking implementation for batch and another for later web. Module/helper names are not prescribed: choose the smallest coherent shared seam, without a plugin framework or a forwarding-only layer.
- Reuse `tests/test_cli.py`, its fixture/temporary-payload helpers and `LLM_RATINGS_ROLES` seam. Update runtime role/objective documentation and obsolete tests so they describe the new supported catalog, metric bases and defaults. Web cutover and final ADR runtime supersession belong to [Complete inline evidence and cut over to the web interface](38-inline-evidence-web-cutover.md).

## Acceptance criteria

- [x] All eight profiles load in the exact approved order with selected index/default, meaningful purpose/capacity prose and no old-name aliases. Default batch output is Explorer/Intelligence/Best value; `--role Coder`, `--role Coordinator` and `--role Utility` use the exact approved policy. A valid edited role file changes consumer behavior; malformed fields fail clearly.
- [x] A real multi-effort fixture selects one configuration per included model under every supported objective and orders models using every comparison key above. Regression cases distinguish score, ratio, cost, effort and canonical-key ties both within and across models. Changing only published timing never changes eligibility, effort, order or grades used for capability.
- [x] Intelligence finite-score/missing-cost, negative-cost, zero-cost and non-finite cases have the exact objective eligibility above. Area score without cost qualifies; missing area score with a valid Intelligence score does not. Unsupported area overrides remain selected and explicitly unavailable.
- [x] Capability grades match a hand-computed distinct-value population across efforts for each selected index, including finite scored configurations without eligible cost and those outside recommendation inclusion. Equal values share grades. DeepSWE/Terminal-Bench grades and best-agent collapse retain their prior independent reference sets.
- [x] A grade exactly 2 passes Lowest qualifying price and grade 1 does not. The same grade-1 model can qualify for Highest capability/Best value; explicit display filtering remains separate. Value/speed/price grade sets do not shrink under display filters.
- [x] Batch consumers expose unranked reasons, all-unqualified and unsupported-objective states without a fabricated score, cost, alternative or recommendation. Source-only rows stay accessible and Artificial Analysis-only models do not enter the recommendation universe.
- [x] Intelligence frontier/replacement/alternative behavior remains floor-free and filter-free; Coding/Agentic consumers show direct score-order advice without cost-frontier or cheaper-alternative claims. Full labels and role-proxy limitations appear in runtime documentation/consumer explanations.

## Verification

Run after implementation:

1. Update the affected consumer contracts in `tests/test_cli.py`; add focused regressions where existing coverage lacks the uncertain boundaries above, especially exact ties, finite/zero costs, cross-effort grade populations, the inclusive floor and unsupported area objectives. Load real saved/temporary source payloads through `fetch_all`/`identity.build` and `load_roles`, then consume actual shared query/render output with hand-computable selected efforts/order. Do not mock policy results, assert only profile text or test a detached scoring copy. Run affected unittest cases after implementation.
2. In a non-TTY shell run `LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --fixtures .scratch/llm-ratings/fixtures/main --role Coder`, then repeat for Explorer, Coordinator and Utility. Expect the named selected-index policy and full objective label, real source attribution, selected measured efforts, independent missing-source states and no area cost-based advice. Fixture results are historical/synthetic test evidence, not current market advice.
3. Run `make test` and `make lint` once after all edits. Keep deterministic expected outputs/selected identities and behavior transitions, not a snapshot pinned to obsolete terminal padding or source-text checks.

## Non-goals and authority

No new provider controls, browser rendering, TUI provider additions, role-specific benchmark, weighted fit score, fixed-effort role, speed objective, saved preferences, harness mapping, routing or config export. Do not broaden sources or infer missing same-index task costs.

- [Spec](../spec.md)
- [Choose human-readable cross-harness role stereotypes — approved Answer](28-name-human-readable-roles.md#answer)
- [Choose AA signals and objectives for the agreed roles — approved Answer](30-role-advice-criteria.md#answer)
- [Verify AA index cost bases and latency semantics — resolved Answer](32-aa-role-metric-bases.md#answer) and [immutable metric findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md)
- [Define quick selection by major model provider — approved Answer](29-provider-quick-selection.md#answer): provider selection does not change score/grade reference populations.
- [Redesign the provider-selection prototype for readable model advice — live Provider lens approval](33-redesign-provider-selection-prototype.md#answer): full visible labels, retained unavailable states and secondary policy explanations.
- [Roles replace categories ADR](../../../docs/adr/0002-roles-replace-categories.md): preserve role profiles, objective-selected efforts and floor-free advice; its five-role/unchanged-data-model clauses are superseded by the resolved spec, not grounds to retain obsolete behavior.

## Answer

Resolved 2026-10-31 on `implement/t35`, based on integration prerequisite
`053812a`. The real batch and existing session consumers now use the approved
eight profiles and one selected-index policy. No provider controls, web
surface, extra source, timing objective or compatibility role aliases were added.

### Downstream contract

- `roles.json` remains the editable file-order catalog. Profiles declare
  `index` as `intelligence`, `coding` or `agentic`, plus the existing objective,
  purpose/capacity prose and floor (default 2). Startup rejects malformed
  fields and duplicate names; a recognized area/value or area/price profile
  remains valid and reports an unavailable objective.
- `render.query(ds, role, objective=None, min_grade=None)` is the shared
  consumer seam replacing `objective_rows`. It returns `index`, `objective`,
  `status`, `reason`, `rows`, `unranked`, `excluded` and `points`.
  Status is `ok`, `no_qualifying` or `unavailable_objective`.
- `rows` contains one actual selected `configuration` (`Rating`) per eligible
  model, in the complete **direct objective order**. Each row has identity,
  measured `effort`, selected-index `score`/`grade`, independent `dsw`/`tb`
  grades, selected-effort source `ratings`, all model `measurements`, timing,
  and the supported Intelligence `cost`/`ppi`/value/price fields.
  Coding/Agentic cost/value/price/frontier/replacement fields stay `None`.
  Source-only and other unqualified identities remain in `unranked` with
  their measurements and a specific reason, without a fabricated selection.
- Capability reference populations include all finite selected-index measured
  configurations across efforts, including Artificial Analysis-only identities
  and cost-ineligible rows. The price floor is inclusive and applies only
  under Lowest qualifying price; display filtering happens after effort
  selection and independent selected-row axis grades, with exclusions kept
  separate from measurement failures.
- Intelligence `points` spans every valid scored/non-negative matching-cost
  effort of included models, independent of floor/display constraints.
  Strict-frontier ties retain identical score/cost points, and negative
  finite scores work. Same-effort-first strict replacements and the three
  cheapest alternatives within 5 Intelligence points retain their prior
  boundaries. Area indexes have no cost-based advice.
- `table` still returns `(lines, display_rows)`. Its Intelligence sections are
  frontier-first, not provider-pick order; area rows use direct score order.
  `detail` keeps full effort/source/metric labels, independent source ranks,
  missing measurements, timing distinctions, context and proxy limitations.
  Later provider consumers must start from `query`, not frontier section order.

Runtime policy/source documentation is updated in the fixture README. Historical
five-role/data-model ADR clauses remain superseded by the approved spec; final
web runtime supersession remains assigned to ticket 38.

### Exercised verification

- Affected consumer command:
  `PYTHONPATH=tests python3 -m unittest test_cli.SelectionPolicy test_cli.RolesFile test_cli.SavedPolicy test_cli.TerminalBench test_cli.SourceContract test_tui`
  ran **65 tests**. It found one stale test expectation: Kimi's new
  cross-effort Intelligence grade 4 differs by two from its independent
  DeepSWE Maximum grade 2, so disagreement must remain visible despite
  missing Terminal-Bench. The expectation was corrected without changing
  the measured grading behavior.
- `make test`: **81 tests passed**, including all affected cases and the
  corrected missing-source/disagreement regression. This replaces obsolete
  wording/terminal-padding checks with selected identities, exact tie keys,
  real-source data boundaries and observable state transitions.
- `make lint`: **exit 0**. Each repository command ran once after code/test
  implementation.
- Separate non-TTY shell invocations of
  `LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --fixtures .scratch/llm-ratings/fixtures/main --role NAME`
  for Coder, Explorer, Coordinator and Utility all returned **exit 0**.
  Coder selected Sol **Extra high / Coding 78.3**; Coordinator selected
  Opus **Maximum / Agentic 55.3**; Explorer used Intelligence/Best value
  with Luna **Low**; Utility used Lowest qualifying price with Luna
  **Extra high / grade 2**. Full objective/index labels, Artificial Analysis
  attribution, independent missing-source states and source-only reasons
  were observed. Area tables contained no cost frontier or value columns.
- `git merge --no-edit integration/role-advice-web`: **Already up to date**.
  Read-only independent review found no concrete correctness or acceptance
  gap; it ran no checks.

All acquisition evidence here is saved historical/synthetic fixtures or the
local HTTP test origin, not a new authenticated source response, current
market recommendation, matching area-index cost or verified token-share feed.
