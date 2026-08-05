# 10 Write the PoC spec

Type: task
Status: resolved
Blocked by: 05, 06, 07, 08, 09

## Question

Assemble `.scratch/llm-ratings/spec.md` — the build-ready spec for the PoC CLI from the resolutions of 05–09: sources & acquisition, data model, categories, tiers, ranking & output, operation. This is the destination artifact; a build session executes it.

## Answer

Spec written to `.scratch/llm-ratings/spec.md`, status `ready-for-agent`. Assembled from the resolutions of 05–09: the three-source acquisition contract (endpoints, auth, fetch-per-run, error contract, attribution), AA-anchored identity + alias join + inclusion rule, the five categories with fixed efforts, three-axis quintile tiering + PPI, and 09's frontier-structured TUI contract (sections, Δ columns, keymap, detail view). Test seam confirmed with the user: fetch boundary — an offline fixture mode so the full CLI is tested end-to-end with no network; the seam section, fixture strategy, and scenario list are in the spec. One deliberate open item handed to the build session: implementation language (Python recommended — prototype is Python, all sources are HTTP+JSON); everything else is locked. The map's five decisions were all locked before this ticket, so the map is complete — no new tickets, no fog to graduate.
