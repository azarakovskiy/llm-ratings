# Amend the spec and write role-advice build tickets

Type: task
Labels: wayfinder:task
Status: resolved
Blocked by: 29, 30, 33
Related: [Choose human-readable cross-harness role stereotypes](28-name-human-readable-roles.md); [Define quick selection by major model provider](29-provider-quick-selection.md); [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md); [Redesign the provider-selection prototype for readable model advice](33-redesign-provider-selection-prototype.md)
Parent: [LLM Ratings: human-readable agent roles and provider quick selection](../map.md)

## Question

What exact amendments to `spec.md` and separately runnable build tickets encode all resolved decisions for human-readable roles, per-role model × effort advice, quick selection by major provider and the user-approved web visual direction?

This AFK task delivers the map's planning artifacts, not the implementation. Use the decision tickets as the authoritative detail; preserve their evidence and source references. Amend terminology, role profiles, ranking criteria, web behavior, missing-data cases and user stories only as the resolved decisions require. Write one ready-for-agent implementation issue per build slice using the repo's implementation-ticket conventions. The 2026-10-30 web clarification supersedes the terminal-only surface constraint; historical terminal layouts and keybindings are not current web requirements.

Before claiming this ticket, ensure all decision prerequisites and any newly surfaced questions are resolved, and add new blocking edges when the frontier exposes them. Do not treat an unresolved research limitation as a settled product decision.

Wait for explicit live user approval recorded in [Redesign the provider-selection prototype for readable model advice](33-redesign-provider-selection-prototype.md). Encode the approved web layout, visual hierarchy, useful accents and secondary-information placement in the amended spec and relevant build tickets, with links to the captured prototype and approval. Specify visible controls for role, objective, capability filter, both advice views, provider shortcuts/full chooser, All providers, model details and explicit recovery; historical terminal keybindings may be optional aids, never substitutes for visible controls. Preserve the settled two-view provider workflow, shared provider state, provider-scoped advice, source attribution and grade-reference invariance under provider changes.

Use Explorer, Researcher, Planner, Coder, Reviewer, Coordinator, Generalist and Utility and the final criteria from [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md), including strict matched-cost rules, unavailable-objective states and no timing-based selection or tie-breaks. Do not carry over the rejected prototype's visual design or its old five-role, Intelligence-only baseline. Keep unresolved role/index/floor/tie choices blocked until that decision resolves.

Require the full visible objective names **Highest capability**, **Best value** and **Lowest qualifying price**, **Artificial Analysis** in source attribution and clear metric labels instead of `cap`, `ppi`, `AA`, `TTFT` or opaque codes. Use clear headers and source attribution once where useful rather than repeating long labels everywhere. Proper source/brand names and currency symbols remain valid; do not invent brand expansions. Internal configuration keys, API fields and raw technical evidence may keep technical names internally; this wording update is not a runtime identifier migration.

This handoff specifies and build-plans the actual web interface without implementing it or merging prototype assets. Do not add unrequested dashboards or other product features.

Remove config-export and harness-integration requirements from the amended spec and build plan. No omp snippet, config diff, selector translation or config writes. Record what was amended and link the build tickets in the resolution.

## Answer

Resolved as an AFK planning task on **2026-10-31**, after the provider workflow and selection criteria were resolved and the live user approved **Provider lens** in [Redesign the provider-selection prototype for readable model advice](33-redesign-provider-selection-prototype.md#2026-10-31--live-visual-approval). No prerequisite remains open.

### Amended specification

[The amended role-advice and provider-selection web spec](../spec.md) replaces the terminal-only, five-role, Intelligence-only framing with:

- The eight agreed task-purpose roles, boundaries, selected indexes and default objectives, retaining the single editable role catalog and objective-selected measured effort per model.
- Exact within-model and cross-model comparison keys, strict matched Intelligence cost eligibility, the inclusive grade-2 price floor, cross-effort selected-index capability grades, independent source ratings, unavailable objectives and explicit unranked/empty results. Timing never selects or breaks ties.
- Model table and direct-objective Primary/Runner-up picks for distinct models, shared creator/filter state, fixed shortcuts plus the full creator chooser, provider-scoped floor/filter-free Intelligence advice and provider-invariant grade reference sets.
- The approved Provider lens hierarchy, useful accents, full labels, visible controls and named-only recovery, aligned comparisons, explicitly requested inline evidence, secondary How picks work disclosures and narrow-screen/access requirements.
- Source/fetch-date provenance, distinct published timing measures, list prices separate from matching benchmark task cost, retained source inclusion/acquisition contracts and truthful best-effort enrichment.
- A concrete local web launch and clean runtime cutover plan, preserving useful batch consumption while removing the superseded interactive terminal surface during implementation. Existing ADR conflicts are identified explicitly, not silently treated as web requirements.

The spec links the canonical decision Answers, immutable metric findings, captured Provider lens commit/screenshots and the live approval. The rejected visual design and its temporary roles/Intelligence-only demo do not govern implementation. Harness export/integration, selector translation, config writes and unrequested dashboards are excluded.

### Ready-for-agent build route

| Build ticket | Prerequisite |
| --- | --- |
| [Preserve index-specific metrics and source provenance](34-preserve-index-metrics-provenance.md) | None |
| [Implement the eight-role selection policy](35-eight-role-selection-policy.md) | Preserve index-specific metrics and source provenance |
| [Add provider-scoped advice and shared selection state](36-provider-scoped-advice-state.md) | Implement the eight-role selection policy |
| [Build the Provider lens web comparison](37-provider-lens-web-comparison.md) | Add provider-scoped advice and shared selection state |
| [Complete inline evidence and cut over to the web interface](38-inline-evidence-web-cutover.md) | Build the Provider lens web comparison |

Each is a separate `ready-for-agent` implementation issue with explicit blocking, bounded ownership, observable acceptance and runnable verification. Dependencies were wired after all files existed. Data/query slices require real fixture-fed consumer smoke; web slices require the actual rendered surface, not archived screenshots or tests alone. These build issues are not new wayfinder decision children.

### Terminology, limits and destination

[The domain glossary](../../../CONTEXT.md) now states the retained value/speed grade populations before provider/capability-display constraints, correcting stale per-effort wording to match the existing role-selected-row implementation and the provider-invariance decision. No role, index or objective identifier migration is added.

The incomplete current Coding/Agentic formulas, undocumented timing prompt/provider aggregation and unverified OpenRouter share access/coverage remain explicit source limitations. They are not settled formulas, a fabricated API contract, zero share or permanent product exclusions. Unsupported cost advice remains unavailable; the verified rating-source advice still works.

Product code, fixtures and runtime configuration are unchanged. No prototype/research assets were copied or merged, no feature implementation was performed, and no product runtime verification is claimed by this planning task.

The map's planning destination is reached: approved visual direction, amended spec and every build slice ticketed. No new decision ticket or fog patch was exposed. Implementation starts with [Preserve index-specific metrics and source provenance](34-preserve-index-metrics-provenance.md), in a separate build session.

Planning validation checked nine affected Markdown artifacts: **125 local links**, including **43 anchor links**, all valid; all 31 tracker issue identities/dependency targets exist and the graph is acyclic. All eight wayfinder children are resolved; five implementation issues are ready-for-agent, with only [Preserve index-specific metrics and source provenance](34-preserve-index-metrics-provenance.md) currently unblocked. Remote references were preserved rather than network-validated as a set. The spec authority review found no material discrepancy. Product tests/builds and browser/runtime smoke were not run because this task changes planning documents only.
