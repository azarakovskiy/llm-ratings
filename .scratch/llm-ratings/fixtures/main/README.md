# Fixtures — main and runtime source/selection contract (tickets 11–18, 34–38)

Saved source payloads, curated to a small subset and supplemented with
synthetic rows, served by the CLI's `--fixtures` mode (the spec's
user-confirmed test seam: no network below the fetch boundary).

These are historical test payloads, not current market measurements. The
recorded snapshot date and Intelligence Index version describe the saved
evidence only. The model set includes fictional names, and the Terminal-Bench
and OpenRouter rows are synthetic; missing creators are not coverage claims.

## Local web launch

The runtime uses only the Python standard library; there is no dependency
installation step. From the repository root, launch directly without `.env`:

```sh
LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --web --fixtures .scratch/llm-ratings/fixtures/main --role Explorer
```

Open the printed `http://127.0.0.1:PORT/` URL. The operating system chooses
the actual port. `--web` works with redirected input/output and does not need
a terminal. The process stays in the foreground until **Ctrl-C**, which closes
the listener. Closing the browser tab does not stop the server.

The supported default launcher sources the local `.env` and forwards `ARGS`:

```sh
make run ARGS='--fixtures .scratch/llm-ratings/fixtures/main --role Explorer'
```

For that offline command, `.env` must set `LLM_RATINGS_AA_API_KEY=dummy`.
For a live run, set a real key and omit `--fixtures`. This launches the real
application, not the archived visual prototype. Full setup and control guidance
is in the [runtime README](../../../../README.md).

Startup loads these saved source payloads and builds the shared dataset once.
Role, objective, creator, capability-filter and view controls reuse that same
loaded snapshot; they do not fetch again. Restart the process to load a new
snapshot. Each launch starts one local-only, in-memory session without saved
preferences or configuration writes. Tabs using the same process share its
choices; this is not a hosted or multi-user service.

The comparison identifies this historical/synthetic fixture as an **offline
snapshot**, with its source dates separate from the current fetch time. It is
not live market advice. The dummy key is still required for offline runs;
credentials and raw source payloads stay on the server. Setup or required
rating-source errors stop startup before any URL/advice is served. Missing
OpenRouter enrichment does not stop the comparison.

For a live refresh, export a real `LLM_RATINGS_AA_API_KEY` and run
`python3 -m llmratings --web`. `--role NAME` chooses the initial role; without
it, the first role in `llmratings/roles.json` is used. Without `--web`, module
invocation always prints batch output and exits, even in a terminal:

```sh
LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --fixtures .scratch/llm-ratings/fixtures/main --role Explorer
```

Visible Role, Objective, Selected-index capability filter, Model creator and
view controls drive the shared policy below. **Details** opens or closes model
evidence inline only on request; focus alone does not expand it. **How picks
work** explains role purposes, objectives, exact ordering, grades and source
limits in a secondary disclosure. Source attribution and the refresh/fetch
date remain visible when disclosures are closed. **Source dates and provenance**
and Details distinguish the current file-read time from historical/synthetic
snapshot and published observation dates. Missing optional timing, context,
modalities or unverified 30-day token share is unavailable, not zero. Setup and
required rating-source failures stop the run; best-effort OpenRouter enrichment
does not. Unknown role names are usage errors (exit status 2).

## Provenance

Fetched live 2026-08-05:

- `deepswe.json` — `https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json`
  (no auth; `generated_at` 2026-08-04T01:34:32Z)
- `aa.json` — `https://artificialanalysis.ai/api/v2/language/models/free?page_size=200&page=1..3`
  (free tier, `x-api-key`; `intelligence_index_version` 4.1)
