# Survey task roles in mainstream coding assistants

Type: research
Labels: wayfinder:research
Status: resolved
Blocked by: —
Parent: [LLM Ratings: human-readable agent roles and provider quick selection](../map.md)
Research branch: `research/mainstream-agent-roles`

## Question

What recurring agent-task stereotypes and model-selection profiles are documented in Claude Code, OpenAI Codex, Cursor and GitHub Copilot, and which are native roles rather than permission modes, user-authored examples or product branding?

Use official documentation and first-party source code. For each harness, record the native term, actual purpose, concrete tasks, whether it is an agent definition, workflow mode or model-routing profile, and any documented model-selection or quality, latency, price, context and modality implications. Distinguish codebase exploration, external research, implementation, planning, review and coordination only when the sources support those distinctions; do not manufacture a role just to fill a comparison table.

Record access dates and version context where available. Negative findings mean that the reviewed sources did not document a feature, not proof that no such feature exists. Report presence within this named sample, not market-wide prevalence. Do not choose final generic names or recommend models.

Capture the cited findings in `assets/27-mainstream-agent-roles.md` on the research branch, push it without a PR and never merge it. The resolution should link the published asset rather than paste it into this ticket.

## Answer

Resolved 2026-10-28. Official sources were accessible for all four named products.

Exploration, planning, implementation, review and coordination recur as tasks, but they are implemented as different combinations of agents, modes, workflows and managed services. External research and independent second-opinion critique have explicit native support in parts of the sample. A recurring purpose does not imply a universal agent name or an exposed, independently selectable model slot.

The survey preserves current surface/version distinctions, custom-example boundaries, and the same-day Copilot cloud transition. It records a conflict between VS Code's Edit settings reference and versioned removal notes rather than flattening them into one inventory. These limits do not prevent the role-naming discussion; they do prevent claims of universal native defaults or market-wide prevalence.

Findings: [Mainstream coding assistants — native roles and model-selection profiles](https://github.com/azarakovskiy/llm-ratings/blob/87ff325fbbffc82c8fc24566e0180cf6de9a4a36/.scratch/llm-ratings/assets/27-mainstream-agent-roles.md).

Published on `research/mainstream-agent-roles`; the research branch is not merged. Final role names, grouping and provider selection remain HITL decisions.
