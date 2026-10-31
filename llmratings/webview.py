"""Escaped HTML over the shared Session result; no selection policy lives here."""

from html import escape
from urllib.parse import quote, urlsplit

from . import evidence, render


def text(value):
    return escape(str(value), quote=True)


def number(value, places=3, signed=False):
    if value is None:
        return '<span class="unavailable" aria-label="Unavailable" title="Unavailable">—</span>'
    body = f"{value:+,.{places}f}" if signed else f"{value:,.{places}f}"
    body = body.rstrip("0").rstrip(".") if "." in body else body
    if value and float(body.replace(",", "")) == 0:
        body = f"{value:+.3g}" if signed else f"{value:.3g}"
    return text(body)


def money(value, signed=False):
    if value is None:
        return number(None)
    sign = "−" if value < 0 else "+" if signed else ""
    return sign + "$" + number(abs(value), places=6)


def link(url, label):
    parsed = urlsplit(url or "")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return text(label)
    return f'<a href="{text(url)}" rel="noreferrer">{text(label)}</a>'


def action(name, value, label, ident, active=None, style=""):
    pressed = "" if active is None else f' aria-pressed="{str(active).lower()}"'
    return (f'<form method="post" action="/" class="action-form {style}">'
            f'<input type="hidden" name="action" value="{text(name)}">'
            f'<button id="{text(ident)}" name="value" value="{text(value)}"'
            f'{pressed}>{text(label)}</button></form>')


def chooser(name, label, options, selected):
    choices = "".join(
        f'<option value="{text(value)}"'
        f'{" selected" if value == selected else ""}>{text(title)}</option>'
        for value, title in options)
    return (f'<form method="post" action="/" class="choice-form">'
            f'<input type="hidden" name="action" value="{name}">'
            f'<label for="{name}">{text(label)}</label>'
            f'<select id="{name}" name="value">{choices}</select>'
            f'<button class="apply" type="submit">Apply {text(label.lower())}</button>'
            '</form>')


def provenance(ds, ident="source-provenance"):
    info = ds.provenance
    sources = info.get("sources", {})
    aa = sources.get("aa", {})
    urls = aa.get("urls", [])
    attribution = link(urls[0] if urls else "https://artificialanalysis.ai",
                       "Artificial Analysis")
    fetched = info.get("fetched_at")
    fetched = (f'<time datetime="{text(fetched)}">{text(fetched)}</time>'
               if fetched else "Unavailable")
    content = (f'<div class="provenance"><p>Ratings and matching Intelligence task costs: '
               f'{attribution}. Refresh fetched: {fetched}.</p>')
    if info.get("mode") == "fixture":
        snapshots = sorted({s["snapshot_date"] for s in sources.values()
                            if s.get("snapshot_date")})
        history = ", ".join(snapshots) if snapshots else "Unavailable"
        content += (f'<p class="fixture-notice"><strong>Offline snapshot — not live market '
                    f'advice.</strong> Recorded source snapshot: {text(history)}. '
                    'Curated data includes fictional model names; Terminal-Bench and '
                    'OpenRouter data may be synthetic. Missing creators are not coverage '
                    'claims. Reading this snapshot does not update its measurements.</p>')
    else:
        content += '<p>Fetch time is not the publication date of each measurement.</p>'
    source_items = []
    names = {"aa": "Artificial Analysis", "deepswe": "DeepSWE",
             "tb": "Terminal-Bench", "or": "OpenRouter"}
    for key, label in names.items():
        source = sources.get(key, {})
        source_urls = source.get("urls", [])
        source_link = link(source_urls[0], label) if source_urls else text(label)
        snapshot = source.get("snapshot_date") or "Unavailable"
        synthetic = source.get("synthetic")
        synthetic_note = (" Synthetic fixture evidence." if synthetic is True else
                          " Synthetic status unavailable." if synthetic is None else "")
        dates = "; ".join(f"{k}: {v}" for k, v in
                          source.get("source_dates", {}).items())
        date_note = f" Published evidence: {text(dates)}." if dates else ""
        source_items.append(f'<li>{source_link}: source snapshot {text(snapshot)}.'
                            f'{synthetic_note}{date_note}</li>')
    return (content + f'<details class="source-dates" id="{text(ident)}">'
            '<summary>Source dates and provenance</summary><ul>'
            + "".join(source_items) + '</ul></details></div>')


def navigation(result):
    provider = result["provider"]
    buttons = action("provider", "", "All providers", "provider-all", provider is None)
    buttons += "".join(action("provider", name, name, f"provider-{i}", provider == name)
                       for i, name in enumerate(result["shortcuts"]))
    names = sorted(set(result["creators"]) | set(result["shortcuts"]), key=str.casefold)
    full = chooser("provider", "Full creator chooser",
                   [("", "All providers"), *((name, name) for name in names)],
                   provider or "")
    return ('<aside class="creator-nav" aria-labelledby="creator-title">'
            '<h2 id="creator-title">Model creator</h2><nav aria-label="Creator shortcuts">'
            + buttons + '</nav>' + full +
            '<p class="secondary">A provider is the model creator, not an API gateway.</p>'
            '</aside>')


def controls(session, result):
    role = result["role"]
    role_control = chooser("role", "Role", [(r["name"], r["name"]) for r in session.roles],
                           role["name"])
    objective = chooser("objective", "Objective", list(render.OBJECTIVE_LABEL.items()),
                        result["objective"])
    capability = chooser("capability", "Selected-index capability filter",
                         [("", "All capability grades"), ("5", "Grade 5"),
                          ("4", "Grade 4 and above")],
                         "" if result["min_grade"] is None else str(result["min_grade"]))
    default = render.OBJECTIVE_LABEL[role["objective"]]
    override = result["objective_override"] is not None
    default_text = " (override active)" if override else " (in use)"
    return ('<div class="controls">' + role_control + objective + capability + '</div>'
            f'<p class="role-purpose">{text(role["description"])} '
            f'<strong>{render.INDEX_LABEL[result["index"]]} index</strong></p>'
            '<div class="role-support">'
            f'<span class="secondary">Role default: {text(default)}{default_text}</span>'
            + action("recover", "role_default", "Use role default", "role-default", style="quiet")
            + '</div>')


