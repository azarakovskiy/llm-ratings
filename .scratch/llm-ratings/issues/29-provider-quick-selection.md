# Define quick selection by major model provider

Type: prototype
Labels: wayfinder:prototype
Status: resolved
Blocked by: —
Related: [Choose human-readable cross-harness role stereotypes](28-name-human-readable-roles.md); [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md)
Parent: [LLM Ratings: human-readable agent roles and provider quick selection](../map.md)

## Question

What quick-selection workflow lets a human choose models by major LLM provider while retaining useful role-based advice?

Resolve this with the user through a cheap concrete prototype. Provider has the existing glossary meaning of model creator, not an API gateway. Decide whether quick selection filters the current role's candidates, shows a best pick per provider, or uses another clearly specified interaction; do not assume these produce the same result. Settle how a provider is selected and reset, what qualifies for the major-provider shortcuts, how other providers remain reachable, and what an empty provider/role intersection shows.

Keep all providers available. The former anthropic/openai restriction applied only to the now-removed config export and is not a restriction on this workflow. Use current role names as temporary labels if the naming decision is still open; this workflow question need not wait for final names.

Link the prototype from the ticket. Do not build the permanent UI or generate harness config as part of this decision.

## Comments

### 2026-10-28 — Workflow prototype, awaiting user decisions

