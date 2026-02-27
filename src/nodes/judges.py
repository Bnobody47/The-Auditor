from __future__ import annotations

import json
from typing import Dict, List

from pydantic import BaseModel, Field

from ..llm import get_chat_model
from ..state import AgentState, Evidence, JudicialOpinion


class JudgeBatchOutput(BaseModel):
    opinions: List[JudicialOpinion] = Field(default_factory=list)


def _evidence_summary(evidences: Dict[str, List[Evidence]]) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {}
    for dim_id, items in evidences.items():
        out[dim_id] = [
            {
                "evidence_id": e.evidence_id,
                "goal": e.goal,
                "found": e.found,
                "location": e.location,
                "rationale": e.rationale,
                "confidence": e.confidence,
            }
            for e in items
        ]
    return out


def _judge_system_prompt(judge: str) -> str:
    if judge == "Prosecutor":
        return (
            "You are the Prosecutor. Trust no one. Assume vibe coding. "
            "You must be strict, cite evidence IDs, and assign low scores when requirements are unmet."
        )
    if judge == "Defense":
        return (
            "You are the Defense Attorney. Reward effort and intent. "
            "Be generous when evidence shows thoughtful engineering, even if imperfect."
        )
    return (
        "You are the Tech Lead. Pragmatic and maintainability-focused. "
        "Score based on what works and what is safe to operate. Provide actionable remediation."
    )


def _run_judge(judge: str, state: AgentState) -> List[JudicialOpinion]:
    dims = state.get("rubric_dimensions", [])
    evidences = state.get("evidences", {})

    # If no LLM keys are configured, fall back to deterministic placeholder output.
    try:
        llm = get_chat_model().with_structured_output(JudgeBatchOutput)
    except Exception:
        opinions: List[JudicialOpinion] = []
        for dim in dims:
            opinions.append(
                JudicialOpinion(
                    judge=judge,  # type: ignore[arg-type]
                    criterion_id=dim["id"],
                    score=3 if judge != "Prosecutor" else 1,
                    argument=f"[{judge}] LLM not configured; placeholder opinion.",
                    cited_evidence=[],
                )
            )
        return opinions

    payload = {
        "rubric_dimensions": dims,
        "evidence_by_dimension": _evidence_summary(evidences),
    }

    prompt = (
        f"{_judge_system_prompt(judge)}\n\n"
        "Task:\n"
        "- For EACH rubric dimension, produce ONE JudicialOpinion with:\n"
        "  - judge: exactly one of Prosecutor, Defense, TechLead\n"
        "  - criterion_id: dimension id\n"
        "  - score: integer 1..5\n"
        "  - argument: specific, criterion-by-criterion reasoning\n"
        "  - cited_evidence: list of evidence_id strings used\n"
        "Rules:\n"
        "- Do not invent evidence. Only cite evidence_id values present in the payload.\n"
        "- If evidence is missing for a criterion, score conservatively and say so.\n\n"
        f"Payload (JSON):\n{json.dumps(payload, ensure_ascii=False)}"
    )

    result: JudgeBatchOutput = llm.invoke(prompt)
    # Ensure correct judge label in all opinions.
    fixed: List[JudicialOpinion] = []
    for op in result.opinions:
        fixed.append(
            JudicialOpinion(
                judge=judge,  # type: ignore[arg-type]
                criterion_id=op.criterion_id,
                score=op.score,
                argument=op.argument,
                cited_evidence=op.cited_evidence,
            )
        )
    return fixed


def prosecutor_node(state: AgentState) -> AgentState:
    """
    Prosecutor: critical lens.

    Placeholder implementation that walks rubric dimensions and emits a conservative
    opinion per criterion. Later, this node will:
    - inspect state['evidences'] filtered by criterion
    - apply Prosecutor-specific judicial_logic from the rubric
    - call an LLM with structured output to generate nuanced arguments
    """
    return {"opinions": _run_judge("Prosecutor", state)}


def defense_node(state: AgentState) -> AgentState:
    """
    Defense: optimistic lens.

    Placeholder implementation that rewards effort with mid-range scores.
    """
    return {"opinions": _run_judge("Defense", state)}


def tech_lead_node(state: AgentState) -> AgentState:
    """
    Tech Lead: pragmatic lens.

    Placeholder implementation that issues neutral scores pending real analysis.
    """
    return {"opinions": _run_judge("TechLead", state)}

