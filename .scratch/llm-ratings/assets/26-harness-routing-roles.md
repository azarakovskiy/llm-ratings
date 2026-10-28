# Harness duties and model-routing profiles

Research ticket: **Survey roles and model-routing profiles in configurable harnesses**.

Access date for all sources: **2026-10-28**. Corpus: **omp, OpenCode, Aider, Cline, Roo Code**. This is a named-source survey, not a measure of market prevalence. Native names below are evidence, not proposed final LLM Ratings names. No model assignments, configuration export, or provider-selection workflow is proposed.

## Main finding and reading key

The sample mixes different layers. A task purpose describes the work; an agent combines instructions and tools; a workflow mode changes how a conversation proceeds; a model-routing slot selects a model. These layers can overlap, but a named specialist or restricted mode does **not** prove that it has a separate model. omp states the distinction directly; OpenCode separates agent settings from session model selection; Aider exposes modes and auxiliary model slots; Cline and Roo support model choices associated with modes. [O1][O2][P1][A1][C1][R2]

| Harness | Native structure and status | Evidence of distinct routing, not just a name |
|---|---|---|
| omp | Built-in routing roles; bundled specialist agents; opt-in planning/advisor/prewalk workflows. | Role aliases resolve to models; agents can request roles or concrete models. Several agents share `@smol`; `security-reviewer` normally falls back to the session model. [O1][O2] |
| OpenCode | Built-in primary agents, child agents and hidden maintenance agents; user-authored agents. | V2 children use their configured model or inherit the parent model. Selecting a primary agent ID alone does not switch the stored session model. Title and compaction have special routing described below. [P1][P3][P4] |
| Aider | Native `code`, `ask`, `architect`, `help` conversation modes; main, weak and editor model slots. | `weak_model` and `editor_model` are configurable separately, but may resolve to the main model. Architect/editor means two requests, not necessarily two different models. [A1][A2][A3] |
| Cline | Plan/Act workflow modes; separate subagent and team features on specified product surfaces. | Optional different Plan/Act models; SDK configured-agent profiles can override parent provider/model. Generic `spawn_agent` is not documented as taking a model argument. [C1][C2][C3] |
| Roo Code | Five built-in instruction/tool modes; custom modes; parent/child Boomerang tasks. | Sticky model/profile selection per mode is supported. Final-release child-profile source and documentation conflict; unconditional inheritance or switching is not established. [R1][R2][R5] |

**Status terms:** “built-in” means supplied by the cited product/version; “custom example” means documentation shows how a user can define it; “example plugin” means an extra installation. “Read-only” below describes documented tool restrictions or intended behavior, not an independently tested security sandbox.

## Source and version boundaries

