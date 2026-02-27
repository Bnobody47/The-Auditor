from __future__ import annotations

from pathlib import Path
from typing import List

from pypdf import PdfReader  # type: ignore[import]

from ..state import Evidence


def analyze_architecture_diagrams(pdf_path: str) -> List[Evidence]:
    """
    Diagram Detective:
    - extract image objects from the PDF using pypdf
    - count how many pages contain diagrams/images
    - classify at a coarse level whether any swarm visuals likely exist

    This implementation does not yet call a multimodal LLM, but it performs
    explicit image extraction and page-level counting so Judges can reason
    about whether diagrams exist at all.
    """
    path = Path(pdf_path)
    goal = "Architecture diagrams: swarm visualization quality"

    if not path.exists():
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale="PDF path does not exist; VisionInspector could not inspect diagrams.",
                confidence=0.2,
            )
        ]

    try:
        reader = PdfReader(str(path))
    except Exception:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale="Failed to open PDF with pypdf; cannot extract diagrams.",
                confidence=0.2,
            )
        ]

    total_pages = len(reader.pages)
    pages_with_images: List[int] = []

    for idx, page in enumerate(reader.pages):
        try:
            resources = page.get("/Resources") or {}
            xobjects = resources.get("/XObject") or {}
        except Exception:
            continue

        page_has_image = False
        for obj in xobjects.values():
            try:
                if obj.get("/Subtype") == "/Image":
                    page_has_image = True
                    break
            except Exception:
                continue

        if page_has_image:
            pages_with_images.append(idx + 1)

    found = len(pages_with_images) > 0
    rationale = (
        f"Detected images on pages {pages_with_images} out of {total_pages} total pages."
        if found
        else f"No image XObjects detected in PDF across {total_pages} pages."
    )

    content = (
        f"pages_with_images={pages_with_images}, total_pages={total_pages}"
        if total_pages
        else None
    )

    return [
        Evidence(
            goal=goal,
            found=found,
            content=content,
            location=str(path),
            rationale=rationale,
            confidence=0.75 if found else 0.6,
        )
    ]

