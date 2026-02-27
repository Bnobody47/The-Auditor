from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..state import AgentState, AuditReport, CriterionResult, Evidence, JudicialOpinion


RUBRIC_PATH = Path(__file__).resolve().parents[2] / "rubric" / "week2_rubric.json"


def context_builder_node(state: AgentState) -> Dict[str, List[Dict]]:
    """
    Loads the rubric JSON and injects rubric dimensions into the AgentState.

    This ensures all downstream nodes (Detectives, Judges, Chief Justice) operate
    from a shared, machine-readable Constitution.
    """
    if state.get("rubric_dimensions"):
        return {}

    with RUBRIC_PATH.open("r", encoding="utf-8") as f:
        rubric = json.load(f)
    return {"rubric_dimensions": rubric.get("dimensions", [])}


def evidence_aggregator_node(_: AgentState) -> Dict:
    """
    Fan-in node for Detective outputs.

    Because AgentState.evidences uses a reducer, parallel branches can safely write
    into the evidences dict; this node currently acts as a synchronization point
    without mutating state.
    """
    return {}


def _score_variance(ops: List[JudicialOpinion]) -> int:
    scores = [o.score for o in ops]
    return (max(scores) - min(scores)) if scores else 0


def _has_confirmed_security_issue(evidences: Dict[str, List[Evidence]]) -> bool:
    # Heuristic: any safe_tool_engineering evidence with found=False and an explicit unsafe marker.
    for ev in evidences.get("safe_tool_engineering", []):
        text = (ev.rationale or "") + " " + (ev.content or "")
        if not ev.found and ("os.system" in text or "shell" in text or "unsafe" in text):
            return True
    return False


def _render_markdown(report: AuditReport) -> str:
    lines: List[str] = []
    lines.append("# Automaton Auditor Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(report.executive_summary.strip())
    lines.append("")
    lines.append(f"**Overall score**: {report.overall_score:.2f}")
    lines.append("")
    lines.append("## Criterion Breakdown")
    for c in report.criteria:
        lines.append(f"### {c.dimension_name} (`{c.dimension_id}`)")
        lines.append(f"- **Final score**: {c.final_score}/5")
        if c.dissent_summary:
            lines.append(f"- **Dissent**: {c.dissent_summary}")
        lines.append("- **Judge opinions**:")
        for op in c.judge_opinions:
            lines.append(f"  - **{op.judge}**: **{op.score}/5** — {op.argument}")
            if op.cited_evidence:
                lines.append(f"    - Cited evidence: {', '.join(op.cited_evidence)}")
        lines.append("- **Remediation**:")
        lines.append(f"  {c.remediation}")
        lines.append("")
    lines.append("## Remediation Plan")
    lines.append(report.remediation_plan.strip())
    lines.append("")
    return "\n".join(lines)


def chief_justice_node(state: AgentState) -> Dict[str, object]:
    """
    Supreme Court synthesis.

    Placeholder implementation:
    - groups JudicialOpinion objects by criterion_id
    - computes a simple average score
    - renders a minimal Markdown report with per-criterion summaries

    Later, this node will encode the full synthesis_rules specified in the rubric
    (security overrides, fact supremacy, dissent requirement).
    """
    repo_url: Optional[str] = state.get("repo_url")
    dims: List[Dict] = state.get("rubric_dimensions", [])
    evidences: Dict[str, List[Evidence]] = state.get("evidences", {})
    opinions: List[JudicialOpinion] = state.get("opinions", [])

    by_criterion: Dict[str, List[JudicialOpinion]] = {}
    for op in opinions:
        by_criterion.setdefault(op.criterion_id, []).append(op)

    security_issue = _has_confirmed_security_issue(evidences)

    criteria_results: List[CriterionResult] = []
    for dim in dims:
        dim_id = dim.get("id", "")
        dim_name = dim.get("name", dim_id)
        ops = by_criterion.get(dim_id, [])
        # Default scoring: TechLead > Prosecutor > Defense weighting, deterministic.
        score_map = {o.judge: o.score for o in ops}
        tech = score_map.get("TechLead")
        pros = score_map.get("Prosecutor")
        defe = score_map.get("Defense")

        # Resolve final score deterministically.
        base = tech if tech is not None else (pros if pros is not None else (defe if defe is not None else 1))

        # Security override caps total at 3 for the affected tooling criterion, and also caps overall.
        final_score = int(base)
        if security_issue and dim_id in {"safe_tool_engineering", "git_forensic_analysis", "state_management_rigor"}:
            final_score = min(final_score, 3)

        dissent = None
        if _score_variance(ops) > 2:
            dissent = (
                "Large variance across judges. Prosecutor and Defense disagreed materially; "
                "Chief Justice applied deterministic rules prioritizing security and functionality."
            )

        remediation_parts: List[str] = []
        if dim_id == "structured_output_enforcement":
            remediation_parts.append(
                "Ensure Judge LLM calls use `.with_structured_output(JudicialOpinion)` (or `.bind_tools`) "
                "and retry on parse failures."
            )
        if dim_id == "graph_orchestration":
            remediation_parts.append(
                "Verify parallel fan-out/fan-in for Detectives and Judges, and add conditional edges for failures."
            )
        if dim_id == "safe_tool_engineering":
            remediation_parts.append(
                "Ensure all git operations are sandboxed with `tempfile.TemporaryDirectory()` and avoid `os.system`."
            )
        if not remediation_parts:
            remediation_parts.append("Address missing evidence and tighten implementation against the rubric success patterns.")

        criteria_results.append(
            CriterionResult(
                dimension_id=dim_id,
                dimension_name=dim_name,
                final_score=final_score,
                judge_opinions=ops,
                dissent_summary=dissent,
                remediation=" ".join(remediation_parts),
            )
        )

    overall = sum(c.final_score for c in criteria_results) / max(1, len(criteria_results))
    if security_issue:
        overall = min(overall, 3.0)

    executive = (
        "This report summarizes forensic evidence collected by the Detectives and "
        "dialectical scoring from Prosecutor/Defense/Tech Lead. "
        + ("A confirmed security issue was detected; overall score capped at 3. " if security_issue else "")
        + "See criterion breakdown for dissent and remediation."
    )

    remediation_plan = " ".join([f"- {c.dimension_id}: {c.remediation}" for c in criteria_results])
    report = AuditReport(
        repo_url=repo_url,
        executive_summary=executive,
        overall_score=float(overall),
        criteria=criteria_results,
        remediation_plan=remediation_plan,
    )
    md = _render_markdown(report)
    return {"final_report": report, "final_report_markdown": md}

