# Choose AA signals and objectives for the agreed roles

Type: grilling
Labels: wayfinder:grilling
Status: resolved
Blocked by: 28, 32
Related: [Choose human-readable cross-harness role stereotypes](28-name-human-readable-roles.md); [Verify AA index cost bases and latency semantics](32-aa-role-metric-bases.md); [Define quick selection by major model provider](29-provider-quick-selection.md); [Redesign the provider-selection prototype for readable model advice](33-redesign-provider-selection-prototype.md)
Parent: [LLM Ratings: human-readable agent roles and provider quick selection](../map.md)

## Question

How should each agreed role select and compare model × effort configurations using the available Artificial Analysis Intelligence, Coding or Agentic index and the role's actual requirements?

Resolve this with the user using grilling and domain-modeling. Start from the existing Highest capability, Best value and Lowest qualifying price objectives rather than assume a new scoring engine. Make the chosen index, objective, any capability floor, ties, and the result when nothing qualifies precise. Establish the appropriate published price basis before using Coding or Agentic scores in a value calculation; the checked-in fixture's Intelligence Index per-task cost does not by itself establish index-specific cost comparability.

Also settle which available latency number should be shown (time to first token, time to first answer token or end-to-end response time), and whether latency affects any role's selection rather than merely explaining the result. Distinguish output tokens per second from latency. Surface any missing source facts as research prerequisites instead of inventing metrics or silently reusing a mismatched denominator.

Keep cross-source ratings distinct and OpenRouter token share display-only. This is model advice, not omp mapping, selectors or config export.

## Comments

### 2026-10-28 — Provider workflow boundary

[Define quick selection by major model provider](29-provider-quick-selection.md) records the provider workflow contract. This ticket still owns the index, objective, floors, ties, missing-data policy and metric bases used consistently by both advice views; it does not need a separate provider-specific scoring rule.

### 2026-10-28 — First grilling round

The user answered **“ok to all”** to these recommendations:

- Default priorities: Planner, Coder, Reviewer and Coordinator favor highest capability; Explorer, Researcher and Generalist favor capability per dollar where a valid cost basis exists; Utility favors the lowest price meeting a capability floor. Exact index assignments, supported value formulas and floor values remain open.
- Timing is explanatory only for every role: no latency or throughput filters, weights or tie-breaks. Remove the current output-speed tie-break under `price`. The displayed latency measure awaits verified source semantics.
- Do not substitute another index or weaken requirements when a model lacks qualifying data or configurations. Leave it unranked with a reason; if the whole candidate set fails, report **“No qualifying configuration”** rather than a fallback recommendation.

This is a partial agreement, not the ticket's resolution. [Verify AA index cost bases and latency semantics](32-aa-role-metric-bases.md) is researching the source facts needed for the next round.

### 2026-10-30 — Cost-basis and latency choices

The user explicitly accepted Q6 and Q7:

- **Strict matching cost bases:** Intelligence supports `cap`, `ppi` and `price`. Coding/Agentic support `cap` only, without price-based ties, cost frontiers or cheaper alternatives. Unsupported objectives explain their unavailability rather than silently switching indexes or using Intelligence task cost as a cross-workload proxy. Coding/Agentic score ties use lower effort, then canonical model key.
- **Latency display:** the main latency column is AA's published median time to first answer token, in seconds, including thinking. Output tokens/s remains separate. Missing latency displays `—`, with no substitution or reconstruction. Detail may show TTFT and estimated response time for 500 answer tokens, distinctly labelled and not described as agent-task duration.

Source facts are resolved in [Verify AA index cost bases and latency semantics](32-aa-role-metric-bases.md). Q4 (floor value and cross-effort reference set) and Q5 (general deterministic comparison rules) remain unanswered. Role-index assignments also remain open; this ticket is not resolved.

