# 09 Ranking & output

Type: grilling
Blocked by: 06, 07, 08
Status: resolved

## Question

What do the per-category tables show — columns (model, provider, rating, price, price-per-intelligence, tier?) and sort order — and how fresh are they? Freshness options: fetch-on-run with a small cache (the charting lean), manual refresh into a snapshot, or scheduled refresh.

## Answer

Grilled 2026-08-05 (two sessions). The chart experiment is dead — the user rejected it ("the chart looks absolutely terrible… the table should be structured to communicate such data"); the frontier/dominated/near-tie message is structural to the table itself. Seven decisions:

**1. Table structure — frontier sections.** Per category, at the category's effort (08): a `★ frontier` section (configurations nothing beats on rating AND price) then a `✗ dominated` section, every dominated row annotated with its best replacement (`→ Sol medium: same rating, save $0.33`). A frontier-path line up top carries the cross-effort story (Flash low → … → Opus 5). Supersedes the league-band grouping of shape D. Sort within each section follows the category's league axis (Chores→cheapest first, Deliberate/Deep→capability grade/AA desc, Everyday/Best Value→PPI desc) so the Δ columns read the ladder.

**2. Interactive TUI contract.** Category nav ←/→ or 1–5; ↑/↓ move; `f` capability filter (all → cap=5 → cap≥4); `e` effort override cycle low→medium→high→xhigh→max→default, **resets on category switch**; Enter drill-down ("why this rating / why this band"); Esc back; q quit. Capability banding key = AA grade; axis mapping + category default efforts per the session log (Chores→low/price, Everyday→medium/value, Deliberate→high/capability, Deep→max/capability, Best Value→high/value).

**3. Frontier = AA vs $/task, AA-only.** A configuration is on the frontier when no other (model × effort) configuration has ≥ AA index at ≤ per-task cost (one side strict). One intelligence axis — mixing sources into the envelope would let a model win on a metric it only leads on by noise. Per-source grades (DSW/AA/TB) stay visible as columns; a model can dominate on AA yet lose on TB, and the columns show it.

**4. Domination advice.** Best strict replacement per dominated row: same-effort first (advice stays in the table's frame), cross-effort fallback (surfaces Sol max → Sol medium: same rating, save $0.33); max AA gain, tie-break max saving. The arrows land on frontier rows — "pick the * instead".

**5. Near-ties — Δ columns.** `ΔAA` / `Δ$` vs the row above within the section make closeness numeric: Luna 0.5 pts from Kimi, Sonnet ties Luna at +$1.06, Opus 1.0 pt / $0.75 over Sol. Near-ties read off the ladder; no closeness threshold or marker needed.

**6. Price basis = per-task cost.** The table's price number is AA per-task cost of the effort variant — PPI denominator, frontier x, Δ base, price-tier input, one consistent basis. AA list price per effort variant appears in the Enter detail view. Refines 06's "price = AA list price" wording. TB column: per-source grade alongside DSW/AA (`—` where TB v2.1 has no row for the effort — Chores/Everyday); best-agent-per-(model×effort) collapse per 06; TB run costs stay out of pricing.

**7. Freshness — fetch on every run.** No cache, no snapshot, no daemon (05's stance; AA free tier 100 req/day is ample at a few runs/day; ratings move weekly and models enter/leave). `--snapshot` noted as a possible later add if quota ever bites.

Columns: DSW | AA | TB | Model | Effort | Provider | $/task | ΔAA | Δ$ | PPI | Spd | `*`. Detail view: per-source raw grades + ranks, PPI division, list price, price tier, speed, frontier/dominated status, source-disagreement flag. Prototype: .scratch/llm-ratings/table-prototype.py (seeded fake data; the verdicts above are the answer).

## Comments

2026-08-05 — Session state: table shape D (league bands + advice columns) and the interactive-TUI contract (category nav, cap filter, effort override, Enter detail / Esc back) locked with the user. Chart experiment rejected by the user ("chart looks terrible; the table should be structured to communicate such data") — next session redesigns the table to surface frontier/dominated/near-tie info. Prototype: .scratch/llm-ratings/table-prototype.py. Full handoff: $TMPDIR/llm-ratings-09-handoff.md. Answer not yet recorded; freshness decision still open.

2026-08-05 — Chart removed; frontier/dominated/near-tie moved into the table. User picked the sections layout (V2): ★ frontier section (rows nothing beats on rating AND price, AA vs $/task over all model×effort) then ✗ dominated section, every dominated row annotated with its best replacement ("→ X: +N pts, save $Y"; same-effort first, cross-effort fallback surfaces Sol max → Sol medium). Frontier path line up top carries the cross-effort story. ΔAA/Δ$ columns vs the row above carry near-ties (Luna 0.5 from Kimi; Sonnet ties Luna at +$1.06). User: "I need effort next to model names" — per-row Effort column added; bands layout deleted (prototype is sections-only now).

2026-08-05 — Price basis: $/task (AA per-task cost) in the table — it's the PPI denominator, the frontier x, and the Δ$ base, one consistent number. List price per effort variant moves to the Enter detail view. Price tier (1–5) bins on per-task cost; refines 06's "list price" wording (09's answer will note it).

2026-08-05 — TB grade column returns in the spec (DSW | AA | TB, per-source grades per 08; "—" where TB v2.1 has no row for the effort — Chores/Everyday; best-agent-per-(model×effort) collapse per 06; TB run costs stay out of pricing). Frontier/domination stays AA-based (one intelligence axis; per-source grades stay visible in the columns).

2026-08-05 — Freshness: fetch on every run (05). AA free tier 100 req/day is ample at a few runs/day; ratings move weekly and models enter/leave, so snapshots go stale and a scheduler is a daemon the CLI doesn't need. No cache, no snapshot, no daemon in the PoC; `--snapshot` noted as a possible later add if quota ever bites.
