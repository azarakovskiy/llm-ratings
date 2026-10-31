# Survey roles and model-routing profiles in configurable harnesses

Type: research
Labels: wayfinder:research
Status: resolved
Blocked by: —
Parent: [LLM Ratings: human-readable agent roles and provider quick selection](../map.md)
Research branch: `research/harness-routing-roles`

## Question

What recurring kinds of agent work and model-routing profiles are documented in omp, OpenCode, Aider, Cline and Roo Code, and what do their actual responsibilities mean rather than just their names?

Use official documentation and first-party source code. Begin with [omp Model roles](https://omp.sh/docs/roles) and its linked explanation of agents versus model roles. For each harness, record the native term, purpose, concrete tasks, whether it is a model-routing slot, an agent definition, a workflow mode or an example/custom extension, and any documented quality, latency, price, context or modality requirements. Do not equate a permission mode with a task stereotype or infer that a named worker has its own model assignment.

Preserve source-specific distinctions, overlaps and unsupported claims. Record access dates and version context where available. Report presence within this named sample, not market-wide prevalence. Do not decide the final human-readable catalog or recommend model assignments.

Capture the cited findings in `assets/26-harness-routing-roles.md` on the research branch, push it without a PR and never merge it. The resolution should link the published asset rather than paste it into this ticket.

## Answer

Resolved 2026-10-28. Official evidence was accessible for all five named harnesses.

The sample distinguishes task purposes, specialist agents, workflow modes and model-routing profiles. Implementation, investigation, planning, review and coordination recur, while small utility work, context maintenance and modality-specific work expose additional requirements. Fast/cheap/thorough profiles cut across task purpose; a specialist name does not prove a separate model assignment.

The findings preserve source/version conflicts rather than invent one universal behavior. OpenCode's removed Scout is not counted as current native specialty evidence. Roo Code is archived and its final release is historical evidence; its conflicting child-profile documentation/source would require runtime verification for an exact routing guarantee. Such harness-specific routing is outside this effort and does not block naming task stereotypes.

Findings: [Harness duties and model-routing profiles](https://github.com/azarakovskiy/llm-ratings/blob/d8bce234e1ae0d97685fe1fc156ff50748bd7ac4/.scratch/llm-ratings/assets/26-harness-routing-roles.md).

Published on `research/harness-routing-roles`; the research branch is not merged. Final names, grouping and provider quick selection remain HITL decisions.
