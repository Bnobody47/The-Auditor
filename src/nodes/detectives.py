from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..state import AgentState, Evidence
from ..tools.repo_tools import (
    analyze_git_history,
    analyze_graph_structure,
    analyze_state_management,
    analyze_tool_safety,
    analyze_structured_output_enforcement,
)
from ..tools.doc_tools import (
    analyze_theoretical_depth,
    analyze_host_accuracy,
)
from ..tools.vision_tools import analyze_architecture_diagrams


FOR_CODE_CRITERION = "forensic_accuracy_code"
FOR_DOCS_CRITERION = "forensic_accuracy_docs"
FOR_VISUAL_CRITERION = "langgraph_architecture"


def _append_evidences(
    evidences: Dict[str, List[Evidence]],
    criterion_id: str,
    new_items: List[Evidence],
) -> Dict[str, List[Evidence]]:
    bucket = evidences.get(criterion_id, [])
    bucket.extend(new_items)
    evidences[criterion_id] = bucket
    return evidences


def repo_investigator_node(state: AgentState) -> AgentState:
    """
    Code Detective: clones & inspects the target GitHub repository.

    Populates evidences for the 'forensic_accuracy_code' rubric dimension, including:
    - Git forensic analysis
    - State management rigor
    - Graph orchestration
    - Safe tool engineering
    - Structured judge outputs
    """
    repo_url = state.get("repo_url")
    evidences = state.get("evidences", {})

    if not repo_url:
        fallback = Evidence(
            goal="Repository availability",
            found=False,
            content=None,
            location="repo_url",
            rationale="No repo_url provided in AgentState; RepoInvestigator could not run.",
            confidence=0.2,
        )
        state["evidences"] = _append_evidences(
            evidences=evidences,
            criterion_id=FOR_CODE_CRITERION,
            new_items=[fallback],
        )
        return state

    git_ev = analyze_git_history(repo_url)
    state_ev = analyze_state_management(repo_url)
    graph_ev = analyze_graph_structure(repo_url)
    tool_ev = analyze_tool_safety(repo_url)
    structured_ev = analyze_structured_output_enforcement(repo_url)

    all_evidence: List[Evidence] = (
        git_ev + state_ev + graph_ev + tool_ev + structured_ev
    )

    state["evidences"] = _append_evidences(
        evidences=evidences,
        criterion_id=FOR_CODE_CRITERION,
        new_items=all_evidence,
    )
    return state


def doc_analyst_node(state: AgentState) -> AgentState:
    """
    Paperwork Detective: analyzes the architectural PDF report.

    Populates evidences for the 'forensic_accuracy_docs' rubric dimension, including:
    - Theoretical depth around Dialectical Synthesis, Fan-In/Fan-Out, Metacognition, etc.
    - Host analysis accuracy: verified vs hallucinated file paths.
    """
    pdf_path = state.get("pdf_path")
    repo_url = state.get("repo_url", "")

    evidences = state.get("evidences", {})

    if not pdf_path or not Path(pdf_path).exists():
        fallback = Evidence(
            goal="PDF report availability",
            found=False,
            content=None,
            location=str(pdf_path or "pdf_path"),
            rationale="PDF path missing or file does not exist; DocAnalyst could not inspect the report.",
            confidence=0.2,
        )
        state["evidences"] = _append_evidences(
            evidences=evidences,
            criterion_id=FOR_DOCS_CRITERION,
            new_items=[fallback],
        )
        return state

    theoretical_ev = analyze_theoretical_depth(pdf_path)
    host_accuracy_ev = analyze_host_accuracy(pdf_path=pdf_path, repo_url=repo_url)

    all_evidence: List[Evidence] = theoretical_ev + host_accuracy_ev

    state["evidences"] = _append_evidences(
        evidences=evidences,
        criterion_id=FOR_DOCS_CRITERION,
        new_items=all_evidence,
    )
    return state


def vision_inspector_node(state: AgentState) -> AgentState:
    """
    Diagram Detective: inspects architectural diagrams extracted from the PDF.

    Populates evidences that support the 'langgraph_architecture' criterion, focusing on
    whether the diagrams clearly depict parallel Detectives/Judges and Chief Justice
    synthesis, or just a linear pipeline.
    """
    pdf_path = state.get("pdf_path")
    evidences = state.get("evidences", {})

    if not pdf_path or not Path(pdf_path).exists():
        fallback = Evidence(
            goal="Diagram availability",
            found=False,
            content=None,
            location=str(pdf_path or "pdf_path"),
            rationale="PDF path missing or file does not exist; VisionInspector could not extract diagrams.",
            confidence=0.1,
        )
        state["evidences"] = _append_evidences(
            evidences=evidences,
            criterion_id=FOR_VISUAL_CRITERION,
            new_items=[fallback],
        )
        return state

    visual_ev = analyze_architecture_diagrams(pdf_path)

    state["evidences"] = _append_evidences(
        evidences=evidences,
        criterion_id=FOR_VISUAL_CRITERION,
        new_items=visual_ev,
    )
    return state


