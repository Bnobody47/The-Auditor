from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import List

from ..state import Evidence


def _run_git_log(repo_dir: Path) -> str:
    result = subprocess.run(
        ["git", "log", "--oneline", "--reverse", "--date=iso", "--pretty=%h %ad %s"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _clone_repo_to_temp(repo_url: str) -> Path:
    tmp_dir = tempfile.TemporaryDirectory()
    target = Path(tmp_dir.name) / "repo"
    subprocess.run(
        ["git", "clone", "--depth", "50", repo_url, str(target)],
        check=False,
        capture_output=True,
        text=True,
    )
    return target


def analyze_git_history(repo_url: str) -> List[Evidence]:
    """
    Git Forensic Analysis:
    - clones the repo into a temporary directory
    - runs git log --oneline --reverse
    - summarizes commit count and progression narrative
    """
    repo_dir = _clone_repo_to_temp(repo_url)
    log_text = _run_git_log(repo_dir)
    commits = [line for line in log_text.splitlines() if line.strip()]

    goal = "Git forensic analysis: commit progression"
    found = len(commits) > 0
    rationale = (
        f"Found {len(commits)} commits using git log --oneline --reverse."
        if found
        else "git log produced no commits; repository may be empty or clone failed."
    )

    return [
        Evidence(
            goal=goal,
            found=found,
            content=log_text[:4000],
            location=str(repo_dir),
            rationale=rationale,
            confidence=0.7 if found else 0.3,
        )
    ]


def analyze_state_management(repo_url: str) -> List[Evidence]:
    """
    Placeholder implementation.

    Intended behavior:
    - use ast to inspect src/state.py or src/graph.py
    - detect Pydantic BaseModel / TypedDict state definitions
    - confirm presence of Evidence collections and JudicialOpinion lists
    """
    repo_dir = _clone_repo_to_temp(repo_url)
    goal = "State management rigor: Pydantic state and reducers"
    return [
        Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(repo_dir / "src" / "state.py"),
            rationale=(
                "AST-based inspection for Pydantic state models not yet implemented; "
                "this node currently serves as a structural placeholder."
            ),
            confidence=0.1,
        )
    ]


def analyze_graph_structure(repo_url: str) -> List[Evidence]:
    """
    Placeholder implementation.

    Intended behavior:
    - use ast to locate StateGraph instantiation
    - inspect builder.add_edge calls for fan-out/fan-in patterns
    - capture the core graph wiring code block
    """
    repo_dir = _clone_repo_to_temp(repo_url)
    goal = "Graph orchestration: StateGraph fan-out/fan-in"
    return [
        Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(repo_dir / "src" / "graph.py"),
            rationale=(
                "AST-based graph orchestration analysis not yet implemented; "
                "this evidence marks a TODO for deeper forensic tooling."
            ),
            confidence=0.1,
        )
    ]


def analyze_tool_safety(repo_url: str) -> List[Evidence]:
    """
    Placeholder implementation.

    Intended behavior:
    - inspect src/tools/ for cloning logic
    - confirm use of tempfile.TemporaryDirectory or equivalent sandboxing
    - flag raw os.system('git clone ...') calls in working directory
    """
    repo_dir = _clone_repo_to_temp(repo_url)
    goal = "Safe tool engineering: sandboxed git tooling"
    return [
        Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(repo_dir / "src" / "tools"),
            rationale=(
                "Static analysis of git cloning safety not yet implemented; "
                "this placeholder evidence reminds the Judges of missing coverage."
            ),
            confidence=0.1,
        )
    ]


def analyze_structured_output_enforcement(repo_url: str) -> List[Evidence]:
    """
    Placeholder implementation.

    Intended behavior:
    - inspect src/nodes/judges.py
    - verify usage of .with_structured_output() or .bind_tools() bound to JudicialOpinion
    """
    repo_dir = _clone_repo_to_temp(repo_url)
    goal = "Structured output enforcement for Judges"
    return [
        Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(repo_dir / "src" / "nodes" / "judges.py"),
            rationale=(
                "Inspection for structured LLM outputs is not yet wired; "
                "this will be upgraded to AST or text-based analysis."
            ),
            confidence=0.1,
        )
    ]