def recoveries(result):
    return '<div class="recoveries">' + "".join(
        action("recover", recovery["action"], recovery["label"],
               "recover-" + recovery["action"])
        for recovery in result["recovery_actions"]
        if recovery["action"] != "role_default") + '</div>'


def model_cell(row):
    return (f'<strong>{text(row["model"])}</strong>'
            f'<span class="secondary block">{text(row["provider"])}</span>')


def score_cell(row):
    return (f'<strong class="score">{number(row["score"])}</strong>'
            f'<span class="secondary block">Grade {row["grade"]} of 5</span>')


def replacement(ds, row):
    if row["dom"] is None:
        return '<span class="secondary">No strict replacement</span>'
    gain, saved, key, effort, _, _ = row["dom"]
    return (f'<strong>{text(ds.models[key].name)}</strong> '
            f'{render.EFFORT_LABEL[effort]}<span class="secondary block">'
            f'Score gain {number(gain, signed=True)}; task cost saving {money(saved)}</span>')


def model_ident(row):
    return quote(row["key"], safe="")


def details_button(result, row):
    ident = model_ident(row)
    expanded = bool(result.get("details") and result["details"]["key"] == row["key"])
    command, value = ("close_details", "") if expanded else ("details", row["key"])
    return (f'<form method="post" action="/" class="action-form details-action">'
            f'<input type="hidden" name="action" value="{command}">'
            f'<button id="details-{ident}" name="value" value="{text(value)}" '
            f'aria-label="Details for {text(row["model"])}" '
            f'aria-expanded="{str(expanded).lower()}" aria-controls="evidence-{ident}">'
            'Details</button></form>')


def source_evidence(model, configurations):
    rows, disagreements = [], []
    for config in configurations:
        effort = render.EFFORT_LABEL.get(config["effort"], "Unmeasured effort")
        for source in config["sources"]:
            rating = source["rating"]
            context = source["population_label"]
            rank = (f'{source["rank"]} of {source["population_size"]}'
                    if source["rank"] is not None else number(None))
            raw = number(source["score"])
            if rating and rating.ci_lo is not None and rating.ci_hi is not None:
                raw += (f'<span class="secondary block">Published interval '
                        f'{number(rating.ci_lo)} to {number(rating.ci_hi)}</span>')
            url = source["source_url"]
            attribution = link(url, f'{source["name"]} evidence for {model}, {effort}')
            if rating and rating.date:
                attribution += f'<span class="secondary block">Observation date: {text(rating.date)}</span>'
            if rating and rating.agent:
                attribution += f'<span class="secondary block">Agent: {text(rating.agent)}</span>'
            if rating and rating.intelligence_index_version is not None:
                attribution += ('<span class="secondary block">Reported Intelligence Index version: '
                                f'{text(rating.intelligence_index_version)}</span>')
            missing = (f'<span class="secondary block">{text(source["reason"])}</span>'
                       if source["reason"] else "")
            rows.append(f'<tr><th scope="row">{text(source["name"])} '
                        f'<span class="secondary block">{text(source["index"])}</span></th>'
                        f'<td>{text(effort)}</td><td class="numeric">{raw}{missing}</td>'
                        f'<td class="numeric">{number(source["grade"])}</td>'
                        f'<td class="numeric">{rank}</td><td>{text(context)}</td>'
                        f'<td>{attribution}</td></tr>')
        if config["disagreement"]:
            grades = "; ".join(
                f'{s["name"]} {s["index"]} grade {s["grade"]}'
                for s in config["disagreement"])
            disagreements.append(
                f'<p class="disagreement"><strong>Sources disagree at {text(effort)} effort: '
                f'{text(grades)}.</strong> At least two available grades differ by two or more. '
                'These are different benchmark signals and reference populations, not '
                'same-index estimates to average or proof of contradictory role performance.</p>')
    return ('<div class="comparison-scroll" role="region" '
            f'aria-label="Independent source scores, grades and ranks for {text(model)}" tabindex="0">'
            '<table class="source-evidence-table"><caption class="sr-only">Independent source evidence</caption>'
            '<thead><tr><th scope="col">Source / index</th><th scope="col">Reasoning effort</th>'
            '<th scope="col">Published score</th><th scope="col">Capability grade</th>'
            '<th scope="col">Rank</th><th scope="col">Reference population</th>'
            '<th scope="col">Source and observation</th></tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div>' + "".join(disagreements))


