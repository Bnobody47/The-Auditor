from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from ..state import AgentState, Evidence
from ..tools.repo_tools import (
    analyze_git_history,
    analyze_graph_structure,
    analyze_state_management,
    analyze_structured_output_enforcement,
    analyze_tool_safety,
    cloned_repo,
)
from ..tools.doc_tools import (
    analyze_theoretical_depth,
    analyze_host_accuracy,
)
from ..tools.vision_tools import analyze_architecture_diagrams


GIT_FORENSIC = "git_forensic_analysis"
STATE_RIGOR = "state_management_rigor"
GRAPH_ORCH = "graph_orchestration"
SAFE_TOOLING = "safe_tool_engineering"
STRUCTURED_OUTPUT = "structured_output_enforcement"
THEORETICAL_DEPTH = "theoretical_depth"
REPORT_ACCURACY = "report_accuracy"
SWARM_VISUAL = "swarm_visual"


def _append_evidences(
    evidences: Dict[str, List[Evidence]],
    criterion_id: str,
    new_items: List[Evidence],
) -> Dict[str, List[Evidence]]:
    bucket = evidences.get(criterion_id, [])
    bucket.extend(new_items)
    evidences[criterion_id] = bucket
    return evidences


def repo_investigator_node(state: AgentState) -> Dict[str, Dict[str, List[Evidence]]]:
    """
    Code Detective: clones & inspects the target GitHub repository.

    Populates evidences for the 'forensic_accuracy_code' rubric dimension, including:
    - Git forensic analysis
    - State management rigor
    - Graph orchestration
    - Safe tool engineering
    - Structured judge outputs
    """
    repo_url: Optional[str] = state.get("repo_url")

    updates: Dict[str, Dict[str, List[Evidence]]] = {"evidences": {}}
    if not repo_url:
        updates["evidences"][GIT_FORENSIC] = [
            Evidence(
                goal="Repository availability",
                found=False,
                content=None,
                location="repo_url",
                rationale="No --repo-url provided; RepoInvestigator did not run.",
                confidence=0.2,
            )
        ]
        return updates

    with cloned_repo(repo_url) as (repo_dir, err):
        if repo_dir is None:
            updates["evidences"][GIT_FORENSIC] = [
                Evidence(
                    goal="Repository clone",
                    found=False,
                    content=None,
                    location=repo_url,
                    rationale=f"Failed to clone repository in sandbox. stderr: {err[:400]}",
                    confidence=0.2,
                )
            ]
            return updates

        updates["evidences"][GIT_FORENSIC] = [analyze_git_history(repo_dir)]
        updates["evidences"][STATE_RIGOR] = [analyze_state_management(repo_dir)]
        updates["evidences"][GRAPH_ORCH] = [analyze_graph_structure(repo_dir)]
        updates["evidences"][SAFE_TOOLING] = [analyze_tool_safety(repo_dir)]
        updates["evidences"][STRUCTURED_OUTPUT] = [
            analyze_structured_output_enforcement(repo_dir)
        ]

    return updates


def doc_analyst_node(state: AgentState) -> Dict[str, Dict[str, List[Evidence]]]:
    """
    Paperwork Detective: analyzes the architectural PDF report.

    Populates evidences for the 'forensic_accuracy_docs' rubric dimension, including:
    - Theoretical depth around Dialectical Synthesis, Fan-In/Fan-Out, Metacognition, etc.
    - Host analysis accuracy: verified vs hallucinated file paths.
    """
    pdf_path: Optional[str] = state.get("pdf_path")
    repo_url: str = state.get("repo_url") or ""

    updates: Dict[str, Dict[str, List[Evidence]]] = {"evidences": {}}
    if not pdf_path or not Path(pdf_path).exists():
        updates["evidences"][THEORETICAL_DEPTH] = [
            Evidence(
                goal="PDF report availability",
                found=False,
                content=None,
                location=str(pdf_path or "pdf_path"),
                rationale="No valid --pdf-path provided; DocAnalyst did not run.",
                confidence=0.2,
            )
        ]
        updates["evidences"][REPORT_ACCURACY] = [
            Evidence(
                goal="Report accuracy cross-reference",
                found=False,
                content=None,
                location=str(pdf_path or "pdf_path"),
                rationale="No valid --pdf-path provided; cannot extract claimed paths for cross-reference.",
                confidence=0.2,
            )
        ]
        return updates

    updates["evidences"][THEORETICAL_DEPTH] = analyze_theoretical_depth(pdf_path)
    updates["evidences"][REPORT_ACCURACY] = analyze_host_accuracy(
        pdf_path=pdf_path, repo_url=repo_url
    )
    return updates


def vision_inspector_node(state: AgentState) -> Dict[str, Dict[str, List[Evidence]]]:
    """
    Diagram Detective: inspects architectural diagrams extracted from the PDF.

    Populates evidences that support the 'langgraph_architecture' criterion, focusing on
    whether the diagrams clearly depict parallel Detectives/Judges and Chief Justice
    synthesis, or just a linear pipeline.
    """
    pdf_path: Optional[str] = state.get("pdf_path")
    updates: Dict[str, Dict[str, List[Evidence]]] = {"evidences": {}}

    if not pdf_path or not Path(pdf_path).exists():
        updates["evidences"][SWARM_VISUAL] = [
            Evidence(
                goal="Diagram availability",
                found=False,
                content=None,
                location=str(pdf_path or "pdf_path"),
                rationale="No valid --pdf-path provided; VisionInspector did not run.",
                confidence=0.1,
            )
        ]
        return updates

    updates["evidences"][SWARM_VISUAL] = analyze_architecture_diagrams(pdf_path)
    return updates