- `tb.json` — **synthesized** (ticket 13) in the shape of the real v2.1
  payloads per the source survey (`assets/02-terminal-bench-source-survey.md`):
  `{"listing": [...]}` mirrors the GitHub contents-API response for
  `harbor-framework/terminal-bench-2-1/leaderboard/submissions`, and
  `submissions` maps each filename to its submission JSON (`source_filter` /
  `metadata` / `metrics` / `disqualified_trials` / `trials`). No live TB
  payloads are saved; the entries are plausible v2.1-shaped rows for the
  fixture models (efforts high/xhigh/max only, accuracy ± stderr, cost USD,
  avg trial duration, tokens). Live shapes land in ticket 15.
- `or.json` — **synthesized** (ticket 18) in the shape of the real OpenRouter
  `GET /api/v1/models` response per the source survey
  (`assets/05-openrouter-source-survey.md`): `{"data": [...]}` rows with a
  vendor-prefixed `id`, `context_length`, and `architecture.modalities`
  (input/output modality lists). Real OR data (400 rows) was fetched live
  2026-08-08 to validate the shape, but the fixture models are fictional, so
  the rows are hand-written in the real shape like `tb.json`. Kimi K3 is
  deliberately omitted — the "no OpenRouter row" detail case.

The recorded DeepSWE/Artificial Analysis rows preserve the historical
payload evidence; Terminal-Bench/OpenRouter rows are synthetic as noted above.
The curated model names and measurements are test evidence, not market advice.

`provenance.json` records the historical snapshot dates from this README for
DeepSWE/Artificial Analysis and marks Terminal-Bench/OpenRouter as synthetic.
Their synthetic snapshot dates are unknown. A run's actual UTC fetch timestamp
is separate: reading these files today does not make their measurements current.

## Model set (7)

| Model | Artificial Analysis rows in fixture | Historical test purpose |
|---|---|---|
| GPT-5.6 Luna (OpenAI, closed) | all efforts | cheapest config; the frontier anchor; near-tie score/cost story |
| GPT-5.6 Sol (OpenAI, closed) | all efforts | frontier at medium/high/xhigh; dominated at low |
| GPT-5.5 (OpenAI, closed) | all efforts | same-effort dominated at low — the replacement-preference case |
| Claude Opus 5 (Anthropic, closed) | all efforts | top of the frontier path at max |
| Kimi K3 (Moonshot, open-weights) | low, max | open-weight model; Artificial Analysis-only config at low (DeepSWE unavailable) |
| GPT-5.6 Terra (OpenAI, closed) | **deliberately excluded** | source-only at low: Intelligence score and task cost unavailable |
| Qwen3.8 Max (Alibaba) | none in recorded payload | no Artificial Analysis row; source-only identity with DeepSWE at Extra high |

Curation notes:

- GPT-5.6 Terra's AA rows exist in the real payload but are excluded so the
  fixture spans "with and without AA rows" per ticket 11 — a real model
  rendering source-only at low effort. The checked-in alias table still maps
  `gpt-5-6-terra`; the join degrades to source-only when the AA row is absent,
  and ticket 15's live payloads restore it.
- `gpt-5-5-instant-*` / `gpt-5-5-pro` AA rows are separate models, not
  GPT-5.5 variants — excluded.
- Rows with no effort setting (non-reasoning AA rows) are kept verbatim; the
  parser ignores them for configs.

## What the historical subset exercises

These are Intelligence comparison cases from the saved evidence, not a claim
that the same models win under another index or a current live refresh:

- Frontier membership and markers (Luna Low is the only frontier config at
  Low effort).
- Replacement arrows: same-effort preferred (GPT-5.5 Low → Sol Low: +5.9
  points, save $0.015 — a cross-effort Luna Maximum arrow has strictly higher
  gain, so the preference is observable); cross-effort fallback (Kimi Low →
  Luna Maximum; Sol Low → Luna Maximum; Opus 5 Low → Sol Medium).
- Score/task-cost changes near ties (Sol Low sits $0.002 above Kimi Low).
- Frontier path: 12 configs spanning Low → Maximum (Luna Low … Opus 5 Maximum).
- Independent source grades, selected measured effort, open and closed
  weights, and unavailable task cost/value on source-only rows.

