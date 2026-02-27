from __future__ import annotations

from langgraph.graph import END, StateGraph

from .state import AgentState
from .nodes.detectives import (
    repo_investigator_node,
    doc_analyst_node,
    vision_inspector_node,
)
from .nodes.judges import prosecutor_node, defense_node, tech_lead_node
from .nodes.justice import context_builder_node, evidence_aggregator_node, chief_justice_node


def _evidence_health_router(state: AgentState) -> str:
    """
    Simple conditional router for error handling.

    If no evidences were collected at all (e.g., missing repo/PDF), skip the
    Judges and go directly to the Chief Justice so it can emit a degraded
    report instead of failing mid-graph.
    """
    evidences = state.get("evidences", {})
    has_any = any(bucket for bucket in evidences.values())
    return "ok" if has_any else "missing_evidence"


def judge_fanout_node(_: AgentState) -> dict:
    """No-op node used to support conditional -> parallel fan-out."""
    return {}


def build_graph() -> StateGraph[AgentState]:
    """
    Construct the Automaton Auditor LangGraph.

    Topology (high-level):
      ContextBuilder
        ├─> RepoInvestigator
        ├─> DocAnalyst
        └─> VisionInspector
          └─> EvidenceAggregator
                ├─> Prosecutor
                ├─> Defense
                └─> TechLead
                      └─> ChiefJustice -> END

    Detectives and Judges run in parallel branches, with reducer-backed state fields
    preventing data overwrites during fan-out / fan-in.
    """
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("context_builder", context_builder_node)
    graph.add_node("repo_investigator", repo_investigator_node)
    graph.add_node("doc_analyst", doc_analyst_node)
    graph.add_node("vision_inspector", vision_inspector_node)
    graph.add_node("evidence_aggregator", evidence_aggregator_node)
    graph.add_node("judge_fanout", judge_fanout_node)
    graph.add_node("prosecutor", prosecutor_node)
    graph.add_node("defense", defense_node)
    graph.add_node("tech_lead", tech_lead_node)
    graph.add_node("chief_justice", chief_justice_node)

    # Start at the context builder
    graph.set_entry_point("context_builder")

    # Fan-out to Detectives
    graph.add_edge("context_builder", "repo_investigator")
    graph.add_edge("context_builder", "doc_analyst")
    graph.add_edge("context_builder", "vision_inspector")

    # Fan-in at EvidenceAggregator
    graph.add_edge("repo_investigator", "evidence_aggregator")
    graph.add_edge("doc_analyst", "evidence_aggregator")
    graph.add_edge("vision_inspector", "evidence_aggregator")

    # Conditional branch after aggregation:
    # - if we have at least one evidence item, fan-out to Judges
    # - otherwise, skip directly to Chief Justice for a degraded report
    graph.add_conditional_edges(
        "evidence_aggregator",
        _evidence_health_router,
        {
            "ok": "judge_fanout",
            "missing_evidence": "chief_justice",
        },
    )

    # Fan-out to Judges (normal path)
    graph.add_edge("judge_fanout", "prosecutor")
    graph.add_edge("judge_fanout", "defense")
    graph.add_edge("judge_fanout", "tech_lead")

    # Fan-in at Chief Justice and terminate
    graph.add_edge("prosecutor", "chief_justice")
    graph.add_edge("defense", "chief_justice")
    graph.add_edge("tech_lead", "chief_justice")
    graph.add_edge("chief_justice", END)

    return graph


def get_compiled_graph():
    """Convenience helper for running the auditor."""
    return build_graph().compile()

