# Mainstream coding assistants — native roles and model-selection profiles

Surveyed **2026-10-28** from official Anthropic, OpenAI, Cursor, GitHub and Microsoft documentation. All linked sources below were accessed on that date. This resolves the factual survey in issue 27; it does not select final LLM Ratings role names, models, benchmarks, provider filters, or configuration exports.

## Answer and classification

The sample supports recurring **tasks**, but not one common native-agent taxonomy. Codebase exploration, planning, implementation, review and coordination occur through different mechanisms. External research and independent critique also have explicit native support in parts of this sample. A task can be a named subagent in one product and a mode, bundled workflow, or separately managed service in another. The tables preserve those distinctions. [Anthropic subagents][CC1] [Codex subagents][OX1] [Cursor subagents][CU1] [Copilot built-ins][GH1]

| Classification used here | Meaning | Why the distinction matters |
| --- | --- | --- |
| Built-in task agent/subagent | A documented bundled agent identity with task instructions and capabilities | A native name is evidence of that product's task split, not proof of a separately selectable model. |
| Session agent/workflow mode | A selectable way for the main session to work, such as Ask or Plan | It can change tools, interaction, or stages without adding an independent model slot. |
| Coordination position/workflow | A parent/lead/coordinator or delegation mechanism | Coordination is not automatically an independent expert-agent definition. |
| Model-routing/resource profile | A model/effort/depth selection mechanism | Speed, price or reasoning controls are not task identities. |
| Permission/execution control | Approval policy, sandbox, background/cloud execution | Autonomy and execution location are separate from task purpose. |
| Custom example/extension | A definition users create or install | An official example is not a bundled product default. |

These are report labels, not proposed application names. Product-specific evidence follows.

## Claude Code

**Version context:** current documentation; the reviewed changelog begins with **v2.1.312, October 27, 2026**. Older descriptions can be wrong for the current release: Explore no longer has the older fixed-Haiku behavior. The June 29–July 3 release summary records that change; the current reference adds provider-dependent exceptions. [Changelog][CC0] [Historical change][CC12] [Current reference][CC1]

### Built-in subagents

| Native term | Classification and actual work | Documented model/capability/resource behavior |
| --- | --- | --- |
| **Explore** | Built-in read-only subagent: find files, search code, analyze a codebase. Invocation can request `quick`, `medium`, or `very thorough` exploration. [CC1] | Uses the main model, except that a Fable parent uses the model resolved by `opus` on subscription, Console and `ANTHROPIC_BASE_URL` gateway connections; on Bedrock, Google Cloud's Agent Platform, Foundry, Claude Platform on AWS and Claude apps gateways, it retains the main model. Write/Edit are denied. Separate context keeps search output out of the main conversation. [CC1] |
| **Plan** | Built-in research subagent used **during plan mode** to gather codebase context before the main conversation presents a plan. It is not the session's plan mode itself. [CC1] | Inherits the main model unless the documented global force override applies. Read-only; Write/Edit denied. Research output has a separate context window. [CC1] |
| **general-purpose** | Built-in subagent for complex research, dependent multi-step operations and code modifications, including tasks requiring both exploration and action. [CC1] | Has all tools available **to subagents**, not necessarily all main-session tools. Uses the subagent-model environment setting if applicable, otherwise the main model, subject to higher-priority model choices. [CC1] |
| **claude** | Built-in catch-all when no specialist fits; also the default for a dispatched background session. [CC1] | No model of its own; normal subagent model resolution. Has the subagent-eligible tool set. [CC1] |
| **statusline-setup**; **claude-code-guide** | Built-in helpers for `/statusline` configuration and questions about Claude Code features respectively. The guide is not a generic external-research role. [CC1] | Documented models: Sonnet and Haiku respectively. [CC1] |

Normal subagent model order is invocation choice → definition choice → `CLAUDE_CODE_SUBAGENT_MODEL` → main model; installed mods can change the invocation choice. Built-in Explore and Plan have their own documented inheritance behavior. Setting `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` with the model variable overrides normal choices across subagents, teammates and workflow agents; this requires v2.1.257+. **Do not treat one environment variable as unconditional routing.** [Choose a model and force override][CC1]

Ordinary subagents start with isolated context, not the parent's conversation history. Their window size follows their own model. Explore and Plan omit startup CLAUDE.md files and the git-status snapshot to keep research fast and inexpensive. Forks are different: they inherit the full conversation/model and can reuse its prompt cache. These are execution/context differences, not extra task stereotypes. [Startup and forks][CC1]

### Native workflows, coordination and routing — not extra built-in subagent types