def configuration_evidence(item):
    rows, metrics = [], []
    for config in item["configurations"]:
        rating = config["configuration"]
        effort = render.EFFORT_LABEL.get(config["effort"], "Unmeasured effort")
        selected = "Objective-selected" if config["selected"] else (
            "Measured; not selected" if rating else "No Artificial Analysis configuration")
        reason = config["eligibility_reason"]
        rows.append(f'<tr><th scope="row">{text(effort)}</th><td>{selected}'
                    + (f'<span class="secondary block">{text(reason)}</span>' if reason else "")
                    + '</td>' + "".join(
                        f'<td class="numeric">{number(getattr(rating, field) if rating else None)}</td>'
                        for field in ("score", "coding_score", "agentic_score"))
                    + f'<td class="numeric">{money(rating.cost if rating else None)}</td></tr>')
        if rating:
            metrics.append(f'<tr><th scope="row">{text(effort)}</th>' + "".join(
                f'<td class="numeric">{number(getattr(rating, field))}</td>'
                for field in ("first_answer_seconds", "speed", "first_token_seconds",
                              "response_500_tokens_seconds")) + "".join(
                f'<td class="numeric">{money(rating.pricing.get(field))}</td>'
                for field in ("price_1m_input_tokens", "price_1m_output_tokens",
                              "price_1m_cache_hit_tokens", "price_1m_cache_write_tokens"))
                + '</tr>')
    cost = ("Benchmark task cost" if item["index"] == "intelligence" else
            "Intelligence benchmark task cost (separate workload context)")
    content = ('<h4>Measured configurations</h4><p>Only retained measured efforts are listed. '
               'Reading another configuration does not change the recommendation.</p>'
               '<div class="comparison-scroll" role="region" '
               f'aria-label="Measured configurations for {text(item["model"])}" tabindex="0">'
               '<table class="configuration-table"><thead><tr><th scope="col">Reasoning effort</th>'
               '<th scope="col">Selection / eligibility</th><th scope="col">Intelligence score</th>'
               '<th scope="col">Coding score</th><th scope="col">Agentic score</th>'
               f'<th scope="col">{cost}<span class="secondary block">USD per Intelligence benchmark task</span>'
               '</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table></div>')
    if metrics:
        content += ('<h4>Published timing and token list prices</h4>'
                    '<p>Timing is explanatory only, never an eligibility, effort, ordering or tie-break rule. '
                    'The 500-answer-token response time is a published estimate, not measured whole-agent '
                    'duration. Token list prices are not benchmark task cost or benchmark-run expenditure.</p>'
                    '<div class="comparison-scroll" role="region" '
                    f'aria-label="Published timing and token list prices for {text(item["model"])}" tabindex="0">'
                    '<table class="timing-price-table"><thead><tr><th scope="col">Reasoning effort</th>'
                    '<th scope="col">Time to first answer token, including thinking'
                    '<span class="secondary block">seconds</span></th>'
                    '<th scope="col">Output tokens per second</th>'
                    '<th scope="col">Time to first token<span class="secondary block">seconds</span></th>'
                    '<th scope="col">Estimated response time for 500 answer tokens'
                    '<span class="secondary block">seconds</span></th>'
                    '<th scope="col">Input token list price'
                    '<span class="secondary block">USD per million input tokens</span></th>'
                    '<th scope="col">Output token list price'
                    '<span class="secondary block">USD per million output tokens</span></th>'
                    '<th scope="col">Cache-read token list price'
                    '<span class="secondary block">USD per million cache-read tokens</span></th>'
                    '<th scope="col">Cache-write token list price'
                    '<span class="secondary block">USD per million cache-write tokens</span></th>'
                    '</tr></thead><tbody>' + "".join(metrics) + '</tbody></table></div>')
    else:
        content += '<p>Published timing and token list prices: —. No measured Artificial Analysis configuration.</p>'
    return content


def intelligence_evidence(ds, result, row):
    label = render.INDEX_LABEL[result["index"]]
    if result["index"] != "intelligence":
        return ('<h4>Cost-based advice</h4><p class="unavailable">Cost-based frontier, replacement, '
                'Best value, Lowest qualifying price and cheaper alternatives: Unavailable — '
                f'no matching {label} benchmark task cost is established. Intelligence costs and '
                'token list prices are separate context, not value evidence for this index. '
                'The separate Coding Agent Index is not a substitute.</p>')
    content = ('<h4>Intelligence comparisons</h4>'
               f'<p><strong>{text(result["advisory_scope"]["label"])}</strong>. '
               'All included valid Intelligence configurations across measured efforts, independent '
               'of the capability display filter and Lowest qualifying price floor.</p>')
    if row["configuration"] is None:
        return content + '<p>Unavailable — no objective-selected scored/priced Intelligence configuration.</p>'
    content += ('<p><strong>Benchmark task cost:</strong> ' + money(row["cost"])
                + f' USD per Intelligence benchmark task. Price tier {number(row["price_tier"])} '
                '(1 is cheapest). <strong>Capability per dollar:</strong> ' + number(row["ppi"], places=3))
    if row["ppi"] is not None:
        content += f' = {number(row["score"])} Intelligence points ÷ {money(row["cost"])} matching task cost'
    else:
        content += ' — requires a finite Intelligence score and positive matching task cost'
    content += (f'. Value grade {number(row["value"])}. This is Intelligence points per '
                'benchmark-task USD, not predicted production-task return.</p>')
    if row["frontier"]:
        content += '<p><strong>Frontier:</strong> no strict Intelligence score/task-cost improvement in this scope.</p>'
    elif row["dom"]:
        content += ('<p><strong>Dominated.</strong> Replacement: ' + replacement(ds, row)
                    + '. Same-effort replacements are preferred; cross-effort fallback is used only '
                    'when none exists, then greatest score gain and task-cost saving.</p>')
    else:
        content += '<p>No strict replacement in this scope.</p>'
    alternatives = row["alternatives"]
    content += ('<h4>Cheaper configurations</h4><p>Up to three strictly cheaper measured configurations '
                'with Intelligence score at least this score minus 5, sorted by matching task cost. '
                'These are not the Provider picks Runner-up rule.</p>')
    if not alternatives:
        return content + '<p>No cheaper configurations within five Intelligence points in this scope.</p>'
    rows = "".join(
        f'<tr><th scope="row">{text(ds.models[key].name)}</th><td>{render.EFFORT_LABEL[effort]}</td>'
        f'<td class="numeric">{money(cost)}</td><td class="numeric">{number(score)}</td>'
        f'<td class="numeric">{number(score - row["score"], signed=True)}</td></tr>'
        for key, effort, cost, score in alternatives)
    return (content + '<div class="comparison-scroll" role="region" '
            f'aria-label="Cheaper Intelligence configurations for {text(row["model"])}" tabindex="0">'
            '<table class="alternatives-table"><thead><tr><th scope="col">Model</th>'
            '<th scope="col">Reasoning effort</th><th scope="col">Benchmark task cost'
            '<span class="secondary block">Intelligence; USD per task</span></th>'
            '<th scope="col">Intelligence score</th><th scope="col">Intelligence score change</th>'
            '</tr></thead><tbody>' + rows + '</tbody></table></div>')


