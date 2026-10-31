# Complete inline evidence and cut over to the web interface

Type: task
Status: resolved
Blocked by: 37

## What to build

Complete the served Provider lens with genuine, explicitly opened inline model evidence and secondary **How picks work** disclosures. Make the web interface the supported interactive product surface and `make run` destination. Remove the obsolete Textual path rather than keeping two interactive products. Preserve a useful noninteractive batch invocation and one shared Python selection/advice policy.

Implement after [Build the Provider lens web comparison](37-provider-lens-web-comparison.md). Read [the amended specification](../spec.md), the canonical Answers in [Choose human-readable cross-harness role stereotypes](28-name-human-readable-roles.md), [Define quick selection by major model provider](29-provider-quick-selection.md), [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md), [Verify AA index cost bases and latency semantics](32-aa-role-metric-bases.md), and the [approved Provider lens Answer](33-redesign-provider-selection-prototype.md#answer). Preserve the [live user approval](33-redesign-provider-selection-prototype.md#2026-10-31--live-visual-approval); older awaiting-approval comments are history.

Relevant specification sections: [Runtime and acquisition seam](../spec.md#1-runtime-and-acquisition-seam) governs the launch and Textual cutover; [Sources, freshness and provenance](../spec.md#2-sources-freshness-and-provenance) governs evidence and token-share limitations; [Provider selection and shared session state](../spec.md#7-provider-selection-and-shared-session-state), [Intelligence comparison advice and the two views](../spec.md#8-intelligence-comparison-advice-and-the-two-views), [Approved Provider lens presentation and visible controls](../spec.md#9-approved-provider-lens-presentation-and-visible-controls), and [Inline model evidence and secondary information](../spec.md#10-inline-model-evidence-and-secondary-information) govern the finished interface.

## Implementation seams

- Extend the real serving/view implementation and shared state from [Build the Provider lens web comparison](37-provider-lens-web-comparison.md). Use retained source rows, source URLs, dates, configurations and catalog metadata from [Preserve index-specific metrics and source provenance](34-preserve-index-metrics-provenance.md).
- `llmratings/render.py` currently contains terminal `detail`/`_alternatives` formatting and source-rank/disagreement/list-price/context logic. Preserve the valid data and comparison behavior through shared structured evidence, not parsed terminal strings or copied JavaScript calculations. Migrate callers before deleting terminal-only helpers; keep any batch formatting that still has a real consumer.
- `llmratings/__main__.py` currently imports `tui` and chooses it when both streams are TTYs. `llmratings/tui.py` owns the obsolete Session/Textual app/key bindings/terminal driver. `requirements.txt` currently contains Textual. Cut over these real seams and all remaining callers, not only the visible launch command.
- Migrate behavioral coverage from `tests/test_tui.py`; retain relevant acquisition, identity, policy and batch coverage in `tests/test_cli.py` and the prerequisite tests. `Makefile` already uses Python unittest discovery through `make test`. No established web-test command or chosen browser framework is implied.

## Binding requirements

### Inline model evidence

1. Add a visible, model-specific **Details** action in both Model table and Provider picks, including accessible unranked entries where evidence exists. Open evidence inline at that model only on explicit request. Passive row selection/focus must not expand it. Make closing visible and keyboard-operable; expose expanded state and its controlled region. No permanent competing evidence panel, modal-only replacement or dead Details control.
2. Evidence identifies creator, canonical model display name, active role/index/objective and the chosen measured reasoning effort. List available measured configurations with their actual source/index values and identify why the objective chose this configuration, including an applicable Lowest qualifying price floor. Missing required data has a specific unranked/ineligible reason; no missing configuration is manufactured. Exploring evidence does not change the recommendation's objective-selected effort.
3. Show **Artificial Analysis**, **DeepSWE** and **Terminal-Bench** scores, capability grades and ranks separately, with source links and explicitly labelled reference populations. Artificial Analysis capability grades use all scored configurations across efforts for the selected index; DeepSWE and Terminal-Bench retain their independent source/effort populations and Terminal-Bench's best-agent collapse. Do not relabel an old Intelligence-only rank as a Coding/Agentic rank, imply that independently graded sources measure the same task, blend their scores or change grades when a provider/filter changes.
4. Retain the source-disagreement indication when the established grade-gap rule is met (at least two available source grades, maximum minus minimum at least 2), with the named grades and their source/index/effort context. Explain that these are different benchmark signals, not same-index estimates to average or proof of contradictory role performance. Missing sources remain unavailable and cannot create disagreement.
5. Link the actual retained source URLs and show fetch/refresh date alongside evidence; distinguish observation/snapshot dates where retained. Keep a clear offline-fixture notice for fixture runs, including the known fictional model names/synthesized source data where relevant. Do not present the visual prototype's preview measurements or dates as live evidence.
6. Keep **Benchmark task cost** at the matching measured Intelligence effort separate from input/output token list prices, benchmark-run expenditure and catalog metadata. Label token prices with their units and input/output direction. Show Capability per dollar and the matching score/cost calculation only on its established Intelligence basis; zero/missing/unusable denominators have an unavailable ratio, not an invented denominator.
7. Show available OpenRouter context length/modalities with attribution and honest unavailable states. Preserve the existing canonical enrichment join from the provenance prerequisite. An absent catalog row does not imply missing model capability, zero context or a nonexistent provider.
8. Show distinctly named published timing measures and units: **Time to first answer token, including thinking** in seconds and **Output tokens per second** separately. Where available, evidence may additionally show **Time to first token** and **Estimated response time for 500 answer tokens** as different measures. Missing timing is **—**, explained as unavailable. Do not substitute, reconstruct from throughput, call a 500-token estimate measured whole-agent duration, or let timing change eligibility, effort, ordering or tie-breaks.
9. For an Intelligence recommendation, show scoped frontier/dominated evidence and an actual replacement when present, preserving same-effort-first preference with cross-effort fallback. Show up to three genuinely cheaper configurations with Intelligence score at least the opened score minus 5, sorted by matching task cost; include model, full effort, cost and Intelligence-score delta. These alternatives are not the Runner-up definition. Use the active provider universe across included valid efforts, independent of the capability display filter and price floor. Show the selected comparison scope; All providers restores the global universe. When none exist, say so without inventing a replacement.
10. Coding/Agentic evidence must explicitly mark cost-based frontier, replacement, value/price advice and cheaper alternatives unavailable because matching area-index task cost is not established. Intelligence/list-price figures, if shown as explanatory context, remain clearly labelled as such and cannot become Coding/Agentic value evidence. The separate Coding Agent Index is not a substitute for the API Coding score.
11. OpenRouter 30-day token share is display-only and displayed numerically only when retained evidence genuinely verifies access/payload coverage, the actual 30-day window, source/date, denominator including other, and variant/day aggregation. Historical access/coverage and 30-day top-50 presence remain unverified source limitations, not hard-coded product exclusions. Missing access or insufficient evidence means **Unavailable**, not zero or inferred market absence. Do not invent an endpoint/credential/schema, claim coverage is settled, or rank/filter/tie-break/grade by share. A supported value is not effort-specific. Apply the provenance prerequisite's truthful data contract without widening this evidence slice into a new acquisition/research project.

### Secondary policy disclosures

12. Add **How picks work** as secondary, accessible disclosures, not an instruction wall ahead of the comparison. Cover:
    - The eight role purposes, selected indexes and defaults from the checked-in role file; capacity guidance remains separate from task-purpose identity. No new specialty role or fixed role effort.
    - Published index proxies versus actual task performance: Coding is not measured review accuracy; Agentic is not verified coordination quality. Retain the unresolved complete Coding/Agentic formula limits from the dated research. Do not present the separate Coding Agent Index as the API Coding formula.
    - Required selected-index data, finite/matched Intelligence cost rules, positive cost for Best value and the absence of a matching Coding/Agentic task-cost basis. No token mix, list price or other-source run cost replaces it.
    - Exact within-model and across-model objective ordering and final ties, the grade-at-least-2 inclusive floor only for Lowest qualifying price, floor-free Highest capability/Best value, and the separate capability display filter. Timing never selects or breaks ties.
    - Distinct source/index grade/reference sets and ranks; provider selection does not re-bin grades. Existing independent value/speed/price grades keep their established refresh populations.
    - Provider picks use the first two distinct models in direct objective order, not frontier-first table order or a cheap-diversity heuristic. Provider selection scopes Intelligence comparisons; advisory effort points remain floor/filter-free. Explain Primary versus frontier and Runner-up versus cheaper alternative.
    - Timing definitions, source provenance/date, unavailable values, best-effort catalog enrichment and display-only/unavailable token share. Link sources and [the immutable metric findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md) without overstating what was verified.
13. Keep comparison source/date visible when disclosures are closed. Preserve the approved full labels and effort names; no `AA`, `cap`, `ppi`, `TTFT` or terse configuration codes as user-facing labels. Internal objective identifiers need not change.

### State, access and narrow screens

14. Use the existing shared state for requested details. Role, objective, capability, provider and view changes clear stale row/detail selection; role changes reset objective override but retain provider/filter, and view changes retain those selections. Opening or closing evidence/disclosures must not refetch sources, change ranking or clear a constraint. All providers, capability recovery and supported-objective recovery still change only their named state.
15. Preserve the Provider lens hierarchy, aligned shelf, readable text, tabular numeric alignment and cobalt/teal/amber meanings with textual equivalents. The finished Model table shows the main published time-to-first-answer and output-throughput measures distinctly; supporting timing and non-primary metrics may live in Details rather than overcrowd each provider pick. Creators without qualifying models stay reachable with reasons and explicit recovery.
16. Use semantic headings/tables, accessible names for repeated model-specific Details actions and source links, visible keyboard focus and meaningful expansion state. The open/close interaction must retain a usable focus target. At 390 pixels, controls reflow and wide evidence/configuration tables scroll inside their own labelled containers without shrinking text or causing page-level horizontal overflow. Opening evidence in either view must not break this behavior.

### Clean runtime cutover

17. Make `make run` launch the real local web application through `python3 -m llmratings --web`, preserving its existing `.env` handling and argument forwarding. `--fixtures` and `--role` must work through that command. Document the actual printed URL and how to stop the server; do not document the archived preview server as the application.
18. Keep `python3 -m llmratings --fixtures DIR --role NAME` without `--web` as a useful noninteractive batch consumer of the same policy, including when invoked from a terminal. Remove automatic TTY-to-Textual routing, the Textual setup check/import, obsolete Session/app/driver/keymap and unused terminal detail-only code. Remove the Textual dependency and obsolete dependency guidance; preserve dependencies that have actual remaining consumers. Do not introduce a replacement terminal UI or compatibility alias.
19. Migrate remaining callers/tests to the shared state/evidence/web interface. Preserve behavior checks for roles, objective reset, filters, ranking, details, source failure and batch operation; remove obsolete Textual Pilot/TTY/ANSI/EOF-driver assertions rather than keeping Textual installed for tests. Avoid pinning exact terminal byte layout as the new behavior contract.
20. Update `README.md` (create the runtime README if still absent at implementation time), CLI help and runtime docs with setup, web launch, fixture notice, role selection, controls, source/date semantics, local-only scope, batch invocation and failure behavior. Annotate [Textual for the interactive TUI](../../../docs/adr/0001-textual-for-interactive-tui.md) as superseded and identify the superseded five-role/unchanged-data-model portions of [Roles replace categories](../../../docs/adr/0002-roles-replace-categories.md). Preserve their historical reasoning and the still-valid role profiles, objective-selected effort and floor-free advisory behavior. Align remaining runtime comments/documentation; do not rewrite historical decision tickets as if their old behavior never existed.

## Acceptance criteria

- [x] In both functional views, model-specific Details opens/closes inline only on request; source-only/unranked evidence remains reachable. No passive-selection expansion, competing permanent panel or stale evidence after a result-state change.
- [x] Real configurations, objective rationale, independent source/index scores/grades/ranks, reference populations, provenance/date, list prices, catalog context/modalities and timing/unavailable states are visible and truthful.
- [x] Source disagreement remains available without same-index or averaged-score claims. Missing timing and OpenRouter metadata/share do not exclude or reorder models; unknown share is unavailable rather than zero or invented market coverage.
- [x] Intelligence replacement/alternative evidence respects provider scope, all included valid efforts, same-effort-first replacements and top-three cheaper/within-5/price-sort rules. Coding/Agentic have no borrowed Intelligence-cost advice.
- [x] How picks work contains approved defaults, limits, eligibility/order/ties/floor/reference sets, comparison scope and timing/source definitions, accessible but secondary to useful comparison data.
- [x] Full-label, keyboard/focus and desktop/390-pixel browser checks pass with expanded evidence in both views; page-level overflow stays absent without hiding evidence or reducing text size.
- [x] `make run` serves the real application, direct `--web`/fixture/role usage works, and the no-`--web` module invocation remains a batch consumer without Textual installed or TTY dispatch.
- [x] Obsolete Textual runtime/state/dependency/callers/tests are removed or migrated. Acquisition/identity/selection policy remains shared and one refresh serves subsequent interactions.
- [x] Runtime README/help/docs and explicit ADR supersession match the new surface, preserve valid historical decisions and do not advertise prototype preview data as live advice. Migrate affected existing behavioral regressions and record actual verification evidence.

## Verification

After implementation, run `make test` once. Migrate affected existing state/detail contracts off Textual while retaining meaningful checks for source/index populations, disagreement, matched prices, distinct/missing timing, explicit details clearing and scoped alternatives. Where an uncovered policy boundary needs a regression, use a real fixture-loaded consumer: for example, a point below the display filter/price floor that remains valid Intelligence advice, or a provider change that alters alternatives but not grades. Do not add a new web-test framework, mocked evidence dictionaries, source-text checks or hard-coded terminal snapshots. The direct browser smoke below proves the rendered evidence, disclosures and access behavior.

Required launch/smoke commands after implementation, not claims of present availability or completed verification:

```sh
# Direct served fixture; open the URL actually printed by the process.
LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --web --fixtures .scratch/llm-ratings/fixtures/main --role Explorer

# Supported default launcher; uses the existing local .env setup.
make run ARGS='--fixtures .scratch/llm-ratings/fixtures/main --role Explorer'

# Preserved noninteractive batch consumer, no --web and no Textual requirement.
LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --fixtures .scratch/llm-ratings/fixtures/main --role Explorer
```

Run the two server commands separately and stop each before starting the next. Direct browser smoke:

1. At desktop width, open the served fixture in Model table. Focus/select a row without expanding evidence; activate Details using the keyboard. Confirm correct inline placement, chosen configuration/rationale, source/index-specific values and links, date/fixture notice and independent grades/ranks. Close and reopen it with focus retained.
2. Open Details for Primary and Runner-up in Provider picks. Confirm distinct models and matching selected efforts, no permanent side panel, and genuine supporting evidence rather than a static fixture card. Use source-only/unranked entries to inspect missing-source reasons.
3. Use Intelligence models with known replacement/alternative behavior from the real fixture/query results. Select a single creator and restore All providers; check scoped evidence and invariant grades. Verify cheaper alternatives against matching costs, the within-5 score bound and price order. Use source-shaped fixture variations if needed; do not add product Preview states.
4. Switch role/provider/filter/objective/view with evidence open; confirm stale evidence clears and retained constraints follow the shared state contract. Exercise an unsupported Coding/Agentic objective, named-only recovery, one-pick and empty results. Coding/Agentic evidence must not present cost-based advice.
5. Inspect all published timing labels and missing-timing/context/share cases. Confirm no timing reconstruction, fake share or source-score substitution. Open How picks work and verify its role defaults, index limitations, order/floor/grade populations and source explanations against the actual policy.
6. Repeat expanded evidence, disclosure, full creator chooser and recovery interactions at 390 pixels in both views. Confirm readable type, keyboard focus, accessible labels/expansion and internal table scrolling with no page-level overflow. Review browser console/network for application errors or leaked credentials; capture actual desktop/narrow evidence, close verification tabs and stop the server cleanly.
7. Exercise `make run` and the batch command above. Confirm real web serving versus batch output, source/setup failures without partial advice, and no remaining Textual runtime requirement. Keep the fixture's fictional/synthesized-data caveat in the recorded smoke evidence.

## Evidence and non-goals

Approved references: [live Provider lens approval](33-redesign-provider-selection-prototype.md#2026-10-31--live-visual-approval), [Model table screenshot](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-desktop.png), [Provider picks screenshot](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-provider-picks.png), [prototype entry HTML](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/index.html), [immutable commit](https://github.com/azarakovskiy/llm-ratings/commit/dd44964), and [isolated unmerged prototype branch](https://github.com/azarakovskiy/llm-ratings/tree/prototype/provider-selection-web-2026-10-30). The asset is visual/workflow evidence only: do not merge/copy its code, fictional models, synthesized recommendations, variant switcher or Preview states. Its recorded browser checks are not verification of the implemented application.

No additional product, dashboard, saved preferences, hosted deployment/authentication, harness selector/config export, gateway/request routing, benchmark execution, new metric formula or acquisition/research project. Do not add a second advice policy or keep an obsolete parallel interactive UI.

## Answer

Resolved 2026-10-31 on `implement/t38`, based on integration prerequisite
`b746790`. The integration tip was merged before final checks and was already
up to date. No prototype or research branch, runtime asset or measurement was
merged or copied.

### Finished runtime and evidence contract

- `make run` now launches `python3 -m llmratings --web`, with the existing
  `.env` export and argument forwarding. Direct module invocation without
  `--web` always prints batch advice and exits, including with terminal
  streams. The runtime now uses only the Python standard library.
- Removed the Textual adapter, TTY routing/setup check, terminal keymap/EOF
  driver, exclusive dependency/install target and terminal-only tests.
  Shared state tests live in `tests/test_session.py`; valid detail contracts
  moved to fixture-loaded structured evidence and HTTP consumer tests.
  The batch table formatter remains because it still has a real consumer.
- `evidence.model_evidence(dataset, result, record)` describes a current
  ranked, display-excluded or unranked query record. It preserves the actual
  selected `Rating`, measured source-effort configurations, eligibility
  reasons and objective rationale. Independent source scores, grades,
  competition ranks and labelled populations use the existing policy and
  Terminal-Bench best-agent/recency collapse, not terminal-string parsing.
  Exploring other efforts never changes the selected configuration.
- Model-specific Details actions open one inline region in either view,
  including excluded/source-only entries. Native `details` and
  `close_details` form actions call the shared Session methods without
  refetching. Controls expose model-specific accessible names, expanded state
  and a controlled region; the visible close action returns focus to its
  opener. Passive focus does not open evidence. Result-state changes clear
  stale evidence, while native policy disclosures and usable table scroll
  positions survive updates.
- Inline evidence shows matching Intelligence benchmark task cost and its
  finite positive score/cost division separately from directional
  USD-per-million token list prices, catalog metadata and published timing.
  Invalid negative retained costs keep their sign rather than appearing
  positive. Missing values are explained as unavailable (—), never filled
  from another effort, source, timing field or denominator.
- Intelligence frontier/replacement/cheaper-configuration evidence consumes
  the current creator-scoped query data, across valid included efforts and
  independently of display filters/price floors. Coding/Agentic explicitly
  have no established cost-based frontier, replacement, value/price advice
  or cheaper alternatives. No JavaScript ranking or second policy was added.
- How picks work is a secondary native disclosure. Its role purposes,
  indexes, defaults and capacity guidance come from the checked-in role
  catalog. It covers exact eligibility/order/ties/floor, independent grade
  and rank populations, provider picks versus frontier/alternatives,
  benchmark proxy/formula limits, timing definitions and retained
  source/date/catalog/share limitations, with the immutable metric findings.
- The runtime README, CLI help and fixture contract describe setup, local-only
  serving, controls, dates, batch operation and failure behavior. ADR 0001
  is explicitly superseded; ADR 0002 identifies the superseded five-role,
  terminal and unchanged-data-model claims while preserving its historical
  reasoning and still-valid profiles, objective-selected effort and
  floor-free advisory comparisons.

### Actual browser and consumer verification

The direct required fixture command served `http://127.0.0.1:56882/`.
All observations came from the real Python server through `browser.open`,
not archived HTML. The saved main data remains a historical 2026-08-05
snapshot with reported Intelligence Index version 4.1, fictional names and
synthesized Terminal-Bench/OpenRouter rows, not current market advice.
Its actual refresh fetch time was displayed separately.

- At **1440 × 1100** and **390 × 844**, both Model table and Provider picks
  opened genuine model evidence inline. Clicking/focusing a row did not
  expand it; keyboard Enter/Space opened Details. Closing and reopening
  retained the opener as a usable focus target. Primary Sol Maximum and
  Runner-up GPT-5.5 Extra high remained distinct measured models/efforts.
- Luna Maximum displayed Intelligence **51.2 / grade 3 / rank 12 of 21**,
  DeepSWE **grade 1 / rank 5 of 5**, and Terminal-Bench **0.757 / grade 4 /
  rank 2 of 3**, with named cross-source disagreement, separate population
  labels, actual links, version, agent and observation date. Sol Maximum
  displayed **58.9 / grade 5 / rank 3 of 21**, DeepSWE **grade 4 / rank
  2 of 5**, and Terminal-Bench **0.769 / grade 5 / rank 1 of 3**.
  Missing Terminal-Bench Extra high evidence for GPT-5.5 stayed unavailable.
- OpenAI selection made Sol Maximum creator-frontier without changing its
  benchmark references. Its cheaper configurations became Sol High
  **$0.5486**, Sol Extra high **$0.8325**, GPT-5.5 Extra high **$1.1748**.
  All providers restored global advice. Opus Maximum's first three cheaper
  configurations were Sol High **$0.5486 / −4.8**, Opus Medium
  **$0.7224 / −4.4**, Sol Extra high **$0.8325 / −3.0**, in task-cost
  order. Grade-5 display filtering did not remove these advisory points.
  Utility's grade-floor-qualified Luna Extra high still offered cheaper
  Luna High **$0.0216 / −3.0** below that selection floor.
- Both views retained reachable source-only Terra evidence, with real
  DeepSWE effort rows but no fabricated Artificial Analysis configuration.
  Coding Sol selected Extra high, **78.3 / rank 1 of 21**, with explicitly
  unavailable area-cost advice. Unsupported Coding Best value and Agentic
  Lowest qualifying price stayed selected until named recovery.
- Role, provider, capability, objective and view changes cleared stale
  details. A role change retained **OpenAI / grade 4 and above / Provider
  picks** but reset the objective override to Coding Highest capability.
  Kimi produced one pick and an honest missing runner-up; Google and a
  grade-5/Kimi intersection produced named empty states. All providers,
  clear-capability and supported-objective recovery changed only their
  named constraint. The full native creator chooser remained usable.
- Opus showed attributed OpenRouter **200,000-token** context and
  **text, image, file input / text output**. Kimi's missing catalog data and
  all unsupported 30-day token shares stayed unavailable, not zero or
  market-absence claims. Actual Artificial Analysis, DeepSWE and individual
  Terminal-Bench submission URLs and observation/snapshot dates remained
  reachable beside the evidence.
- The main fixture supplies all four timing fields. A separately labelled
  temporary source-shaped variation served at
  `http://127.0.0.1:59051/`: Luna Low first-answer time was null, while
  **146.91 output tokens/s**, **1.96 s first-token time** and **5.36 s
  500-answer-token estimate** stayed distinct. Explorer still selected Low;
  first-answer remained **—**, not a substituted estimate. An included
  Synthetic zero cost model was unranked for Best value but eligible at
  **$0** for Highest capability, with **Capability per dollar —** and the
  positive-denominator reason. The temporary fixture was removed.
- At 390 pixels, the document stayed **390px** wide with page horizontal
  scroll **0**. Expanded evidence stayed **324px** wide; its tables scrolled
  inside labelled **295px** regions (configuration **950px**, timing/prices
  **1680px**, source evidence **1180px**, alternatives **750px**). Table
  text stayed **15px**. Keyboard horizontal scrolling moved an inner region
  past **71px** while page scroll stayed zero, with a **3px cobalt** focus
  outline. Runner-up evidence stayed within the viewport even when the outer
  picks shelf had scrolled **455px**. Narrow labels were corrected to wrap
  at word boundaries, not split inside words.
- Expanded policy sections, creator selection, source-only evidence,
  single/empty/unavailable states and recoveries were exercised on the
  narrow screen. Browser console/error logs were empty; inspected documents
  and recorded requests had no API-key field/header or credential value.
  All three verification tabs were closed.
- The required `make run ARGS='--fixtures
  .scratch/llm-ratings/fixtures/main --role Explorer'` command separately
  served the real application at **http://127.0.0.1:59290/** and opened
  Luna Low evidence. The direct and variation servers exited **0** on
  Ctrl-C. Ctrl-C stopped the Make-launched server and closed its listener;
  the Make wrapper reported interruption status **1**, with no application
  traceback or remaining listening process.
- The required no-`--web` batch command exited **0** with Explorer /
  Intelligence / Best value output. The shell tool could not allocate a
  terminal, so an additional stdlib `pty.openpty()` subprocess put **both**
  child streams on a real terminal: the same module invocation produced
  batch output, no terminal-UI escape sequences, and exited **0** in about
  **0.07 s**. A separate `python3 -S` consumer disabled site packages,
  confirmed Textual was unavailable, and still produced the same successful
  batch advice. Missing-key and missing-DeepSWE-file launches exited **1**
  with named errors and no serving URL or partial advice.

Captured evidence:

- [Desktop Model table evidence](../assets/38-inline-evidence-web/desktop-model-evidence.png)
- [Desktop Provider picks evidence](../assets/38-inline-evidence-web/desktop-provider-evidence.png)
- [Desktop source-only evidence](../assets/38-inline-evidence-web/desktop-source-only.png)
- [Desktop unsupported-objective evidence](../assets/38-inline-evidence-web/desktop-unsupported-evidence.png)
- [Desktop How picks work](../assets/38-inline-evidence-web/desktop-policy.png)
- [390px Model table evidence](../assets/38-inline-evidence-web/phone-model-evidence.png)
- [390px Provider picks evidence](../assets/38-inline-evidence-web/phone-provider-evidence.png)
- [390px keyboard focus and internal scroll](../assets/38-inline-evidence-web/phone-keyboard-scroll.png)
- [390px How picks work](../assets/38-inline-evidence-web/phone-policy.png)
- [390px one-pick evidence](../assets/38-inline-evidence-web/phone-single-pick.png)
- [390px empty creator](../assets/38-inline-evidence-web/phone-empty-provider.png)
- [390px source-only evidence](../assets/38-inline-evidence-web/phone-source-only.png)
- [390px missing-timing variation](../assets/38-inline-evidence-web/phone-missing-timing.png)
- [390px zero-cost variation](../assets/38-inline-evidence-web/phone-zero-cost.png)

### Final repository checks

- `make test`: **102 tests passed**, once after all implementation edits,
  including migrated state/detail contracts, source/index populations,
  disagreement, matched prices, distinct/missing timing, stale evidence,
  scoped floor/filter-free alternatives, real HTTP forms, source failure,
  source escaping and batch behavior.
- `make lint`: **passed**, once after implementation. Ruff is not installed
  here, so the existing Makefile fallback ran the Python syntax check.
- No new browser-test framework, runtime dependency, acquisition endpoint,
  preview state, harness/config export or second policy was introduced.

