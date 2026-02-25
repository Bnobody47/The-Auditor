from __future__ import annotations

from pathlib import Path
from typing import List

from ..state import Evidence


def analyze_architecture_diagrams(pdf_path: str) -> List[Evidence]:
    """
    Diagram Detective:
    - extract images from the PDF
    - send them to a multimodal LLM
    - classify whether they depict parallel Detectives/Judges and Chief Justice
      synthesis, or only a linear pipeline

    This is currently a structural placeholder; image extraction and multimodal
    analysis will be implemented once the core graph and judge orchestration are
    stable.
    """
    path = Path(pdf_path)
    goal = "Architecture diagrams: swarm visualization quality"
    return [
        Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(path),
            rationale=(
                "Vision-based analysis of architectural diagrams is not yet wired; "
                "this placeholder evidence keeps the VisionInspector node in the "
                "overall LangGraph topology."
            ),
            confidence=0.05,
        )
    ]

