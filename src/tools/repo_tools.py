from __future__ import annotations

import ast
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

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


@contextmanager
def cloned_repo(repo_url: str):
    """
    Context manager that clones the target repo into a sandboxed temp directory.

    Yields (repo_dir, error_message). repo_dir will be None on failure.
    """
    tmp_dir = tempfile.TemporaryDirectory()
    try:
        target = Path(tmp_dir.name) / "repo"
        proc = subprocess.run(
            ["git", "clone", "--depth", "50", repo_url, str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        err = (proc.stderr or "").strip()
        if proc.returncode != 0 or not target.exists():
            yield None, (err or f"git clone failed with return code {proc.returncode}")
        else:
            yield target, err
    finally:
        tmp_dir.cleanup()


def analyze_git_history(repo_dir: Path) -> Evidence:
    """
    Git Forensic Analysis:
    - runs git log --oneline --reverse
    - summarizes commit count and progression narrative
    """
    goal = "Git forensic analysis: commit progression"

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

    return Evidence(
        goal=goal,
        found=found,
        content=log_text[:4000] if log_text else None,
        location=str(repo_dir),
        rationale=" ".join(rationale_parts),
        confidence=0.8 if found else 0.4,
    )


def _load_ast_if_exists(root: Path, relative: str) -> Tuple[ast.Module | None, Path]:
    path = root / relative
    if not path.exists():
        return None, path
    try:
        source = path.read_text(encoding="utf-8")
        return ast.parse(source), path
    except Exception:
        return None, path


def _base_name(expr: ast.expr) -> Optional[str]:
    if isinstance(expr, ast.Name):
        return expr.id
    if isinstance(expr, ast.Attribute):
        return expr.attr
    return None


def _extract_class_block(source: str, class_name: str) -> Optional[str]:
    try:
        module = ast.parse(source)
    except Exception:
        return None
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return ast.get_source_segment(source, node) or None
    return None


def analyze_state_management(repo_dir: Path) -> Evidence:
    """
    AST-based inspection of state definitions:
    - looks for Pydantic BaseModel and TypedDict subclasses
    - verifies presence of Evidence / JudicialOpinion collections
    - checks for Annotated reducers in AgentState
    """
    module, path = _load_ast_if_exists(repo_dir, "src/state.py")

    goal = "State management rigor: Pydantic state and reducers"
    if module is None:
        return Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(path),
            rationale="src/state.py not found or failed to parse as Python.",
            confidence=0.3,
        )

    has_evidence_model = False
    has_opinion_model = False
    has_agent_state = False
    has_reducers = False

    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        source = ""

    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef):
            base_names = {_base_name(b) for b in node.bases}
            if "BaseModel" in base_names and node.name == "Evidence":
                has_evidence_model = True
            if "BaseModel" in base_names and node.name == "JudicialOpinion":
                has_opinion_model = True
            if "TypedDict" in base_names and node.name == "AgentState":
                has_agent_state = True

    # Second pass: look for Annotated[...] with operator.add / operator.ior
    for node in ast.walk(module):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "Annotated":
            seg = ast.get_source_segment(source, node) or ""
            if "operator.add" in seg or "operator.ior" in seg:
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

    agent_state_block = _extract_class_block(source, "AgentState")
    content_parts: List[str] = []
    if summary:
        content_parts.append(" ".join(summary))
    if agent_state_block:
        content_parts.append("\n--- AgentState snippet ---\n" + agent_state_block[:2000])

    return Evidence(
        goal=goal,
        found=found,
        content="\n".join(content_parts) if content_parts else None,
        location=str(path),
        rationale=(
            "AST inspection of src/state.py for Pydantic models, TypedDict AgentState, and reducers."
        ),
        confidence=0.85 if found else 0.45,
    )