| Native term | Classification and actual work | Documented implications |
| --- | --- | --- |
| **Plan mode** | Session permission/workflow mode for analysis before editing; distinct from the **Plan** research subagent. [CC2] [CC1] | Read-only planning behavior and approval rules, not by itself a different model. Other permission modes include Manual/`default`, `acceptEdits`, `auto`, `dontAsk`, and `bypassPermissions`; auto's action classifier is not a code reviewer. [CC2] |
| **`opusplan`** | Explicit model-routing mode: Opus in plan mode, Sonnet for execution. [CC3] | A real planning/execution model split, subject to availability/allowlists. The docs position Opus for complex reasoning and Sonnet for daily coding; this is vendor guidance, not measured comparative evidence here. [CC3] |
| **Team lead / teammates** | Agent-team positions: the main session assigns work and synthesizes results; separate Claude Code sessions work independently and message one another. Native mechanism, but experimental and disabled by default. Tasks include research/review, separate modules, competing debugging hypotheses and cross-layer changes. [CC4] | Each teammate has its own context; models can be chosen at spawn or through applicable definitions/settings. Teams add coordination overhead and use significantly more tokens than one session. No fixed catalog of expert teammate names follows from this mechanism. [CC4] |
| **`/deep-research`** | Bundled dynamic workflow, explicitly invoked: parallel web searches, fetched sources, cross-checking/voting on claims, and a cited report. Requires WebSearch. [CC5] | Intermediate results live in script variables rather than filling the main context. Workflow agents follow documented subagent model selection; the page does not prescribe one fixed researcher/verifier model pair. Large multi-agent runs use more tokens. [CC5] |
| **Local `/code-review`** (`/review` alias) | Bundled skill, normally a background subagent: review branch changes, PRs, paths or revision ranges for correctness. `--fix` also requests changes under the session's permissions. [CC6] | Own context, ordinary session usage/API billing. Lower effort favors higher-confidence findings; higher effort broadens coverage. No dedicated fixed reviewer model is published on this page. The alias behavior changed in v2.1.223. [CC6] |
| **Ultrareview** (`/code-review ultra`) | Research-preview cloud review: a fleet finds bugs and independently reproduces/verifies findings. Not the ordinary local review. [CC7] | Vendor estimates: typically 15–25 minutes and $5–$25 usage credits per paid review, with plan-dependent free runs. Cloud sandbox rather than local compute; no selectable reviewer model documented on the reviewed page. These estimates are not benchmarks. [CC7] |
| **Managed Code Review** | Separate organization service for GitHub PRs: parallel finding, verification, deduplication/ranking and comments. [CC8] | Service selects models; admin settings offer no model choice. Quick/Standard/Deep trade speed/cost against thoroughness. Repository access inside a review is read-only; it does not build or run the code. [CC8] |
| **Advisor** | Experimental server-side second-model tool for approach decisions, repeated failures and completion checks; receives the full conversation and returns guidance. Not an ordinary isolated subagent. [CC9] | A real separate model setting (`advisorModel`/`--advisor`/`/advisor`) with supported-pair restrictions. Anthropic API route required, including eligible subscription usage; not supported on the listed third-party cloud providers. Each consultation adds advisor usage and rereads the transcript without advisor-side cache reuse. [CC9] |

**Custom-example boundary:** `code-reviewer`, `debugger`, `data-scientist`, `db-reader` and the `coordinator` definition in the subagent guide are user-created examples, not the built-in inventory. Agents installed through plugins remain extensions; marketplace presence does not imply bundled behavior. [Example definitions and scopes][CC1] [Marketplace distinctions][CC11]

## OpenAI Codex

**Version/surface context:** current live documentation. The original `developers.openai.com/codex/...` URLs redirect to `learn.chatgpt.com`; the current pages include ChatGPT Work and local Codex surface blocks. Findings below use the **local Codex app/CLI/IDE** sections unless explicitly stated. They are not a claim that every hosted ChatGPT surface exposes local configuration. [Subagents][OX1] [Configuration][OX4]

