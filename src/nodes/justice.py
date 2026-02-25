from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from ..state import AgentState, JudicialOpinion


RUBRIC_PATH = Path(__file__).resolve().parents[2] / "rubric" / "week2_rubric.json"


def context_builder_node(state: AgentState) -> AgentState:
    """
    Loads the rubric JSON and injects rubric dimensions into the AgentState.

    This ensures all downstream nodes (Detectives, Judges, Chief Justice) operate
    from a shared, machine-readable Constitution.
    """
    if state.get("rubric_dimensions"):
        return state

    with RUBRIC_PATH.open("r", encoding="utf-8") as f:
        rubric = json.load(f)
    state["rubric_dimensions"] = rubric.get("dimensions", [])
    return state


def evidence_aggregator_node(state: AgentState) -> AgentState:
    """
    Fan-in node for Detective outputs.

    Because AgentState.evidences uses a reducer, parallel branches can safely write
    into the evidences dict; this node currently acts as a synchronization point
    without mutating state.
    """
    return state


def chief_justice_node(state: AgentState) -> AgentState:
    """
    Supreme Court synthesis.

    Placeholder implementation:
    - groups JudicialOpinion objects by criterion_id
    - computes a simple average score
    - renders a minimal Markdown report with per-criterion summaries

    Later, this node will encode the full synthesis_rules specified in the rubric
    (security overrides, fact supremacy, dissent requirement).
    """
    opinions: List[JudicialOpinion] = state.get("opinions", [])
    by_criterion: Dict[str, List[JudicialOpinion]] = {}
    for op in opinions:
        by_criterion.setdefault(op.criterion_id, []).append(op)

    lines: List[str] = []
    lines.append("# Automaton Auditor Report")
    lines.append("")
    lines.append("## Executive Summary")
    if not opinions:
        lines.append("No judicial opinions were generated. The system is not yet fully wired.")
    else:
        lines.append("Preliminary scores have been generated using placeholder judicial logic.")
    lines.append("")
    lines.append("## Criterion Breakdown")

    for criterion_id, ops in by_criterion.items():
        scores = [op.score for op in ops]
        avg = sum(scores) / len(scores)
        lines.append(f"### {criterion_id}")
        lines.append(f"- Final (placeholder) score: **{avg:.1f}**")
        for op in ops:
            lines.append(f"  - **{op.judge}** gave **{op.score}** – {op.argument}")
        lines.append("")

    lines.append("## Remediation Plan (Placeholder)")
    lines.append(
        "This is a scaffolded report. As the Detectives and Judges are upgraded with "
        "real AST, PDF, and vision analysis, this section will provide file-level, "
        "actionable remediation guidance."
    )

    state["final_report"] = "\n".join(lines)
    return state

