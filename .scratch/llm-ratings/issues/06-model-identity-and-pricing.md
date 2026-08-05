# 06 Model identity & pricing

Type: grilling
Blocked by: 05
Status: resolved

## Question

How is a model identified and joined across sources — canonical name ↔ provider ↔ ratings rows? Whose price data counts when a model is sold by multiple providers (e.g. OpenRouter vs direct), and which providers are in scope? Which models appear in the tables (all with price and at least one rating? open and closed both?).

## Answer

Grilled 2026-08-05, four decisions:

**1. Identity — AA-anchored.** Canonical identity = an Artificial Analysis row: stable UUID as key, AA `name` as display name, AA `creator` as provider. DeepSWE/TB model strings map onto AA rows via a small checked-in alias table (normalized source string → AA slug; ~25–30 models at PoC scale, seeded once). Models with no AA row keep a source-only identity — no price, and effectively absent from tables (see 3). Rationale: AA's UUIDs are the only stable identifiers any source offers, and AA is already the price/speed anchor (decision 05).

**2. Price — AA list price only; relative signal.** The price column is AA's list price per (model × effort variant) — AA prices per-effort variants separately, and the anchor example compares at specific efforts. Exact USD shown when present. The cheap/expensive signal is five relative price tiers (1 = cheapest … 5 = most expensive), computed from the priced set per refresh; binning method lands in 08. DeepSWE/TB cost fields are excluded — benchmark-run expenditure on a different basis (Datacurve's Modal cost, per-run cost), never mixed into the price column. Provider-level pricing (OpenRouter vs direct) is out of scope: AA free tier has none, and adding a provider-pricing source would redraw the decision-05 source set. Provider (AA creator) is display/grouping only.

**3. Inclusion — benchmark curation is the usage proxy.** A model appears iff it has ≥1 rating row from a chosen source (DeepSWE or TB v2.1). Their maintainers only run models the market actually uses — that curation is the "not minor players" filter, and it's why DeepSeek/Kimi sit beside frontier models. No numeric rating floor: low ratings rank low, and value math already rules out bad price-to-quality. Not frontier-only; open- and closed-weight both, no license filter. AA's ~591-model tail never enters tables. A rated model missing from AA (rare) shows price n/a and is skipped by price tiers.

**4. Join shape — attach all rows, collapse TB on display.** The identity layer attaches every rating row (source, effort, score, CI, agent) to the canonical model — nothing discarded, 07/08/09 stay free. Tables display one rating per (model × source × effort): TB collapses its agent×model rows to the best-scoring agent per (model × effort), tie-broken by recency; DeepSWE (single harness) and AA (model-level rows) need no collapse.

**Data-model facts for 10:** alias table is a repo file; AA stable `id` is the join key; rating rows carry (source, effort, score, CI, agent where TB); price rows carry AA list in/out USD per effort variant.
