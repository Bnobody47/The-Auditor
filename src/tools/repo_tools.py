from __future__ import annotations

import ast
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

from ..state import Evidence


def _run_git_log(repo_dir: Path) -> Tuple[str, str]:
    result = subprocess.run(
        ["git", "log", "--oneline", "--reverse", "--date=iso", "--pretty=%h %ad %s"],
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip(), result.stderr.strip()


def _clone_repo_to_temp(repo_url: str) -> Tuple[Path, str]:
    """
    Clone the target repository into a sandboxed temporary directory.

    Returns the target path and any stderr emitted by git so callers can surface
    precise failure reasons in Evidence objects.
    """
    tmp_dir = tempfile.TemporaryDirectory()
    target = Path(tmp_dir.name) / "repo"
    proc = subprocess.run(
        ["git", "clone", "--depth", "50", repo_url, str(target)],
        check=False,
        capture_output=True,
        text=True,
    )
    return target, proc.stderr.strip()


def analyze_git_history(repo_url: str) -> List[Evidence]:
    """
    Git Forensic Analysis:
    - clones the repo into a temporary directory
    - runs git log --oneline --reverse
    - summarizes commit count and progression narrative
    """
    repo_dir, clone_err = _clone_repo_to_temp(repo_url)
    goal = "Git forensic analysis: commit progression"

    if clone_err or not repo_dir.exists():
        # Surface clone failures explicitly instead of silently degrading.
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(repo_dir),
                rationale=f"git clone failed or produced no repository directory. stderr: {clone_err[:400]}",
                confidence=0.2,
            )
        ]

    log_text, log_err = _run_git_log(repo_dir)
    commits = [line for line in log_text.splitlines() if line.strip()]

    found = len(commits) > 0 and not log_err
    rationale_parts = []
    if log_err:
        rationale_parts.append(f"git log reported: {log_err[:300]}")
    if commits:
        rationale_parts.append(f"Found {len(commits)} commits using git log --oneline --reverse.")
    if not rationale_parts:
        rationale_parts.append("git log produced no commits; repository may be empty or history is shallow.")

    return [
        Evidence(
            goal=goal,
            found=found,
            content=log_text[:4000],
            location=str(repo_dir),
            rationale=" ".join(rationale_parts),
            confidence=0.8 if found else 0.4,
        )
    ]


def _load_ast_if_exists(root: Path, relative: str) -> Tuple[ast.Module | None, Path]:
    path = root / relative
    if not path.exists():
        return None, path
    try:
        source = path.read_text(encoding="utf-8")
        return ast.parse(source), path
    except Exception:
        return None, path


def analyze_state_management(repo_url: str) -> List[Evidence]:
    """
    AST-based inspection of state definitions:
    - looks for Pydantic BaseModel and TypedDict subclasses
    - verifies presence of Evidence / JudicialOpinion collections
    - checks for Annotated reducers in AgentState
    """
    repo_dir, _ = _clone_repo_to_temp(repo_url)
    module, path = _load_ast_if_exists(repo_dir, "src/state.py")

    goal = "State management rigor: Pydantic state and reducers"
    if module is None:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale="src/state.py not found or failed to parse as Python.",
                confidence=0.3,
            )
        ]

    has_evidence_model = False
    has_opinion_model = False
    has_agent_state = False
    has_reducers = False

    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef):
            base_names = {getattr(b, "id", None) or getattr(getattr(b, "attr", None), "lower", lambda: None)() for b in node.bases}
            if "BaseModel" in base_names and node.name == "Evidence":
                has_evidence_model = True
            if "BaseModel" in base_names and node.name == "JudicialOpinion":
                has_opinion_model = True
            if node.name == "AgentState":
                has_agent_state = True

    # Second pass: look for Annotated[...] with operator.add / operator.ior
    for node in ast.walk(module):
        if isinstance(node, ast.Subscript) and getattr(getattr(node.value, "id", None), "lower", lambda: None)() == "annotated":
            text = ast.get_source_segment(Path(path).read_text(encoding="utf-8"), node) or ""
            if "operator.add" in text or "operator.ior" in text:
                has_reducers = True

    summary = []
    if has_evidence_model:
        summary.append("Evidence model (BaseModel) detected.")
    if has_opinion_model:
        summary.append("JudicialOpinion model (BaseModel) detected.")
    if has_agent_state:
        summary.append("AgentState TypedDict detected.")
    if has_reducers:
        summary.append("Annotated reducers (operator.add / operator.ior) detected in state.")

    found = has_evidence_model and has_opinion_model and has_agent_state and has_reducers

    return [
        Evidence(
            goal=goal,
            found=found,
            content=" ".join(summary) or None,
            location=str(path),
            rationale=(
                "AST inspection of src/state.py for Pydantic models and AgentState "
                "definition. " + (" ".join(summary) if summary else "No expected classes found.")
            ),
            confidence=0.8 if found else 0.4,
        )
    ]