## TB set (ticket 13) — 11 submissions, 4 models

| File (abridged) | Agent | Model | Effort | Acc ± CI | Date | Role |
|---|---|---|---|---|---|---|
| …-gpt-5-6-luna-max-codex-cli | codex-cli | GPT-5.6 Luna | max | .757 ± .021 | 07-11 | the recency tie-break winner |
| …-gpt-5-6-luna-max-junie-cli | junie-cli | GPT-5.6 Luna | max | .757 ± .024 | 07-01 | same score, older — loses the tie |
| …-gpt-5-6-luna-xhigh-codex-cli | codex-cli | GPT-5.6 Luna | xhigh | .733 ± .021 | 07-05 | Extra high coverage |
| …-gpt-5-6-luna-high-codex-cli | codex-cli | GPT-5.6 Luna | high | .701 ± .022 | 06-20 | TB grade 4 at high |
| …-gpt-5-6-sol-max-codex-cli | codex-cli | GPT-5.6 Sol | max | .769 ± .020 | 07-10 | best TB score at max → grade 5 |
| …-gpt-5-6-sol-xhigh-codex-cli | codex-cli | GPT-5.6 Sol | xhigh | .745 ± .022 | 07-08 | xhigh coverage |
| …-gpt-5-6-sol-high-codex-cli | codex-cli | GPT-5.6 Sol | high | .712 ± .023 | 06-25 | TB grade 5 at high |
| …-gpt-5-5-high-warp | warp | GPT-5.5 | high | .671 ± .025 | 07-02 | best-agent collapse winner (.671 > .664) |
| …-gpt-5-5-high-codex-cli | codex-cli | GPT-5.5 | high | .664 ± .024 | 06-15 | loses the collapse; no Terminal-Bench Maximum row |
| …-claude-opus-5-max-claude-code | claude-code | Claude Opus 5 | max | .689 ± .019 | 07-09 | TB grade 2 at max |
| …-claude-opus-5-max-terminus-2 | terminus-2 | Claude Opus 5 | max | .661 ± .020 | 07-03 | loses the collapse |

Notes:

- Model strings (`model_name`) are the TB v2.1 display style ("GPT-5.6 Luna",
  "GPT-5.5", "Claude Opus 5") and map to AA base slugs via the alias table;
  every TB row joins onto a canonical model — none degrades to `tb:` identity.
- No Terminal-Bench rows at Low/Medium (v2.1 does not offer them): an
  unavailable rating at either effort is an honest absence, not a dropped row.
- Kimi K3, Terra and Qwen3.8 Max have no Terminal-Bench rows. Their ratings
  remain unavailable at every effort; the fixture retains all 11 submissions.

## Runtime normalized source contract

`fetch.fetch_all(directory)` reads the saved responses without network;
`fetch.fetch_all(None)` uses the existing live endpoints. Both return the
source payloads plus `_provenance`. `identity.build(aliases, raw)` carries that
record into `Dataset.provenance` and preserves each original row in
`Rating.raw`. No second acquisition path or production snapshot is introduced.

For Artificial Analysis, each measured effort has these independent nullable
fields. Published paths below are relative to `data[]`:

| Rating field | Published path and basis |
|---|---|
| `score` | `evaluations.artificial_analysis_intelligence_index` — Intelligence only |
| `coding_score` | `evaluations.artificial_analysis_coding_index` |
| `agentic_score` | `evaluations.artificial_analysis_agentic_index` |
| `cost` | `artificial_analysis_intelligence_index_cost.cost_per_task.total_cost` — matching Intelligence benchmark USD/task |
| `first_answer_seconds` | `performance.median_time_to_first_answer_token_seconds` — includes thinking |
| `speed` | `performance.median_output_tokens_per_second` — output throughput |
| `first_token_seconds` | `performance.median_time_to_first_token_seconds` — may stop at a reasoning token |
| `response_500_tokens_seconds` | `performance.median_end_to_end_response_time_seconds` — published synthetic estimate for 500 answer tokens |
| `pricing` | `pricing.price_1m_input_tokens`, `price_1m_output_tokens`, `price_1m_cache_hit_tokens`, `price_1m_cache_write_tokens` — separate USD per million tokens |