def inline_evidence(session, result, row):
    ident = model_ident(row)
    if not result.get("details") or result["details"]["key"] != row["key"]:
        return f'<section id="evidence-{ident}" class="model-evidence" hidden></section>'
    item = evidence.model_evidence(session.ds, result, row)
    model = session.ds.models[row["key"]]
    selected = item["configuration"]
    selected_effort = (render.EFFORT_LABEL.get(item["effort"], "Unmeasured effort")
                       if selected else "Unranked — no objective-selected configuration")
    content = (f'<section id="evidence-{ident}" class="model-evidence" role="region" '
               f'aria-labelledby="evidence-title-{ident}"><div class="evidence-heading">'
               f'<div><h3 id="evidence-title-{ident}">Evidence for {text(row["model"])}</h3>'
               f'<p>{text(row["provider"])} · {text(selected_effort)}</p></div>'
               '<form method="post" action="/" class="action-form">'
               '<input type="hidden" name="action" value="close_details">'
               f'<button id="close-details-{ident}" name="value" value="" '
               f'data-focus-target="details-{ident}">Close details'
               f'<span class="sr-only"> for {text(row["model"])}</span></button></form></div>'
               f'<p>{text(result["role"]["name"])} · {render.INDEX_LABEL[result["index"]]} index · '
               f'{render.OBJECTIVE_LABEL[result["objective"]]}</p>'
               '<h4>Why this configuration</h4>'
               f'<p>{text(item["rationale"])}</p>')
    if item["reason"]:
        content += f'<p class="unavailable">{text(item["reason"])}</p>'
    content += ('<p class="secondary">— means unavailable: a source, effort or metric was not supplied '
                'or was unusable. No other source, effort or timing measure is substituted.</p>'
                + provenance(session.ds, f"provenance-{ident}") + configuration_evidence(item))
    chosen = [c for c in item["configurations"] if c["selected"]]
    content += '<h4>Independent source scores, grades and ranks</h4>'
    content += source_evidence(row["model"], chosen or item["configurations"])
    if chosen and len(item["configurations"]) > 1:
        content += (f'<details class="configuration-sources" id="all-sources-{ident}">'
                    '<summary>Independent source evidence at other measured efforts</summary>'
                    + source_evidence(row["model"],
                                      [c for c in item["configurations"] if not c["selected"]])
                    + '</details>')
    content += intelligence_evidence(session.ds, result, row)
    catalog_source = session.ds.provenance.get("sources", {}).get("or", {}).get("urls", [])
    catalog_link = link(catalog_source[0] if catalog_source else None, "OpenRouter catalog")
    content += ('<h4>Catalog context and modalities</h4>'
                f'<p>Best-effort enrichment from {catalog_link}. Missing catalog metadata is not '
                'evidence of missing model capability, zero context or a nonexistent creator.</p>'
                f'<dl class="catalog-metadata"><div><dt>Context length</dt><dd>'
                f'{number(model.context_length)} tokens</dd></div>'
                f'<div><dt>Input / output modalities</dt><dd>{text(model.modalities) if model.modalities else number(None)}'
                '</dd></div></dl><h4>OpenRouter 30-day token share</h4>'
                '<p><strong>Unavailable.</strong> Retained evidence does not verify access/payload coverage, '
                'the actual 30-day window, denominator including other, and variant/day aggregation. '
                'Historical top-50 presence remains unverified; missing evidence is not zero or market '
                'absence. Share is display-only, not effort-specific, and never selects, ranks, '
                'filters, breaks ties or grades models.</p>')
    if selected:
        content += (f'<p class="secondary">Output-speed grade: {number(row.get("spd"))}. '
                    'Value, output-speed and price grades keep their independent valid reference '
                    'sets in the unfiltered role-selected model population, before provider and '
                    'capability-display constraints.</p>')
    return content + '</section>'


def evidence_row(session, result, row, columns):
    opened = bool(result.get("details") and result["details"]["key"] == row["key"])
    return (f'<tr class="evidence-row" data-details-for="{text(row["key"])}"'
            f'{"" if opened else " hidden"}><td colspan="{columns}">'
            + inline_evidence(session, result, row) + '</td></tr>')

def model_table(session, result):
    intelligence = result["index"] == "intelligence"
    score_label = render.INDEX_LABEL[result["index"]] + " score"
    headers = ('<th scope="col">Model</th><th scope="col">Reasoning effort</th>'
               f'<th scope="col" class="numeric">{score_label}'
               '<span class="secondary block">Artificial Analysis; capability grade below</span></th>')
    headers += ('<th scope="col" class="numeric">Time to first answer token, including thinking'
                '<span class="secondary block">seconds; published median</span></th>'
                '<th scope="col" class="numeric">Output tokens per second'
                '<span class="secondary block">published median throughput</span></th>')
    if intelligence:
        headers += ('<th scope="col" class="numeric">Benchmark task cost'
                    '<span class="secondary block">Intelligence; USD per task</span></th>'
                    '<th scope="col" class="numeric">Capability per dollar'
                    '<span class="secondary block">Intelligence score ÷ task cost</span></th>'
                    '<th scope="col" class="numeric">Score change</th>'
                    '<th scope="col" class="numeric">Task cost change</th>'
                    '<th scope="col">Replacement</th>')
    bodies = []
    for section_index, section in enumerate(result["sections"]):
        if not section["rows"]:
            continue
        count = len(section["rows"])
        color = "frontier" if intelligence and section_index == 0 else ""
        section_html = (f'<tbody class="{color}"><tr class="section-row">'
                        f'<th scope="colgroup" colspan="{10 if intelligence else 5}">'
                        f'{text(section["label"])} <span class="section-count">'
                        f'{count} model{"s" if count != 1 else ""}</span></th></tr>')
        for row in section["rows"]:
            section_html += (f'<tr data-model="{text(row["key"])}">'
                             f'<th scope="row">{model_cell(row)}{details_button(result, row)}</th>'
                             f'<td>{render.EFFORT_LABEL[row["effort"]]}</td>'
                             f'<td class="numeric">{score_cell(row)}</td>'
                             f'<td class="numeric">{number(row["first_answer_seconds"])}</td>'
                             f'<td class="numeric">{number(row["speed"])}</td>')
            if intelligence:
                score_delta = (number(row["score_change"], signed=True)
                               if row["score_change"] is not None else
                               '<span class="secondary">No previous row</span>')
                cost_delta = (money(row["cost_change"], signed=True)
                              if row["cost_change"] is not None else
                              '<span class="secondary">No previous row</span>')
                section_html += (f'<td class="numeric">{money(row["cost"])}</td>'
                                 f'<td class="numeric">{number(row["ppi"], places=1)}</td>'
                                 f'<td class="numeric" data-score-change>{score_delta}</td>'
                                 f'<td class="numeric" data-cost-change>{cost_delta}</td>'
                                 f'<td class="replacement">{replacement(session.ds, row)}</td>')
            section_html += '</tr>' + evidence_row(session, result, row, 10 if intelligence else 5)
        bodies.append(section_html + '</tbody>')
    return ('<div class="comparison-scroll" role="region" aria-label="Model comparison table" '
            'tabindex="0"><table class="model-table"><caption class="sr-only">'
            f'{score_label}; {text(result["provider_label"])}; '
            f'{text(render.OBJECTIVE_LABEL[result["objective"]])}</caption>'
            f'<thead><tr>{headers}</tr></thead>{"".join(bodies)}</table></div>')


