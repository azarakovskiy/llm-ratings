# Redesign the provider-selection prototype for readable model advice

Type: prototype
Labels: wayfinder:prototype
Status: resolved
Blocked by: 30
Related: [Define quick selection by major model provider](29-provider-quick-selection.md); [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md)
Parent: [LLM Ratings: human-readable agent roles and provider quick selection](../map.md)

## Question

Which concrete web layout and hierarchy make the settled Model table and Provider picks workflows readable, with full user-facing labels, clear structure and deliberate, useful accents instead of debug-state panels, instruction walls and equal-weight sections crowding the main model comparison?

This is a HITL visual decision for the actual planned web interface, not a new workflow decision. Preserve the functional contract in [Define quick selection by major model provider](29-provider-quick-selection.md): both views, distinct primary/runner-up models, provider shortcuts and full chooser, shared selection, provider-scoped advice, no provider-relative re-binning of grades, and explicit empty/short-result recovery. Do not reopen these decisions to simplify the presentation. Historical terminal keybindings are optional aids, not current requirements or substitutes for visible web controls.

Wait for [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md) to resolve, then use its final index, objective, cost, floor, tie, missing-data and latency policies in both views, including strict matched-cost rules and no timing-based selection or tie-breaks. Use the eight agreed roles: Explorer, Researcher, Planner, Coder, Reviewer, Coordinator, Generalist and Utility. Do not copy the old prototype's five-role, Intelligence-only baseline or present unsupported cost comparisons as valid advice.

### Prototype and review requirements

- Use the `prototype` skill's UI branch (`UI.md`) together with `frontend-design`; this question is about visual presentation, not another logic/debug-state demo.
- Make model comparison and the active role, provider and comparison scope easy to scan. Give accents a useful purpose, such as selection or recommendation priority, rather than equal emphasis on every section.
- Provide visible controls for role, objective, capability filter, Model table / Provider picks, provider shortcuts and full chooser, All providers, model details and applicable recovery actions. Retain provider selection and capability filter across role/view changes; each recovery action changes only its named constraint.
- Use **Highest capability**, **Best value** and **Lowest qualifying price** as the visible objective names. Use **Artificial Analysis**, not `AA`, in source attribution; use clear metric labels such as capability score, capability per dollar, task cost, time to first answer token, time to first token and output tokens per second rather than `cap`, `ppi`, `TTFT` or opaque codes. Keep the distinct timing meanings clear and apply the resolved availability policies. Use clear headers and source attribution once where useful, not repeated long labels on every row. Proper source/brand names and currency symbols are fine; do not invent brand expansions.
- Internal configuration keys, API field names and raw technical evidence may retain their technical names internally. This planning decision does not migrate runtime identifiers or choose a new technical stack.
- Use progressive disclosure or secondary surfaces for supporting state, definitions, caveats and walkthroughs. Keep required advice, caveats, both views, detail information and edge states reachable and understandable; do not delete them to fake low noise. Include empty, single-pick, unranked and unavailable-metric/objective states under the resolved criteria.
- Design the actual planned web interface. The throwaway prototype remains a review artifact, not product implementation or authorization for unrequested dashboards or features.
- Review the actual rendered variants, including screenshots or equivalent visual evidence, for hierarchy, scanability, useful accents, readable comparison data and access to secondary information. A source-code review or functional smoke check alone does not settle the visual question.
- Present the rendered alternatives to the live user, iterate on their feedback and obtain explicit approval of a concrete direction. Agent self-approval cannot resolve this HITL ticket.
- Capture the future prototype asset on a throwaway `prototype/<name>` branch, outside the working branch, and link the published branch, commit and asset here. Do not merge the prototype or build product features. Record the user's verdict and the selected layout/hierarchy with that evidence.

### Rejected visual reference

