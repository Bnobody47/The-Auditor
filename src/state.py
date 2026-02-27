import operator
import uuid
from typing import Annotated, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Evidence(BaseModel):
    """A single, objective piece of forensic evidence."""

    evidence_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for citations and cross-referencing.",
    )
    goal: str = Field(
        ...,
        description="What this evidence was trying to verify (e.g., 'Graph fan-out present').",
    )
    found: bool = Field(
        ...,
        description="Whether the target artifact or condition was actually found.",
    )
    content: Optional[str] = Field(
        default=None,
        description="Optional snippet or structured summary backing this evidence.",
    )
    location: str = Field(
        ...,
        description="File path, commit hash, or other locator for this evidence.",
    )
    rationale: str = Field(
        ...,
        description="Brief explanation of why this evidence supports the conclusion.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence (0.0–1.0) in this evidence’s correctness.",
    )


class JudicialOpinion(BaseModel):
    """Structured opinion from a single judge about one rubric criterion."""

    judge: Literal["Prosecutor", "Defense", "TechLead"] = Field(
        ..., description="Which judicial persona issued this opinion."
    )
    criterion_id: str = Field(
        ...,
        description="ID of the rubric dimension this opinion targets "
        "(e.g., 'langgraph_architecture').",
    )
    score: int = Field(
        ...,
        ge=1,
        le=5,
        description="Discrete score for this criterion on a 1–5 scale.",
    )
    argument: str = Field(
        ...,
        description="Concise but specific reasoning behind the score.",
    )
    cited_evidence: List[str] = Field(
        default_factory=list,
        description="Keys or identifiers of Evidence items this opinion relies on.",
    )


class CriterionResult(BaseModel):
    dimension_id: str = Field(..., description="Rubric dimension ID.")
    dimension_name: str = Field(..., description="Human-readable dimension name.")
    final_score: int = Field(..., ge=1, le=5, description="Final resolved score.")
    judge_opinions: List[JudicialOpinion] = Field(default_factory=list)
    dissent_summary: Optional[str] = Field(
        default=None, description="Required when judge score variance > 2."
    )
    remediation: str = Field(
        ...,
        description="Specific file-level instructions for improving this criterion.",
    )


class AuditReport(BaseModel):
    repo_url: Optional[str] = Field(default=None)
    executive_summary: str = Field(...)
    overall_score: float = Field(..., description="Average across final scores.")
    criteria: List[CriterionResult] = Field(default_factory=list)
    remediation_plan: str = Field(...)


class AgentState(TypedDict):
    """
    Global LangGraph state for the Automaton Auditor.

    The reducer annotations on evidences and opinions enable safe parallel fan-out
    and fan-in, preventing branches from overwriting each other's contributions.
    """

    # Inputs
    repo_url: Optional[str]
    pdf_path: Optional[str]

    # Loaded from rubric/week2_rubric.json at runtime
    rubric_dimensions: List[Dict]

    # Forensic outputs from Detectives, keyed by criterion ID or evidence class.
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]

    # Judicial outputs from the Prosecutor, Defense, and Tech Lead judges.
    opinions: Annotated[List[JudicialOpinion], operator.add]

    # Final structured report and a rendered Markdown string.
    final_report: Optional[AuditReport]
    final_report_markdown: str