| Native term | Classification and actual work | Documented model/capability/resource behavior |
| --- | --- | --- |
| **`default`** | Built-in general-purpose fallback agent. [OX1] | Subagent model/reasoning can be inherited or explicitly configured; no distinct fixed model is assigned to this name by the reviewed inventory. [OX1] |
| **`worker`** | Built-in execution-focused agent for implementation and fixes. [OX1] | Same routing controls; the name identifies purpose, not an automatically different provider/model. [OX1] |
| **`explorer`** | Built-in read-heavy codebase exploration agent. [OX1] | Read-heavy is its documented purpose. Do **not** equate that with an independent enforced read-only sandbox: subagents inherit the parent's sandbox/approvals, and custom-agent instructions alone do not create another sandbox. [OX1] |
| **Plan mode** (`/plan`) | Main-session planning workflow: gather context, ask questions, form a plan before implementation. Not listed as a built-in `planner` subagent. [OX2] [OX3] [OX1] | `plan_mode_reasoning_effort` is a real plan-specific reasoning override; when unset, a built-in preset default applies. That setting is not evidence of a separate planning-model slot. [OX4] |
| **`/review`**, **`codex review`** | Built-in review workflow. CLI `/review` starts a dedicated reviewer that reads a selected diff and reports prioritized findings without changing the worktree; review targets include uncommitted changes, base-branch comparisons and commits. [OX5] [OX6] | **`review_model`** is an explicit optional model override, defaulting to the session model. Thus review has a documented routing slot even though `reviewer` is not one of the three listed built-in general subagent names. [OX4] [OX1] |
| **Main agent / subagents** | Native orchestration: spawn, steer, wait, collect summaries and close agent threads. Examples include parallel exploration, tests, log analysis, triage and review. [OX1] | Separate work keeps noisy intermediate output outside the main thread. Parallel work can save time, but comparable multi-agent workflows consume more tokens; parallel writes can conflict and add coordination overhead. Current local releases enable subagents by default and delegate after direct requests or applicable project/skill instructions. [OX1] |
| **Sandbox / approval policy / `auto_review`** | Execution/permission controls, not coding-task roles. Sandbox controls what commands can access; approval policy controls when confirmation is needed. `approvals_reviewer=auto_review` sends eligible approvals to a reviewer subagent. [OX7] [OX4] | An **approval reviewer** evaluates proposed actions, not source-code correctness. Inherited permission controls remain distinct from per-agent model settings. [OX1] [OX4] |

Local Codex supports subagent model/reasoning selection at spawn, `[agents]` defaults and custom-agent files. Without an override, subagents inherit model and effort. Custom files can override resolved settings; choosing a new model without effort can introduce that model's default effort under the documented resolution rules. Higher reasoning effort adds response time and tokens and may improve difficult-task quality. These are resource/model controls, not fixed task-to-model assignments. [OX1]

**Custom-example boundary:** `pr_explorer`, `reviewer`, `docs_researcher`, `code_mapper`, `browser_debugger` and `ui_fixer` are explicitly **example custom agents**. The docs-researcher example uses a docs MCP server; it does not prove a bundled external-research specialist. External context through MCP and web-search tools is documented separately. [Examples][OX1] [External context][OX3] [Web-search controls][OX7]

## Cursor

**Version context:** current editor/CLI/cloud documentation, not one frozen application build. Agent Review explicitly notes a settings move starting in **3.11**. Projects cites **3.21.9+** for Enterprise. These are feature-specific version qualifications, not a claim that every source describes that exact release. [CU5] [CU7]