def provider_picks(session, result):
    intelligence = result["index"] == "intelligence"
    score_label = render.INDEX_LABEL[result["index"]] + " score"
    metric = "Capability per dollar" if result["objective"] == "ppi" else "Benchmark task cost"
    metric_note = ("Intelligence score ÷ task cost" if result["objective"] == "ppi" else
                   "Intelligence; USD per task")
    per_pick = 3 if intelligence else 2
    headings = '<th scope="col" rowspan="2">Model creator</th>'
    headings += (f'<th scope="colgroup" colspan="{per_pick}" class="primary">Primary</th>'
                 f'<th scope="colgroup" colspan="{per_pick}">Runner-up</th>')
    columns = (f'<th scope="col">Model / reasoning effort</th>'
               f'<th scope="col" class="numeric">{score_label}'
               '<span class="secondary block">Artificial Analysis; capability grade below</span></th>')
    if intelligence:
        columns += (f'<th scope="col" class="numeric">{metric}'
                    f'<span class="secondary block">{metric_note}</span></th>')
    groups = []
    for i, group in enumerate(result["picks"]):
        row_html = ('<tr><th scope="row">' + action("provider", group["provider"],
                    group["provider"], f"pick-creator-{i}", style="quiet") + '</th>')
        for label in ("primary", "runner_up"):
            row = group[label]
            if row is None:
                row_html += (f'<td colspan="{per_pick}" class="secondary absent-runner">'
                             '<strong>No qualifying runner-up</strong>'
                             '<span class="block">Only one distinct model meets the active constraints.</span></td>')
                continue
            row_html += (f'<td class="{label}" data-pick="{label}" '
                         f'data-model="{text(row["key"])}"><strong>{text(row["model"])}</strong>'
                         f'<span class="secondary block">{render.EFFORT_LABEL[row["effort"]]} '
                         'reasoning effort</span>' + details_button(result, row) + '</td>'
                         f'<td class="numeric">{score_cell(row)}</td>')
            if intelligence:
                value = (number(row["ppi"], places=1) if result["objective"] == "ppi" else
                         money(row["cost"]))
                row_html += f'<td class="numeric">{value}</td>'
        groups.append(row_html + '</tr>' + "".join(
            evidence_row(session, result, row, 1 + per_pick * 2)
            for row in (group["primary"], group["runner_up"]) if row))
    return ('<div class="comparison-scroll" role="region" aria-label="Provider picks comparison" '
            'tabindex="0"><table class="picks-table"><caption class="sr-only">'
            f'Primary and Runner-up by creator; {score_label}</caption><thead>'
            f'<tr>{headings}</tr><tr>{columns}{columns}</tr></thead>'
            f'<tbody>{"".join(groups)}</tbody></table></div>'
            '<p class="comparison-note">Picks use direct objective order within each creator. '
            'Primary does not mean global frontier membership; Runner-up is another model, '
            'not another effort or a specially chosen cheap alternative.</p>')


def frontier_path(session, result):
    if result["index"] != "intelligence" or result["status"] == "unavailable_objective":
        return ""
    path = []
    for key, effort, cost, score in result["frontier_path"]:
        path.append(f'<li><strong>{text(session.ds.models[key].name)}</strong> '
                    f'{render.EFFORT_LABEL[effort]}: Intelligence score {number(score)}, '
                    f'task cost {money(cost)}</li>')
    return ('<details class="secondary-disclosure" id="frontier-path"><summary>Intelligence frontier path '
            f'— {text(result["advisory_scope"]["label"])}</summary>'
            '<p>All valid scored/priced configurations of included models in this scope, '
            'across measured efforts. Capability display filters and the role price floor '
            'do not remove comparison points. Replacements prefer the same effort, '
            'then the greatest score gain and task cost saving.</p><ol class="frontier-path">'
            + ("".join(path) or '<li>No valid comparison points.</li>') + '</ol></details>')


