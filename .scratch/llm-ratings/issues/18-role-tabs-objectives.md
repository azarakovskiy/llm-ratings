# 18 Role tabs: configurable roles with per-role objectives

Type: task
Status: resolved
Blocked by: none

## What to build

Reshape the five fixed categories (Chores/Everyday/Deliberate/Deep/Best
Value) into configurable **role tabs** — the user's goal: "easily choose the
best quality-to-price model for each auxiliary and agentic task." Roles are
stereotypes of agent tasks (Researcher, Coder, Orchestrator, Generic,
Chores). Each role defines an **objective** that selects each model's best
reasoning effort; the `e` effort override is deleted and replaced by an
`o` objective override. Table structure (★ frontier / ✗ dominated, ΔAA/Δ$,
path line) is kept; the detail view gains an alternatives list and an
OpenRouter-sourced context field. Grilling session verdict, user-confirmed
2026-08-08; spec §2/§4/§6/§7 amended; ADR 0002; CONTEXT.md already updated.

## Decisions (user-confirmed, binding)

1. **Roles replace categories.** Five default roles: Chores, Generic,
   Researcher, Coder, Orchestrator. Defined in a checked-in
   `llmratings/roles.json` (same pattern as `aliases.json`); tab order =
   file order; users add roles by editing the file. No config surface
   beyond this one file.
2. **Role schema** — `name`, `description` (what the role does),
   `capacity` (what to look for: reasoning, speed, size, context — prose;
   must include speed guidance per role), `objective` (`cap` | `ppi` |
   `price`), `floor` (AA grade, default 2, active only under the `price`
   lens).
3. **Objectives** — `cap`: highest AA index over the model's
   configurations, lower price on tie. `ppi`: highest price-per-intelligence,
   higher AA on tie. `price`: cheapest configuration above the floor;
   higher AA, then higher speed tier, on tie. Each model enters the table
   at its objective-selected configuration — one row per model, per-row
   Effort column. A model with no configuration above the floor does not
   appear under the `price` lens.
4. **Default objectives** — Chores→`price`, Generic→`ppi`, Researcher→`cap`,
   Coder→`cap`, Orchestrator→`ppi`.
5. **`o` override** — cycles `cap` → `ppi` → `price` → role default; resets
   on role switch. **`e` effort override is deleted** (keymap, Session
   state, footer, tests).
6. **Table structure kept** — ★ frontier / ✗ dominated sections, frontier
   path line, ΔAA/Δ$ vs row above, per-row Effort, `f` capability filter
   unchanged. Sort within sections by the active objective's value.
   Frontier/dominated definitions unchanged (AA vs $/task over every
   model × effort, AA-only).
7. **Alternatives in the detail view** — up to three configurations with
   price < row's price and AA index ≥ row's AA − 5, sorted by price; each
   row shows model, effort, price, ΔAA vs the opened row. Band is one
   constant.
8. **OpenRouter enrichment** — fetch `GET /api/v1/models` per run,
   **best-effort** (on failure the run proceeds without the context field;
   does NOT join the hard-fail contract of the three rating sources), join
   `context_length` (+ modalities) onto canonical models, show in the
   detail view. No source replaced: OpenRouter has no per-effort scored
   ratings, no per-task cost, speed needs an API key (survey:
   `.scratch/llm-ratings/assets/05-openrouter-source-survey.md`).
9. **CLI** — `--category` → `--role <name>`; number keys 1..N follow role
   order; unknown name → exit 2. Batch mode renders the role's default
   lens. Tab header shows role description + capacity guidance + active
   objective (+ floor under the price lens).

## Acceptance criteria

- [ ] `make test` green: objective-driven per-model effort selection;
      `o` cycle + reset on role switch; `e` gone; floor behaviour under the
      price lens (model below floor absent); alternatives band (≤3, price-
      sorted, ΔAA shown); roles.json drives tabs (adding a role to the file
      creates the tab); `--role` + unknown-name exit 2; OpenRouter context
      field in the detail view; OR fetch failure degrades gracefully
- [ ] Role descriptions render in the tab header with capacity guidance
      incl. speed
- [ ] Spec §2/§4/§6/§7 amended and consistent; ADR 0002 written;
      CONTEXT.md reflects role/objective/alternative
- [ ] OpenRouter fixture in the test seam (saved `GET /models` subset)

## Notes

- The 09/12/14 machinery is untouched in spirit: frontier, domination
  arrows, tiers, PPI all keep their contracts; only the row set (per-model
  best configuration under the active objective) and the sort change.
- Tab order default: Chores, Generic, Researcher, Coder, Orchestrator
  (cheap → capable; file order is authoritative).
- Keymap after the change: ←/→ or 1–N role · ↑/↓ move · `f` filter · `o`
  objective · Enter detail · Esc/q quit · Ctrl-C.
- Effort values per model come from the objective search; the per-row
  Effort column (already shipped) is what makes the mixed-effort table
  legible — keep it.
- Alternatives replace none of the dominated-arrow machinery; they are a
  detail-view block only.

## Comments

2026-10-28 tracker recovery: `Status` is aligned with the map's historical shipped record (`c21e146`). This is a metadata repair, not a new implementation or verification run. The role catalog has since been reopened in [Choose human-readable cross-harness role stereotypes](28-name-human-readable-roles.md).