| Native term | Classification and actual work | Documented model/capability/resource behavior |
| --- | --- | --- |
| **Agent** | Main coding assistant: independently edit files, run terminal commands, search code and the web, build and verify changes. [CU2] | User-selected model is a separate component of Agent. Images enter context for vision-capable models; browser actions and screenshots are documented tools. Those capabilities do not establish a distinct general researcher model slot. [CU2] |
| **Ask** | Workflow mode: search/explain code without editing files. CLI documents Agent, Plan and Ask and says its modes match the editor. [CU3] | No separate fixed Ask model is documented on this page. Read-only workflow differs from a delegated Explore context. [CU3] [CU1] |
| **Plan Mode** | Workflow mode: research the codebase, clarify requirements, create a reviewable/editable implementation plan, then build on approval. Suits multi-file features, uncertain requirements and architecture decisions. [CU4] | Mode is not a built-in `planner` subagent. No fixed planning model is assigned by this page. [CU4] [CU1] |
| **Debug Mode** | Workflow mode for difficult bugs: form hypotheses, instrument, ask the human to reproduce, analyze runtime logs, make a targeted fix, verify and remove instrumentation. Examples include races, performance/memory problems and regressions. [CU6] | Runtime evidence and human reproduction are the distinguishing capabilities; no separate debugger model slot is documented on this page. [CU6] |
| **Explore** | Built-in subagent: search and analyze codebases. [CU1] | Automatically used; own context keeps noisy search output out of the parent. Uses a faster model by default. The docs attribute parallel-search speed and lower cost to this routing; these are vendor claims, not measurements here. [CU1] |
| **Browser** | Built-in subagent: control the browser through MCP tools, filter DOM snapshots/screenshots to relevant results. [CU1] | Own context; built-ins can select models for subtasks independently of the parent. The reviewed page does not identify one permanent Browser model. [CU1] |
| **Project coordinator** | Native Projects position: plan a feature/migration/app, manage/delegate agents and return work for review. The coordinator explicitly does **not** write code itself. [CU7] | Coordinator model is selected when creating the Project. Projects use Cloud Agents, preserve shared context over long-running work and can run many agents in parallel. Availability is plan/policy dependent. [CU7] |
| **Agent Review** | Dedicated local-change review feature; automatic or manual. Not one of the two documented built-in subagents. [CU5] [CU1] | **Quick**: fast/low cost for small diffs and sanity checks. **Deep**: slower/high cost for complex logic, security-sensitive code and large refactors. The page does not expose the underlying reviewer model. [CU5] |
| **Bugbot** | Separate PR review automation: analyze diffs and post bugs, security/code-quality findings and fix suggestions. [CU8] | Runs on updates or explicit request; bounded by review-size and bot-authored-PR limits. Product review automation is not the user-authored `code-reviewer` example. [CU8] [CU1] |
| **Cloud Agents** | Execution surface: same agent fundamentals in isolated cloud VMs, with build/test and computer/browser capabilities. Formerly called Background Agents. [CU9] | Curated model selection and supported context-window choices. Larger context can increase usage/cost; billed at the selected model's rate. Cloud location is not an expert-task role. [CU9] |
| **Auto / Cursor Router** | Model-routing profile, currently Teams/Enterprise. Routes requests by task/complexity; Cost, Balance and Intelligence optimization modes. [CU10] | Cost optimizes token spend; Balance trades intelligence/speed/cost; Intelligence uses more capable models for hard tasks. Balance/Intelligence use limits faster than Cost; pool/models change and users do not choose each underlying route. Not a task-agent inventory. [CU10] |
| **Auto-review / Allowlist / Run Everything** | Permission run modes. Auto-review's classifier judges tool calls; it is not Agent Review or Bugbot. [CU11] | The classifier uses Cursor-managed small models, with documented fallback/access constraints; the page says this is not a security boundary. This is separate safety-model routing, not a coding role. [CU11] |

Custom subagents use `model: inherit` by default or an explicit model ID; supported model parameters can set effort, speed and context size. Admin/plan/legacy-Max restrictions can cause fallback. The parent picker, including Auto, does not imply that every subagent uses that model. Requests bill at the rate of the model that actually ran. [CU1]

**Custom-example boundary:** `verifier`, `security-auditor`, `planner`, `code-reviewer`, `search-agent` and `reasoning-agent` are creation/configuration examples. The current built-in table lists **Explore and Browser**, not those examples. General web search is an Agent tool; that is not evidence of a separately named built-in external-research subagent. [CU1] [CU2]

## GitHub Copilot

**Surface/version context:** Copilot IDE modes, CLI subagents and managed review are not interchangeable inventories. Current VS Code docs distinguish the **Copilot harness** from the **Local harness**; Cloud is an execution target. A Claude model inside Copilot is still the Copilot harness. On **October 28, 2026**, GitHub starts the new paid-plan **Copilot in the cloud** experience, so same-day documentation includes old and new workflows. [GH2] [GH6]

### Main-session agents and workflows