def source_ratings(result):
    rows = result["rows"]
    if not rows:
        return ""
    label = render.INDEX_LABEL[result["index"]]
    body = []
    for row in rows:
        cells = (f'<th scope="row">{text(row["model"])}</th>'
                 f'<td>{render.EFFORT_LABEL[row["effort"]]}</td>'
                 f'<td class="numeric">{number(row["score"])} / grade {row["grade"]}</td>')
        for source, grade in (("deepswe", "dsw"), ("tb", "tb")):
            rating = row["ratings"][source]
            value = number(rating.score if rating else None)
            grade_value = number(row[grade])
            cells += f'<td class="numeric">{value}<span class="secondary block">Grade {grade_value}</span></td>'
        body.append('<tr>' + cells + '</tr>')
    return ('<details class="secondary-disclosure" id="independent-sources"><summary>Independent source ratings '
            f'for {len(rows)} selected configurations</summary><p>These are different '
            'benchmark populations, not a blended score. Artificial Analysis grades use '
            f'all scored {label} configurations across efforts in this refresh; DeepSWE '
            'and Terminal-Bench grades use their own rated effort populations. Provider '
            'and display filters do not re-bin grades. Missing source/effort values stay '
            'unavailable.</p><div class="comparison-scroll" role="region" '
            'aria-label="Independent source ratings" tabindex="0"><table>'
            '<thead><tr><th scope="col">Model</th><th scope="col">Reasoning effort</th>'
            f'<th scope="col">Artificial Analysis {label} score / grade</th>'
            '<th scope="col">DeepSWE pass@1 / grade</th>'
            '<th scope="col">Terminal-Bench accuracy / grade</th></tr></thead><tbody>'
            + "".join(body) + '</tbody></table></div></details>')


def excluded_models(session, result):
    rows = result["excluded"]
    if not rows:
        return ""
    label = render.INDEX_LABEL[result["index"]]
    items = "".join(
        f'<li><strong>{text(row["model"])}</strong> ({text(row["provider"])}), '
        f'{render.EFFORT_LABEL[row["effort"]]}: {label} score {number(row["score"])}, '
        f'grade {row["grade"]} of 5. {text(row["reason"])}. '
        f'{"Benchmark task cost " + money(row["cost"]) + ". " if result["index"] == "intelligence" else ""}'
        'This is the objective-selected configuration; the filter does not select a different effort.'
        + details_button(result, row) + inline_evidence(session, result, row) + '</li>'
        for row in rows)
    opened = bool(result.get("details") and any(r["key"] == result["details"]["key"] for r in rows))
    return (f'<details class="secondary-disclosure" id="excluded-models"{" open" if opened else ""}><summary>'
            f'Excluded by capability display filter ({len(rows)}) — '
            f'{text(result["provider_label"])}</summary><ul>{items}</ul></details>')


def unranked_models(session, result):
    rows = result["unranked"]
    if not rows:
        return ""
    items = "".join(f'<li><strong>{text(row["model"])}</strong> '
                    f'({text(row["provider"])}): {text(row["reason"])}.'
                    + details_button(result, row) + inline_evidence(session, result, row)
                    + '</li>' for row in rows)
    opened = bool(result.get("details") and any(r["key"] == result["details"]["key"] for r in rows))
    return (f'<details class="secondary-disclosure" id="unranked-models"{" open" if opened else ""}><summary>'
            f'Unranked included models ({len(rows)})</summary><p>Independent source evidence '
            'is retained, but these models lack a qualifying measured configuration for '
            f'the active objective. They are not recommendations.</p><ul>{items}</ul></details>')


def empty_creators(result):
    groups = result["providers_without_picks"]
    if not groups or result["view"] != "picks" or result["status"] == "unavailable_objective":
        return ""
    items = "".join('<li>' + action("provider", group["provider"], group["provider"],
                    f"empty-creator-{i}", style="quiet") +
                    f'<span>{text(group["reason"])}</span></li>'
                    for i, group in enumerate(groups))
    return ('<details class="secondary-disclosure" id="empty-creators"><summary>'
            f'Creators without qualifying models ({len(groups)})</summary><ul class="creator-reasons">'
            + items + '</ul></details>')


