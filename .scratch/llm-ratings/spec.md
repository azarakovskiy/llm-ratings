# LLM Ratings — role advice and provider-selection web spec

Status: ready-for-agent
Amended: 2026-10-31

## Scope and authority

This is the planning handoff for [LLM Ratings: human-readable agent roles and provider quick selection](map.md). It specifies the actual web interface, not another prototype. This amendment does not change product code or merge prototype assets.

The resolved decisions govern this spec:

- [Choose human-readable cross-harness role stereotypes](issues/28-name-human-readable-roles.md#answer): role names, purposes and boundaries, with the immutable cross-harness survey evidence.
- [Define quick selection by major model provider](issues/29-provider-quick-selection.md#answer): both advice views, shared provider selection, distinct-model picks and provider-scoped comparisons.
- [Choose AA signals and objectives for the agreed roles](issues/30-role-advice-criteria.md#answer): selected indexes, objectives, grades, eligibility, exact comparisons and timing policy. Its Answer supersedes its earlier proposals.
- [Verify AA index cost bases and latency semantics](issues/32-aa-role-metric-bases.md#answer): source facts and their limits. The [immutable metric findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md) retain dated primary-source citations and schema paths; unresolved source facts are not product guarantees.
- [Redesign the provider-selection prototype for readable model advice](issues/33-redesign-provider-selection-prototype.md#answer): **Provider lens**, approved by the live user on 2026-10-31. The [recorded live approval](issues/33-redesign-provider-selection-prototype.md#2026-10-31--live-visual-approval), [captured prototype commit](https://github.com/azarakovskiy/llm-ratings/commit/dd44964), [Provider lens Model table](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-desktop.png) and [Provider lens Provider picks](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-provider-picks.png) are the visual handoff.

Earlier source, identity, independent-grade and Intelligence-comparison decisions remain binding where these later decisions do not supersede them. In particular, preserve the DeepSWE/Terminal-Bench inclusion boundary and existing source acquisition seam. The former five-role defaults, Intelligence-only policy, speed-based price ties, terminal layouts/keybindings and prohibition on web surfaces are superseded.

The web surface supersedes [Textual for the interactive TUI](../../docs/adr/0001-textual-for-interactive-tui.md) as the target product interface. [Roles replace categories](../../docs/adr/0002-roles-replace-categories.md) still supplies configurable profiles, objective-selected efforts and floor-free advisory comparisons; its five-role catalog and unchanged-data-model consequences no longer describe this multi-index plan. Runtime documentation and obsolete terminal code are migrated during the build, not by rewriting historical decision records here.

## Problem statement

Published model ratings, reasoning-effort results and prices use different sources and units. The user needs current, auditable advice about which **model and measured effort** to use for a task, including within one creator's catalog. A cheaper configuration may be near an expensive model's Intelligence score while the expensive model still wins on highest capability. Show that tradeoff where matching measurements support it; do not turn incompatible costs, missing scores or benchmark proxies into claims about real task performance.

## Solution

A locally run web interface reuses the existing Python acquisition, identity, grading and comparison pipeline. Each live launch fetches the current three rating sources and best-effort enrichment once. Role, objective, capability and provider controls operate on that same refresh; they do not fetch another data moment for each click.

The initial **Model table** compares every eligible included model at its objective-selected effort. **Provider picks** uses the same selection policy to show up to two distinct models per creator. The approved Provider lens puts creator navigation at the left, task controls above aligned comparisons, and evidence inline on request. Linked sources, fetch date, selected index and comparison scope make the advice auditable.

This is advice only: no harness config export, integration, selector translation, config writes, request routing, inference or benchmark execution.

## User stories

1. As a user, I can launch the local web interface and compare freshly fetched ratings without opening multiple leaderboards; a missing key or failed rating source gives a named setup/source error rather than partial advice.
2. I can choose Explorer, Researcher, Planner, Coder, Reviewer, Coordinator, Generalist or Utility by purpose, and see the role's purpose, selected index and default objective.
3. I receive one measured effort per recommended model, not one fixed effort for every model in a role. Every pick has its selected score, applicable objective numbers, linked source and fetch date.
4. I can choose Highest capability, Best value or Lowest qualifying price and return explicitly to the role default. A role change resets the objective override; an unsupported objective remains selected and explains why it is unavailable.
5. I can filter by all capability grades, grade 5, or grade 4 and above on the selected index, independently of the Lowest qualifying price floor.
6. I start with All providers and Model table. I can choose a fixed creator shortcut or any creator in the full chooser, including one with no currently eligible models.
7. I can switch between Model table and Provider picks without losing provider selection, capability filter or the active objective.
8. I can compare a creator's Primary and Runner-up as distinct models, not two efforts of one model. A single qualifying model gives one pick with a reason for the missing runner-up.
9. Selecting a creator scopes candidates and Intelligence comparison advice to that creator without changing scores or relative grades. The visible scope prevents a provider-local frontier from looking global.
10. In Intelligence advice, I can distinguish frontier and dominated configurations, follow the cross-effort frontier path, inspect same-effort-first replacement advice, and read score/task-cost changes against the preceding row within a section.
11. I can inspect independent DeepSWE, Artificial Analysis and Terminal-Bench scores and grades rather than a blended rating. Missing effort/source results stay unavailable; Terminal-Bench best-agent collapse does not inflate model counts.
12. I can distinguish a matching Intelligence benchmark task cost from token list prices and other benchmarks' run expenditures. Coding/Agentic advice never pretends that an Intelligence cost measures area-index value or cheapness.
13. I can compare published time to first answer token, including thinking, separately from output tokens per second. Missing timing does not remove or reorder a recommendation.
14. A visible Details action opens model evidence inline: measured configurations, selection rationale, source-specific scores/grades/ranks, source links, prices with units, timing, catalog metadata and applicable Intelligence advice.
15. I can inspect up to three cheaper Intelligence configurations within five points below the opened score, sorted by task cost and scoped to the provider selection; this is not the Provider picks runner-up rule.
16. Unranked source-only or insufficient-data models remain reachable with reasons. If nothing qualifies, the interface names my role, provider and constraints instead of changing them silently.
17. Explicit All providers, clear capability filter and supported-objective recovery actions change only the named constraint.
18. How picks work explains defaults, grade reference sets, eligibility, comparison keys, index-proxy and source-formula limits, cost matching and timing without crowding the main comparison.
19. Open- and closed-weight models are both eligible under the source inclusion rule. Prices, scores and grades change with the current refresh, not a vendored market snapshot.
20. I can add a role by editing the existing checked-in role catalog, without adding a second taxonomy or a UI settings editor. Context/modality metadata remains available in model evidence when supplied.
21. I can read and operate both views and expanded evidence on a narrow screen, with keyboard-visible controls and no page-level horizontal overflow or reduced text size.
22. If 30-day OpenRouter token share is unavailable, I see that limitation rather than zero, an invented share or a popularity-based recommendation.

## Implementation requirements

### 1. Runtime and acquisition seam

- Reuse the existing Python program and modules: `llmratings/fetch.py`, `identity.py`, `tier.py`, `rank.py`, the reusable policy currently in `render.py`, and `roles.json`. Separate reusable advice data from terminal-formatted text only where the web consumer requires it; do not build a second ranking engine in browser JavaScript.
- Provide a documented explicit local web entry, `python3 -m llmratings --web`, accepting the existing `--fixtures DIR` and `--role NAME` seams. Bind locally and report the URL. Keep source credentials on the Python side, never in browser assets, responses or errors. No hosted deployment or authentication product is required.
- `make run` becomes the normal web launch at cutover. Preserve the useful existing noninteractive batch path through module invocation without `--web`; it consumes the same advice policy, not a frozen five-role implementation. Unknown role names remain a clear usage error with exit status 2.
- Remove the obsolete Textual interactive path, its exclusive dependency and obsolete terminal-only tests/callers at cutover. Historical keybindings may be optional web aids, never requirements or substitutes for visible controls. There is no parallel terminal-UI build in this plan.
- Use the least machinery needed to serve a real browser interface from the existing pipeline. No frontend framework is prescribed by the visual approval; it does not authorize a new dashboard or a rewrite of acquisition.
- Fetch once on each live run, with no cache, saved preferences, automatic refresh, scheduler or retry service. A new run recomputes the dataset and grades.

### 2. Sources, freshness and provenance

- **DeepSWE v1.1**: `GET https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`, without authentication. Retain model/effort, pass@1, confidence interval and available raw cost/token/duration/task-count evidence. Its benchmark-run expenditure is not the task-price basis.
- **Terminal-Bench v2.1**: enumerate `https://api.github.com/repos/harbor-framework/terminal-bench-2-1/contents/leaderboard/submissions`, then fetch the listed JSON payloads through their download URLs. Retain model, measured effort, agent, accuracy, confidence interval, date and available raw expenditure/duration/token evidence. Existing high/extra-high/maximum-only coverage is a missing-effort case, not a reason to copy another effort's score.
- **Artificial Analysis**: use `https://artificialanalysis.ai/api/v2/language/models/free?page_size=200`, the existing pagination contract and `x-api-key` from `LLM_RATINGS_AA_API_KEY`. Use the API, not scraping. Retain available Intelligence, Coding and Agentic scores, index/version evidence when supplied, creator, per-effort Intelligence benchmark task cost, token list prices and the distinct published performance fields. Do not assume every free-tier row supplies every metric.
- A missing Artificial Analysis key produces a clear setup error and nonzero exit before serving advice. Any of the three rating sources failing acquisition or payload parsing produces a clear source-named error and nonzero exit, with no silent partial advice. The browser launch must not convert a startup failure into empty successful data.
- **OpenRouter catalog enrichment**: `GET https://openrouter.ai/api/v1/models`, best effort. Preserve available context length and input/output modalities in model evidence; failure does not invalidate the three-source advice. Use the documented `canonical_slug → id → alias` identity hop where supplied, not a guessed derivation of canonical identity from an endpoint ID.
- **30-day OpenRouter token share** is display-only. The historical plan uses daily ranking data, sums a model's variants/dated snapshots across the actual 30-day window, has no effort split, and includes `other` in the denominator. Access/payload coverage and 30-day top-50 presence were **not verified** in the available historical record. Preserve that source limitation: a value may be shown only with verified coverage, denominator, join, window and source/date. Missing access or insufficient evidence means **Unavailable**, not zero or inferred market absence. Do not invent credentials, a working authenticated endpoint contract or a claim that coverage is settled. This uncertainty never permits share-based eligibility, ranking, ties or grades and never blocks the verified rating-source advice.
- Keep source URLs and fetch timestamps with the refresh and its measurements. Put linked **Artificial Analysis** attribution and fetch date beside the comparison; expose each source's URL/date in evidence. A fetch date is not a claim that all source measurements were published that day.
- Use the existing offline fetch boundary: `--fixtures` supplies saved DeepSWE, Artificial Analysis, Terminal-Bench and OpenRouter responses with no network. Fixture source dates and synthetic data must be explicit. The approved prototype's fictional names, synthesized rows and missing creator coverage are not market facts.

### 3. Identity, inclusion and configurations

- Canonical model identity remains the Artificial Analysis **base slug**, display name and creator. Artificial Analysis UUIDs identify effort variants and are not stable cross-effort model keys. Preserve the checked-in aliases joining DeepSWE/Terminal-Bench names to canonical models; an unmatched rated model keeps a source-only identity instead of blocking acquisition.
- Preserve the existing inclusion rule from [Model identity & pricing](issues/06-model-identity-and-pricing.md#answer): at least one DeepSWE or Terminal-Bench rating. Do not admit the Artificial Analysis-only long tail as recommendation candidates. No additional license, popularity or numeric inclusion floor; both open- and closed-weight models remain in scope.
- Retain all source rows. A configuration is a model at one **measured** effort with its source/index ratings, matching cost where established, available timing and provenance. Missing source/index/effort data remains missing; no score or effort substitution, automatic-effort estimate or inferred measurement.
- Collapse Terminal-Bench agents to the best score per model × effort for display, breaking score ties by recency. Grade that collapsed population, not each agent as another model. Do not average or merge the independent rating sources.
- Token list input/output prices, with their source units, remain separate from Intelligence benchmark task cost. DeepSWE/Terminal-Bench run costs and OpenRouter gateway prices never become the recommendation denominator.
- Use full visible effort names: **Low**, **Medium**, **High**, **Extra high**, **Maximum**, in that order for effort ties. Internal effort/API spellings may remain unchanged.

### 4. Role catalog and supported objectives

Roles describe task purpose, not cheap/fast/thorough modes, context needs, reasoning effort or vision. Keep the existing single checked-in `llmratings/roles.json`, file-order navigation and profile descriptions/capacity guidance. Add the selected index to the profile contract and migrate every consumer. Internal objective keys `cap`, `ppi`, `price` can remain internal; this is not an identifier-migration project.

| Role | Purpose and boundary | Selected Artificial Analysis index | Default objective |
| --- | --- | --- | --- |
| Explorer | Find and explain existing code/repository behavior; not implementation planning. | Intelligence | Best value |
| Researcher | Verify external facts and produce sourced findings; not a local repository map. | Intelligence | Best value |
| Planner | Choose an approach and produce decisions/actionable plans; not implementation or worker management. | Intelligence | Highest capability |
| Coder | Make and verify changes, including fault diagnosis, UI, tests and documentation. | Coding | Highest capability |
| Reviewer | Independently assess changes/proposals, including security and second-opinion critique; fixes are separate work. | Coding | Highest capability |
| Coordinator | Divide/delegate work, manage dependencies and combine results; not each worker's implementation. | Agentic | Highest capability |
| Generalist | Mixed end-to-end work when no specialist fits. | Intelligence | Best value |
| Utility | Bounded auxiliary output such as titles, commit messages, classification and text transformations. Small output does not imply trivial capability needs; faithful summarization/memory extraction is not automatically utility work. | Intelligence | Lowest qualifying price |

- These are the bundled roles and order. Retain descriptions and capacity guidance, including speed/context guidance as prose; guidance is not an undeclared scoring/filter rule. Existing user-edited profiles remain a single-file mechanism and must declare a supported index/objective with clear validation errors, not silently inherit a different index.
- The bundled capability floor is **2**, active only under Lowest qualifying price, including an Intelligence role's manual override to that objective. Highest capability and Best value have no role floor. Do not add separate Debugger, Designer, Security Reviewer, Test Writer, Documentation Writer or Advisor defaults.
- Intelligence supports **Highest capability**, **Best value** and **Lowest qualifying price**. Coding and Agentic support **Highest capability only**. Keep all objective names visible/inspectable; selecting an unsupported area-index objective shows its explicit unavailable state rather than removing the user's choice or substituting a proxy.
- These scores are **role-selection proxies**, not validated performance on every role. Coding is not a measured review-accuracy score; Agentic is not proof of multi-agent coordination quality. The complete current Coding/Agentic composite formulas remain a documented source gap. The separate Coding Agent Index and its costs are not substitutes.
- Vision is a capability tag, not another role or a ranking axis. Available modalities/context are evidence; this plan does not add a vision table column or an extra filter/editor product.

### 5. Eligibility, effort selection and deterministic order

Select one configuration **within each model**, then use the same comparison keys **across selected models**. Never choose one fixed effort for a role.

| Index/objective | Required data at the measured effort | Ordered comparison keys |
| --- | --- | --- |
| Intelligence / Highest capability | Finite Intelligence score and finite, non-negative matching Intelligence benchmark task cost. | Score descending; matching task cost ascending; lower effort; canonical model key. |
| Intelligence / Best value | Finite Intelligence score and finite, strictly positive matching Intelligence benchmark task cost. | Score divided by matching task cost descending; score descending; matching task cost ascending; lower effort; canonical model key. |
| Intelligence / Lowest qualifying price | Finite Intelligence score and finite, non-negative matching task cost; inclusive capability grade ≥ 2 for bundled roles. | Qualifying matching task cost ascending; score descending; lower effort; canonical model key. |
| Coding or Agentic / Highest capability | Finite score on that selected index; no matching task cost is required or established. | Selected score descending; lower effort; canonical model key. |

- Remaining exact ties follow the keys above, not fetch/input order. Use these same keys in provider picks, not a separate provider score or price-diversity heuristic.
- Zero matching task cost can qualify for Intelligence Highest capability/Lowest qualifying price, but never gives a finite Best value ratio. Missing/non-finite required values do not qualify. Do not manufacture a denominator from token prices, a token mix or another benchmark's expenditure.
- Timing and throughput **never** filter, weight, rank or break ties. Remove the former output-speed tie-break for Lowest qualifying price. Missing timing cannot exclude an otherwise eligible configuration.
- No qualifying effort leaves that included model **unranked with a reason**. Do not give a source-only model an Artificial Analysis score or select another index. The whole candidate set failing produces **No qualifying configuration**, naming role, provider and active constraints.
- Unsupported Coding/Agentic Best value or Lowest qualifying price produces an **unavailable-objective state**, not normal empty results, a cost frontier or a silent fallback. Retain the selected objective until the user changes it.
- The capability display filter applies to each model's objective-selected configuration, not as another effort-selection rule. Its choices are **All capability grades**, **Grade 5**, **Grade 4 and above**, using the role's selected-index grade. This filter is separate from the price objective's inclusive floor.

### 6. Grades and reference populations

- Keep the existing distinct-value 1–5 method: sort an axis's unique valid values; equal values share a grade and are never split. For a higher-is-better axis, descending distinct value at zero-based position `i` among `n` values has grade `6 - (floor(i * 5 / n) + 1)`. The reverse price axis makes 1 cheapest. Empty axes remain unavailable; small sets can populate fewer than five grades. Recompute on every refresh.
- **Artificial Analysis capability grades** use **all scored model × effort configurations for the selected index in the refresh**, across efforts and before provider/capability constraints. An Intelligence grade is not a Coding/Agentic grade. Do not divide that reference population into effort groups or re-bin within one creator.
- **DeepSWE and Terminal-Bench capability grades** remain independent within each source's rated effort population; Terminal-Bench uses best-agent-collapsed rows. A missing score/effort shows **—**, not another source's grade.
- **Value grade** uses Intelligence score / matching positive Intelligence task cost; **output-speed grade** uses the published output tokens per second; **price tier** uses matching Intelligence task cost with 1 cheapest. Preserve their existing independent valid reference sets from the unfiltered role-selected model population. Compute them before provider and capability-display constraints, so selecting one creator cannot promote its grades. No cost-based value/price grade is inferred for Coding/Agentic advice.
- All providers restores global comparisons, not new grades. Provider selection, an empty intersection or a narrow capability display filter never changes a score or its grade. Other sources' ratings and benchmark disagreements are not averaged away.

### 7. Provider selection and shared session state

- Provider means the model **creator**, not an API gateway. Select exactly one creator or **All providers**. A new session starts with the first catalog role (Explorer), its default objective, All capability grades, All providers and Model table, with no open model details.
- Keep fixed visible shortcuts for **OpenAI, Anthropic, Google, DeepSeek and xAI**, plus All providers and a full creator chooser. The list is a curated product choice, not a rating/share threshold or an eligibility-derived list. Every loaded catalog creator remains reachable; do not hide creators because the current role/filter has no picks.
- Role changes retain provider and capability filter but reset the objective override to the new role's default. View changes retain role, provider, capability filter and active objective. Provider/capability changes do not reset the objective. Controls are session state, not saved preferences or harness configuration.
- Role, objective, view, provider or capability changes reset stale row/detail selection. Opening evidence is a deliberate Details action, not a passive row-selection side effect.
- **All providers** clears only the provider constraint. **Clear capability filter** changes only that filter. A supported-objective action changes only the objective; **Use role default** resets only its override. Recovery never silently changes another constraint.
- Both views consume one policy/query path. Do not derive picks from already-sectioned table output or compute another set of scores in the browser.

### 8. Intelligence comparison advice and the two views

#### Common comparison scope

Provider selection constrains candidates **and**, for Intelligence, the frontier/path/replacements/detail alternatives. With one creator selected, compare only that creator's included models; All providers restores global comparisons. Show the selected creator and comparison scope beside the result.

The advisory universe spans every valid Intelligence score/matching-cost configuration of included models in that provider scope, across measured efforts. Preserve its **floor-free and display-filter-free** behavior: neither Lowest qualifying price's role floor nor the capability display filter removes those comparison points. They constrain displayed candidates, not the available replacement evidence. Invalid/missing measurements never become comparison points.

Coding/Agentic advice has no matching cost frontier, replacement arrows, price-based ties or cheaper alternatives. Token list prices or an independently published Intelligence cost in evidence are not cost advice for those indexes.

#### Model table

- Initial view, one row per eligible model at the active objective's selected effort, restricted by provider selection and capability display filter.
- For Intelligence, a configuration is on the **frontier** if no other configuration has a score at least as high at a task cost at most as large, with at least one strict improvement. Render a **Frontier** section before **Dominated**, with the active objective's complete deterministic order inside each section. This section order is not the direct order used for provider picks.
- Retain the cross-effort frontier path. For a dominated configuration, prefer a strict **same-effort replacement**; use cross-effort fallback only when none exists. Within that machinery, maximize score gain, then saving. Show replacement model, effort, score gain and task-cost saving with an explicit provider/global scope.
- Show **Score change** and **Task cost change** against the preceding visible row within each Intelligence section; the first row has no previous-row delta. No near-tie threshold/marker replaces those numbers.
- For Coding/Agentic, show the directly ordered selected-score comparison without false Frontier/Dominated labels, task-cost deltas or value columns.
- Keep model, selected full effort name, selected-index score and grade aligned. Show applicable Intelligence benchmark task cost/capability per dollar and the main published latency/throughput distinctly. Independent source grades, price/value/speed tiers and extra source evidence may be secondary/inline rather than a terminal-width stack repeated in every row.
- Keep excluded/unranked included models and their reasons reachable in a labelled secondary area, separate from ranked recommendations. Do not silently drop source-only evidence or label a display-filter exclusion as a measured failure.

#### Provider picks

- For each selected creator, apply the same eligibility, per-model effort selection and active capability display filter, then take the first two **distinct models in direct objective order** as **Primary** and **Runner-up**.
- Primary/Runner-up is an aligned comparison shelf: model, selected effort, selected-index score, grade and applicable objective metric are easy to compare. Supporting timing and non-primary metrics may move into Details instead of becoming repeated stacks.
- A globally dominated Intelligence model may be a creator's primary or runner-up. Primary is not a claim of global frontier membership. The runner-up is not another effort of the primary and is not the specially chosen cheaper alternative from model evidence.
- Creators with picks precede a labelled secondary disclosure for creators without qualifying models; retain each reason. Selecting an empty creator still shows the full explicit empty state and recovery actions.
- One eligible model yields one Primary with **No qualifying runner-up** explained. Zero gives the explicit empty state. Never repeat a model, substitute another creator, widen eligibility or relax a constraint without a named user action.

### 9. Approved Provider lens presentation and visible controls

- **Left creator navigation**: All providers, five fixed creator shortcuts and the full chooser. Main header: eight-role chooser, objective and capability filter, active purpose and selected index. Keep selected creator/comparison scope visible next to results.
- **Primary comparison area**: visible **Model table / Provider picks** tabs, aligned model comparisons and the aligned Primary/Runner-up shelf. Preserve readable density, humanist sans-serif text, tabular numeric alignment and restrained cool neutral surfaces with dark readable text. No equal-weight debug panels, instruction walls or decorative dashboard.
- **Useful accents**: cobalt denotes current selection/focus; teal denotes frontier or primary-pick priority; amber denotes unavailable advice/recovery. Carry every meaning in text as well as color, especially provider-local versus global scope.
- Required visible controls: role, all three objectives and role-default recovery, capability filter, both views, creator shortcuts/full chooser/All providers, model Details and applicable empty/unavailable-state recoveries. Native keyboard operation and visible focus are required; terminal keybindings cannot stand in for them.
- Use full objective names **Highest capability**, **Best value**, **Lowest qualifying price**. Use **Artificial Analysis** in attribution and **Intelligence score**, **Coding score**, **Agentic score**, **Benchmark task cost**, **Capability per dollar**, **Time to first answer token**, **Output tokens per second** and other clear headers where applicable. No `cap`, `ppi`, `AA`, `TTFT` or opaque internal codes as user-facing labels. Proper source/brand names and currency symbols remain valid; do not invent brand expansions.
- Put attribution and fetch date beside the comparison. Definitions, capacity guidance, limitations and walkthrough-level explanation belong in deliberate secondary disclosures, not full-size competing status panels. Required information remains reachable; noise reduction is not deletion.
- Narrow screens reflow controls and keep wide tables inside labelled horizontal scroll containers. Both views and expanded evidence must have no page-level horizontal overflow and must not shrink text to fit.
- Charts are not required; the approved comparison structure is the advice. Prototype variant switching, Preview states, embedded fixture rows and their caveats are review aids, not new product controls. A real fixture run still labels its fixture/synthetic-data status accurately.

### 10. Inline model evidence and secondary information

- A visible **Details** action opens/closes evidence inline at the relevant model, only on request, not as a permanent competing panel. Clear stale evidence when the result set/scope changes.
- Retain measured effort configurations, the chosen configuration and selection rationale, independent source raw scores, capability grades and ranks, source URLs/dates, and the source-disagreement indication when available source grades differ by at least two. Explain that these are different benchmark populations, not interchangeable measurements.
- Keep token input/output list prices with their units separate from matching Intelligence benchmark task cost, price tier and the explicit Intelligence score/cost division. Missing values show **—** with an accessible explanation, not an inferred number.
- Retain context length and input/output modalities from the available catalog metadata. An OpenRouter enrichment failure leaves these unavailable without invalidating ratings. Display 30-day token share only under the provenance/availability rules above, never as an effort-specific rating or selection signal.
- **Time to first answer token** is the published median in seconds **including thinking** and is the main latency measure. **Output tokens per second** is separate throughput. Missing timing shows **—**; never substitute time to first token, reconstruct latency, or estimate it from throughput.
- Detail may additionally show distinctly labelled **Time to first token** and **Estimated response time for 500 answer tokens** when published. Neither is whole-agent task duration; the free route's exact prompt preset/provider aggregation and current area-index formulas remain source limitations, not established comparability facts.
- Intelligence evidence includes scoped frontier/dominated status, the retained replacement policy and up to **three cheaper configurations** with task cost strictly below the opened row and Intelligence score **at least the opened score minus five**, sorted by task cost. Show model, effort, task cost and score change. These advisory comparisons remain independent of the display filter/role floor. They are unavailable, not reinterpreted, for Coding/Agentic.
- **How picks work** provides secondary disclosures for role defaults and boundaries, index/proxy limitations, objective order/eligibility, inclusive floor, grade reference sets, strict matching-cost limits, ties, distinct timing definitions and source provenance. Do not silently omit required caveats to imitate the prototype's low visual noise.

## Verification requirements for implementation

The repository already has Python unittest-based CLI/TUI coverage; this is not a greenfield test suite. Preserve the **fetch boundary** as the offline seam, then update affected consumer contracts for the final policy and web cutover. Tests must cover behavior/boundaries, not copied source text, wiring, incidental terminal wording or mock echoes.

- Saved source payloads and small deterministic edge fixtures exercise real acquisition parsing, canonical joins and the shared advice path without network. Label fictional/synthesized data; do not use fixture gaps as real provider coverage evidence.
- Meaningful regression scenarios: distinct selected-index scores/efforts; exact within-model/cross-model order; zero/missing/negative/non-finite matching costs; unsupported objectives; cross-effort selected-index grade sets and inclusive grade-2 floor; independent other-source grades; timing-independent ties; source-only/unranked/empty cases; Terminal-Bench collapse/missing efforts; named hard rating-source failure and best-effort enrichment.
- Shared-state/provider scenarios: direct-objective picks differ from frontier-first table order; two distinct models; single/zero picks; creator-only advice across all included efforts despite display/floor constraints; grade invariance under provider changes; full chooser/shortcuts including an empty creator; role/view retention, override reset and named-only recovery; stale details reset.
- Every nontrivial build slice leaves a runnable smoke of the real changed path. Data/policy/state slices may use a small throwaway consumer of the real fixture-loaded pipeline in addition to regression tests; no fake web scaffolds or mock-only proof.
- Web proof uses the **actual served interface**, with the fixture seam, not only unit tests or source inspection. Exercise both views, visible controls, unsupported/empty/single/unranked states, Details, secondary definitions, source links/date and recovery. Observe rendered Provider lens at desktop and 390-pixel width, including expanded evidence; verify no page-level overflow, usable scroll containers, full readable labels, focus and non-color meaning. Close verification tabs afterward.
- Update or remove tests that enforce superseded terminal UI/byte wording; preserve still-valid acquisition, identity and advice behavior. Run affected checks and the repository checks once after each implementation slice, not during this planning handoff.

## Build route

These are implementation issues, not new wayfinder decisions. Each owns a runnable result after its named prerequisites; later slices complete the product without inactive placeholder controls.

| Build slice | Prerequisite | Runnable result |
| --- | --- | --- |
| [Preserve index-specific metrics and source provenance](issues/34-preserve-index-metrics-provenance.md) | None | The real fetch/identity seam retains distinct index, cost, timing and provenance data, with truthful missing/enrichment states. |
| [Implement the eight-role selection policy](issues/35-eight-role-selection-policy.md) | Preserve index-specific metrics and source provenance | The real fixture-fed policy/batch path selects the approved model/effort rankings, grades and availability states. |
| [Add provider-scoped advice and shared selection state](issues/36-provider-scoped-advice-state.md) | Implement the eight-role selection policy | The real shared query/state path produces both view projections and scoped evidence with invariant grades. |
| [Build the Provider lens web comparison](issues/37-provider-lens-web-comparison.md) | Add provider-scoped advice and shared selection state | A real locally served, fixture-fed Provider lens with both functional views, visible controls and explicit recovery. |
| [Complete inline evidence and cut over to the web interface](issues/38-inline-evidence-web-cutover.md) | Build the Provider lens web comparison | Inline evidence and secondary explanations complete; web is the normal launch, obsolete terminal surface removed, runtime docs migrated and complete browser smoke observed. |

## Out of scope

- Implementing the features during this wayfinding handoff or merging either prototype/research branch.
- Harness integration/export: no omp snippet, config diff, config reads/writes, model-selector translation, request routing or changes to non-model harness settings.
- Unrequested dashboards, new chart products, saved sessions/preferences, UI role/config editors, hosted deployment, inference or running benchmarks.
- SWE-Atlas-QnA as a rating source; replacing the settled three-source policy; provider/gateway-specific pricing; OpenRouter per-token prices/ratings/speed as recommendation inputs.
- Caching, vendored live snapshots, scheduled/automatic refresh or a daemon. Offline test fixtures are the existing explicit seam, not a market-data cache.
- Mixing DeepSWE/Terminal-Bench run expenditure, token list prices or a manufactured token mix into matching benchmark task cost; cost-based Coding/Agentic advice without an established matching basis.
- Additional role defaults, vision as a role/column, license/popularity inclusion filters, weighted role-fit scores, price-diversity picks, and timing-based filtering/ranking/ties.