| Native term | Classification and actual work | Documented model/capability/resource behavior |
| --- | --- | --- |
| **Ask** | Built-in selectable session agent in the current VS Code Copilot and Local harnesses: answer questions/research code without changes. [GH2] | Copilot Ask uses read-only tools and cannot edit or run state-changing commands. This is a session-agent choice, not proof of another model. [GH2] |
| **Agent** | Built-in session agent / IDE agent mode: identify files, edit, run commands, inspect output and iterate on a high-level task; implement and validate. [GH2] [GH3] | User can steer, review edits and approve commands. Tools/permissions differ by surface. Agent mode is documented across VS Code, Visual Studio, JetBrains, Xcode and Eclipse. [GH3] |
| **Plan** (`/plan`) | Built-in planning session agent/workflow: research, clarify constraints and requirements, divide work into steps and present a plan for review before implementation. [GH4] [GH5] | Model choice is separate. In a Copilot session, choose a planning model and later change it for implementation. Local-only `chat.planAgent.defaultModel` and experimental `github.copilot.chat.implementAgent.model` do **not** configure Copilot Plan mode. Vendor guidance says stronger reasoning can help complex planning, but cheaper implementation saves only if retries/rework do not erase it. [GH5] |
| **`/research`** | Native research workflow: codebase, accessible GitHub repositories and web sources → cited Markdown report. VS Code Insiders exposes a preview built-in research agent in Copilot-harness sessions. [GH14] [GH5] | CLI research uses a dedicated configured model irrespective of the main session's `/model`; cannot change it with that command. It takes longer than normal chat and produces findings rather than code changes. [GH14] |
| **`/fleet`** | Native CLI coordination workflow: split parallelizable parts of a multi-step implementation plan among subagents; can select suitable custom agents. [GH15] | Parallelism can speed suitable tasks. Fleet is orchestration, not a fixed `coordinator` specialist/model assignment. Autopilot+fleet and manually steered fleet are different continuation choices. [GH15] |
| **Cloud agent** (formerly **coding agent**) / **Copilot in the cloud** | Remote execution/product surface: research a repository, plan, edit and run tests/linters; inspect/refine before creating a PR. The old/new names are not two task specialists. [GH6] [GH7] | Entry point controls model-picker availability; Auto applies where no picker exists. New cloud sandboxes support cross-client continuity and multi-repository organization work; Actions-based sessions have single-repository scope and a 59-minute limit. Both have one branch/PR per task. Compute/memory/storage billing is separate from AI model credits. [GH6] [GH8] [GH9] |
| **Autopilot / approval levels** | Workflow/permission controls, not extra built-in task agents. Copilot-harness Autopilot is a workflow mode; Local Autopilot is a permission level. [GH2] [GH10] | Assisted permissions uses an LLM action judge. Advanced Autopilot is preview functionality with a separate small/fast completion-checking model. Do not confuse permission review or task-completion checks with code review. [GH10] |

GitHub's Plan guide currently documents VS Code, JetBrains, Xcode and Eclipse; Xcode/Eclipse are public preview. Do not assume identical availability in Visual Studio or every other entry point. [GH4]

**Edit is version-qualified, not a fourth equally current default:** historical guidance used Edit for well-defined changes with finer request-count control. VS Code 1.110 deprecated/hid it; 1.126 removed `chat.editMode.hidden`, while retaining legacy Edit for users whose policy disables Agent. The current AI settings reference still lists that setting, so the sources conflict. Preserve the versioned qualification instead of silently presenting Ask/Edit/Agent/Plan as today's universal inventory. [Historical description][GH17] [1.110][GH18] [1.126][GH19] [Settings conflict][GH20]

### Current CLI built-in subagents

The official CLI reference explicitly labels the following **built-in agents**. Model IDs are recorded defaults from that reference, **not recommendations or promises that the defaults never change**. Do not apply this CLI table to every IDE harness. [GH1]

| Native term | Actual task / restrictions | Documented default model |
| --- | --- | --- |
| **`explore`** | Fast file/code search and questions; focused answers under 300 words; safe parallel use. [GH1] | `gpt-5.6-luna`. [GH1] |
| **`task`** | Run tests, builds and lints; brief success summary, full failure output. This is narrower than the word “task” might imply. [GH1] | `gpt-5.6-luna`, fallback `claude-haiku-4.5`. [GH1] |
| **`general-purpose`** | Full-capability, complex multi-step work in separate context. [GH1] | `claude-sonnet-4.6`. [GH1] |
| **`code-review`** | Diff review for bugs, security issues and logic errors; does not modify code. [GH1] | `claude-sonnet-4.6`. [GH1] |
| **`research`** | Search GitHub repositories, fetch files, verify claims and return detailed cited findings. [GH1] | `claude-haiku-4.5`. [GH1] |
| **`rubber-duck`** | Constructive critique of plans, designs, implementations and tests; read-only. [GH1] [GH11] | Automatically selected complementary model, deliberately different from the current session's model. [GH11] |
| **`security-review`** | Change-focused security review across 11 categories; reports severity/confidence, does not modify code. The reference specifies >80% exploitability confidence as its reporting threshold. [GH1] | `claude-sonnet-4.6`. [GH1] |

Rubber duck is normally explicit but can be enabled for proactive consultation. An extra reasoning pass adds latency and model usage; the intended benefit is a second perspective, not a measured quality gain in this report. [GH11]

Current VS Code docs distinguish Copilot's `task` delegation tool from Local's `runSubagent`; separate context and focused results add model usage/coordination. Historical VS Code **1.110** documented an uppercase **Explore** subagent for Local-era Plan research, with `chat.exploreAgent.defaultModel`. Do not silently equate that historical setting with the current CLI `explore` defaults. [GH12] [GH18]

### Managed code review and custom definitions

