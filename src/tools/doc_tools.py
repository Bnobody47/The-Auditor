from __future__ import annotations

import re
from pathlib import Path
from typing import List, Sequence, Tuple

from ..state import Evidence


KEY_TERMS = [
    "Dialectical Synthesis",
    "Fan-In",
    "Fan-Out",
    "Metacognition",
    "State Synchronization",
]


def _ingest_pdf_chunks(pdf_path: Path) -> Tuple[Sequence[str], str]:
    """
    Ingest the PDF into text chunks suitable for targeted querying.

    Returns (chunks, error_message). If ingestion fails, chunks will be empty
    and error_message will describe the failure.
    """
    try:
        from docling.document_converter import DocumentConverter  # type: ignore[import]
    except Exception as exc:  # Docling not installed
        return [], f"Docling not available: {exc}"

    conv = DocumentConverter()
    try:
        doc = conv.convert(pdf_path)
    except Exception as exc:
        return [], f"Docling failed to parse PDF: {exc}"

    chunks: List[str] = []
    for section in getattr(doc, "sections", []):
        text = getattr(section, "text", None)
        if text:
            chunks.append(text)

    if not chunks:
        return [], "PDF was parsed but produced no textual sections."

    return chunks, ""


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
    chunks, err = _ingest_pdf_chunks(path)
    goal = "Theoretical depth in PDF: dialectics, fan-in/fan-out, metacognition"

    if err:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale=f"Failed to ingest PDF into chunks: {err}",
                confidence=0.3,
            )
        ]

    evidences: List[Evidence] = []
    for term in KEY_TERMS:
        term_contexts: List[str] = []
        for chunk in chunks:
            term_contexts.extend(_find_keyword_contexts(chunk, term))
        if not term_contexts:
            continue
        evidences.append(
            Evidence(
                goal=f"{goal} – {term}",
                found=True,
                content="\n...\n".join(term_contexts[:3])[:4000],
                location=str(path),
                rationale=f"Found {len(term_contexts)} occurrences of '{term}' across PDF chunks.",
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
    chunks, err = _ingest_pdf_chunks(path)
    goal = "Host analysis accuracy: claimed paths vs repository reality"

    if err:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale=f"Failed to ingest PDF into chunks; cannot collect claimed file paths. {err}",
                confidence=0.3,
            )
        ]

    # Simple heuristic to find src/... style paths
    joined = "\n".join(chunks)
    paths = re.findall(r"(src/[A-Za-z0-9_./]+\.py)", joined)
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


