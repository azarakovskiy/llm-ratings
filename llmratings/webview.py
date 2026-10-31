"""Escaped HTML over the shared Session result; no selection policy lives here."""

from html import escape
from urllib.parse import urlsplit

from . import render


def text(value):
    return escape(str(value), quote=True)


def number(value, places=3, signed=False):
    if value is None:
        return '<span class="unavailable">Unavailable</span>'
    body = f"{value:+,.{places}f}" if signed else f"{value:,.{places}f}"
    body = body.rstrip("0").rstrip(".") if "." in body else body
    if value and float(body.replace(",", "")) == 0:
        body = f"{value:+.3g}" if signed else f"{value:.3g}"
    return text(body)


def money(value, signed=False):
    if value is None:
        return number(None)
    sign = ("−" if value < 0 else "+") if signed else ""
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


def provenance(ds):
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
    return (content + '<details class="source-dates"><summary>Source dates and provenance'
            '</summary><ul>' + "".join(source_items) + '</ul></details></div>')


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
            + '<details><summary>Capacity guidance and index limits</summary>'
            f'<p>{text(role["capacity"])}</p><p>{text(render.INDEX_NOTE[result["index"]])}</p>'
            '</details></div>')


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


def model_table(session, result):
    intelligence = result["index"] == "intelligence"
    score_label = render.INDEX_LABEL[result["index"]] + " score"
    headers = ('<th scope="col">Model</th><th scope="col">Reasoning effort</th>'
               f'<th scope="col" class="numeric">{score_label}'
               '<span class="secondary block">Artificial Analysis; capability grade below</span></th>')
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
                        f'<th scope="colgroup" colspan="{8 if intelligence else 3}">'
                        f'{text(section["label"])} <span class="section-count">'
                        f'{count} model{"s" if count != 1 else ""}</span></th></tr>')
        for row in section["rows"]:
            section_html += (f'<tr data-model="{text(row["key"])}">'
                             f'<th scope="row">{model_cell(row)}</th>'
                             f'<td>{render.EFFORT_LABEL[row["effort"]]}</td>'
                             f'<td class="numeric">{score_cell(row)}</td>')
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
            section_html += '</tr>'
        bodies.append(section_html + '</tbody>')
    return ('<div class="comparison-scroll" role="region" aria-label="Model comparison table" '
            'tabindex="0"><table class="model-table"><caption class="sr-only">'
            f'{score_label}; {text(result["provider_label"])}; '
            f'{text(render.OBJECTIVE_LABEL[result["objective"]])}</caption>'
            f'<thead><tr>{headers}</tr></thead>{"".join(bodies)}</table></div>')


def provider_picks(result):
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
                         'reasoning effort</span></td>'
                         f'<td class="numeric">{score_cell(row)}</td>')
            if intelligence:
                value = (number(row["ppi"], places=1) if result["objective"] == "ppi" else
                         money(row["cost"]))
                row_html += f'<td class="numeric">{value}</td>'
        groups.append(row_html + '</tr>')
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
    return ('<details class="secondary-disclosure"><summary>Intelligence frontier path '
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
    return ('<details class="secondary-disclosure"><summary>Independent source ratings '
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


def excluded_models(result):
    rows = result["excluded"]
    if not rows:
        return ""
    label = render.INDEX_LABEL[result["index"]]
    items = "".join(
        f'<li><strong>{text(row["model"])}</strong> ({text(row["provider"])}), '
        f'{render.EFFORT_LABEL[row["effort"]]}: {label} score {number(row["score"])}, '
        f'grade {row["grade"]} of 5. {text(row["reason"])}. '
        f'{"Benchmark task cost " + money(row["cost"]) + ". " if result["index"] == "intelligence" else ""}'
        'This is the objective-selected configuration; the filter does not select a different effort.</li>'
        for row in rows)
    return ('<details class="secondary-disclosure" id="excluded-models"><summary>'
            f'Excluded by capability display filter ({len(rows)}) — '
            f'{text(result["provider_label"])}</summary><ul>{items}</ul></details>')


def unranked_models(result):
    rows = result["unranked"]
    if not rows or result["status"] == "unavailable_objective":
        return ""
    items = "".join(f'<li><strong>{text(row["model"])}</strong> '
                    f'({text(row["provider"])}): {text(row["reason"])}.</li>' for row in rows)
    return ('<details class="secondary-disclosure" id="unranked-models"><summary>'
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
             f'{render.VIEW_LABEL[result["view"]]}; {count} ranked models')
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
        comparison += provider_picks(result)
    comparison += (frontier_path(session, result) + source_ratings(result) +
                   excluded_models(result) + unranked_models(result) + empty_creators(result))
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