The user also requested to see the earlier [provider quick-selection prototype](https://github.com/azarakovskiy/llm-ratings/blob/29beda7bb4872c8640d19c4b15e4d01405d134c3/.scratch/llm-ratings/assets/29-provider-quick-selection.prototype.html). Its temporary role labels and Intelligence-only fixture objectives are not this ticket's final criteria.

### 2026-10-30 — Final criteria proposal and separate visual redesign

The user rejected the earlier prototype's visual presentation and asked to finish this decision before redesigning it. [Redesign the provider-selection prototype for readable model advice](33-redesign-provider-selection-prototype.md) now owns the visual question; it does not reopen the agreed provider workflow or resolve the remaining selection choices on the user's behalf.

The following final bundle is proposed for live confirmation, not yet approved:

| Role | Artificial Analysis index | Default objective |
| --- | --- | --- |
| Explorer | Intelligence | Best value |
| Researcher | Intelligence | Best value |
| Planner | Intelligence | Highest capability |
| Coder | Coding | Highest capability |
| Reviewer | Coding | Highest capability |
| Coordinator | Agentic | Highest capability |
| Generalist | Intelligence | Best value |
| Utility | Intelligence | Lowest qualifying price |

- These assignments use published scores as proxies, not verified task-role performance. Intelligence preserves the confirmed value preference for Explorer, Researcher and Generalist on the only established matching cost basis. Coding is a proxy for implementation and code-oriented assessment, not a measured review-accuracy score. Agentic is a tool-work proxy, not proof of multi-agent coordination quality. The current area-index formula gaps remain explicit source limitations.
- **Floor and grades:** use an inclusive minimum capability grade of 2 only under Lowest qualifying price, including an Intelligence role's manual override to that objective. Calculate Artificial Analysis capability grades from all scored model × effort configurations for the selected index in the refresh, not separate effort groups or provider-relative populations. Preserve the existing distinct-value grading method; other sources' independent grades remain unchanged. Highest capability and Best value remain floor-free.
- **Intelligence comparisons:** Highest capability sorts by score descending, then task price ascending; Best value by score/task price descending, then score descending and task price ascending; Lowest qualifying price by qualifying task price ascending, then score descending. Apply the same keys to per-model effort selection and cross-model objective order, including provider picks. Remaining exact ties use lower effort, then canonical model key. Frontier-first table sections remain distinct from the direct objective order used by provider picks.
- **Required data:** an Intelligence recommendation needs the selected score and a finite, non-negative matching Intelligence task cost; Best value additionally requires a positive cost. A Coding/Agentic Highest capability recommendation needs its selected score, not a nonexistent matching cost. Non-finite or missing required values do not qualify. A published zero task cost does not provide a finite value ratio.
- **Unavailable objectives and data:** a Coding/Agentic Best value or Lowest qualifying price override shows an explicit unsupported-objective state without switching indexes, using a proxy denominator or silently reverting the user's selection. No qualifying effort leaves a model unranked with its reason; no eligible model produces the already-agreed explicit empty state. Missing timing does not make an otherwise eligible configuration unranked.

The already-confirmed strict cost-basis, no-timing-selection, first-answer-latency and no-fallback policies remain unchanged. This HITL ticket remains claimed until the user confirms the final bundle; no runtime code or permanent spec is changed here.

### 2026-10-30 — Web interface and full visible names

The user requested removal of the abbreviations, explaining that the interface is now web rather than terminal. Use **Highest capability**, **Best value** and **Lowest qualifying price** as the objective labels. Use **Artificial Analysis** for source attribution and clear metric names such as **Intelligence score**, **Benchmark task cost**, **Output tokens per second**, **Time to first answer token** and **Time to first token**. Do not expose compact terminal headings or configuration codes as interface labels; source attribution and definitions can be placed once where useful instead of repeated in every cell.

The existing internal configuration identifiers `cap`, `ppi` and `price`, API field names and historical technical evidence are not renamed by this wording decision. Their visible labels change, not the selection formulas. Use full effort labels such as **Extra high** and **Maximum** instead of configuration spellings. The current role-index, floor and general comparison bundle remains proposed rather than approved.

### 2026-10-30 — Live approval of the final bundle

The user answered **“yes”** to **“Can I close the selection-criteria decision using the proposed bundle with these full labels?”** This approves the final role/index/objective bundle, floor, reference population, deterministic comparisons and required-data rules above, together with the earlier cost-basis and timing approvals. The preceding comments remain chronological history; their pending-approval wording is superseded by this approval and the canonical Answer below.

## Answer

Resolved with the live user on **2026-10-30**. The final bundle is approved with full visible labels for the planned web interface. This is a planning decision, not a runtime or permanent-spec change.

### Roles, indexes and default objectives

| Role | Artificial Analysis index | Default objective |
| --- | --- | --- |
| Explorer | Intelligence | Best value |
| Researcher | Intelligence | Best value |
| Planner | Intelligence | Highest capability |
| Coder | Coding | Highest capability |
| Reviewer | Coding | Highest capability |
| Coordinator | Agentic | Highest capability |
| Generalist | Intelligence | Best value |
| Utility | Intelligence | Lowest qualifying price |

- Select **one measured reasoning effort per model** under the active objective, using that role's selected index. Do not fix an effort by role or substitute another index when the selected index lacks data.
- Intelligence supports **Highest capability**, **Best value** and **Lowest qualifying price**. Coding and Agentic support **Highest capability only**, with no price-based ties, cost frontier or cheaper alternatives.
- These are published-score proxies, not verified role performance. Intelligence preserves the value preference for Explorer, Researcher and Generalist on the only established matching task-cost basis. Coding is a proxy for implementation and code-oriented assessment, not a measured review-accuracy score. Agentic is a tool-work proxy, not proof of multi-agent coordination quality.
- [Verify AA index cost bases and latency semantics](32-aa-role-metric-bases.md) is the resolved research prerequisite for metric source facts and comparison limits. Its [immutable findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md) retain the uncertainty about the complete current Coding and Agentic formulas; the separate Coding Agent Index is not a substitute.

### Objective order and deterministic ties

For Intelligence, use the following comparison keys in order:

| Objective | Comparison keys |
| --- | --- |
| Highest capability | Selected Intelligence score descending, then matching Intelligence benchmark task cost ascending |
| Best value | Selected Intelligence score / matching Intelligence benchmark task cost descending, then selected score descending, then matching task cost ascending |
| Lowest qualifying price | Qualifying matching Intelligence benchmark task cost ascending, then selected Intelligence score descending |

- Apply the **same keys within each model to select its effort and across models to order the selected configurations**, including provider picks. After those keys, resolve remaining exact ties by **lower reasoning effort, then canonical model key**.
- Coding and Agentic Highest capability order by **selected index score descending, lower reasoning effort, then canonical model key**. Do not add an Intelligence price tie-break to either area index.
- Timing never filters, weights, orders or breaks ties. Remove the former output-speed tie-break from Lowest qualifying price; do not introduce other weights or scoring rules.

### Capability floor and grade reference population

- Apply an **inclusive capability grade ≥ 2** only for **Lowest qualifying price**. This also applies when an Intelligence role is manually overridden to that objective; it is not limited to Utility.
- **Highest capability and Best value are floor-free.** The active capability display filter remains a separate constraint.
- Artificial Analysis capability grades use **all scored model × effort configurations for the selected index in the refresh**, across reasoning efforts and independent of provider selection. Do not grade separate effort groups or re-bin within a creator.
- Preserve the existing **distinct-value grading method**. Other sources' capability grades remain independent and unchanged; do not blend source ratings or transfer a grade from a different index.

### Matching cost and required data

- Intelligence eligibility requires the **selected Intelligence score** and a **finite, non-negative matching Intelligence benchmark task cost** at that measured effort. Best value additionally requires a **positive** matching task cost.
- A published zero task cost does not provide a finite value ratio. Do not invent a denominator or use token list prices, another benchmark's run cost or a manufactured token mix.
- Coding and Agentic Highest capability require their **selected index score only**; no matching task cost is required or currently established. Do not reuse Intelligence task cost for area-index value, price, frontier or cheaper-alternative advice.
- Missing or non-finite required values do not qualify. If no effort qualifies, leave that model **unranked with a reason**; if no model qualifies, show **“No qualifying configuration”**, with the selected role, provider and active constraints.
- An unsupported Coding or Agentic Best value / Lowest qualifying price override shows an **explicit unavailable-objective state**. Retain the user's selection rather than switching indexes, inventing a cost, silently reverting the objective or relaxing requirements.
- Missing timing never excludes an otherwise eligible configuration. Missing source values remain unavailable; they are not fallback measurements.

### Provider picks and advisory comparisons

- [Define quick selection by major model provider](29-provider-quick-selection.md) remains the provider-workflow authority: Model table first, Provider picks with up to two distinct models per creator, shared provider selection and capability filter, fixed shortcuts plus the full creator chooser, and explicit empty/short-result recovery.
- Provider picks use **direct objective order** after active eligibility and capability filters, not the first two rows of the **frontier-first Model table sections**. A dominated Intelligence model can therefore be a primary or runner-up. The runner-up is neither another effort of the primary nor a specially selected cheaper alternative.
- Provider selection constrains candidates and the Intelligence frontier, path, replacements and detail alternatives, not benchmark scores or grade reference populations. All providers restores global advisory comparisons; picks remain per creator.
- Preserve the existing **floor-free advisory comparison scope** across the included models' efforts: neither the capability display filter nor the Lowest qualifying price floor removes comparison points from that universe. Do not change the settled same-effort-first replacement policy or cheaper-near-equal alternative machinery. These cost-based comparisons remain Intelligence-only.
- Keep ratings from Artificial Analysis, DeepSWE and Terminal-Bench distinct. **OpenRouter token share is display-only**, not a ranking, eligibility, tie-break or grade input.

### Latency and metric labels

- The main latency measure is Artificial Analysis's published median **Time to first answer token**, in seconds, **including thinking**. Show **Output tokens per second** separately; throughput is not latency.
- Missing timing displays **“—” as unavailable**, without substitution or reconstruction. Detail may show distinctly named **Time to first token** and **Estimated response time for 500 answer tokens**; none of these is whole-agent task duration.
- Timing is explanatory only for every role and objective, never a selection or tie-break input.
- Use full visible objective names: **Highest capability**, **Best value** and **Lowest qualifying price**. Attribute the source as **Artificial Analysis** and use clear metrics such as **Intelligence score**, **Coding score**, **Agentic score**, **Benchmark task cost**, **Output tokens per second**, **Time to first answer token** and **Time to first token**.
- Use full effort labels such as **Extra high** and **Maximum**, not configuration spellings. Put source attribution and definitions once where useful rather than repeat them in every cell. Internal configuration identifiers, API fields and historical technical evidence remain internal; this decision does not rename runtime identifiers.

### Handoff

- `CONTEXT.md` records the compact multi-index terminology and selected-index, cross-effort Artificial Analysis capability-grade population; it is not a duplicate specification.
- Next is the separate, still **open and unclaimed** [Redesign the provider-selection prototype for readable model advice](33-redesign-provider-selection-prototype.md). This approval settles criteria, not a visual direction; rendered web design still requires live user approval.
- After the visual decision, [Amend the spec and write role-advice build tickets](31-amend-spec-and-build-tickets.md) must encode these criteria, the resolved provider workflow and approved web direction, then produce the build tickets.
- No new decision or fog patch is introduced. No runtime code, permanent spec, visual redesign or product implementation is changed by this resolution.