- [Provider quick-selection workflow prototype](https://github.com/azarakovskiy/llm-ratings/blob/29beda7bb4872c8640d19c4b15e4d01405d134c3/.scratch/llm-ratings/assets/29-provider-quick-selection.prototype.html) — self-contained HTML, now archived on its throwaway branch. The first iteration compared table filtering with one objective winner per provider; the final version includes the user's runner-up requirement and provider-scoped comparisons.
- Uses recorded configurations from the checked-in fixture snapshot, with temporary role names and the existing Intelligence-based objectives. Shortcut membership and workflow defaults in the demo are proposals, not decisions; missing snapshot rows are not evidence of a provider's real-world coverage.
- Browser smoke exercised both views, cross-role retention, the full creator menu, empty intersections and explicit recovery. No browser errors were reported. The permanent TUI is unchanged.
- Awaiting the live user's choice before recording an answer, closing this ticket or adding a decision to the map.

### 2026-10-28 — First user choices

- The user requested both views, adding “2nd best model too” to the provider-picks view.
- The user accepted the fixed shortcut list: OpenAI, Anthropic, Google, DeepSeek and xAI; every other creator remains reachable through the full provider menu.
- Updated the linked prototype to show up to two distinct models per provider. Distinct-model semantics, objective ranking, shared provider state, advisory comparison scope and empty/short shortlist behavior remain proposals pending the next live exchange.

## Answer

Resolved with the user on 2026-10-28 through the linked prototype and two live question rounds. The user explicitly selected both views with a second-best model, the fixed shortcut list, two-distinct-model semantics, shared selection with the table first, and provider-constrained advice.

### Two views, one ranking policy

- **Model table** is the initial view. It retains all eligible models for the active role, restricted by the provider selection and active capability filter. Each row is a model at its objective-selected effort. Keep frontier/dominated sections, with the role's objective ordering within each section.
- **Provider picks** shows a **Primary** and **Runner-up** for each selected creator: up to two distinct models, each at its objective-selected effort. Apply active eligibility rules and capability filters before taking the first two models under the active role objective.
- Picks use the objective's ranking directly, not the first two rows of the frontier-first model table. A dominated model can therefore be a primary or runner-up. There is no added price-diversity heuristic, weighted score or provider-specific scoring rule.
- The second pick is a different model, not another effort of the primary. It is not a specially selected cheaper alternative; the existing detail-alternative concept remains separate.
- [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md) owns each role's index, objective, floors, tie-breaks, metric bases and missing-data eligibility. Both views must consume that same policy rather than invent competing rankings.

### Provider selection and shortcuts

- A provider is the AA model creator, not an API gateway. Select exactly one creator or **All providers**; a new session starts with All providers.
- The fixed shortcut set is **OpenAI, Anthropic, Google, DeepSeek and xAI**. This is a curated product choice, not a market-share threshold or a list recomputed from ratings, token share, the current role or its filters.
- The full provider chooser also exposes every other creator in the loaded catalog. Shortcuts are not an allowlist; a creator without a shortcut remains selectable. Do not remove a creator merely because the current role/filter has no eligible model for it.
- A shortcut whose creator has no qualifying data can still lead to the explicit empty state. Do not mistake the prototype's small fixture coverage for real-world provider coverage.

### Navigation and reset

- **`p`** opens the provider chooser, containing the shortcuts, the full creator list and All providers. **`v`** switches Model table / Provider picks. Existing role navigation remains unchanged.
- Role and view changes retain the provider selection and capability filter. Reset the row cursor when the role, view, provider or capability filter changes; do not carry a stale selected row across different result sets.
- **All providers** clears only the provider constraint. It does not clear the capability filter, change the role or switch views. Capability-filter recovery is a separate, explicit action.
- These are session state, not a request for saved preferences or harness configuration. Existing role/objective behavior remains the baseline except where the separate ranking decision changes it.

### Provider selection constrains advice, not scores

- Selecting one creator restricts candidate rows **and** the comparison universe for the frontier, frontier path, replacement arrows and detail alternatives to that creator.
- Comparison points still span the included models' reasoning efforts. Preserve the existing floor-free advisory behavior: the capability display filter and the role's price-lens floor do not discard comparison points within the selected creator universe.
- Scores and capability/value/speed/price grades keep their existing reference sets. Do not re-bin a selected creator into misleading provider-relative grades.
- With All providers selected, restore global comparisons. Provider picks still choose primary/runner-up within each creator, even when their configurations are globally dominated.
- Show the selected provider/comparison scope so provider-local frontier membership is not presented as a global claim.

### Empty and short results

- One eligible model produces one pick, with no fabricated runner-up. Zero eligible models produces an explicit empty state naming the selected role, provider and active constraints.
- Retain the user's selection. Do not substitute another creator, repeat the same model at a second effort, silently relax filters, invent a missing score or widen eligibility.
- Offer explicit recovery through All providers and, when applicable, clearing the capability filter. Each action changes only its named constraint.

### Prototype source and verification

- [Captured HTML source](https://github.com/azarakovskiy/llm-ratings/blob/29beda7bb4872c8640d19c4b15e4d01405d134c3/.scratch/llm-ratings/assets/29-provider-quick-selection.prototype.html) · [raw self-contained HTML](https://raw.githubusercontent.com/azarakovskiy/llm-ratings/29beda7bb4872c8640d19c4b15e4d01405d134c3/.scratch/llm-ratings/assets/29-provider-quick-selection.prototype.html).
- Published on `prototype/provider-quick-selection-2026-10-28`, commit `29beda7bb4872c8640d19c4b15e4d01405d134c3`, without a PR or merge. Download the raw HTML and open it directly; no server or dependencies are required. The prototype is not kept on the working branch.
- The prototype records five fixture models and all 21 of their AA effort configurations. Its temporary shipped role labels and Intelligence-based objectives are not the final role catalog or new role-specific metric policy.
- Browser smoke completed all five guided walkthroughs: table/top-two, provider constraint, role switching, empty intersection and unpinned creator. It exercised primary/runner-up ordering, single-pick behavior, retained filters, explicit recovery and `p`/`v`; no browser errors were reported.
- Concrete scope check: in the Coder fixture, OpenAI's Sol max becomes provider-frontier when OpenAI is selected; All providers restores its global domination by Claude Opus 5 high. OpenAI's picks remain Sol max and GPT-5.5 xhigh, each retaining its original grade.
- Visual verification covers the throwaway HTML workflow only. The permanent TUI, full frontier path and detail screen were not implemented or exercised as new features.

### Handoff

- `CONTEXT.md` now defines provider selection and provider picks, and scopes frontier/dominated/alternative terminology to that selection.
- [Amend the spec and write role-advice build tickets](31-amend-spec-and-build-tickets.md) already depends on this decision and must encode it after the remaining ranking prerequisites resolve. The permanent spec and runtime remain intentionally unchanged in this planning session.
- No new decision ticket or fog patch was exposed. Harness export, gateway routing and provider-level pricing remain outside this destination.
