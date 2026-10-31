# Roles replace categories

**Status: partially superseded by the [amended specification](../../.scratch/llm-ratings/spec.md)
and [ticket 38](../../.scratch/llm-ratings/issues/38-inline-evidence-web-cutover.md).**
The former five-role catalog is superseded by Explorer, Researcher, Planner,
Coder, Reviewer, Coordinator, Generalist and Utility in `llmratings/roles.json`.
The historical claim below that the data model and rating machinery are
unchanged is superseded: profiles now choose distinct Intelligence, Coding or
Agentic indexes, with index-specific eligibility, reference populations and
retained provenance. Matching task-cost advice is established for Intelligence
only. The terminal tabs/keymap are superseded by visible web controls; there is
no fixed role effort or parallel terminal UI.

Still valid: checked-in role profiles separate task purpose from capacity
guidance; the active objective selects each model's measured reasoning effort;
a role change resets the objective override; the capability floor applies only
to Lowest qualifying price; Highest capability and Best value remain floor-free;
and Intelligence frontier, replacement and cheaper-alternative advice remains
floor-free (and display-filter-free) within the selected provider scope. See
the [runtime README](../../README.md) for current role defaults and controls.

## Historical decision

The original reasoning and consequences below are retained as history.

Ticket 07 consolidated "OMP's 10 roles + 7 agents" into five abstract
use-case categories — Chores, Everyday, Deliberate, Deep, Best Value —
each fixing one reasoning effort. In practice the abstraction did not
stick: the user asks "what should I run for my researcher / coder /
orchestrator?", not "what fits the Deliberate lens", and the effort is
part of the buy decision (the anchor example: DeepSeek Flash ≈ ChatGPT
Luna 5.6 at high/extra-high, far cheaper — the effort *is* the story, and
a fixed per-category effort hides it behind an override key). The grilling
session (ticket 18) reverses 07: **categories become configurable role
tabs**, each role carrying an **objective** that selects each model's best
reasoning effort, plus an `o` override that cycles the three lenses
(`cap` / `ppi` / `price`-with-floor).

The alternatives were: keep the five categories and add role tabs beside
them (two taxonomies over the same frontier, near-identical rows — the
redundancy we were removing); keep fixed per-role efforts (hides the
per-model effort advice that the anchor example exists to surface); and a
weighted "fit score" per role (arbitrary weights, a new scoring engine,
when three objective lenses over the existing axes — AA index, PPI, price
+ capability floor — express the same choice with zero new math). We picked
the objective model: each role is a profile (description, capacity
guidance, objective, floor) in a checked-in `roles.json`, one row per
model at its objective-selected configuration, ★ frontier / ✗ dominated
structure unchanged.

Consequences: the CLI contract changes — `--category` becomes `--role`,
the `e` effort override is deleted (efforts now come from the objective),
the `o` objective override joins the keymap; the spec's category and
ranking sections are amended; the glossary gains *role*, *objective*,
*alternative*; `roles.json` is the PoC's first user-editable config file.
The rating/pricing/tiering machinery itself is untouched — this is a
reshaping of the top-level navigation and row selection, not of the data
model. The floor is a row-selection rule under the price lens only —
advisory surfaces (the frontier path line, dominated arrows, detail
alternatives) stay floor-free, consistent with the pre-existing arrow
machinery, and the old "no rating floor" inclusion rule is amended
accordingly.
