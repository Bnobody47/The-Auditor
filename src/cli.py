from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from .graph import get_compiled_graph


def run_audit(repo_url: str, pdf_path: str, output_path: Path) -> Path:
    """Run the Automaton Auditor graph and write the Markdown report."""
    load_dotenv()  # load API keys and LANGCHAIN_TRACING_V2, if set

    graph = get_compiled_graph()

    initial_state: Dict[str, Any] = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": "",
    }

    result = graph.invoke(initial_state)
    report = result.get("final_report", "")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Automaton Auditor on a target Week 2 repository."
    )
    parser.add_argument(
        "--repo-url",
        required=True,
        help="GitHub repository URL to audit (e.g. https://github.com/user/week2-repo.git)",
    )
    parser.add_argument(
        "--pdf-path",
        required=True,
        help="Path to the architectural PDF report associated with the repo.",
    )
    parser.add_argument(
        "--output",
        default="audit/report_onpeer_generated/audit_report.md",
        help="Path where the Markdown audit report will be written.",
    )

    args = parser.parse_args()
    output_path = Path(args.output)
    final_path = run_audit(args.repo_url, args.pdf_path, output_path)
    print(f"Audit report written to: {final_path}")


if __name__ == "__main__":
    main()