The [archived provider-selection prototype](https://github.com/azarakovskiy/llm-ratings/blob/29beda7bb4872c8640d19c4b15e4d01405d134c3/.scratch/llm-ratings/assets/29-provider-quick-selection.prototype.html), captured on `prototype/provider-quick-selection-2026-10-28`, remains evidence for the agreed workflow in [Define quick selection by major model provider](29-provider-quick-selection.md). Its visual design is rejected, not an accepted direction to polish or reproduce.

### Resolution and handoff

Resolve only after the live user approves the rendered web visual direction. Record the layout, visual priorities, useful accent semantics, visible controls, full labels and placement of secondary information, with links to the captured asset and the user's approval. [Amend the spec and write role-advice build tickets](31-amend-spec-and-build-tickets.md) must encode that approved direction while preserving the resolved functional and ranking decisions and source attribution; this ticket does not implement the permanent web interface or amend the spec itself.

## Comments

### 2026-10-30 — User rejected the visual presentation

The user's exact rejection of the earlier prototype was: “terrible unreadable design with so much noise, zero accents, zero structure”.

The provider workflow remains agreed. This new, open ticket addresses its visual presentation only; no redesign, prototype asset or product UI is implemented in this planning update.

### 2026-10-30 — Web interface and full labels clarified

The user clarified: “I want to get rid of these abbreviations since we're now in web and not in terminal”. The planned product interface is web, with full user-facing labels; the earlier CLI/TUI-only direction is superseded. Runtime implementation and internal identifiers are unchanged by this planning update. The provider workflow remains settled, and a concrete rendered visual direction still requires explicit live user approval.

### 2026-10-30 — Rendered alternatives published for live review

The replacement prototype is captured on [the provider-selection web prototype branch](https://github.com/azarakovskiy/llm-ratings/tree/prototype/provider-selection-web-2026-10-30), [commit `dd44964`](https://github.com/azarakovskiy/llm-ratings/commit/dd44964), without a PR or merge. [Prototype assets](https://github.com/azarakovskiy/llm-ratings/tree/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web) include [the entry HTML](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/index.html), classic JavaScript, CSS and rendered screenshots. Product code, the permanent spec and build tickets remain unchanged.

Three candidate directions share the approved role and selection policies:

- **Focus desk**: left role navigation, a wide model comparison, and an on-demand evidence drawer. [Rendered Focus desk](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/A-desktop.png); [local interactive Focus desk](http://127.0.0.1:4186/?variant=A).
- **Comparison canvas**: top role navigation, with model comparison and the selected model's evidence side by side. Throughput moves into evidence where needed to retain readable desktop columns. [Rendered Comparison canvas](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/B-desktop.png); [local interactive Comparison canvas](http://127.0.0.1:4186/?variant=B).
- **Provider lens**: left creator navigation, role and objective above the comparison, an aligned primary/runner-up shelf, and explicitly opened inline evidence. [Rendered Provider lens](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-desktop.png); [local interactive Provider lens](http://127.0.0.1:4186/?variant=C).

Cobalt identifies the current selection; teal identifies frontier or primary-pick priority; amber identifies unavailable advice and its recovery. Comparable numbers align in table columns. Full labels and visible web controls replace terminal abbreviations. Source/date and the preview caveat sit beside the comparison. Policy, definitions and preview scenarios use secondary disclosures; creators without picks remain accessible in a labelled disclosure rather than preceding useful picks.

The artifact embeds five scored fixture models at all 21 recorded configurations plus two identifiable source-only models. It explicitly says **curated preview fixture, not live market advice**, gives the README-recorded 5 August 2026 snapshot date, and discloses the fixture's fictional model names and synthesized Terminal-Bench/OpenRouter data. Missing shortcut coverage is not evidence about real providers. OpenRouter token share remains unavailable. The one synthetic scenario hides Luna's timing without changing its scores, matching task cost or rank.

Browser verification exercised:

- Nineteen selection-policy assertions against the running artifact: index-specific effort/order, the inclusive price floor, unsupported objectives without fallback, no Coding cost advice, distinct picks, single/empty results, source-only unranked models, provider-invariant grades and provider-scoped, floor-free advisory comparisons, and timing-independent selection.
- Twelve final visible-control assertions: retained constraints, objective defaults, each named-only recovery, full creator selection, single-pick explanation, model evidence and independent sources, distinct timing measures, missing timing, native dialog dismissal and keyboard/URL variant navigation.
- All three rendered variants in both views at 390 pixels wide: document width stayed 390 pixels; wide tables scroll within their own containers. An observed accessible-label overflow was fixed by positioning its shared scroll wrapper, not by hiding page overflow.
- Desktop visual review at 1440 pixels wide; direct `file://` loading; no application browser errors observed.

Additional visual evidence: [Provider picks](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-provider-picks.png), [Coding-index comparison](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/A-coding-index.png), [unavailable objective and recovery](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/A-objective-unavailable.png), and [phone layout](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/B-phone.png).

Local preview command:

```sh
python3 -m http.server 4186 --bind 127.0.0.1 --directory /tmp/llm-ratings-provider-web-20261030/.scratch/llm-ratings/assets/33-provider-selection-web
```

The local server is running; verification tabs were closed. The floating arrows switch the three URL-addressable layouts while retaining working selections. **Awaiting the live user's verdict; no direction is approved and this ticket remains claimed.** No resolution or Decisions-so-far entry is recorded yet.

### 2026-10-31 — Live visual approval

After reviewing the rendered alternatives, the user selected **“Approve Provider lens”** in response to “Which rendered direction do you approve for the planned web interface?” This explicitly approves Provider lens, not the agent's recommended Focus desk. The earlier awaiting-verdict comments are chronological history; the Answer below is the resolved direction.

## Answer

Resolved with the live user on **2026-10-31**. **Provider lens, variant C, is the approved visual direction** for the planned web interface.

### Approved layout and hierarchy

- **Creator navigation at the left.** Keep All providers, the fixed OpenAI, Anthropic, Google, DeepSeek and xAI shortcuts, and the full creator chooser visible. A provider is the model creator, not an API gateway.
- **Selection controls above the comparison.** The main header contains the eight-role chooser, objective and capability filter, with the active role's purpose and selected index. Keep the active provider and advisory comparison scope visible beside the results.
- **Comparison is the primary work area.** Start in Model table. Keep Model table / Provider picks as visible tabs. Model table uses aligned model, effort, selected-index score and applicable comparison columns; retain the Intelligence frontier/dominated distinction without implying that Coding or Agentic have a cost frontier.
- **Provider picks is an aligned comparison shelf.** Show Primary and Runner-up side by side for each creator, with model, selected effort, score, grade and applicable objective metric aligned for scanning. Creators with picks appear before the secondary disclosure for creators without qualifying models. Opening that disclosure preserves their reasons; choosing an empty creator still produces the full explicit empty state and recovery actions.
- **Model evidence opens inline, only on request.** A visible Details action expands evidence at the relevant model rather than opening a permanent competing panel or expanding from a passive selection. Keep provider and capability selection across role/view changes and reset stale row/detail selection when the result set changes.

### Visual priorities and labels

- Use restrained cool neutral surfaces, dark readable text, humanist sans-serif typography and tabular numeric alignment. Preserve readable text and comparison density; avoid decorative dashboards, equal-weight status panels and instruction walls.
- **Cobalt means current selection or focus; teal means frontier or primary-pick priority; amber means unavailable advice or recovery.** Text labels and the comparison scope must carry the meaning without relying on color alone. A creator's Primary label does not claim global frontier membership.
- Use **Highest capability**, **Best value**, **Lowest qualifying price**, full effort names and **Artificial Analysis**. Use clear selected-index score, benchmark task cost, capability per dollar, time-to-first-answer and output-throughput labels rather than terminal codes.
- Put linked source attribution and fetch date beside the comparison. The captured prototype's preview-fixture caveat belongs with its data, not below a long page.

### Secondary information and edge states

- **How picks work** holds role defaults, index/proxy limitations, objective order, eligibility, grade reference sets, strict matched-cost limits, tie rules, timing definitions and source provenance in secondary disclosures.
- **Inline model evidence** retains measured efforts, chosen configuration, source-specific scores/grades and source URLs, distinct published timing measures, available catalog metadata, and Intelligence-only frontier, replacement and cheaper-alternative evidence. Keep token list prices separate from matching benchmark task cost.
- In Provider picks, supporting timing and non-primary comparison metrics can move into Details rather than repeat long metric stacks in every pick. Time to first answer token includes thinking; output tokens per second remains a separate measure. Missing timing stays unavailable, with no reconstruction or effect on selection.
- Preserve explicit empty, single-pick, unranked and unsupported-objective states. Never fabricate a runner-up or silently change the selected index/objective, provider or capability filter. Each visible recovery action changes only its named constraint.
- On narrow screens, controls reflow and wide comparison tables scroll inside their own containers, without page-level horizontal overflow or reduced text size.

### Captured primary source and verification

- [Published prototype branch](https://github.com/azarakovskiy/llm-ratings/tree/prototype/provider-selection-web-2026-10-30), [commit `dd44964`](https://github.com/azarakovskiy/llm-ratings/commit/dd44964), and [complete prototype assets](https://github.com/azarakovskiy/llm-ratings/tree/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web).
- Approved surfaces: [Provider lens Model table](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-desktop.png) and [Provider lens Provider picks](https://github.com/azarakovskiy/llm-ratings/blob/dd44964/.scratch/llm-ratings/assets/33-provider-selection-web/C-provider-picks.png). The entry HTML selects this direction with `?variant=C`.
- The preceding rendered-review comment records the browser evidence: nineteen policy assertions, twelve final visible-control assertions, desktop review, all three variants in both views at 390 pixels without page overflow, direct-file loading, and no observed application browser errors.
- The embedded fixture is explicitly not live market advice. Its fictional model names, synthesized source rows and missing creator coverage do not establish real model performance or provider coverage. The variant switcher and Preview states are review aids, not additional product requirements.

### Handoff and scope

[Define quick selection by major model provider](29-provider-quick-selection.md) remains the workflow authority; [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md) remains the ranking and availability authority. This visual approval does not replace or relax either decision.

[Amend the spec and write role-advice build tickets](31-amend-spec-and-build-tickets.md) is now unblocked and must encode Provider lens, its full labels, secondary information and explicit recovery alongside those authorities. No new decision ticket or fog patch is needed.

The prototype remains isolated and unmerged. Product code, the permanent spec, build tickets and internal identifiers are unchanged by this decision. No new domain term was introduced, so `CONTEXT.md` is intentionally unchanged.