An absent, null, nonnumeric or non-finite optional number becomes `None`;
zero remains zero. A malformed optional object leaves its metrics unavailable
without dropping the configuration or its raw row. No timing, score or cost is
copied from another effort. The outer Intelligence suite `total_cost`, token
list prices, and DeepSWE/Terminal-Bench run expenditures are different bases.
There is no established matching Coding/Agentic task cost. The separate Coding
Agent Index is not a substitute for these scores, and the complete current
Coding/Agentic formulas remain a source gap.

`Dataset.provenance` exposes `mode` (`fixture` or `live`), actual UTC
`fetched_at`, and per-source `urls`, `snapshot_date`, `synthetic`, and labelled
`source_dates` when published. Optional fixture metadata also retains the
boolean `fictional_model_names`; this main fixture sets it to true. Other
saved responses are not called fictional or synthetic without their own flags.
Unknown history stays null/empty. Live Artificial Analysis pagination retains
page URLs, row ranges, reported index versions and dates. Each rating gets its
page's `intelligence_index_version`, `source_url` and `source_dates`; the final
page's dates are not attached to the first page. Terminal-Bench ratings retain
individual listing `download_url` values in `source_url`, plus submission
`date`, agent, published `accuracy_stderr` and wholesale raw evidence. Its
standard error is not a published confidence interval and is not normalized
into `ci_lo`/`ci_hi`; those fields retain DeepSWE's published endpoints.
Source URLs omit credentials, headers, fragments and non-pagination query
parameters.

The canonical model key is still the Artificial Analysis base slug; UUIDs
remain per-effort evidence. Existing aliases and Terminal-Bench best-agent,
then recency collapse are unchanged. Recommendation inclusion requires at
least one DeepSWE or Terminal-Bench rating. Source-only models remain
auditable with no manufactured Artificial Analysis values. Artificial
Analysis-only catalog models cannot become recommendations, but their finite
scores contribute to the selected-index capability-grade reference population.

OpenRouter catalog enrichment remains best effort. Context and input/output
modalities are optional; malformed or missing catalog data does not fail
ratings. Original joined rows remain in `Model.catalog_rows`.
`Dataset.openrouter_models` maps a supplied catalog `canonical_slug` (the
rankings permaslug) through that row's `id`, then the existing ID/alias join,
to the canonical model key. A permaslug is never derived from an `id`.
Existing ID-only and vendor-prefix joins still work.

`Model.token_share_30d` remains explicitly `None`, not zero. No authenticated
rankings payload, complete 30-day coverage or top-50 presence has been verified
by the recorded evidence. Catalog fields or illustrative totals do not prove
share; top-50 absence is not zero usage. A future positive display value needs
verified window/coverage, source/date, a denominator including `other`, and
one canonical-model aggregation across variants, dated snapshots and days
without double-counting or effort splits. This is an evidence/access limit,
not a claim that the intended feed is impossible. Share cannot affect policy.

Timing is explanatory, not whole-agent task duration or evidence about a
creator's particular serving endpoint. Time to first answer token includes
thinking; time to first token may stop at a reasoning token. Output tokens per
second is throughput, and the published 500-answer-token response time is a
separate estimate. Do not substitute one for another or reconstruct missing
latency. None filters, weights, orders or breaks ties, and missing timing
does not disqualify a configuration. The Free route's exact prompt preset and
provider aggregation remain unestablished. This implementation and its offline
checks do not claim a newly inspected authenticated live response.