def analyze_graph_structure(repo_dir: Path) -> Evidence:
    """
    AST-based inspection of graph orchestration:
    - locates StateGraph instantiation
    - inspects add_edge calls for basic fan-out/fan-in patterns
    """
    module, path = _load_ast_if_exists(repo_dir, "src/graph.py")

    goal = "Graph orchestration: StateGraph fan-out/fan-in"
    if module is None:
        return Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(path),
            rationale="src/graph.py not found or failed to parse as Python.",
            confidence=0.3,
        )

    add_edges = []
    cond_edges = 0
    has_stategraph = False

    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        source = ""

    for node in ast.walk(module):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_conditional_edges":
                cond_edges += 1
            if node.func.attr == "add_edge" and len(node.args) >= 2:
                try:
                    src = node.args[0].value  # type: ignore[attr-defined]
                    dst = node.args[1].value  # type: ignore[attr-defined]
                    add_edges.append(f"{src} -> {dst}")
                except Exception:
                    continue
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "StateGraph":
            has_stategraph = True

    found = has_stategraph and len(add_edges) > 0

    build_graph_block = None
    if source:
        try:
            module2 = ast.parse(source)
            for n in module2.body:
                if isinstance(n, ast.FunctionDef) and n.name == "build_graph":
                    build_graph_block = ast.get_source_segment(source, n)
                    break
        except Exception:
            build_graph_block = None

    content_parts: List[str] = []
    if add_edges:
        content_parts.append("Edges: " + "; ".join(add_edges[:80]))
    content_parts.append(f"Conditional edge calls: {cond_edges}")
    if build_graph_block:
        content_parts.append("\n--- build_graph snippet ---\n" + build_graph_block[:2500])

    return Evidence(
        goal=goal,
        found=found,
        content="\n".join(content_parts) if content_parts else None,
        location=str(path),
        rationale=f"AST inspection found StateGraph={has_stategraph}, edges={len(add_edges)}, conditional_edges_calls={cond_edges}.",
        confidence=0.85 if found else 0.45,
    )


def analyze_tool_safety(repo_dir: Path) -> Evidence:
    """
    Static inspection of src/tools/ for safe git tooling:
    - confirms use of tempfile.TemporaryDirectory / subprocess.run
    - flags raw os.system('git clone ...') usage
    """
    tools_dir = repo_dir / "src" / "tools"
    goal = "Safe tool engineering: sandboxed git tooling"

    if not tools_dir.exists():
        return Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(tools_dir),
            rationale="src/tools directory not found in cloned repository.",
            confidence=0.3,
        )

    has_tempdir = False
    has_os_system = False
    inspected_files: List[str] = []

    for py in tools_dir.glob("*.py"):
        inspected_files.append(py.name)
        try:
            source = py.read_text(encoding="utf-8")
        except Exception:
            continue
        try:
            module = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(module):
            # Detect tempfile.TemporaryDirectory usage by name.
            if isinstance(node, ast.Attribute) and node.attr == "TemporaryDirectory":
                has_tempdir = True
            if isinstance(node, ast.Name) and node.id == "TemporaryDirectory":
                has_tempdir = True

            # Detect os.system(...) calls structurally (avoid docstring false positives).
            if isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Attribute) and fn.attr == "system":
                    if isinstance(fn.value, ast.Name) and fn.value.id == "os":
                        has_os_system = True

    rationale_parts = []
    if has_tempdir:
        rationale_parts.append("Detected use of tempfile.TemporaryDirectory for sandboxing.")
    if has_os_system:
        rationale_parts.append("Detected raw os.system() calls, which may be unsafe.")
    if not rationale_parts:
        rationale_parts.append("No sandboxing or raw os.system usage detected by AST analysis.")

    return Evidence(
        goal=goal,
        found=has_tempdir and not has_os_system,
        content=None,
        location=str(tools_dir),
        rationale=f"{' '.join(rationale_parts)} Inspected: {', '.join(inspected_files) or '(none)'}",
        confidence=0.8 if has_tempdir and not has_os_system else 0.5,
    )


def analyze_structured_output_enforcement(repo_dir: Path) -> Evidence:
    """
    Text-based inspection of Judge nodes for structured output enforcement:
    - checks for .with_structured_output(...) or .bind_tools(...)
    """
    judges_path = repo_dir / "src" / "nodes" / "judges.py"
    goal = "Structured output enforcement for Judges"

    if not judges_path.exists():
        return Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(judges_path),
            rationale="src/nodes/judges.py not found in cloned repository.",
            confidence=0.3,
        )

    try:
        text = judges_path.read_text(encoding="utf-8")
    except Exception:
        return Evidence(
            goal=goal,
            found=False,
            content=None,
            location=str(judges_path),
            rationale="Failed to read src/nodes/judges.py for inspection.",
            confidence=0.3,
        )

    has_structured = ".with_structured_output" in text or ".bind_tools" in text

    return Evidence(
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


def list_repo_files(repo_dir: Path) -> Sequence[str]:
    files: List[str] = []
    for p in repo_dir.rglob("*"):
        if p.is_file():
            try:
                files.append(str(p.relative_to(repo_dir)).replace("\\", "/"))
            except Exception:
                continue
    return files


