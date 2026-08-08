# Roles replace categories

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
