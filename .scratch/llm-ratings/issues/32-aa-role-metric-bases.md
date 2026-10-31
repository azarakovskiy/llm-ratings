# Verify AA index cost bases and latency semantics

Type: research
Labels: wayfinder:research
Status: resolved
Related: [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md)
Parent: [LLM Ratings: human-readable agent roles and provider quick selection](../map.md)

## Question

Which published Artificial Analysis measurements can support per-role advice using the Intelligence, Coding and Agentic indexes without mixing incompatible price or timing bases?

Establish from primary sources what each available index measures and how its current API fields identify it. Determine whether AA publishes a comparable per-task cost for each index, whether the Intelligence Index per-task cost can legitimately be reused for Coding or Agentic value calculations, and which costs are actually available through the project's free-tier source. Distinguish list input/output token prices, blended token prices and observed benchmark per-task costs; do not manufacture a task token mix.

Also establish the definitions and workload basis of TTFT, time to first answer token, end-to-end response time and output tokens/s, including reasoning-token treatment, effort specificity, missing values and any public comparison limits. Separate public documentation, observed API or fixture fields, and unsupported assumptions.

Capture dated, cited findings in an isolated `research/<name>` branch, push it without a PR and link the immutable findings from this ticket. This prerequisite supplies facts; the parent grilling ticket retains the user's role mappings, objectives and latency-policy decisions.

## Answer

Resolved 2026-10-28 by primary-source research. [AA index, cost and latency findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md) contain the dated citations, schema paths, comparison limits and search boundary.

- Only Intelligence has an established matching per-task cost in the current Free or paid language-model schemas. Coding/Agentic score divided by Intelligence task cost would be an explicit cross-workload proxy, not measured same-index value; the same issue affects price-above-floor and frontier claims.
- The API Coding and Agentic scores are composites, but their complete current formulas could not be established after the Intelligence v5 change. The separate Coding Agent Index and its costs are not substitutes for the API Coding score.
- The Free schema supports TTFT, time to first answer token, output tokens/s and estimated end-to-end time for 500 answer tokens when reported. Their meanings differ; the Free route's exact prompt preset and provider aggregation remain undocumented. No authenticated live API response was inspected.

Published on `research/aa-role-metrics`, commit `0c26a6174644ef292b616bf704bf2c72a4043b79`, from a separate worktree; no PR and no merge. [Choose AA signals and objectives for the agreed roles](30-role-advice-criteria.md) retains the user's index, objective, floor and display-policy decisions.