| Feature | Classification / tasks | Documented implications |
| --- | --- | --- |
| **Copilot code review** | Purpose-built product for PR/IDE change review and fix suggestions, separate from the CLI `code-review` identity. [GH13] | Uses a managed mixture of models; **model switching is not supported**. Lite is fast/targeted; Balanced (default) uses higher reasoning and longer analysis; Max (preview) uses multiple high-reasoning models. Higher effort consumes more AI credits. Agentic context gathering uses Actions runners; unavailable runners can reduce review capabilities. [GH13] |
| **Code-review effort estimates** | Resource profiles, not three reviewer roles. [GH13] | GitHub estimates average model-credit consumption of $0.25 / $1.50 / $10 for Lite/Balanced/Max, excluding Actions minutes. Actual costs can fall outside stated ranges and change with models. Not fixed prices or benchmarks. [GH13] |
| **Custom agents** | User/repository/organization/extension/plugin definitions, which may appear beside built-ins. [GH16] | Instructions, tools and optional model selection can define many specialists. Official Planner/Reviewer/Implementer and customization-library examples are **not proof of bundled defaults**. [GH16] [GH12] [GH21] |

## Recurrence candidates — interpretation, not final names

The following are **task-pattern interpretations of this four-product sample**. They are neither a market-prevalence claim nor a proposal to keep a fixed number of application roles. Presence of a task does not imply presence of a model slot.

| Candidate task pattern | Evidence within the named sample | Boundary to preserve |
| --- | --- | --- |
| **Read and map a codebase** | Claude Explore; Codex `explorer`; Cursor Explore; Copilot CLI `explore` and session Ask. [CC1] [OX1] [CU1] [GH1] [GH2] | Read-only enforcement, model inheritance and context isolation differ. Claude's current Explore does not have Cursor's documented faster-model default. |
| **Work out an implementation approach** | Claude plan mode + Plan research; Codex Plan mode; Cursor Plan Mode; Copilot Plan. [CC1] [CC2] [OX3] [CU4] [GH5] | These are not four equivalent planner subagents. Explicit model-phase routing exists in Claude `opusplan` and Local VS Code controls, not automatically in every Plan workflow. |
| **Make and validate changes** | Claude general-purpose; Codex `worker`; Cursor Agent; Copilot Agent/general-purpose/cloud. [CC1] [OX1] [CU2] [GH1] [GH3] [GH6] | Copilot CLI `task` specifically runs commands; it is not a synonym for the implementation agent. |
| **Inspect a proposed change for problems** | Native review workflows/products in all four; CLI `code-review`/`security-review` in Copilot. [CC6] [CC8] [OX5] [CU5] [CU8] [GH1] [GH13] | Diff review, security review, runtime verification and approval safety classification are different tasks. Managed review may not expose model choice. |
| **Investigate external sources and produce evidence** | Claude bundled `/deep-research`; Copilot native research agent/workflow. Codex docs show custom `docs_researcher` + MCP; Cursor documents web tools but no separate generic research agent in its built-in table. [CC5] [GH14] [OX1] [CU1] [CU2] | External research is not interchangeable with fast local code search. Custom examples/tools are weaker evidence of a native role than bundled workflows. |
| **Divide work and combine results** | Claude team lead/workflows; Codex main-agent orchestration; Cursor Project coordinator; Copilot `/fleet`. [CC4] [CC5] [OX1] [CU7] [GH15] | Could be a structural parent position, a script or a workflow, not a named independently routed specialist. |
| **Get a second opinion at a decision point** | Claude Advisor and Copilot rubber duck explicitly use another model for guidance/critique. [CC9] [GH11] | Server-side full-transcript advice and a read-only critique subagent are not identical. This is distinct evidence from ordinary final-diff review. |

## Resource and capability conclusions

- **Model assignment is a separate evidence field.** Documented examples range from inheritance (Codex defaults, many Claude agents), through a faster built-in (Cursor Explore), fixed documented CLI defaults (Copilot), phase routing (Claude `opusplan`), separate second-model advice/critique, and managed review with no user model switch. No universal role-to-model mapping follows. [OX1] [CC1] [CU1] [GH1] [CC3] [CC9] [GH11] [GH13]
- **Context is part of the task shape.** Exploration/browser/log-heavy work is explicitly isolated to avoid filling the parent context. Isolation does not mean free work: multiple agents still make model/tool requests and can add coordination or write conflicts. [CC1] [OX1] [CU1] [GH12]
- **Depth is not another occupation.** Quick/Deep review, reasoning effort, Auto routing preferences and exploration thoroughness are documented speed/cost/coverage controls. They should not be counted as independent task-role occurrences. [CC1] [CC8] [OX1] [CU5] [CU10] [GH13]
- **Modality is not established by a role label.** Cursor explicitly documents Browser DOM/screenshots and vision-capable image input; Copilot input support depends on the model. The reviewed sources do not establish role-specific audio/video requirements or a universal “multimodal agent” stereotype. [CU1] [CU2] [GH22] [GH23]

