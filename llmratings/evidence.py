"""Source comparisons for an existing shared-query record, never a new pick."""

from . import render
from .identity import EFFORTS, best_tb
from .tier import grades

SOURCE_NAMES = {"aa": "Artificial Analysis", "deepswe": "DeepSWE",
                "tb": "Terminal-Bench"}


def _rationale(result, record):
    index, objective = result["index"], result["objective"]
    label = render.INDEX_LABEL[index]
    if result["status"] == "unavailable_objective":
        return (f"{render.OBJECTIVE_LABEL[objective]} · {label}. {record['reason']} "
                "No configuration selected. There is no fixed effort for a role.")
    if index != "intelligence":
        eligibility = f"A finite {label} score is required; no matching area-index task cost is established."
        order = f"{label} score descending; lower measured effort; canonical model key."
    else:
        eligibility = ("A finite Intelligence score and finite, non-negative matching "
                       "Intelligence benchmark task cost are required.")
        if objective == "ppi":
            eligibility += (" Best value also requires positive matching task cost "
                            "and finite Capability per dollar.")
            order = ("Capability per dollar descending; Intelligence score descending; "
                     "matching task cost ascending; lower measured effort; canonical model key.")
        elif objective == "price":
            eligibility += f" Capability grade ≥ {result['role']['floor']} qualifies, inclusively."
            order = ("Matching task cost ascending; Intelligence score descending; "
                     "lower measured effort; canonical model key.")
        else:
            order = ("Intelligence score descending; matching task cost ascending; "
                     "lower measured effort; canonical model key.")
    selected = record["configuration"]
    choice = (f"Chosen measured effort: {render.EFFORT_LABEL[selected.effort]}."
              if selected is not None else
              f"No configuration selected: {record['reason']}.")
    return (f"{render.OBJECTIVE_LABEL[objective]} · {label}. {eligibility} "
            f"Within each model and across selected models: {order} {choice} "
            "There is no fixed effort for a role. Timing never selects or breaks ties.")


def model_evidence(ds, result, record):
    """Return actual effort/source evidence for a ranked, excluded or unranked row.

    ``configuration`` and ``effort`` retain the query's selection, including None.
    Each entry in ``configurations`` groups only efforts present in measurements;
    its Rating retains prices, distinct timing, source URL/date/version and raw data.
    Advice is passed through from the row, not recalculated for explored efforts.
    """
    index, objective = result["index"], result["objective"]
    field = render.INDEX_FIELD[index]
    key, selected = record["key"], record["configuration"]
    measurements = record["measurements"]
    aa_scores = render._capability_scores(ds, index)
    capability = grades(aa_scores)
    efforts = sorted({r.effort for r in measurements},
                     key=lambda e: EFFORTS.index(e) if e in EFFORTS else len(EFFORTS))
    configurations = []
    for effort in efforts:
        at_effort = [r for r in measurements if r.effort == effort]
        chosen = selected is not None and effort == selected.effort
        aa = selected if chosen else next((r for r in at_effort if r.source == "aa"), None)
        if result["status"] == "unavailable_objective":
            eligibility_reason = record["reason"]
        elif effort not in EFFORTS:
            eligibility_reason = "No measured reasoning effort; not eligible for objective selection"
        else:
            _, eligibility_reason = render._select(
                [aa] if aa is not None else [], index, objective,
                result["role"]["floor"], capability)
        tb_population = render._source_population(ds, "tb", effort)
        tb_scores = [r.score for r in tb_population]
        dsw_scores = [r.score for r in render._source_population(ds, "deepswe", effort)]
        source_grades = {"aa": capability, "deepswe": grades(dsw_scores),
                         "tb": grades(tb_scores)}
        populations = {"aa": aa_scores, "deepswe": dsw_scores, "tb": tb_scores}
        ratings = {"aa": aa,
                   "deepswe": next((r for r in at_effort if r.source == "deepswe"), None),
                   "tb": next((r for r in tb_population if r.model_key == key), None)
                   or best_tb(at_effort, effort).get(key)
                   or next((r for r in at_effort if r.source == "tb"), None)}
        effort_context = (f"at {render.EFFORT_LABEL[effort]} effort" if effort in EFFORTS
                          else "with no measured reasoning effort")
        sources = []
        for source, name in SOURCE_NAMES.items():
            rating = ratings[source]
            source_index = render.INDEX_LABEL[index] if source == "aa" else (
                "pass@1" if source == "deepswe" else "accuracy")
            score = getattr(rating, field) if source == "aa" and rating else (
                rating.score if rating else None)
            grade = source_grades[source].get(score)
            if effort not in EFFORTS:
                grade = None
            if chosen:
                grade = record[{"aa": "grade", "deepswe": "dsw", "tb": "tb"}[source]]
            reason = None
            if rating is None:
                reason = f"No {name} row {effort_context}"
            elif not render._finite(score):
                reason = f"No finite {name} {source_index} score {effort_context}"
            elif effort not in EFFORTS:
                reason = "No measured reasoning effort; capability grade and rank unavailable"
            population_label = (
                f"All scored Artificial Analysis {source_index} configurations across measured efforts"
                if source == "aa" else f"{name} {source_index} {effort_context}"
                + (", best agent per model" if source == "tb" else ""))
            scores = populations[source]
            sources.append(dict(
                source=source, name=name, index=source_index, effort=effort,
                rating=rating, score=score, grade=grade,
                rank=1 + sum(s > score for s in scores) if grade is not None else None,
                population_size=len(scores), population_label=population_label,
                source_url=rating.source_url if rating else None, reason=reason))
        available = [s for s in sources if s["grade"] is not None]
        disagreement = (available if len(available) >= 2 and
                        max(s["grade"] for s in available) -
                        min(s["grade"] for s in available) >= 2 else [])
        configurations.append(dict(
            effort=effort, selected=chosen, configuration=aa,
            eligibility_reason=eligibility_reason, sources=sources,
            disagreement=disagreement))
    return dict(
        key=key, model=record["model"], provider=record["provider"],
        index=index, objective=objective, configuration=selected,
        effort=selected.effort if selected is not None else None,
        reason=record.get("reason"), rationale=_rationale(result, record),
        configurations=configurations, frontier=record.get("frontier"),
        dom=record.get("dom"), alternatives=record.get("alternatives", []),
        advisory_scope=record.get("advisory_scope", result["advisory_scope"]))