| Harness | Version context used |
|---|---|
| omp | Live, unversioned `omp.sh` pages, plus repository documentation pinned to [`48ab8687eed83c1f33a73bdc5489034c41b9a935`](https://github.com/can1357/oh-my-pi/commit/48ab8687eed83c1f33a73bdc5489034c41b9a935), a main-branch commit dated 2026-10-28. The site is not proven to be built from this commit. Its role overview is narrower than the repository role catalog. [O1][O2][O6] |
| OpenCode | V1 release [`v1.19.5`](https://github.com/anomalyco/opencode/releases/tag/v1.19.5), commit [`810c0eba1a7348036f8bdf61e6632d0c36c6876c`](https://github.com/anomalyco/opencode/commit/810c0eba1a7348036f8bdf61e6632d0c36c6876c), and separately V2 development docs/source at [`da702a85a6a1f8d0cd7503920763bafc38775d7a`](https://github.com/anomalyco/opencode/commit/da702a85a6a1f8d0cd7503920763bafc38775d7a). Do not read V2 behavior as a guarantee for V1 installations. [P1][P2][P3] |
| Aider | Latest release found: [`v0.86.0`](https://github.com/Aider-AI/aider/releases/tag/v0.86.0), commit [`a4be6ccd87ebaa59b361f3f028d116ce1761b626`](https://github.com/Aider-AI/aider/commit/a4be6ccd87ebaa59b361f3f028d116ce1761b626). Source details below use later main commit [`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`](https://github.com/Aider-AI/aider/commit/5dc9490bb35f9729ef2c95d00a19ccd30c26339c), not necessarily the released package. [A3][A4] |
| Cline | Latest release found: [`v4.1.26`](https://github.com/cline/cline/releases/tag/v4.1.26), released 2026-10-26; tagged source where available, live docs otherwise. Its release notes say cloud sessions hide Plan/Act and auto-approval controls. Features differ by CLI, Desktop, SDK and IDE surface. [C2][C3][C4] |
| Roo Code | Final release [`v3.54.0`](https://github.com/RooCodeInc/Roo-Code/releases/tag/v3.54.0), commit `27001b2`. The [official repository](https://github.com/RooCodeInc/Roo-Code) is archived and says the extension shut down on 2026-05-15. These findings describe that release and its remaining official docs, not a successor fork. [R1] |

## omp: routing slots are not agents

The website lists these ten built-in roles. They route product features as well as agents; unassigned roles can resolve automatically, so a role does not imply a distinct paid model or provider. Assignments can include supported thinking levels. [O1][O2]

| Native role | Type/status | Work and documented routing/performance meaning |
|---|---|---|
| `default` | Built-in routing slot | Normal interactive work and the main session. [O1] |
| `smol` | Built-in routing slot | Fast, inexpensive utility work; normal fast prewalk handoff target. Not a task specialty. [O1][O4] |
| `slow` | Built-in routing slot | Thorough reasoning, difficult planning/review, accepting extra latency. Not a claim that every task needs it. [O1] |
| `plan` | Built-in routing slot used by a workflow mode | Plan-mode architecture and review; can select a dedicated architect model. Merely assigning it does not enter plan mode. [O1][O5][O6] |
| `vision` | Built-in modality-specific routing slot | Image inspection when the main model cannot inspect images, or when analysis should use another model. An assignment does not manufacture image-input support. [O1][O6] |
| `designer` | Built-in role in website catalog | Routes the designer subagent. The repository's chat-role enumeration does not list it; preserve that source difference rather than calling the two lists identical. [O1][O2][O6] |
| `commit` | Built-in routing slot | Commit-message generation; commit flows may fall through to other usable roles if unassigned. [O1] |
| `tiny` | Built-in utility routing slot | Very small classifications, titles, memory support and speech cleanup in the site overview; unassigned routing follows the `smol` preference. More specific memory/speech routes are documented in repository docs below. [O1][O6][O7] |
| `task` | Built-in routing slot | General subagent work when the agent does not request another model. [O1][O2] |
| `advisor` | Built-in slot for an optional independent reviewer | Reviews an opted-in session/worker as it proceeds; independent requests and context, not the ordinary implementation agent. [O2][O3] |

The seven agents listed as bundled on the website have distinct duties. The normal routes below are defaults, not immutable assignments: settings overrides win over agent frontmatter, then ordinary named workers fall back to the parent's active/default model. Project/user definitions can replace bundled definitions. [O2]

| Bundled agent | Actual duty / concrete task | Normal model route |
|---|---|---|
| `scout` | Fast, read-only repository exploration; find implementing code and return compressed findings. | `@smol`. [O2] |
| `librarian` | Source-verified external library/API research; verify upstream API behavior. | `@smol`. [O2] |
| `sonic` | Strictly mechanical edits or data collection with little reasoning; not ambiguous design or review. | `@smol`. [O2] |
| `task` | General multi-step work with full available capabilities when no narrow specialist fits. | `@task`. [O2] |
| `designer` | UI/UX implementation, accessibility and visual refinement. | `@designer`. [O2] |
| `reviewer` | Evidence-backed correctness, quality and security review of changes. | `@slow`. [O2] |
| `security-reviewer` | Read-only vulnerability discovery and security analysis. | Current session-model fallback; no distinct default model established by this name. [O2] |

Additional routing families in **pinned repository documentation** must remain visible. Its built-in catalog includes chat roles `memory` and model-kind roles `image`, `web`, `speech`, `dictation`, `judge`, beyond the site's ten-role overview. `image` generates/edits images and is different from `vision` image analysis; `web` selects search/grounded chat; `speech` is TTS; `dictation` is STT. `judge` selects typed judgments and also accepts compatible chat/tiny models. These are workload/model-kind routes, not six more autonomous coding specialists. [O6]

- **Memory versus titles:** `memory` extracts durable structured items and consolidates memories; when unset it follows `tiny`. The local-model experiments say titles can use smaller models than faithful memory extraction/consolidation. Those are historical, environment-specific experiments, not universal capability thresholds or current model recommendations. [O7]
- **Judgment:** auto-thinking, unexpected-stop detection, typed Eval judgments and AI-assisted staging use `judge`; this differs from general code review or a long-running agent. [O7]
- **Prewalk:** disabled by default; one-time handoff in the *same* session after investigation, todos and the first edit, usually toward `@smol`. It preserves conversation and changes. Docs describe possible cost/latency savings for hard planning followed by repetitive execution, but warn against handing off work that still needs subtle debugging, repeated design or high-risk decisions. [O4]
- **Advisor:** optional independent supervision can flag missed requirements, risky APIs, weak verification and needless complexity. It has separate billing/context. Larger or multiple advisors add cost; background review and optional catch-up can add latency. Architecture/Security/Release roster entries are **custom examples**, not extra bundled agents. [O3]
- **Plan mode:** read-only investigation and draft before approval; implementation can use a chosen role with fresh, compacted or retained context. Planning adds a turn and consumes context. The plan page says an unset `plan` model keeps the current model, while the general role page broadly describes automatic built-in resolution. This survey establishes the configurable planner route, not one unconditional unset-role default across versions. [O1][O5]

## OpenCode: primary agents, subagents and maintenance agents

| Native term | Type/status | Actual responsibility and important boundary |
|---|---|---|
| Build (`build`) | Built-in primary agent; normal default | Implement coding work with tools subject to permissions. V2 allows workspace-external access by default but asks for sensitive environment-file reads. [P1] |
| Plan (`plan`) | Built-in primary agent/workflow | Explore and plan without ordinary project-file edits; designated plan-file writes can be allowed. Shell commands remain permission-controlled, so this is not a proven side-effect-free sandbox. [P1][P5] |
| General (`general`) | Built-in subagent | Complex research and multi-step work, including delegated work units. V2 gives broad tool access but denies spawning further children. [P1][P3] |
| Explore (`explore`) | Built-in subagent | Fast discovery: locate files/symbols and explain code or web-source findings without editing. V2's prompt requires read-only shell commands, but shell access exists. “Fast” does not establish a cheap-model default. [P1][P3] |
| `compaction` | Built-in hidden maintenance agent | Reduce long-session context. V2 summary compaction defaults to the session model; `agents.compaction.model` can override it, with session-model fallback. Provider-native compaction uses the session model. [P1][P4] |
| `title` | Built-in hidden maintenance agent | Produce short session titles. V1 tries an explicit agent model, then `small_model`/provider small-model choice, then session model. V2 tries an explicit title model or small-family/lower-reasoning/session fallback. That is not a lowest-price guarantee. [P2][P6] |
| `summary` | Built-in hidden maintenance agent | V1 docs describe session summaries; V2 registry prompt asks for a short PR-style account of completed work. No distinct default model route was established for this agent. [P1][P2][P3] |

**Routing:** V2 subagents start with fresh child context and use a configured model or inherit the parent model. A primary-agent ID and session model are separate selections. V1 `small_model` is migrated to V2 `agents.title.model`; this is a title utility setting, not a general “all fast agents” slot. [P1][P6]

**Context/cost:** V2 compaction is lossy. Its retained recent tail trades preserved detail against room for new work. Experimental background compaction can reduce a pause but can bill for an unused summary. These are context-maintenance implications, not measured improvements in implementation quality. [P4]

**Custom examples, not defaults:** official examples include `review`/`code-reviewer` for bugs, quality, security and performance; `security-auditor` for authentication, input validation, data exposure and dependencies; and `docs-writer` for documentation. V2's opening reviewer example explicitly denies edits and shell access and supplies a model preference. [P1][P5]

**Source conflict:** V1's tagged documentation still describes a built-in external-docs/dependency-research `scout`, but the release registry does not register it. The removal PR documents removal in June 2026; V2 explicitly says no built-in Scout. Therefore do not count that stale V1 description as current native specialty evidence. [P1][P2][P7]

**Separate model kinds:** V2's experimental API distinguishes chat from image generation/editing and typed decision models (predicate/choice/score). Only chat models are offered for sessions. The API is not proof of automatic delegation from Build/Explore to these other kinds. [P8]

## Aider: chat modes plus weak/editor routing

| Native term | Type/status | Actual responsibility and routing implications |
|---|---|---|
| `code` | Native chat mode; documented usual default | Make requested code changes. Source can choose an initial coder from the model's edit format; one preset starts in architect mode, so the general default statement has model-specific exceptions. [A1][A4] |
| `ask` | Native chat mode | Discuss code, approaches and options without editing. The same-model ask/code workflow preserves the discussion when switching to implementation; it is not a separate researcher worker. [A1] |
| `architect` | Native two-stage workflow | Main model proposes the coding solution; editor translates it into concrete edits. Two requests can help a model that reasons well but formats edits poorly; they can take longer and cost more. [A1] |
| `help` | Native chat mode | Answer Aider usage/configuration/troubleshooting questions using retrieved Aider docs and conversation context. No separate default help-model route established. [A1][A5] |
| `weak_model` / `--weak-model` | Native auxiliary model slot | Commit-message generation and chat-history summarization. Defaults depend on the main-model preset; absent a distinct choice, it resolves to the main model. Summary code tries weak then main. This is utility work, not a named autonomous agent. [A2][A3][A6] |
| `editor_model` / `--editor-model` | Native auxiliary model slot for architect workflow | Independently configurable, or the main model is reused. The editor gets the architect proposal and in-chat files; the inspected handoff clears copied conversation messages and disables the editor repo map for this pass. [A1][A3][A7] |
| `/voice` transcription | Native modality-specific route | Turns speech into a normal chat instruction. Inspected source uses a separate `whisper-1` transcription call with an OpenAI API key, not the weak/editor slot. Image input instead needs a vision-capable chat model. [A8] |

**Do not turn “weak” into “all simple coding”:** the documented slot has specific utility consumers. Likewise, “editor” means applying an architect proposal in an edit format, not a generic second implementation teammate. [A1][A2][A7]

**Format and context matter as well as model:** whole-file output can be slower and more expensive than diff output. The repo map selects relevant repository structure within a token budget; docs suggest 1k tokens, while inspected main derives 1,024–4,096 from model capacity. Token counts are estimates, not enforcement of provider limits. [A9][A10]

Aider's architect article contains September 2024 quality benchmarks. They are old, model/task/format-specific evidence, not a current model ranking or proof that separation alone causes a quality gain. The general supported implication is the documented two-request quality/latency/cost tradeoff above. [A1][A11]

## Cline: mode routing is separate from delegated workers

| Native term | Type/status | Actual responsibility and boundary |
|---|---|---|
| Plan | Native workflow mode | Explore/search code, discuss architecture, investigate hard bugs or review before implementation. Main-mode docs say it cannot edit files or execute commands. [C1] |
| Act | Native workflow mode | Implement, edit files, run commands/tests or make a direct fix. Switching retains conversation context. [C1] |
| `spawn_agent` | Built-in child-agent feature on CLI/Desktop, not VS Code/JetBrains | Focused delegated work with separate context; children can run in parallel and return reports. Current-mode built-in tools, no MCP tools; usage contributes to session totals. Generic schema accepts `systemPrompt` and `task`, not a model argument. [C2][C3] |
| Configured agent / `subagent_<name>` | SDK configured worker profile | Optional provider/model overrides and built-in-tool restrictions; omitted provider/model values inherit the parent. This is actual independent worker routing, but not a default fixed specialty catalog. [C3] |
| Agent Teams / `/team` | Coordination feature on SDK/CLI/Kanban, not IDE extensions | Coordinator and teammates use a persistent task board, mailbox and mission log; distinct from a session-scoped child. [C4] |

**Actual mode routing:** optional “Use different models for Plan and Act” remembers the model for each mode and switches on mode change. Docs give a stronger reasoning planner/faster implementation model as a possible workflow, not a measured guarantee or proof of concurrent workers. Approval/auto-approval remains a separate control. [C1][C6]

**Important permission qualification:** Plan-mode child agents have no edit tools and reject some mutating commands, but the subagent docs explicitly warn that other commands can still write files. Approving delegation approves the child's later tool calls without individual prompts. Thus main Plan-mode descriptions cannot be generalized into a hard sandbox guarantee for every Cline surface. [C2]

**Specialty status:** code review is a Plan use case and an SDK bot example, not a built-in Review mode in the examined mode list. Separately installed **Agent Squad example-plugin** presets are `phantom` (reconnaissance), `oracle` (planning), `anvil` (implementation), `inquisitor` (adversarial review), with separate model settings. These names are not default Cline modes. Scripted multi-model CLI runs also exist, but do not change the generic spawn schema. [C1][C5]

**Context/modality/cost:** focused children have their own context and return reports; their usage is included in totals. Images require a vision-capable model. Token usage and caching affect cost; a “fast implementation” label alone gives no context-capacity or price guarantee. [C2][C7]

## Roo Code: five built-in modes, custom specialties and profile caveats

Roo's final-release `DEFAULT_MODES` contains the following five modes. A mode combines instructions and direct tool groups; it is not by itself a separately running model. [R1]

| Native mode | Purpose and concrete work | Default direct tool groups |
|---|---|---|
| Architect | Gather context, design a system and write an actionable plan before implementation. | `read`, `mcp`; `edit` restricted to Markdown. [R1] |
| Code | Write/modify/refactor code; implement features and fixes. | `read`, `edit`, `command`, `mcp`. [R1] |
| Ask | Explain code/concepts and answer technical questions without direct implementation. | `read`, `mcp`. [R1] |
| Debug | Diagnose errors, narrow causes, add logs and confirm a diagnosis before fixing. | `read`, `edit`, `command`, `mcp`. [R1] |
| Orchestrator / Boomerang | Split complex work, delegate to suitable modes, track and synthesize results. | No read/edit/command/MCP group by default; delegates with `new_task`. [R1][R3] |

`switch_mode` and `new_task` are always-available tools subject to approval settings; Ask/Architect retain MCP. Direct tool groups therefore do not prove a universal read-only security boundary. [R3]

**Defaults and independent routing:** docs call Code the default, whereas final source sets `defaultModeSlug` from the first list entry, Architect. **[INFERENCE]** Architect is that source-level fallback when no stored mode applies; another startup path or persisted selection can change what users see. No runtime test was performed. Each mode can remember a model/profile (“Sticky Models”), but final source initially associates all built-in modes with the same default profile. A workspace profile lock can suppress changes on mode switching. [R1][R2][R4]

**Delegation and context:** Boomerang pauses the parent while a child runs in separate conversation context, then returns a completion summary. Needed context must be explicitly sent down. Creation/completion require approval by default unless auto-approved. This documents a sequential parent/child handoff, not a parallel-worker guarantee. [R3]

**Material profile conflict:** profile docs say an Orchestrator child inherits and retains the parent's profile. Final-release delegation source instead calls `handleModeSwitch` before task creation, and that method can load the destination mode's saved profile when unlocked. **[INFERENCE]** With a valid child-mode profile and no workspace lock, the inspected static path appears to create the child using that profile. This was not runtime-tested. Neither unconditional parent inheritance nor unconditional per-specialty switching is safe to claim. [R5]

**Custom specialties, not built-ins:** Review Mode, Documentation Writer, Test Engineer and Refactoring Expert are official custom-mode examples. The repository's own `.roomodes` also defines project-specific Issue Fixer, PR Fixer, Merge Resolver, Docs Extractor and Issue Investigator. These are useful duty examples, not universal shipped modes. [R6]

**Utility/modality profiles:** Roo docs discuss smaller/faster models as potentially cheaper for simple work, not fixed cheap/thorough routing slots. Context condensing uses the active conversation model and incurs a model call. Image mentions require vision support and cover UI review, screenshot debugging and diagram analysis; no dedicated image-analysis routing slot was established. [R7]

## Cross-harness recurrence candidates — interpretation, not final names

The following groups are **[INTERPRETATION]** of the cited duties. They are not a fixed catalog, naming decision, recommended model setup or prevalence ranking. A native mode, custom example and routing slot remain different evidence types.

| Work pattern worth considering | Evidence within this sample | Distinction to preserve |
|---|---|---|
| Implement requested changes | omp `task`/`sonic`; OpenCode Build/General; Aider `code`/editor; Cline Act; Roo Code. [O2][P1][A1][C1][R1] | Mechanical execution is narrower than general implementation; Aider's editor consumes an existing proposal. |
| Investigate a repository or verify external sources | omp scout **and** librarian; OpenCode Explore/General; Cline Plan; Roo Ask/Architect. [O2][P1][C1][R1] | Repository discovery, upstream/API research and explanation are related but not identical. Do not count removed OpenCode Scout. |
| Design and plan before editing | omp plan mode; OpenCode Plan; Aider architect or ask/code; Cline Plan; Roo Architect. [O5][P1][A1][C1][R1] | Only some have explicit planner model routes; read-only planning differs from prewalk, which already begins editing. |
| Review correctness or supervise risky work | omp reviewer/advisor; OpenCode **custom** reviewer; Cline Plan/code-review bot/**example-plugin** inquisitor; Roo **custom** Review. [O2][O3][P1][C5][R6] | One-shot review versus continuous supervision; security discovery is a distinct specialty, not a synonym. |
| Diagnose faults and test hypotheses | Roo built-in Debug; Cline Plan bug investigation; omp prewalk docs warn against cheap handoff during subtle debugging. [R1][C1][O4] | This is not just code implementation or a thoroughness setting. |
| Coordinate delegated work | Main/subagent systems in omp/OpenCode/Cline; Cline teams; Roo Orchestrator/Boomerang. [O2][P1][C2][C4][R3] | Parallel workers, persistent teams and paused sequential child tasks have different context/control behavior. |
| Produce small auxiliary outputs / manage context | omp tiny/commit/memory/judge; OpenCode title/summary/compaction; Aider weak slot; Roo context condensing. [O6][O7][P1][P4][A2][R7] | Small-output utility, memory extraction, context compaction and typed judgment are distinct consumers; not all use cheap models by default. |
| Spend more reasoning versus reduce time/cost | omp smol/slow and prewalk; Cline optional stronger-plan/faster-act; Aider weak/editor slots; Roo cost guidance; OpenCode title selection. [O1][O4][C1][A1][A2][R7][P6] | A performance profile cuts across task purpose. “Explore is fast” does not prove separate routing; two-stage work can cost **more**. |
| UI/UX, security, documentation and test specialties | omp bundled designer/security-reviewer; OpenCode custom security/docs examples; Roo custom documentation/test/refactoring examples. [O2][P5][R6] | Keep these separate specialty families visible. Their presence/status differs; do not force them into a single residual role. |
| Image, audio and typed-decision work | omp vision/image/speech/dictation/judge; OpenCode V2 image/decision APIs; Aider voice/vision; Cline/Roo vision inputs. [O6][O7][P8][A8][C7][R7] | Model-kind capability constraints differ from behavior profiles; image analysis is not image generation, and speech input is not a coding agent. |

## Limits and factual prerequisites for later decisions

- No builds, tests, formatters, model benchmarks or runtime mode-switch experiments were run. This report records documented/source behavior and labels static-code conclusions as inference.
- All five named harnesses had accessible official evidence. Reader extraction initially omitted omp's streamed articles; raw HTML exposed the role, agent, advisor, prewalk and plan articles. This was an extraction issue, not evidence that the docs were absent.
- Version/surface matters: OpenCode V1/V2 and Cline IDE/CLI/Desktop/SDK are not interchangeable. Roo is archived/shut down; it can support historical pattern evidence, not an assumption of a currently supported offering. [P1][P2][C2][C4][R1]
- Material inconsistencies remain recorded, not hidden: omp overview versus extended role catalog and unset-plan wording; OpenCode stale Scout docs; Aider documented defaults versus model presets/map budget; Roo default-mode and child-profile conflicts. These do not block purpose-level findings, but exact routing claims must carry their version/configuration conditions. [O1][O5][O6][P7][A4][A10][R4][R5]
- **New factual prerequisites:** any later harness-specific routing decision needs the actual installed version/surface and effective user/project agent, model and permission settings. A Roo child-routing guarantee additionally needs a runtime check of the final release's profile-lock/delegation path. These prerequisites are for exact routing, not a reason to defer the human-readable naming discussion.
- No source sample establishes what users most often configure, market-wide prevalence, current cross-provider quality rankings, or a minimum number of generalized roles. Final names, grouping and the separate provider quick-selection HITL workflow remain undecided.

## Sources

All accessed **2026-10-28**. References attached to table rows and paragraphs support those claims; versions above bound interpretation.

### omp

- [O1] [Model roles](https://omp.sh/docs/roles) — raw streamed article; built-in site table, defaults, effort and role configuration.
- [O2] [Agents & model roles](https://omp.sh/docs/agents-and-roles) — raw streamed article; bundled-agent duties, normal routes, precedence and custom definitions.
- [O3] [Advisor models](https://omp.sh/docs/advisor) — raw streamed article; optional supervision, independent billing/context and example roster.
- [O4] [Prewalk](https://omp.sh/docs/prewalk) — raw streamed article; one-time handoff, defaults and quality/cost tradeoffs.
- [O5] [Plan mode](https://omp.sh/docs/plan) — raw streamed article; read-only planning, approval/context choices, model switching/default wording.
- [O6] [Pinned repository model documentation](https://github.com/can1357/oh-my-pi/blob/48ab8687eed83c1f33a73bdc5489034c41b9a935/docs/models.md#role-aliases-and-settings) — extended built-in chat/model-kind roles, vision/image distinction, alias and fallback behavior.
- [O7] [Pinned local-model documentation](https://github.com/can1357/oh-my-pi/blob/48ab8687eed83c1f33a73bdc5489034c41b9a935/docs/local-models.md) — title/memory duties and historical experiments, speech/dictation, judgment consumers.

### OpenCode

- [P1] [V2 agents](https://dev.opencode.ai/v2/docs/agents/) — built-ins, child context/model inheritance, primary/session distinction and custom reviewer.
- [P2] [V1 release agent registry](https://github.com/anomalyco/opencode/blob/v1.19.5/packages/opencode/src/agent/agent.ts) and [tagged agent docs](https://github.com/anomalyco/opencode/blob/v1.19.5/packages/web/src/content/docs/agents.mdx).
- [P3] [Pinned V2 agent registry/prompts](https://github.com/anomalyco/opencode/blob/da702a85a6a1f8d0cd7503920763bafc38775d7a/packages/core/src/plugin/agent.ts).
- [P4] [V2 compaction](https://dev.opencode.ai/v2/docs/compaction/) — configurable summary model, context/cost tradeoffs and provider-native route.
- [P5] [V1-style agent docs](https://opencode.ai/docs/agents/) — Plan permissions and custom review/security/docs examples.
- [P6] [V1 title caller](https://github.com/anomalyco/opencode/blob/v1.19.5/packages/opencode/src/session/prompt.ts), [pinned V2 context/title caller](https://github.com/anomalyco/opencode/blob/da702a85a6a1f8d0cd7503920763bafc38775d7a/packages/core/src/session/context.ts), [V2 model selection](https://github.com/anomalyco/opencode/blob/da702a85a6a1f8d0cd7503920763bafc38775d7a/packages/core/src/model.ts), [migration guide](https://dev.opencode.ai/v2/docs/migrate-v1/).
- [P7] [Official Scout removal PR](https://github.com/anomalyco/opencode/pull/30435), compared with [P1][P2].
- [P8] [V2 experimental model API](https://dev.opencode.ai/v2/docs/api#model).

### Aider

- [A1] [Chat modes](https://aider.chat/docs/usage/modes.html), including architect/editor and same-model ask/code workflows.
- [A2] [Weak-model option](https://aider.chat/docs/config/options.html#--weak-model-weak_model).
- [A3] [Pinned model resolution](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/models.py) and [model presets](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/resources/model-settings.yml).
- [A4] [Pinned initial coder selection](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py), compared with [A3].
- [A5] [In-chat help](https://aider.chat/docs/troubleshooting/support.html).
- [A6] [Pinned history summary fallback](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/history.py).
- [A7] [Pinned architect/editor handoff](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/architect_coder.py).
- [A8] [Voice docs](https://aider.chat/docs/usage/voice.html), [pinned transcription](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/voice.py), [pinned command/key check](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py), [image input](https://aider.chat/docs/usage/images-urls.html).
- [A9] [Edit formats](https://aider.chat/docs/more/edit-formats.html).
- [A10] [Repository map](https://aider.chat/docs/repomap.html), [pinned budget source](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/models.py), [token-limit caveats](https://aider.chat/docs/troubleshooting/token-limits.html).
- [A11] [Architect benchmark article, 2024-09-26](https://aider.chat/2024/09/26/architect.html).

### Cline

- [C1] [Plan & Act](https://docs.cline.bot/core-workflows/plan-and-act), including different models per mode.
- [C2] [Subagents](https://docs.cline.bot/features/subagents) — surface availability, tools, context, cost and approval/sandbox warnings.
- [C3] [Tagged generic spawn schema](https://github.com/cline/cline/blob/v4.1.26/sdk/packages/core/src/extensions/tools/team/spawn-agent-tool.ts#L30-L35), [configured-agent reference](https://github.com/cline/sdk-skill/blob/main/skill/cline-sdk/references/multi-agent/REFERENCE.md), [tagged override implementation](https://github.com/cline/cline/blob/v4.1.26/sdk/packages/core/src/extensions/tools/team/configured-agent-tool.ts#L133-L164).
- [C4] [Agent Teams](https://docs.cline.bot/cli/agent-teams), [SDK multi-agent teams](https://docs.cline.bot/sdk/guides/multi-agent-teams), [v4.1.26 release](https://github.com/cline/cline/releases/tag/v4.1.26).
- [C5] [SDK review bot example](https://docs.cline.bot/sdk/guides/building-an-agent), [tagged Agent Squad example plugin](https://github.com/cline/cline/blob/v4.1.26/sdk/examples/plugins/agents-squad/README.md), [scripted model orchestration](https://docs.cline.bot/cli/samples/model-orchestration).
- [C6] [Auto-approval](https://docs.cline.bot/features/auto-approve), [tools reference](https://docs.cline.bot/tools-reference/all-cline-tools).
- [C7] [Working with files/images](https://docs.cline.bot/core-workflows/working-with-files), [task management and cost](https://docs.cline.bot/core-workflows/task-management).

### Roo Code

- [R1] [Tagged default-mode definitions](https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/packages/types/src/mode.ts#L168-L227), [final release](https://github.com/RooCodeInc/Roo-Code/releases/tag/v3.54.0), [archived repository/shutdown notice](https://github.com/RooCodeInc/Roo-Code).
- [R2] [Using modes / Sticky Models](https://docs.roocode.com/basic-usage/using-modes), [linking profiles to modes](https://docs.roocode.com/features/api-configuration-profiles#linking-profiles-to-modes).
- [R3] [Boomerang tasks](https://docs.roocode.com/features/boomerang-tasks), [`new_task`](https://docs.roocode.com/advanced-usage/available-tools/new-task), [always-available tools](https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/src/shared/tools.ts#L303-L326), [auto-approval](https://docs.roocode.com/features/auto-approving-actions).
- [R4] [Tagged default slug](https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/src/shared/modes.ts#L44-L48), [default profile initialization](https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/src/core/config/ProviderSettingsManager.ts#L45-L64), [mode-switch profile/lock handling](https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/src/core/webview/ClineProvider.ts#L1288-L1333).
- [R5] [Profile inheritance docs](https://docs.roocode.com/features/api-configuration-profiles#per-task-profile-persistence), [tagged delegation path](https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/src/core/webview/ClineProvider.ts#L2849-L2879), [task creation/current config](https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/src/core/webview/ClineProvider.ts#L2583-L2600), compared with [R4].
- [R6] [Custom-mode examples](https://docs.roocode.com/features/custom-modes), [repository-specific `.roomodes`](https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/.roomodes).
- [R7] [Cost guidance](https://docs.roocode.com/advanced-usage/rate-limits-costs), [context condensing](https://docs.roocode.com/features/intelligent-context-condensing), [image mentions](https://docs.roocode.com/basic-usage/context-mentions#image-mentions).