## Limits and newly surfaced factual prerequisites

1. **Named sample only.** This survey records presence in Claude Code, Codex, Cursor and Copilot. It does not estimate market-wide prevalence or validate vendor performance claims. No independent benchmark, cost experiment, latency measurement or product execution was performed.
2. **Current docs are mutable.** This asset is commit-pinned, but linked documentation generally is not. Date, surface and available release qualifications are recorded; no claim is made that all described features shipped together in every binary.
3. **Same-day Copilot transition matters.** Any later comparison must identify IDE/harness/CLI/cloud environment, account/policy availability and rollout date. Cloud/coding branding, old Edit mode and Local planning settings cannot be flattened into current universal roles. The Edit settings-reference/release-note conflict remains explicitly documented. [GH2] [GH6] [GH19] [GH20]
4. **Routing availability is a factual prerequisite, not a choice made here.** To claim that a future role selector can affect a model, first identify an exposed slot, inheritance/fallback rules, supported provider/model access, and whether a managed service hides model selection. Relevant counterexamples are managed Claude/Copilot review and CLI research's dedicated model. [CC8] [GH13] [GH14]
5. **Negative findings are bounded.** “Not documented” means absent from the reviewed inventory/page, not proof that the entire product lacks a feature. This is not an exhaustive inventory of every plugin, SDK template, automation or internal agent.
6. **No inaccessible-source blocker.** Official sources for all four products were reachable. OpenAI redirects and multi-surface content were handled by recording canonical URLs and surface scope. No credentials, private product settings or user decision were needed to complete the factual survey.
7. **HITL remains separate.** Final generalized names, grouping/count, provider quick selection and any UI/model assignments remain human decisions. This report supplies native terms and task/resource evidence only.

## Source URLs

All sources accessed **2026-10-28**. Inline reference links attach claims to their owning primary source. Section fragments provide navigation, not a claim of immutable content.

### Anthropic

- [CC0 — Changelog, v2.1.312][CC0]
- [CC1 — Built-in/custom subagents, model choice, context, tools and examples][CC1]
- [CC2 — Permission modes][CC2]
- [CC3 — Model configuration and `opusplan`][CC3]
- [CC4 — Agent teams][CC4]
- [CC5 — Dynamic workflows and bundled deep research][CC5]
- [CC6 — Local code review][CC6]
- [CC7 — Ultrareview][CC7]
- [CC8 — Managed Code Review][CC8]
- [CC9 — Advisor tool][CC9]
- [CC11 — Anthropic marketplaces][CC11]
- [CC12 — June 29–July 3, 2026 changes][CC12]

### OpenAI

- [OX1 — Subagents and custom-agent examples][OX1]
- [OX2 — Slash commands][OX2]
- [OX3 — Best practices, planning and external context][OX3]
- [OX4 — Configuration reference][OX4]
- [OX5 — Code review][OX5]
- [OX6 — Developer/CLI commands][OX6]
- [OX7 — Agent approvals and security][OX7]

### Cursor

- [CU1 — Built-in and custom subagents][CU1]
- [CU2 — Agent overview and tools][CU2]
- [CU3 — CLI modes][CU3]
- [CU4 — Plan Mode][CU4]
- [CU5 — Agent Review][CU5]
- [CU6 — Debug Mode][CU6]
- [CU7 — Projects and coordinator][CU7]
- [CU8 — Bugbot][CU8]
- [CU9 — Cloud Agents][CU9]
- [CU10 — Cursor Router][CU10]
- [CU11 — Permission run modes][CU11]

### GitHub / Microsoft

- [GH1 — Copilot CLI built-in-agent reference][GH1]
- [GH2 — VS Code harnesses and built-in session agents][GH2]
- [GH3 — IDE Agent mode][GH3]
- [GH4 — IDE Plan mode][GH4]
- [GH5 — VS Code planning; Copilot versus Local settings][GH5]
- [GH6 — Copilot on GitHub; October 28 cloud transition][GH6]
- [GH7 — April 1 cloud-agent rename and expanded work][GH7]
- [GH8 — Cloud model selection][GH8]
- [GH9 — Cloud/local sandbox billing][GH9]
- [GH10 — VS Code permissions and Autopilot][GH10]
- [GH11 — Rubber duck second opinion][GH11]
- [GH12 — VS Code subagents by harness][GH12]
- [GH13 — Copilot code review, model limits and effort][GH13]
- [GH14 — CLI research workflow and dedicated model][GH14]
- [GH15 — CLI fleet orchestration][GH15]
- [GH16 — VS Code custom agents][GH16]
- [GH17 — April 7, 2025 Agent/Edit guidance][GH17]
- [GH18 — VS Code 1.110 Edit and Explore history][GH18]
- [GH19 — VS Code 1.126 Edit history][GH19]
- [GH20 — Current AI settings reference][GH20]
- [GH21 — Custom-agent inspiration library][GH21]
- [GH22 — VS Code model capabilities][GH22]
- [GH23 — Copilot image input][GH23]

