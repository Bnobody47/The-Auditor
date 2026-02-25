from __future__ import annotations

import re
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
    Lightweight PDF text extraction.

    If Docling is available, use it; otherwise, fall back to an empty string so
    the rest of the pipeline can still run without crashing.
    """
    try:
        from docling.document_converter import DocumentConverter  # type: ignore[import]
    except Exception:
        return ""

    conv = DocumentConverter()
    try:
        doc = conv.convert(pdf_path)
    except Exception:
        return ""

    # Concatenate all text segments into a single string.
    return "\n".join(block.text for block in doc.sections if getattr(block, "text", None))


def _find_keyword_contexts(text: str, keyword: str, window: int = 120) -> List[str]:
    contexts: List[str] = []
    for match in re.finditer(re.escape(keyword), text, flags=re.IGNORECASE):
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        contexts.append(text[start:end].strip())
    return contexts


def analyze_theoretical_depth(pdf_path: str) -> List[Evidence]:
    """
    Theoretical Depth:
    - parse the PDF
    - search for key orchestration concepts
    - capture surrounding context for each mention
    """
    path = Path(pdf_path)
    text = _read_pdf_text(path)
    goal = "Theoretical depth in PDF: dialectics, fan-in/fan-out, metacognition"

    if not text:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale="Failed to extract text from PDF; Docling unavailable or parsing error.",
                confidence=0.3,
            )
        ]

    evidences: List[Evidence] = []
    for term in KEY_TERMS:
        contexts = _find_keyword_contexts(text, term)
        if not contexts:
            continue
        evidences.append(
            Evidence(
                goal=f"{goal} – {term}",
                found=True,
                content="\n...\n".join(contexts[:3])[:4000],
                location=str(path),
                rationale=f"Found {len(contexts)} occurrences of '{term}' with surrounding context.",
                confidence=0.8,
            )
        )

    if not evidences:
        evidences.append(
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale="No occurrences of the key theoretical terms were found in the parsed PDF text.",
                confidence=0.7,
            )
        )

    return evidences


def analyze_host_accuracy(pdf_path: str, repo_url: str) -> List[Evidence]:
    """
    Host Analysis Accuracy:
    - extract file paths mentioned in the report
    - (future) cross-check with RepoInvestigator’s discovered files
    - currently surfaces claimed paths as evidence for later cross-reference
    """
    path = Path(pdf_path)
    text = _read_pdf_text(path)
    goal = "Host analysis accuracy: claimed paths vs repository reality"

    if not text:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale="Failed to extract text from PDF; cannot collect claimed file paths.",
                confidence=0.3,
            )
        ]

    # Simple heuristic to find src/... style paths
    paths = re.findall(r"(src/[A-Za-z0-9_./]+\.py)", text)
    unique_paths = sorted(set(paths))

    if not unique_paths:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale="No file paths matching src/*.py patterns were mentioned in the report.",
                confidence=0.7,
            )
        ]

    return [
        Evidence(
            goal=goal,
            found=True,
            content="\n".join(unique_paths),
            location=str(path),
            rationale=(
                "Extracted claimed file paths from the report text. "
                "These will be cross-referenced with repository contents by code detectives."
            ),
            confidence=0.8,
        )
    ]


