# LLM Ratings

Compare models for a task-purpose role using published Artificial Analysis,
DeepSWE and Terminal-Bench v2.1 evidence. The local web application offers a
**Model table** and **Provider picks**. Both views and batch output use the same
Python selection policy. Scores are benchmark proxies, not proof of success
on your task.

## Setup and launch

Use Python 3, `make` and a browser. The runtime uses only the Python standard
library: no dependency installation, frontend build or terminal UI is required.
Run commands from the repository root.

For live sources, get an API key from [Artificial Analysis](https://artificialanalysis.ai/).
Create or edit the local `.env` file with:

```sh
LLM_RATINGS_AA_API_KEY=your-key
```

Keep the key private. `make run` sources `.env`, exports its values and launches
`python3 -m llmratings --web`. It forwards `ARGS`:

```sh
make run
make run ARGS='--role Coder'
```

To use saved fixtures without network access, use a dummy key. For `make run`,
set `LLM_RATINGS_AA_API_KEY=dummy` in `.env`, then run:

```sh
make run ARGS='--fixtures .scratch/llm-ratings/fixtures/main --role Explorer'
```

Or launch directly, without reading `.env`:

```sh
LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --web --fixtures .scratch/llm-ratings/fixtures/main --role Explorer
```

After loading the sources, the process prints exactly one loopback URL in this
form:

```text
http://127.0.0.1:PORT/
```

`PORT` is the actual port chosen by the operating system, not a literal value
to type. Open the exact printed URL, including `127.0.0.1`. The process stays in
the foreground; press **Ctrl-C** in its terminal to close the listener. Closing
the browser tab does not stop it. `--web` also works with redirected input or
output. The application is not the archived visual prototype or a preview server.

**Fixtures are historical test evidence, not live market advice.** This curated
set includes fictional model names and synthesized Terminal-Bench/OpenRouter
rows. Recorded source snapshot dates and index versions describe only the saved
evidence. Reading it today does not make it current. Missing creators in this
small fixture set are not market-coverage claims. See the
[fixture provenance and policy contract](.scratch/llm-ratings/fixtures/main/README.md).
Other fixture directories can contain real saved responses. Their offline notice
does not imply fictional names or synthetic sources: those caveats use the
optional `provenance.json` boolean `fictional_model_names` and per-source
`synthetic` flags. Missing metadata remains unknown.

## Roles and controls

`--role NAME` selects the initial role. Without it, the first profile in
[`llmratings/roles.json`](llmratings/roles.json), currently **Explorer**, is used.
The same file defines role order, purpose, index, default objective, capacity
guidance and price floor. The application never writes this file.

| Role | Selected Artificial Analysis index | Default objective |
|---|---|---|
| Explorer | Intelligence | Best value |
| Researcher | Intelligence | Best value |
| Planner | Intelligence | Highest capability |
| Coder | Coding | Highest capability |
| Reviewer | Coding | Highest capability |
| Coordinator | Agentic | Highest capability |
| Generalist | Intelligence | Best value |
| Utility | Intelligence | Lowest qualifying price |

Use the visible controls with mouse or keyboard:

- **Role** selects the task purpose, not a fixed reasoning effort. The objective
  selects one measured effort per model. A role change resets an objective
  override but retains the provider, capability filter and view.
- **Objective** selects Highest capability, Best value or Lowest qualifying
  price. **Use role default** clears only its override. Coding and Agentic have
  no established matching task-cost basis: value/price objectives remain
  explicitly unavailable until changed, without a fallback to Intelligence.
- **Selected-index capability filter** displays all grades, Grade 5, or Grade 4
  and above. It hides rows after effort selection; it does not pick a different
  effort. The inclusive grade-2 floor in bundled profiles applies only to Lowest
  qualifying price. Highest capability and Best value are floor-free.
- **Model creator** shortcuts and the **Full creator chooser** constrain
  recommendations and Intelligence comparisons. **All providers** clears only
  that constraint. Provider means model creator, not a serving endpoint. Grades
  retain their source/index reference populations when this choice changes.
- **Model table** presents Intelligence frontier sections before dominated rows;
  Coding/Agentic use their own score order. **Provider picks** shows each
  creator's first two distinct eligible models in direct objective order:
  **Primary** and **Runner-up**. Primary need not be on the frontier; Runner-up
  is not a cheaper alternative or another effort of Primary.
- **Details** explicitly opens evidence inline for that model; its visible close
  action closes it. Focus or passive selection does not open evidence. Available
  unranked and display-excluded models retain evidence and specific reasons.
  Role, objective, provider, filter and view changes clear stale model details.
  In Provider picks, eligible models without a published creator remain under
  **Creator unavailable**, with their own Details action, not an invented creator.
  A queued Details request cannot open a model absent from the active view.
- **How picks work** is a secondary disclosure with role purposes, index limits,
  eligibility, objective ordering and ties, grade populations and source
  definitions. Opening it or Details does not refetch sources or alter choices.

Empty results keep the active constraints. Use the named recovery action to
change only the provider, capability filter or objective it names. A missing
runner-up does not cause another effort or creator to be substituted.

## Evidence, sources and dates

The comparison keeps source attribution and the refresh/fetch date visible.
**Source dates and provenance** and model Details distinguish the actual UTC
fetch time from retained publication, observation or snapshot dates. Artificial
Analysis page URLs and dates stay paired; an opened measurement shows its own
page's dates, not the last page's date. Unknown source dates remain unavailable.
Each live launch fetches once; controls reuse that loaded dataset. Restart the
process for a new refresh. There is no cache, automatic refresh or scheduler.

Artificial Analysis, DeepSWE and Terminal-Bench scores, grades and ranks are
separate signals with labelled reference populations and source links; they
are not averaged. Details keeps the selected effort, measured configurations,
objective rationale, available catalog context/modalities, source disagreement
and scoped Intelligence alternatives visible. **Benchmark task cost** means
matching Intelligence benchmark USD per task, not token list prices or another
benchmark's run expenditure. **Capability per dollar** uses that matching
Intelligence score/cost basis only. Input/output token prices have separate
USD-per-million-token units.
Raw scores with no measured effort remain visible, but their capability grades,
ranks and disagreement are unavailable. Published confidence intervals remain
distinct from Terminal-Bench's published accuracy standard error; a standard
error is not labelled as a confidence interval.

**Time to first answer token, including thinking** (seconds), **Output tokens per
second**, **Time to first token**, and **Estimated response time for 500 answer
tokens** are distinct published measures. Missing timing is unavailable, not
reconstructed; none selects an effort, filters models or breaks ties. Coding
is not measured review accuracy; Agentic is not verified coordination quality.
The complete Coding/Agentic formulas remain unresolved in the
[dated metric findings](https://github.com/azarakovskiy/llm-ratings/blob/0c26a6174644ef292b616bf704bf2c72a4043b79/.scratch/llm-ratings/assets/32-aa-role-metric-bases.md).

OpenRouter catalog context and modalities are best-effort enrichment. Missing
catalog evidence does not mean zero context or missing model capability.
OpenRouter 30-day token share is display-only and currently **Unavailable**:
retained evidence does not verify the needed access, 30-day coverage and
aggregation denominator. It is not zero, a market-absence claim or a ranking
input.

## Local scope and failures

The server binds only `127.0.0.1` and serves one in-memory session. Browser tabs
using that process share its choices; it is not a hosted or multi-user service.
Credentials and raw source payloads stay on the server. Controls do not write
configuration, saved preferences or harness exports. A restart starts a new
session.

A missing API key, malformed role file, or required Artificial Analysis,
DeepSWE or Terminal-Bench source failure stops startup with a named error and
no partial advice or serving URL. The key is required even for fixtures; use
`dummy` there. An unknown `--role` is a usage error (exit status 2). Missing or
malformed OpenRouter enrichment does not fail the comparison. Missing optional
metrics remain unavailable; missing required measurements produce explicit
unranked/ineligible reasons rather than invented values.

## Batch output and development checks

Without `--web`, module invocation prints a noninteractive advice table and
exits, **even when both streams are terminals**. It does not source `.env`:

```sh
LLM_RATINGS_AA_API_KEY=dummy python3 -m llmratings --fixtures .scratch/llm-ratings/fixtures/main --role Explorer
```

Omit `--fixtures` for a live batch refresh with your real exported key.
Use `python3 -m llmratings --help` for arguments. Development checks are
`make test` (unittest discovery) and `make lint` (Ruff if installed, otherwise a
Python syntax check).
