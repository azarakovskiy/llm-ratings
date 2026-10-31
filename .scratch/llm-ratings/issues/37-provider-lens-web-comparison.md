# Build the Provider lens web comparison

Type: task
Status: resolved
Blocked by: 36

## What to build

Serve the approved **Provider lens** as a real local web interface over the existing Python dataset and shared advice state. Deliver both **Model table** and **Provider picks** as functional views in this issue. The result must be useful before the later evidence/cutover issue: no inactive view tabs, embedded prototype recommendations or browser-only ranking policy.

Implement after [Add provider-scoped advice and shared selection state](36-provider-scoped-advice-state.md). Read [the amended specification](../spec.md), then the canonical Answers in [Define quick selection by major model provider](29-provider-quick-selection.md), [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md) and [Redesign the provider-selection prototype for readable model advice](33-redesign-provider-selection-prototype.md#answer). The later Answers supersede chronological proposals. The visual decision includes the [live approval of Provider lens](33-redesign-provider-selection-prototype.md#2026-10-31--live-visual-approval), not approval of Focus desk.

Relevant specification sections: [Runtime and acquisition seam](../spec.md#1-runtime-and-acquisition-seam), [Sources, freshness and provenance](../spec.md#2-sources-freshness-and-provenance), [Provider selection and shared session state](../spec.md#7-provider-selection-and-shared-session-state), [Intelligence comparison advice and the two views](../spec.md#8-intelligence-comparison-advice-and-the-two-views), and [Approved Provider lens presentation and visible controls](../spec.md#9-approved-provider-lens-presentation-and-visible-controls). [Inline model evidence and secondary information](../spec.md#10-inline-model-evidence-and-secondary-information) is completed by the next issue; this slice must not expose inactive evidence controls.

## Implementation seams

- Extend `llmratings/__main__.py` argument parsing and dispatch with explicit `--web`, preserving `--fixtures DIR`, `--role NAME`, role-file order and setup/source errors. The current entry calls `fetch.fetch_all`, `identity.load_aliases` and `identity.build`; reuse that path.
- Consume the real shared query/state implementation from the prerequisite and the selection policy used by `llmratings/render.py`. Use structured result data, not terminal text parsed into HTML. Browser code may handle interaction/presentation, but must not implement a second eligibility, effort-selection, grading, ordering or frontier engine.
- Add the smallest local serving and web assets needed. Reuse Python and native browser controls; no particular frontend framework is required. Do not add a framework, build pipeline or dependency merely to serve this page.
- Keep the existing noninteractive batch consumer working. Final removal of the superseded Textual surface, its dependency and runtime callers belongs to [Complete inline evidence and cut over to the web interface](38-inline-evidence-web-cutover.md); do not add new TUI functionality here.

## Binding requirements

### Serving and data lifetime

1. Add and document the new explicit launch `python3 -m llmratings --web`. It must serve on loopback, print the actual local URL and work without TTY detection. Honor `--role` as the initial role and use the first role in file order otherwise. Keep API keys on the server: never serialize credentials into HTML, scripts, responses, URLs or browser storage. Escape source-derived display content and retain normal safe browser rendering.
2. One startup refresh calls the existing acquisition/identity path once. Role, objective, provider, capability and view changes reuse that dataset; they do not refetch sources. No cache service, scheduler, background refresh or retry subsystem is needed.
3. Retain the `LLM_RATINGS_AA_API_KEY` setup requirement, including the dummy key for offline fixtures. A missing key or failure of DeepSWE, Artificial Analysis or Terminal-Bench names the setup/source error and produces no partial advice. OpenRouter enrichment remains best-effort, with missing context explicitly unavailable rather than a failed ratings run.
4. Document the future fixture command in CLI help/runtime usage:

   ```sh
   LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --web --fixtures .scratch/llm-ratings/fixtures/main --role Explorer
   ```

   This command is an implementation requirement, not a currently available or verified command. Read fixture provenance and identify served fixture results beside the comparison as an offline snapshot, not live market advice. Show linked source attribution and the refresh/fetch date truthfully; do not present an old source observation as a new measurement.

### Visible controls and shared state

5. Use creator navigation at the left on wide screens: **All providers**, the fixed **OpenAI**, **Anthropic**, **Google**, **DeepSeek**, **xAI** shortcuts, and a visible full creator chooser. The full catalog remains selectable, including creators with no qualifying model for the current constraints. A provider means model creator, not API gateway. Shortcuts do not depend on loaded scores, token share or fixture coverage.
6. Above the comparison, show the eight-role chooser in file order, active role purpose, selected index, objective and capability filter. Put capacity guidance in a secondary disclosure rather than a long header. Use visible **Model table** / **Provider picks** controls. Initial state is Model table, All providers, all capability grades, and the role default objective. Honor the prerequisite's capability filter choices: all, grade 5, grade at least 4; label these as selected-index capability grades, not terminal `cap` codes.
7. All three objective labels stay inspectable and selectable: **Highest capability**, **Best value**, **Lowest qualifying price**. Coding/Agentic price-based choices retain an explicit unavailable-objective state explaining that no matching benchmark task cost is established. They must not silently revert, change index or borrow Intelligence cost. Offer a visible **Highest capability** recovery that changes only the objective.
8. Route every control through the shared selection state. Role changes reset only the objective override while retaining provider and capability filter. View changes retain role, objective, provider and filter. Role, objective, provider, filter and view changes clear stale row/requested-detail state. **All providers** changes only the provider constraint; clearing the capability filter changes only that filter. Provide visible **Use role default** recovery that resets only the objective override. No control silently relaxes another constraint or persists preferences across sessions.

### Both comparison views

9. **Model table** shows each eligible model once at its objective-selected measured effort, with aligned model, full effort name, selected-index score, capability grade and applicable objective metrics. Keep Artificial Analysis, DeepSWE and Terminal-Bench ratings/grades distinct, with unavailable values explicit rather than blended or replaced. Preserve source-only/ineligible models in a reachable labelled unranked disclosure with reasons; do not recommend them with fabricated scores. Also keep included models excluded only by the capability display filter reachable in a labelled secondary disclosure within the selected provider scope, showing their selected configurations and filter-exclusion reasons separately from unranked measurement failures.
10. For Intelligence, retain real frontier/dominated sections, the frontier path and replacements, with objective order within each section. Show **Score change** and **Task cost change** against the preceding visible row within the same section; the first row of each section has no previous-row delta. Recompute these deltas after provider or capability display constraints change the visible rows; never compare across section boundaries or against a hidden row. Label Intelligence benchmark task cost and **Capability per dollar** accurately. Display the active provider/advisory comparison scope beside the results: provider-local frontier membership is not global membership. The comparison universe includes the selected creators' included valid scored/priced configurations across efforts, unaffected by the capability display filter or Lowest qualifying price floor.
11. For Coding/Agentic Highest capability, use direct selected-score order and no cost frontier, dominated-by-cost sections, Intelligence-cost tie-break, value ratio or cheaper-advice claims. Keep the selected index visible. Missing timing never excludes a model or changes order.
12. **Provider picks** is an aligned shelf with **Primary** and **Runner-up** side by side for each selected creator. Show model, effort, selected-index score, grade and the applicable objective metric in comparable positions. Use the direct objective ranking after eligibility, per-model effort selection and capability filtering, not the first two frontier-first table rows. A dominated Intelligence model can be a pick; Primary does not assert global frontier membership. The second pick is another model, not another effort or a separately chosen cheap alternative.
13. With All providers, picks are still chosen separately for each creator while Intelligence advisory comparisons remain global. Selecting one creator scopes both views and Intelligence advice to it. Scores and all grade reference sets remain unchanged by provider selection.
14. One model produces one pick and an explicit absent runner-up; zero produces **No qualifying configuration** with role, provider and active constraints. Retain the selection. Creators with picks appear before a secondary **Creators without qualifying models** disclosure; show reasons there and allow selecting those creators. Empty-state recovery offers All providers and, when applicable, clearing the capability filter as separate named actions. Unsupported objectives, unranked models and missing source values are different states, not one generic loading/empty message.

### Presentation and access

15. Match the approved hierarchy: restrained cool neutrals, readable dark text, humanist sans-serif typography and tabular numbers. **Cobalt** identifies selection/focus, **teal** frontier or primary priority, and **amber** unavailable advice/recovery. Text, labels and scope convey these meanings without color. Keep the comparison primary; avoid decorative dashboards, repeated instruction walls and equally prominent status panels.
16. Use full labels: Artificial Analysis; Intelligence score, Coding score or Agentic score; Benchmark task cost; Capability per dollar; full effort names such as Extra high and Maximum. Do not expose `AA`, `cap`, `ppi`, `TTFT` or configuration spellings as interface labels. Brands and currency symbols are not prohibited abbreviations. Supporting timing/non-primary metrics may be deferred to inline evidence in the next issue; any timing shown here must distinguish **Time to first answer token, including thinking** from **Output tokens per second** and show missing values as unavailable.
17. Controls must have visible associated labels, native keyboard operation and visible focus. Expose the selected view/provider and state changes accessibly; use semantic tables/headings and readable contrast. Retained unsupported objectives must remain reachable by keyboard, not be hidden as disabled unexplained options.
18. At 390-pixel width, reflow navigation/controls and keep readable text size. Wide tables/shelves scroll within labelled comparison containers; the page itself must not overflow horizontally. Keep recovery and the full provider chooser usable without hover-only interaction.
19. Do not display a dead Details action. [Complete inline evidence and cut over to the web interface](38-inline-evidence-web-cutover.md) adds the genuine per-model inline control and secondary policy disclosures.

## Acceptance criteria

- [x] The explicit web entry serves the actual fixture-built Python advice dataset on loopback; startup fetch/build runs once, and working controls use the shared policy/state without a second scoring engine.
- [x] Both views are fully functional with role/objective/provider/capability controls, correct initial state and retained/reset state rules. The full creator list includes non-shortcut and empty creators.
- [x] Intelligence table sections/path/replacements and direct-order provider picks agree with the shared query results, including a case where a dominated model is a valid pick. Coding/Agentic compare selected scores without cost claims.
- [x] Intelligence Score change and Task cost change use the preceding visible row within each section, with no delta on either section's first row. Provider/capability changes recompute deltas without crossing a section boundary or referencing hidden rows.
- [x] Included models excluded only by the capability display filter remain reachable in a labelled secondary disclosure with their objective-selected configurations and filter reasons, distinct from source-only/unranked models lacking qualifying measurements.
- [x] Single-pick, no-qualifying, source-only/unranked, unavailable-value and unsupported-objective states are visible and distinct. Each recovery changes only its named constraint.
- [x] Scores/grades stay invariant across provider changes; rows, selected efforts, order and applicable scope agree across table/picks projections.
- [x] Full labels, linked attribution, truthful date and fixture notice appear beside the comparison. No key, archived preview data, variant switcher, Preview states control or dead Details action reaches the product page.
- [x] Direct browser review passes at desktop and 390 pixels, using mouse and keyboard with visible focus, readable comparison columns and no page-level horizontal overflow. Record actual runtime evidence; archived screenshots alone do not satisfy this check.
- [x] Keep affected batch/acquisition/advice behavior tests working, updating broken contracts for the new entry and policy. Update launch help/usage; final default-run documentation and Textual cleanup remain assigned to the next issue.

## Verification

After implementation, run `make test` once and update existing tests whose runtime/advice contracts change. Do not add a web-test framework or tests of source text, forwarding, mock scoring or exact terminal byte layouts. Preserve meaningful setup/source-failure, best-effort enrichment, loaded-refresh and shared-state coverage through the existing source seam; use small source-shaped fixture variations for deterministic one/zero/unsupported/unranked browser scenarios and label synthetic rows. Direct browser smoke below proves the new UI; do not import the archived demo's rows or treat unit tests alone as surface proof.

Direct browser smoke, using the new fixture command above:

1. Open the printed URL at desktop width. Confirm Explorer / Best value / Intelligence / All providers / all capability / Model table, real dataset rows, attribution/date and offline-snapshot notice.
2. Select OpenAI, capability grade at least 4 and another Intelligence objective; switch to Provider picks and back. Check retained selections, distinct Primary/Runner-up, effort/score agreement with Python query results and unchanged source grades. Select a non-shortcut creator from the full chooser. In the Intelligence table, verify Score change and Task cost change against the preceding visible row within each section, no deltas on either section's first row, and correct recomputation after provider/filter changes hide rows. Use a labelled fixture variation if needed to exercise both sections with multiple visible rows and a hidden predecessor. Open the secondary disclosure for capability-filter exclusions and verify selected configurations and filter reasons remain reachable and distinct from unranked measurement failures.
3. Switch to Coder and Coordinator: objective resets to Highest capability, provider/filter remain, and the correct selected index is shown. Select Best value, observe the retained unavailable state, then use Highest capability recovery and verify only the objective changes.
4. Select a creator with no qualifying results; verify named constraints and separate recovery actions. Exercise one-pick and unranked cases with fixture variations if the main snapshot cannot produce them. Confirm no fabricated runner-up or silent constraint reset.
5. Repeat view/control/recovery operations at 390 pixels, including keyboard-only navigation. Confirm wide comparison content scrolls inside its container, not the page, and that focus/state remains visible. Inspect browser console/network for application errors and credential exposure. Close verification tabs and stop the local server cleanly.

## Evidence and non-goals

- Live approval: [Approve Provider lens](33-redesign-provider-selection-prototype.md#2026-10-31--live-visual-approval).
- Immutable approved references: [Provider lens Model table](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-desktop.png), [Provider lens Provider picks](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-provider-picks.png), [entry HTML](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/index.html), [captured commit](https://github.com/azarakovskiy/llm-ratings/commit/dd44964), [unmerged prototype branch](https://github.com/azarakovskiy/llm-ratings/tree/prototype/provider-selection-web-2026-10-30).
- Metric limits: [immutable index/cost/timing findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md). Only Intelligence has an established matching benchmark task cost.
- References establish hierarchy and behavior, not product code or real performance/coverage. Do not copy or merge the throwaway prototype, its fictional/synthesized advice, visual-variant controls or Preview states into runtime.
- No hosted deployment, authentication, new public API product, harness/config export, gateway routing, benchmark execution, saved preferences or added market-share ranking. OpenRouter token share is display-only; do not infer it from fixture coverage. Unverified access/payload coverage is a source limitation, not a permanent product exclusion: display a value only under the specification's verified provenance rules; otherwise show Unavailable without guessing an endpoint, credentials or schema.

## Answer

Resolved 2026-10-31 on `implement/t37`, based on integration prerequisite
`ec3a698`. The real fixture-fed Provider lens now serves both working views.
The approved screenshots were viewed as visual references only; no prototype
branch, assets, source rows or scoring code were copied into the runtime.

### Runtime and ticket 38 contract

- `python3 -m llmratings --web` uses the existing once-only
  `fetch.fetch_all` → `identity.build` → `Session` startup path. It honors
  `--fixtures`, `--role`, ordered role defaults, the required key and named
  source/setup failures, and bypasses the TTY/Textual gate. Batch and the
  existing TUI remain unchanged until ticket 38. CLI help and the fixture
  README document the exact offline launch command.
- `llmratings.web.create_server(session, port=0)` returns a standard-library
  `HTTPServer` bound to `127.0.0.1`; `serve(session)` prints its actual URL,
  serves in the foreground and closes cleanly on Ctrl-C. One process owns
  one in-memory selection session. Controls never refetch sources.
- `llmratings.webview.page(session, result)` renders a complete escaped HTML
  document from the already computed shared query result. It preserves
  `sections`, section deltas, `picks`, scoped replacements/path, excluded
  configurations, unranked reasons and empty creators. No raw source payload,
  environment, credential or second ranking engine is sent to the browser.
- Native `POST /` forms contain exactly `action` and `value`. Actions are
  `role`, `objective`, `capability`, `provider`, `view` and `recover`; empty
  values clear only the matching optional choice. Each action calls the
  existing `Session` transition and renders its returned result. `GET /`
  renders `Session.query()`. Static routes allow only `/web.css` and
  `/web.js`; there is no JSON API or general filesystem serving.
- `web.js` only submits native forms, replaces `#app`, retains focus/scroll
  and updates the persistent `#state-summary` live region. Forms still work
  without JavaScript. `web.css` supplies creator-left navigation, labelled
  controls, cobalt selection/focus, teal priority, amber recovery and labelled
  internal comparison scroll regions. Ticket 38 can extend the form dispatch
  with the existing explicit `Session.request_details`/`close_details`
  methods and render evidence inline at `data-model` records. No inactive
  Details action is exposed now.
- Host/origin checks, bounded strict form parsing, a fixed static allowlist,
  no-store responses, a restrictive Content Security Policy and escaped
  source-derived text protect the local surface. Requests do not log their
  URLs or values. Source attribution, actual refresh fetch time, historical
  snapshot dates and synthetic/unavailable provenance remain distinct.

### Exercised runtime and browser evidence

The exact offline command in this ticket served the main snapshot at
`http://127.0.0.1:63837/`. A separately labelled, temporary source-shaped
variation served at `http://127.0.0.1:65491/`. All observations below came
from those real Python servers through `browser.open`, not archived HTML.

- Desktop **1440 × 1100** and phone **390 × 844** exercised both views,
  role/objective/creator/capability controls, fixed shortcuts, the full
  chooser, all named recoveries and secondary disclosures. Initial state
  was Explorer / Best value / Intelligence / All providers / all grades /
  Model table, with five selected models and two source-only unranked
  records. Historical 2026-08-05 evidence was shown separately from the
  actual 2026-10-31 refresh time, with an offline/synthetic-data notice.
- Direct Python `Session` projections agreed with the served rows and
  picks. OpenAI / Highest capability / grade 4 and above selected Sol
  **Maximum, 58.9, grade 5** and GPT-5.5 **Extra high, 54.8, grade 4**.
  Both scores/grades stayed identical under All providers. Independent
  source disclosures retained Sol's DeepSWE grade 4 / Terminal-Bench
  grade 5 and GPT-5.5's unavailable Terminal-Bench result. The filter
  disclosure separately retained excluded Luna Maximum, score 51.2,
  grade 3, and its display-filter reason.
- Coder reset only the objective override and used Coding: Sol Extra high
  **78.3** and GPT-5.5 Extra high **74.9**. Coordinator used Agentic:
  Sol Maximum **54** and Luna Maximum **45.6**. Provider, capability
  filter and view stayed selected. Area tables had direct score order,
  no cost frontier/value columns or task-cost deltas. Unsupported Coding
  Best value and Agentic Lowest qualifying price stayed selected with
  explicit unavailable-objective explanations; Highest capability recovery
  changed only the objective. Use role default reset only its override.
- The non-shortcut **Kimi** creator produced one real pick and **No
  qualifying runner-up**. Google and the variation's AA-only **Empty
  synthetic creator** produced named no-qualifying states without relaxing
  constraints. All providers and Clear capability filter were separate
  actions. Creators without qualifying models retained reasons and working
  creator-selection buttons. Unranked source-only records stayed distinct
  from capability exclusions and unavailable source measurements.
- The temporary variation used explicitly named Synthetic delta A–E:
  A **40 / $1**, B **100 / $5**, C **95 / $6**, D **85 / $5.5**,
  E **90 / $7**, plus a non-selected A Maximum **80 / $20**, a catalog-only
  creator and a source-only record. Both Intelligence sections had multiple
  visible rows. Frontier B showed **+60 / +$4** after A. Dominated C had no
  predecessor; D showed **−10 / −$0.5**, E **+5 / +$1.5**. Grade ≥ 4 hid
  A and D: both section first rows lost their deltas, and E recomputed
  against C to **−5 / +$1**. Selecting OpenAI also hid D and produced
  that same C→E delta. The scoped frontier path still included filtered
  A. Filtered Provider picks chose B Primary / dominated C Runner-up,
  agreeing with direct shared-query order.
- Keyboard Tab navigation, native creator type-ahead, Space/Enter buttons,
  view switching and named recovery worked. Focus was retained
  after server updates and visibly used a **3px cobalt outline**.
  At 390 pixels, document width remained **390**, while the model table
  scrolled **1130px** inside a **352px** region, the picks shelf **1050px**
  inside **352px**, and the independent-source table **800px** inside
  **352px**. Keyboard horizontal scrolling changed the region's scroll
  position while page horizontal scroll stayed **0**. Comparison type
  stayed **15px**, not reduced to fit.
- All four verification tabs had empty console/error logs. Inspected
  rendered documents and recorded requests contained no API-key field,
  key header or credential sentinel. No archived preview controls or
  dead Details control appeared. All verification tabs were closed,
  both final servers exited **0** on Ctrl-C, and the temporary fixture
  directory was removed.

Actual captured visual evidence:

- [Desktop Model table and source-only/provenance disclosures](../assets/37-provider-lens-web/desktop-model-table.png)
- [Desktop Provider picks](../assets/37-provider-lens-web/desktop-provider-picks.png)
- [Desktop unsupported objective](../assets/37-provider-lens-web/desktop-unavailable-objective.png)
- [Desktop single pick](../assets/37-provider-lens-web/desktop-single-pick.png)
- [Desktop empty creator](../assets/37-provider-lens-web/desktop-empty-creator.png)
- [Desktop synthetic deltas/exclusions/frontier path](../assets/37-provider-lens-web/desktop-synthetic-deltas.png)
- [390px Model table and disclosures](../assets/37-provider-lens-web/phone-model-table.png)
- [390px Provider picks](../assets/37-provider-lens-web/phone-provider-picks.png)
- [390px keyboard focus and internal scroll](../assets/37-provider-lens-web/phone-keyboard-focus.png)
- [390px unsupported objective](../assets/37-provider-lens-web/phone-unavailable-objective.png)
- [390px single pick](../assets/37-provider-lens-web/phone-single-pick.png)
- [390px synthetic deltas and distinct exclusion/unranked disclosures](../assets/37-provider-lens-web/phone-synthetic-deltas.png)

### Repository verification

- `make test`: **107 tests passed** on the final run. An earlier run
  exposed two new test-expectation mistakes: the saved creator is Kimi,
  not Moonshot, and a chunked request without Content-Length correctly
  returns 411 before the media-type check. Those assertions were corrected;
  the product behavior was not weakened.
- `make lint`: **exit 0**, run after the final test pass.
- Public HTTP/source/CLI regressions cover real fixture serving,
  retained/reset state, area-objective unavailability, scoped deltas,
  capability exclusions versus unranked records, dominated runner-up
  selection, source-content escaping, omitted raw/credential sentinels,
  hostile/invalid requests, named startup failures, best-effort enrichment
  and once-only acquisition across control changes.
- `git merge --no-edit integration/role-advice-web`: **Already up to date**.

Inline model evidence, complete How picks work disclosures, default `make run`
web cutover and Textual removal remain assigned to ticket 38. The glossary and
historical ADRs are intentionally unchanged by this presentation slice.