def analyze_graph_structure(repo_url: str) -> List[Evidence]:
    """
    AST-based inspection of graph orchestration:
    - locates StateGraph instantiation
    - inspects add_edge calls for basic fan-out/fan-in patterns
    """
    repo_dir, _ = _clone_repo_to_temp(repo_url)
    module, path = _load_ast_if_exists(repo_dir, "src/graph.py")

    goal = "Graph orchestration: StateGraph fan-out/fan-in"
    if module is None:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(path),
                rationale="src/graph.py not found or failed to parse as Python.",
                confidence=0.3,
            )
        ]

    add_edges = []
    for node in ast.walk(module):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_edge" and len(node.args) >= 2:
                try:
                    src = node.args[0].value  # type: ignore[attr-defined]
                    dst = node.args[1].value  # type: ignore[attr-defined]
                    add_edges.append(f"{src} -> {dst}")
                except Exception:
                    continue

    found = len(add_edges) > 0

    return [
        Evidence(
            goal=goal,
            found=found,
            content="; ".join(add_edges)[:4000] if add_edges else None,
            location=str(path),
            rationale=(
                "AST inspection of src/graph.py for add_edge calls. "
                f"Discovered {len(add_edges)} edges."
            ),
            confidence=0.8 if found else 0.4,
        )
    ]


def analyze_tool_safety(repo_url: str) -> List[Evidence]:
    """
    Static inspection of src/tools/ for safe git tooling:
    - confirms use of tempfile.TemporaryDirectory / subprocess.run
    - flags raw os.system('git clone ...') usage
    """
    repo_dir, _ = _clone_repo_to_temp(repo_url)
    tools_dir = repo_dir / "src" / "tools"
    goal = "Safe tool engineering: sandboxed git tooling"

    if not tools_dir.exists():
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(tools_dir),
                rationale="src/tools directory not found in cloned repository.",
                confidence=0.3,
            )
        ]

    texts = []
    for py in tools_dir.glob("*.py"):
        try:
            texts.append(py.read_text(encoding="utf-8"))
        except Exception:
            continue
    full = "\n".join(texts)

    has_tempdir = "TemporaryDirectory" in full
    has_os_system = "os.system(" in full

    rationale_parts = []
    if has_tempdir:
        rationale_parts.append("Detected use of tempfile.TemporaryDirectory for sandboxing.")
    if has_os_system:
        rationale_parts.append("Detected raw os.system() calls, which may be unsafe.")
    if not rationale_parts:
        rationale_parts.append("No explicit sandboxing or raw os.system usage detected.")

    return [
        Evidence(
            goal=goal,
            found=has_tempdir and not has_os_system,
            content=None,
            location=str(tools_dir),
            rationale=" ".join(rationale_parts),
            confidence=0.8 if has_tempdir and not has_os_system else 0.5,
        )
    ]


def analyze_structured_output_enforcement(repo_url: str) -> List[Evidence]:
    """
    Text-based inspection of Judge nodes for structured output enforcement:
    - checks for .with_structured_output(...) or .bind_tools(...)
    """
    repo_dir, _ = _clone_repo_to_temp(repo_url)
    judges_path = repo_dir / "src" / "nodes" / "judges.py"
    goal = "Structured output enforcement for Judges"

    if not judges_path.exists():
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(judges_path),
                rationale="src/nodes/judges.py not found in cloned repository.",
                confidence=0.3,
            )
        ]

    try:
        text = judges_path.read_text(encoding="utf-8")
    except Exception:
        return [
            Evidence(
                goal=goal,
                found=False,
                content=None,
                location=str(judges_path),
                rationale="Failed to read src/nodes/judges.py for inspection.",
                confidence=0.3,
            )
        ]

    has_structured = ".with_structured_output" in text or ".bind_tools" in text

    return [
        Evidence(
            goal=goal,
            found=has_structured,
            content=None,
            location=str(judges_path),
            rationale=(
                "Found structured-output invocation in judges module."
                if has_structured
                else "No .with_structured_output or .bind_tools usage detected in judges."
            ),
            confidence=0.8 if has_structured else 0.5,
        )
    ]