## Runtime role catalog and defaults

[Ticket 35](../../issues/35-eight-role-selection-policy.md) and the
[approved spec](../../spec.md) define this runtime policy. They supersede
the historical five-role/unchanged-data-model clauses of ADR 0002; the ADR
and historical fixture evidence are not rewritten as new measurements.

`llmratings/roles.json` remains the single editable profile file.
`LLM_RATINGS_ROLES` is a test-only file override, not a second user configuration
surface. File order is presentation order:

| Role | Purpose and boundary | Artificial Analysis index | Default objective |
|---|---|---|---|
| Explorer | Find and explain existing repository behavior; approach selection belongs to Planner. | Intelligence | Best value |
| Researcher | Verify external facts and produce sourced findings; not local repository discovery. | Intelligence | Best value |
| Planner | Choose an approach, decisions and an actionable plan; not implementation or worker management. | Intelligence | Highest capability |
| Coder | Make and verify changes, including fault diagnosis, UI design, tests and documentation. | Coding | Highest capability |
| Reviewer | Independently assess changes/proposals, security and second opinions; implementing fixes is separate. | Coding | Highest capability |
| Coordinator | Divide/delegate work, manage dependencies and combine results; not each worker's implementation. | Agentic | Highest capability |
| Generalist | Mixed end-to-end work when no specialist fits; not an alias for every specialist. | Intelligence | Best value |
| Utility | Bounded auxiliary outputs: titles, commit messages, classification and straightforward transformations. | Intelligence | Lowest qualifying price |

Every bundled profile has capability floor **2**. Explorer is the default,
so default batch output uses **Explorer / Intelligence / Best value**.
`--role` selects a named profile; unknown names exit 2. The former default
names have no compatibility aliases. Profiles retain purpose descriptions,
speed/context/reasoning guidance, selected index, objective and floor.
Capacity guidance is prose only: it adds no weights, timing rules, fixed
effort or hidden capability filter. Roles describe purpose, not cheap/fast/
thorough modes. Utility is not necessarily cheap or easy: a short output can
require substantial reasoning and source context, and faithful summarization
or memory extraction is not automatically trivial utility work.

The profile index keys are `intelligence`, `coding` and `agentic`; objective
keys are `cap`, `ppi` and `price`. Visible objective labels are **Highest
capability**, **Best value** and **Lowest qualifying price**, not these
internal keys. Malformed profiles and unknown indexes/objectives produce
actionable startup errors. A recognized but unsupported combination is
instead an explicit **unavailable objective**, not a malformed profile.

Intelligence supports all three objectives. Coding/Agentic support Highest
capability only. An area-index Best value or Lowest qualifying price override
remains selected and unavailable until changed: no fallback objective, index
switch or invented denominator. The web application and batch output consume
the shared session/query path. Provider selection and both projections are
available in the browser, with explicit model Details and How picks work
disclosures; there is no parallel terminal UI.

## Eligibility, effort and exact objective order

Select one measured configuration per included model on the role's index.
Apply the same complete comparison keys within a model and across models:

| Index / objective | Required data at that effort | Comparison keys, in order |
|---|---|---|
| Intelligence / Highest capability | Finite Intelligence score; finite non-negative matching Intelligence task cost. | Score descending; task cost ascending; lower effort; canonical model key. |
| Intelligence / Best value | Finite Intelligence score; finite positive matching task cost; finite usable quotient. | Score / task cost descending; score descending; task cost ascending; lower effort; canonical model key. |
| Intelligence / Lowest qualifying price | Finite Intelligence score; finite non-negative matching task cost; selected-index grade at least the role floor. | Task cost ascending; score descending; lower effort; canonical model key. |
| Coding / Highest capability | Finite Coding score; no task cost required. | Coding score descending; lower effort; canonical model key. |
| Agentic / Highest capability | Finite Agentic score; no task cost required. | Agentic score descending; lower effort; canonical model key. |