def how_picks_work(session):
    roles = "".join(
        f'<tr><th scope="row">{text(role["name"])}</th>'
        f'<td>{text(role["description"])}<details id="policy-capacity-{quote(role["name"], safe="")}">'
        '<summary>Capacity guidance for '
        f'{text(role["name"])}</summary><p>{text(role["capacity"])}</p></details></td>'
        f'<td>{render.INDEX_LABEL[role["index"]]}</td>'
        f'<td>{render.OBJECTIVE_LABEL[role["objective"]]}</td>'
        f'<td>{role["floor"]}</td></tr>' for role in session.roles)
    findings = link(
        "https://github.com/azarakovskiy/llm-ratings/blob/"
        "0c26a6174644ef292b616bf704bf2c72a4043b79/"
        ".scratch/llm-ratings/assets/32-aa-role-metric-bases.md",
        "Immutable metric findings, researched 2026-10-28")
    return (
        '<details class="secondary-disclosure policy" id="how-picks-work">'
        '<summary>How picks work</summary>'
        '<details id="policy-roles"><summary>Role purposes, indexes and defaults</summary>'
        '<p>These profiles come from the checked-in role file. Roles describe task purpose, '
        'not cheap, fast or thorough modes, a fixed reasoning effort, context needs or vision. '
        'Capacity guidance is separate prose, not a hidden score or filter. The objective '
        'selects one measured effort for each model; implementation specialties stay with '
        'Coder and independent security/second-opinion assessment with Reviewer.</p>'
        '<div class="comparison-scroll" role="region" aria-label="Role purposes and defaults" tabindex="0">'
        '<table><thead><tr><th scope="col">Role</th><th scope="col">Purpose and separate capacity guidance</th>'
        '<th scope="col">Selected index</th><th scope="col">Default objective</th>'
        '<th scope="col">Lowest qualifying price floor</th></tr></thead><tbody>'
        + roles + '</tbody></table></div></details>'
        '<details id="policy-eligibility"><summary>Eligibility, objective order and exact ties</summary>'
        '<p>Inclusion requires at least one DeepSWE or Terminal-Bench rating; Artificial '
        'Analysis-only catalog models do not become candidates. Unmatched independently rated '
        'models stay reachable as source-only evidence. Required values must be finite and '
        'belong to the same measured effort. Missing scores never borrow another index or effort.</p>'
        '<div class="comparison-scroll" role="region" aria-label="Objective eligibility and comparison keys" tabindex="0">'
        '<table><thead><tr><th scope="col">Index / objective</th><th scope="col">Required data</th>'
        '<th scope="col">Comparison keys, in order</th></tr></thead><tbody>'
        '<tr><th scope="row">Intelligence / Highest capability</th>'
        '<td>Intelligence score and finite non-negative matching Intelligence benchmark task cost.</td>'
        '<td>Score descending; matching task cost ascending; lower reasoning effort; canonical model key.</td></tr>'
        '<tr><th scope="row">Intelligence / Best value</th>'
        '<td>Intelligence score, positive matching task cost and a finite score/cost ratio.</td>'
        '<td>Capability per dollar descending; score descending; matching task cost ascending; '
        'lower reasoning effort; canonical model key.</td></tr>'
        '<tr><th scope="row">Intelligence / Lowest qualifying price</th>'
        '<td>Intelligence score and non-negative matching task cost; inclusive capability '
        'grade at least the role floor (2 in the bundled profiles).</td>'
        '<td>Qualifying matching task cost ascending; score descending; lower reasoning '
        'effort; canonical model key.</td></tr>'
        '<tr><th scope="row">Coding or Agentic / Highest capability</th>'
        '<td>Finite score on the selected index. No matching area-index cost is established or required.</td>'
        '<td>Selected score descending; lower reasoning effort; canonical model key.</td></tr>'
        '</tbody></table></div>'
        '<p>The same complete keys first choose an effort within each model, then order '
        'the selected models across creators. Effort ties follow Low, Medium, High, Extra high, '
        'Maximum. The canonical model key is the final tie-break, never fetch order or timing.</p>'
        '<p>Only Lowest qualifying price applies the inclusive role capability floor, including '
        'a manual override. Highest capability and Best value are floor-free. The separate '
        'capability display filter applies after effort selection; it does not choose another '
        'effort to pass. Zero task cost can qualify for Highest capability and Lowest qualifying '
        'price but never creates a finite Best value ratio. Missing or unusable required data '
        'leaves a model unranked with a specific reason.</p>'
        '<p>Intelligence benchmark task cost is not input/output token list price, a manufactured '
        'token mix, whole-suite expenditure or another benchmark run cost. Coding/Agentic '
        'Best value and Lowest qualifying price remain explicitly unavailable; they are not '
        'silently replaced by Intelligence advice.</p></details>'
        '<details id="policy-signals"><summary>Benchmark proxies, grades and reference populations</summary>'
        '<p>Published indexes are task-selection proxies, not verified performance on every '
        'role. Coding is not measured review accuracy; Agentic is not verified multi-agent '
        'coordination quality. The complete current Coding and Agentic composite formulas '
        'remain unresolved in the dated research. The separate Coding Agent Index and its '
        'costs are not the API Coding formula or a matching area-index denominator. '
        + findings + ' records those limits; it did not inspect an authenticated live API response.</p>'
        '<p>Capability grades use distinct finite values, 1–5 with 5 best: equal values '
        'share a grade and are never split. Distinct values are ordered high to low; the '
        'grade is 5 − floor(5 × zero-based position ÷ distinct-value count). Price tiers '
        'order costs low to high and use 1 + floor(5 × position ÷ count). Small sets can '
        'populate fewer than five grades. Ranks use one plus the number of strictly greater scored rows; '
        'equal scores share rank, and the displayed population size counts scored configurations.</p>'
        '<p>Artificial Analysis grades and ranks use all scored configurations for the '
        'selected index across measured efforts in this refresh, including the Artificial '
        'Analysis-only long tail, before eligibility or display constraints. An Intelligence '
        'rank is not a Coding or Agentic rank. DeepSWE uses its own rated effort population. '
        'Terminal-Bench uses its own effort population after collapsing to the best agent '
        'per model; equal agent scores use the newest submission. Independent source scores '
        'are never blended.</p>'
        '<p>Provider selection and capability display filters never re-bin grades. Value '
        'grade uses valid Intelligence score / positive matching task cost, output-speed '
        'grade uses published output tokens per second, and price tier uses matching '
        'Intelligence task cost (1 cheapest). Each keeps its own valid reference set from '
        'the unfiltered role-selected model population on this refresh. No Coding/Agentic '
        'value or price grade is inferred.</p>'
        '<p>Source disagreement is shown only when at least two available source grades '
        'have a maximum-minus-minimum gap of at least 2, naming their source, index and '
        'effort. These are different benchmark signals, not same-index estimates to average '
        'or proof of contradictory role performance. Missing sources cannot create disagreement.</p></details>'
        '<details id="policy-comparisons"><summary>Provider picks, frontier and cheaper configurations</summary>'
        '<p>A provider is the model creator, not an API gateway. Provider picks takes the '
        'first two distinct models in direct objective order after eligibility, effort '
        'selection and the active capability display filter. It does not use the frontier-first '
        'table order, a cheap-diversity heuristic or two efforts of the same model. Primary '
        'means first for that creator, not global frontier membership. Runner-up means '
        'second model, not the cheaper-alternative rule. One qualifying model has no fabricated '
        'runner-up; zero models retains constraints and offers named-only recovery.</p>'
        '<p>Intelligence comparisons span all included valid scored/priced efforts within '
        'the selected creator. All providers restores the global universe. Capability display '
        'filters and the price floor do not discard advisory points. A frontier configuration '
        'has no other configuration with at least its score at at most its task cost and one '
        'strict improvement. Model table lists Frontier before Dominated, with objective '
        'order inside each section. Score and task-cost changes compare the preceding '
        'visible row within that section.</p>'
        '<p>Dominated replacements prefer the same measured effort before cross-effort '
        'fallback, then greatest score gain and task-cost saving. Evidence lists at most '
        'three genuinely cheaper configurations with Intelligence score at least the opened '
        'score minus 5, ordered by matching task cost (then higher score, lower effort and '
        'canonical model key for ties). No replacement or cheaper configuration is invented '
        'when none exists. Coding/Agentic have no cost-based frontier, replacement, value/price '
        'advice or cheaper alternatives.</p></details>'
        '<details id="policy-timing"><summary>Timing, source dates and unavailable enrichment</summary>'
        '<p>Time to first answer token, including thinking is the published median in '
        'seconds from request to the first answer token. Output tokens per second is '
        'separate throughput. Time to first token may stop at a reasoning token. Estimated '
        'response time for 500 answer tokens is a separately published synthetic estimate, '
        'not measured whole-agent duration. The Free route’s exact prompt preset and provider '
        'aggregation are not established, so these are not selected creator endpoint claims.</p>'
        '<p>Timing never changes eligibility, effort, ranking or ties. Missing timing '
        'is —, unavailable; no measure is substituted or reconstructed from throughput. '
        'Linked source URLs and the actual refresh fetch time stay with the comparison '
        'and evidence; source observation/publication and historical snapshot dates are '
        'different. A fixture refresh does not make its old or synthesized rows live measurements. '
        'One launch loads sources once; controls and evidence do not refetch them.</p>'
        '<p>OpenRouter context length and input/output modalities are best-effort catalog '
        'enrichment through retained canonical identity joins. Missing metadata does not '
        'mean zero context, missing model capability or a nonexistent creator. OpenRouter '
        '30-day token share is display-only and not effort-specific. Numeric share requires '
        'verified access/payload coverage, the actual 30-day window, source/date, denominator '
        'including other, and variant/day aggregation. Historical access/coverage and top-50 '
        'presence are unverified source limitations, not permanent product exclusions. Without '
        'sufficient retained evidence, share is Unavailable, never zero or inferred market absence.</p>'
        '<p>Sources: ' + link("https://artificialanalysis.ai", "Artificial Analysis")
        + '; ' + link("https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json", "DeepSWE v1.1")
        + '; ' + link("https://github.com/harbor-framework/terminal-bench-2-1", "Terminal-Bench v2.1")
        + '; ' + link("https://openrouter.ai/api/v1/models", "OpenRouter catalog")
        + '. Actual retained page/submission URLs appear in model evidence.</p></details></details>')


