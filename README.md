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

   With `uv` (using `pyproject.toml`):

   ```bash
   uv sync
   ```

   Or with `pip` and `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment variables**

   - Create a `.env` file (not committed) with your LLM provider API keys
     (e.g., OpenAI, Gemini).
   - Ensure `LANGCHAIN_TRACING_V2=true` is set if you want LangSmith-style tracing.
   - See `.env.example` for the full list of expected variables.

### Project layout (work in progress)

 - `src/state.py` – Pydantic models and `AgentState` TypedDict with reducers.
 - `src/tools/repo_tools.py` – Sandboxed git tooling and placeholders for AST-based analysis.
 - `src/tools/doc_tools.py` – PDF/RAG-lite tooling scaffolding.
 - `src/nodes/detectives.py` – RepoInvestigator, DocAnalyst, VisionInspector nodes.
 - `src/graph.py` – LangGraph `StateGraph` wiring Detectives (and placeholder Judges/Chief Justice).
 - `rubric/week2_rubric.json` – Automaton Auditor rubric (Constitution).
 - `reports/interim_report.pdf` – Textual interim architecture report for submission.

To run the full (placeholder) swarm end-to-end against a target repo and PDF:

```bash
python -m src.cli \
  --repo-url "https://github.com/your-peer/week2-repo.git" \
  --pdf-path "path/to/report.pdf"
```

