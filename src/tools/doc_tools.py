from __future__ import annotations

from pathlib import Path
from typing import List

from ..state import Evidence


KEY_TERMS = [
    "Dialectical Synthesis",
    "Fan-In",
    "Fan-Out",
    "Metacognition",
    "State Synchronization",
]


def _read_pdf_text(pdf_path: Path) -> str:
    """
    Placeholder for PDF parsing.

    Intended implementation: use Docling or similar library to extract structured text
    from the architectural report. For now, this function simply returns an empty
    string so the rest of the pipeline can be wired without hard dependency on PDF
    tooling.
    """
    # TODO: integrate Docling or another robust PDF parser.
    return ""


def analyze_theoretical_depth(pdf_path: str) -> List[Evidence]:
    """
    Theoretical Depth:
    - parse the PDF
    - search for key orchestration concepts
    - capture surrounding context for each mention
    """
    path = Path(pdf_path)
    text = _read_pdf_text(path)

    # Simple placeholder: mark that parsing is not yet implemented.
    goal = "Theoretical depth in PDF: dialectics, fan-in/fan-out, metacognition"
    return [
        Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(path),
            rationale=(
                "PDF parsing and keyword context extraction not yet implemented; "
                "DocAnalyst currently only reserves space for this evidence."
            ),
            confidence=0.1,
        )
    ]


def analyze_host_accuracy(pdf_path: str, repo_url: str) -> List[Evidence]:
    """
    Host Analysis Accuracy:
    - extract file paths mentioned in the report
    - cross-check with RepoInvestigator’s discovered files
    - distinguish verified paths vs hallucinated ones
    """
    path = Path(pdf_path)
    goal = "Host analysis accuracy: claimed paths vs repository reality"
    return [
        Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(path),
            rationale=(
                "Cross-referencing report file paths with repository contents "
                "is not yet implemented; this placeholder evidence signals missing "
                "DocAnalyst coverage."
            ),
            confidence=0.1,
        )
    ]