def page(session, result):
    """Render a complete page from one query, preserving its rows and comparisons."""
    role = result["role"]
    label = render.INDEX_LABEL[result["index"]]
    title = ("Models across providers" if result["provider"] is None else
             f'Models from {result["provider"]}')
    tabs = "".join(action("view", value, name, "view-" + value,
                          result["view"] == value) for value, name in render.VIEW_LABEL.items())
    comparison_title = "Model comparison" if result["view"] == "table" else "Primary and Runner-up"
    count = len(result["rows"])
    selected_grade = ("All capability grades" if result["min_grade"] is None else
                      f'Capability grade {result["min_grade"]} and above')
    state = (f'{role["name"]}; {label} index; {render.OBJECTIVE_LABEL[result["objective"]]}; '
             f'{result["provider_label"]}; {selected_grade}; '
             f'{render.VIEW_LABEL[result["view"]]}; {count} ranked models; '
             + (f'Details opened for {result["details"]["model"]}' if result.get("details")
                else 'No model details open'))
    comparison = ""
    if result["status"] != "ok":
        heading = ("Unavailable objective" if result["status"] == "unavailable_objective"
                   else "No qualifying configuration")
        comparison += (f'<section class="state-message" aria-labelledby="state-title">'
                       f'<h3 id="state-title">{heading}</h3><p>{text(result["reason"])}</p>'
                       + recoveries(result) + '</section>')
    elif result["view"] == "table":
        comparison += model_table(session, result)
        if result["index"] == "intelligence":
            comparison += ('<p class="comparison-note">Score change and Task cost change '
                           'compare the preceding visible row in the same section. The first '
                           'row of each section has no previous-row delta. Task costs are '
                           'Intelligence benchmark costs, not token list prices.</p>')
    else:
        comparison += provider_picks(session, result)
    comparison += ('<p class="comparison-note">Missing published timing (—) is unavailable; '
                   'it is not reconstructed and never changes selection or order.</p>'
                   + frontier_path(session, result) + source_ratings(result)
                   + excluded_models(session, result) + unranked_models(session, result)
                   + empty_creators(result) + how_picks_work(session))
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>LLM Ratings — model advice</title><link rel="icon" href="data:,">'
            '<link rel="stylesheet" href="/web.css"><script src="/web.js" defer></script>'
            '</head><body><a class="skip-link" href="#comparison">Skip to comparison</a>'
            '<header class="masthead"><strong>LLM Ratings</strong><span>Model advice</span></header>'
            '<div id="app" class="workspace">' + navigation(result) + '<main>'
            f'<h1>{text(title)}</h1>' + controls(session, result) +
            f'<nav class="view-tabs" aria-label="Comparison view">{tabs}</nav>'
            '<section id="comparison" aria-labelledby="comparison-title">'
            '<div class="comparison-heading"><div>'
            f'<h2 id="comparison-title">{comparison_title}</h2>'
            f'<p class="provider-label">{text(result["provider_label"])}</p>'
            f'<p class="secondary">Advice scope: {text(result["advisory_scope"]["label"])}</p>'
            '</div><p class="result-count">'
            f'<strong>{count} ranked model{"s" if count != 1 else ""}</strong>'
            f'<span class="secondary block">{label} index</span></p></div>'
            + provenance(session.ds) + comparison + '</section></main></div>'
            f'<p id="state-summary" class="sr-only" role="status" aria-live="polite">{text(state)}</p>'
            '<p id="request-error" class="request-error" role="alert" hidden></p>'
            '</body></html>')