[CC0]: https://code.claude.com/docs/en/changelog.md#2-1-312
[CC1]: https://code.claude.com/docs/en/sub-agents
[CC2]: https://code.claude.com/docs/en/permission-modes
[CC3]: https://code.claude.com/docs/en/model-config#model-aliases
[CC4]: https://code.claude.com/docs/en/agent-teams
[CC5]: https://code.claude.com/docs/en/workflows#bundled-workflows
[CC6]: https://code.claude.com/docs/en/code-review-local
[CC7]: https://code.claude.com/docs/en/ultrareview
[CC8]: https://code.claude.com/docs/en/code-review
[CC9]: https://code.claude.com/docs/en/advisor
[CC11]: https://code.claude.com/docs/en/plugins/anthropic-marketplaces
[CC12]: https://code.claude.com/docs/en/whats-new/2026-w27
[OX1]: https://learn.chatgpt.com/docs/agent-configuration/subagents
[OX2]: https://learn.chatgpt.com/docs/reference/slash-commands
[OX3]: https://learn.chatgpt.com/guides/best-practices
[OX4]: https://learn.chatgpt.com/docs/config-file/config-reference
[OX5]: https://learn.chatgpt.com/docs/code-review
[OX6]: https://learn.chatgpt.com/docs/developer-commands?surface=cli
[OX7]: https://learn.chatgpt.com/docs/agent-approvals-security
[CU1]: https://cursor.com/docs/subagents
[CU2]: https://cursor.com/docs/agent/overview
[CU3]: https://cursor.com/docs/cli/using
[CU4]: https://cursor.com/docs/agent/plan-mode
[CU5]: https://cursor.com/docs/agent/agent-review
[CU6]: https://cursor.com/docs/agent/debug-mode
[CU7]: https://cursor.com/docs/agent/projects
[CU8]: https://cursor.com/docs/bugbot
[CU9]: https://cursor.com/docs/cloud-agent
[CU10]: https://cursor.com/docs/cursor-router
[CU11]: https://cursor.com/docs/agent/security/run-modes
[GH1]: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference#built-in-agents
[GH2]: https://code.visualstudio.com/docs/agents/run/agent-harnesses
[GH3]: https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-agent-mode
[GH4]: https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-plan-mode
[GH5]: https://code.visualstudio.com/docs/agents/run/planning#customize-planning
[GH6]: https://docs.github.com/en/copilot/concepts/copilot-surfaces/copilot-on-github
[GH7]: https://github.blog/changelog/2026-04-01-research-plan-and-code-with-copilot-cloud-agent/
[GH8]: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/changing-the-ai-model
[GH9]: https://docs.github.com/en/billing/concepts/product-billing/cloud-and-local-sandboxes
[GH10]: https://code.visualstudio.com/docs/agents/run/approvals
[GH11]: https://docs.github.com/en/copilot/concepts/agent-capabilities/choosing-and-delegating-agent-work/getting-a-second-opinion
[GH12]: https://code.visualstudio.com/docs/agents/run/subagents
[GH13]: https://docs.github.com/en/copilot/concepts/agent-capabilities/agent-powered-workflows-and-operations/code-review
[GH14]: https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/research-with-copilot-cli
[GH15]: https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/speed-up-task-completion
[GH16]: https://code.visualstudio.com/docs/agent-customization/custom-agents
[GH17]: https://code.visualstudio.com/blogs/2025/04/07/agentMode
[GH18]: https://code.visualstudio.com/updates/v1_110
[GH19]: https://code.visualstudio.com/updates/v1_126#_edit-mode
[GH20]: https://code.visualstudio.com/docs/agents/reference/ai-settings
[GH21]: https://docs.github.com/en/copilot/tutorials/customization-library/custom-agents
[GH22]: https://code.visualstudio.com/docs/agent-customization/language-models
[GH23]: https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/chat-with-copilot/chat-in-ide#using-images-in-copilot-chat