Full effort labels and tie order are **Low < Medium < High < Extra high <
Maximum**. Never rely on fetch order or table section order for exact ties.
No role fixes an effort, borrows another index's score or combines one
effort's score with another's cost.

Intelligence cost means **Benchmark task cost** from the matching measured
Intelligence workload, even under Highest capability. A published zero cost
can qualify for Highest capability or Lowest qualifying price, but cannot
provide Best value. Missing, negative or non-finite required costs fail
eligibility. **Capability per dollar** means Intelligence points divided by
matching benchmark-task USD, not predicted production-task return. Token list
prices, blended prices, another benchmark's run costs and invented token
mixes cannot supply that denominator. There is no established matching
Coding/Agentic task cost, price tie, value/price objective or cost-based advice.

Source-only and other included models without a qualifying configuration
stay reachable as **unranked**, with specific reasons and independent source
evidence. An empty eligible set shows **No qualifying configuration** with
the role, provider, objective and active constraints; it does not silently relax
them. A later capability display exclusion is separate from missing measurements
and retains the objective-selected configuration and its display-filter reason.

## Grades, floor and Intelligence advice

Artificial Analysis capability grades use **every finite scored model ×
measured-effort configuration for the selected index in the refresh**, across
all efforts and the full catalog, including models outside recommendation
inclusion and scores without an eligible cost. Compute this population before
objective eligibility, per-model effort selection or capability display
filtering. Do not grade per effort or creator, or borrow another index's
grade. Provider constraints never change these reference sets.

Use `tier.grades` on distinct valid values: equal values always share a grade.
For descending distinct value position `i` (zero-based) among `n` values,
the higher-is-better grade is `6 - (floor(i * 5 / n) + 1)`. Small sets can
populate fewer than five grades; empty axes stay unavailable. Recompute on
refresh. DeepSWE and Terminal-Bench grades remain **source-independent within
each source's rated effort population**. Unknown-effort raw scores stay
available, but do not receive capability grades or ranks and cannot create
source disagreement. Shared population selectors keep grades and rank
denominators aligned. Terminal-Bench first collapses best agent per model ×
effort, breaking score ties by recency. Never average these ratings or different
Artificial Analysis indexes into one score.

The floor applies **only** to Lowest qualifying price, including a manual
override on any Intelligence role. For bundled profiles grade **2 qualifies**
and grade 1 does not. Highest capability and Best value are floor-free.
The separate display filter (all grades, grade 5, grade 4 and above) uses the
objective-selected configuration's selected-index grade; it never selects a
different effort. Value, output-speed and price grades keep their independent
valid axes over the unfiltered role-selected rows. Intelligence value requires
a usable score/positive-cost quotient; price tier uses matching task cost
with 1 cheapest. Output-speed evidence remains independently available for
area roles, without inferring area value/price grades. Capability display filters
and provider constraints do not re-bin any of these grades.

Intelligence advice spans all included models' valid scored/priced efforts
**within the selected creator scope**, independent of the role floor and display
filter. All providers restores the global included-model comparison universe.
Provider means the Artificial Analysis model creator, not a gateway/endpoint or
price dimension. A non-selected effort can supply replacement or alternative
evidence. Artificial Analysis-only catalog models never enter this universe.
Preserve the cross-effort
frontier, strict same-effort replacement preference with cross-effort fallback,
and up to three strictly cheaper alternatives with Intelligence score at least
the opened score minus five, sorted by task cost. The Intelligence table puts
Frontier before Dominated, with full objective order within each section; the
shared policy's direct objective order is independent of that presentation.
Coding/Agentic tables use direct score order with no frontier, replacement,
cheaper-alternative or cross-workload value claim.

## Shared selection state and Provider picks

