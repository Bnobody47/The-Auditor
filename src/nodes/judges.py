from __future__ import annotations

from typing import List

from ..state import AgentState, JudicialOpinion


def _make_opinion(judge: str, criterion_id: str, argument: str, score: int) -> JudicialOpinion:
    return JudicialOpinion(
        judge=judge, criterion_id=criterion_id, score=score, argument=argument, cited_evidence=[]
    )


def prosecutor_node(state: AgentState) -> AgentState:
    """
    Prosecutor: critical lens.

    Placeholder implementation that walks rubric dimensions and emits a conservative
    opinion per criterion. Later, this node will:
    - inspect state['evidences'] filtered by criterion
    - apply Prosecutor-specific judicial_logic from the rubric
    - call an LLM with structured output to generate nuanced arguments
    """
    for dim in state.get("rubric_dimensions", []):
        criterion_id = dim["id"]
        name = dim["name"]
        argument = f"[Prosecutor] Placeholder assessment for '{name}'."
        state.setdefault("opinions", []).append(
            _make_opinion("Prosecutor", criterion_id, argument, score=1)
        )
    return state


def defense_node(state: AgentState) -> AgentState:
    """
    Defense: optimistic lens.

    Placeholder implementation that rewards effort with mid-range scores.
    """
    for dim in state.get("rubric_dimensions", []):
        criterion_id = dim["id"]
        name = dim["name"]
        argument = f"[Defense] Placeholder recognition of effort for '{name}'."
        state.setdefault("opinions", []).append(
            _make_opinion("Defense", criterion_id, argument, score=3)
        )
    return state


def tech_lead_node(state: AgentState) -> AgentState:
    """
    Tech Lead: pragmatic lens.

    Placeholder implementation that issues neutral scores pending real analysis.
    """
    for dim in state.get("rubric_dimensions", []):
        criterion_id = dim["id"]
        name = dim["name"]
        argument = f"[TechLead] Placeholder pragmatic assessment for '{name}'."
        state.setdefault("opinions", []).append(
            _make_opinion("TechLead", criterion_id, argument, score=3)
        )
    return state

