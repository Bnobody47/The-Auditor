## The Automaton Auditor – Week 2

This repository implements a **Digital Courtroom** using LangGraph: a multi-agent swarm
that audits a Week 2 repository (code + PDF report) and produces a structured audit
report.

### Environment setup

1. **Create and activate a virtual environment**

   Using `uv` (recommended):

   ```bash
   uv venv
   source .venv/bin/activate  # on Windows: .venv\Scripts\activate
   ```

   Or with standard Python:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # PowerShell on Windows
   ```

2. **Install dependencies**

   With `uv` (recommended, using `pyproject.toml` and `uv.lock`):

   ```bash
   uv sync
   ```

   Or with `pip` and `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment variables**

   - Copy `.env.example` to `.env` and fill in your LLM provider API keys
     (e.g., OpenAI, Gemini) and LangSmith credentials.
   - Ensure `LANGCHAIN_TRACING_V2=true` is set if you want LangSmith-style tracing.

### Project layout

- `src/state.py` – Pydantic models and `AgentState` TypedDict with reducers.
- `src/tools/repo_tools.py` – Sandboxed git tooling and AST/text-based forensic analysis.
- `src/tools/doc_tools.py` – PDF ingestion into chunks and theoretical-depth/host-accuracy analysis.
- `src/nodes/detectives.py` – RepoInvestigator, DocAnalyst, VisionInspector nodes operating on `AgentState`.
- `src/nodes/judges.py` – Placeholder Prosecutor/Defense/TechLead judge nodes (to be upgraded with LLMs).
- `src/nodes/justice.py` – Context builder, evidence aggregator, and Chief Justice synthesis node.
- `src/graph.py` – LangGraph `StateGraph` wiring Detectives and Judges with fan-out/fan-in and a basic error-handling branch.
- `rubric/week2_rubric.json` – Automaton Auditor rubric (Constitution).
- `reports/interim_report.pdf` – Textual interim architecture report for submission.
- `reports/stategraph_architecture.mmd` – Mermaid diagram of the StateGraph architecture.
- `pyproject.toml` – Primary dependency and project metadata (used by `uv`).
- `requirements.txt` – Flat dependency list for `pip` users.
- `uv.lock` – Lockfile for reproducible installs with `uv`.
- `.env.example` – Template for required environment variables.

### End-to-end run example

Assumptions:
- You have `git` and Python 3.10+ installed.
- You have a target Week 2 repo URL and a local PDF report path.

Steps:

1. Install dependencies (see above) and create `.env`.
2. From the project root, run:

   ```bash
   python -m src.cli \
     --repo-url "https://github.com/your-peer/week2-repo.git" \
     --pdf-path "path/to/report.pdf" \
     --output "audit/report_onpeer_generated/audit_report.md"
   ```

3. Open `audit/report_onpeer_generated/audit_report.md` to inspect the generated
   (currently partially placeholder) Digital Courtroom audit report.