`llmratings.session.Session(dataset, roles, role_name=None)` owns the active
role, optional objective override, capability display filter, one creator or
All providers, active view, passive model selection and requested model details.
It starts on the first file-ordered role and its default objective, all grades,
All providers and Model table, with no selected model or details. An explicit
supported `--role` selects that initial profile. Nothing is saved.

`Session.query()` uses `render.query` for both projections on the already loaded
dataset; transitions do not acquire sources or create a new market snapshot.
The batch Model table uses that same session and query. The query retains
direct-objective `rows` separately from frontier-first `table_rows`/`sections`,
plus creator-grouped `picks`, `providers_without_picks`, unranked measurement
reasons and capability-display `excluded` records. It identifies the selected
role/index/objective/provider/filter/view and an explicit global, creator-local
or unavailable `advisory_scope`. Row replacement/alternative evidence and the
cross-effort frontier path use that same scope. Coding/Agentic return no cost
frontier, replacement or cheaper-alternative advice.

Provider picks takes the first two **distinct models in direct objective
order** within each creator: **Primary**, then **Runner-up**, each at its
objective-selected effort. It does not read the first two frontier-first table
rows. A dominated Intelligence model can be a pick; Primary does not mean global
frontier membership. Runner-up is not another effort of Primary or a
price-diversity/cheapest-alternative choice. One model yields one Primary and
**No qualifying runner-up**; zero yields no picks and an explicit reason.
All providers produces picks per creator, not two global picks.

The full creator chooser contains every known creator in the loaded catalog,
including Artificial Analysis-only creators without eligible picks. Fixed
shortcuts are **OpenAI, Anthropic, Google, DeepSeek and xAI**, independent of
scores, token share, role and eligible counts. A shortcut with no eligible model
remains selectable. Unknown source-only creator evidence stays unranked and
reachable under All providers rather than being assigned to an invented creator.
An otherwise eligible Artificial Analysis configuration without a creator is
retained separately as `creator_unavailable`. Provider picks exposes this
evidence under **Creator unavailable** and explains when no creator-attributed
picks exist; it does not add `—` as a creator or silently omit the model.

Use explicit `set_role`, `set_objective`, `set_min_grade`, `set_provider` and
`set_view` transitions. A role change clears the override and uses the new
profile's index/default; every other choice is retained. Other transitions
change only their named choice. All result-set changes clear passive selection
and requested details. `select_model` never opens evidence;
`request_details(model_key)` and `close_details()` open and close it explicitly.
Requests resolve only against the active view's `detail_targets`: Model table
rows or actual Primary/Runner-up rows, plus creator-unavailable, excluded and
unranked disclosures where rendered. A stale queued table request cannot
announce opened evidence for a model absent from Provider picks.

Empty or unavailable results retain all selected choices. Query
`recovery_actions` exposes named-only actions: **All providers** clears only the
creator, **Clear capability filter** clears only that filter, **Highest
capability** changes only the objective, and **Use role default** clears only
its override. `Session.recover(action)` applies that named transition. No
recovery changes index, creator, filter or view as a hidden fallback.

## Visible evidence and proxy limits

Use **Artificial Analysis**, **Intelligence score**, **Coding score**,
**Agentic score**, **Benchmark task cost** and **Capability per dollar** in
consumer explanations, with the full objective and effort labels above.
Selected configuration, raw selected-index score/grade and source-specific
ratings remain distinct and auditable; unavailable data is not a zero.
OpenRouter share is display-only and cannot affect any score, grade,
eligibility, objective or tie.

These published scores are **role-selection proxies**. Intelligence is not
universal task success; Coding is not measured review accuracy; Agentic is
not proof of multi-agent coordination quality. The complete current Coding/
Agentic composite formulas remain an unresolved source fact. Do not substitute
the separate Coding Agent Index or imply that fixture output validates role
performance. See the [dated metric findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md)
for primary-source evidence and its limits. Historical/synthetic fixture
results and passing offline checks are not current market recommendations.

