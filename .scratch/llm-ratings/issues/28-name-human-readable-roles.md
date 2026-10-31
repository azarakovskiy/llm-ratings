# Choose human-readable cross-harness role stereotypes

Type: grilling
Labels: wayfinder:grilling
Status: resolved
Blocked by: 26, 27
Related: [Survey roles and model-routing profiles in configurable harnesses](26-survey-harness-routing-roles.md); [Survey task roles in mainstream coding assistants](27-survey-mainstream-agent-roles.md)
Parent: [LLM Ratings: human-readable agent roles and provider quick selection](../map.md)

## Question

Which recurring stereotypes from the cross-harness evidence should become LLM Ratings roles, and what clear human-readable names, short purposes, concrete task examples and boundaries distinguish them?

Resolve this with the user using grilling and domain-modeling. The shipped Chores/Generic/Researcher/Coder/Orchestrator catalog is a baseline, not a constraint. The desired names should explain what a model is being selected for without requiring knowledge of omp or another harness's internal keys.

Use the surveys to distinguish task purpose from operating profiles such as fast/cheap versus thorough, and from capabilities such as vision. Decide which distinctions merit separate roles and which are attributes; do not import every native harness label or treat custom examples as common defaults. Test overlapping names against concrete tasks so that research, exploration, planning, implementation, review and coordination are neither collapsed nor split without a reason.

Record the agreed catalog in the resolution and update `CONTEXT.md` as terms settle. Preserve source mappings as evidence, not as configuration-export requirements. The agent must not choose the final names on the user's behalf.

## Answer

Resolved 2026-10-28 through a live grilling and domain-modeling discussion. The user answered **“yes to all”** to the four questions covering task-purpose roles, the six core roles, Generalist and Utility, and the decision not to add specialist roles to the initial catalog.

### Agreed catalog

| Role | Purpose | Concrete task | Boundary |
| --- | --- | --- | --- |
| **Explorer** | Find and explain existing code and repository behavior. | “Where is authentication checked?” | Describes what exists; choosing an implementation approach belongs to Planner. |
| **Researcher** | Verify external facts and produce sourced findings. | “Which API supports resumable uploads?” | External evidence, not a local repository map. |
| **Planner** | Choose an approach and produce decisions and an actionable plan. | “How should we migrate authentication?” | Planning, not implementation or management of delegated workers. |
| **Coder** | Make and verify changes, including fault diagnosis. | “Find why uploads fail, fix the cause and verify the result.” | Owns changes and verification; independent assessment belongs to Reviewer. |
| **Reviewer** | Independently assess a change or proposal for problems. | “What breaks in this patch or migration plan?” | Includes security assessment and second-opinion critique; implementing fixes is separate work. |
| **Coordinator** | Divide and delegate work, manage dependencies and combine results. | “Manage this cross-module migration across workers.” | Owns work boundaries and synthesis, not each worker's implementation. |
| **Generalist** | Handle mixed, end-to-end work when no specialist fits. | “Investigate this request, make the change and explain the result.” | A mixed-purpose selection, not a synonym for every narrower role. |
| **Utility** | Produce bounded auxiliary outputs. | “Write a title or commit message; classify these items; transform this text.” | Small output does not imply low capability needs. Memory extraction and faithful summarization are not automatically trivial utility work. |

### Distinctions and naming

- Roles describe **what work is needed**. Fast/cheap/thorough preferences, reasoning effort, context needs and capabilities such as vision remain separate requirements or selection guidance. “Research this API quickly” is still Researcher, not a separate Fast role.
- Keep Explorer and Researcher separate: locating and explaining local evidence differs from verifying external sources.
- Keep Planner, Coder, Reviewer and Coordinator separate: choosing an approach, making changes, assessing them independently, and managing delegated work have different responsibilities.
- Rename Chores → Utility, Generic → Generalist and Orchestrator → Coordinator. Retain Researcher and Coder with the boundaries above; add Explorer, Planner and Reviewer.
- Do not add separate Debugger, Designer, Security Reviewer, Test Writer, Documentation Writer or Advisor roles to the initial catalog. Fault diagnosis and implementation specialties, including UI design, tests and documentation, sit with Coder. Security assessment and second-opinion critique sit with Reviewer. Preserve specialist requirements in descriptions; revisit a separate role when it represents a distinct model-selection need, not merely a native harness name.

### Source mappings

These are interpretations of documented duties, not claims of universal native roles, market prevalence, equivalent permissions or independently selectable model slots. The linked surveys preserve native agents versus modes, custom examples, routing profiles and version limits.

| Agreed role | Representative evidence |
| --- | --- |
| Explorer | [Harness survey]: omp scout and OpenCode Explore. [Assistant survey]: Claude Explore, Codex explorer, Cursor Explore and Copilot CLI explore. |
| Researcher | [Harness survey]: omp librarian. [Assistant survey]: Claude's bundled deep-research workflow and Copilot research; Codex's docs_researcher is a custom example, not a bundled default. |
| Planner | [Harness survey]: omp/OpenCode planning, Aider architect's proposal stage, Cline Plan and historical Roo Architect. [Assistant survey]: planning workflows in all four sampled products; they are not four equivalent planner subagents. |
| Coder | [Harness survey]: omp task/sonic, OpenCode Build, Aider code/editor, Cline Act and historical Roo Code. [Assistant survey]: Codex worker and the products' general implementation workflows. Roo Debug and Cursor Debug support the diagnosis duty without requiring a separate catalog role. |
| Reviewer | [Harness survey]: omp reviewer/security-reviewer/advisor, plus explicitly qualified custom review examples elsewhere. [Assistant survey]: native review workflows, Claude Advisor and Copilot rubber-duck; managed review does not necessarily expose model choice. |
| Coordinator | [Harness survey]: parent/child delegation, Cline teams and historical Roo Orchestrator. [Assistant survey]: Claude team lead, Codex main-agent orchestration, Cursor Project coordinator and Copilot fleet. |
| Generalist | [Harness survey]: omp task and OpenCode General. [Assistant survey]: Claude general-purpose/claude, Codex default and Copilot general-purpose. |
| Utility | [Harness survey]: omp tiny/commit, OpenCode title and Aider weak-model commit generation. Those native slots can have other duties; this mapping does not classify all summarization or context maintenance as simple work. |

[Harness survey]: https://github.com/azarakovskiy/llm-ratings/blob/d8bce234e1ae0d97685fe1fc156ff50748bd7ac4/.scratch/llm-ratings/assets/26-harness-routing-roles.md
[Assistant survey]: https://github.com/azarakovskiy/llm-ratings/blob/87ff325fbbffc82c8fc24566e0180cf6de9a4a36/.scratch/llm-ratings/assets/27-mainstream-agent-roles.md

### Planning handoff

- Canonical terms are recorded in [the domain glossary](../../../CONTEXT.md).
- [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md) now has its catalog prerequisite resolved. It must choose each role's index, objective, floors, ties, missing-data behavior and latency treatment; this resolution assigns none of those.
- [Amend the spec and write role-advice build tickets](31-amend-spec-and-build-tickets.md) will encode the catalog and boundaries after the remaining decisions. The shipped runtime catalog and current spec are intentionally unchanged in this planning session.
- No new decision ticket or fog patch was exposed. Provider quick selection remains with [Define quick selection by major model provider](29-provider-quick-selection.md); harness configuration export remains outside the destination.
