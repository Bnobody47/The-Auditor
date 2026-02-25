import operator
from typing import Annotated, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Evidence(BaseModel):
    """A single, objective piece of forensic evidence."""

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


class AgentState(TypedDict):
    """
    Global LangGraph state for the Automaton Auditor.

    The reducer annotations on evidences and opinions enable safe parallel fan-out
    and fan-in, preventing branches from overwriting each other's contributions.
    """

    # Inputs
    repo_url: str
    pdf_path: str

    # Loaded from rubric/week2_rubric.json at runtime
    rubric_dimensions: List[Dict]

    # Forensic outputs from Detectives, keyed by criterion ID or evidence class.
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]

    # Judicial outputs from the Prosecutor, Defense, and Tech Lead judges.
    opinions: Annotated[List[JudicialOpinion], operator.add]

    # Final Markdown audit report produced by the Chief Justice.
    final_report: str

