from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, PlainTextResponse

from src.graph import get_compiled_graph


load_dotenv()
app = FastAPI(title="The Automaton Auditor")
compiled_graph = get_compiled_graph()


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>The Automaton Auditor</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; background: #0f172a; color: #e5e7eb; display: flex; flex-direction: column; align-items: center; }}
    h1 {{ font-size: 1.9rem; margin-bottom: 0.5rem; }}
    h2 {{ font-size: 1.2rem; margin-top: 2rem; }}
    form {{ background: #020617; padding: 1.5rem; border-radius: 0.75rem; box-shadow: 0 10px 25px rgba(0,0,0,0.4); max-width: 720px; width: 100%; position: relative; }}
    label {{ display: block; margin-top: 1rem; font-weight: 600; }}
    input[type="text"] {{ width: 100%; padding: 0.5rem 0.75rem; border-radius: 0.5rem; border: 1px solid #1f2937; background: #020617; color: #e5e7eb; }}
    input[type="text"]:focus {{ outline: 2px solid #22c55e; border-color: transparent; }}
    button {{ margin-top: 1.5rem; padding: 0.6rem 1.4rem; border-radius: 9999px; border: none; background: linear-gradient(135deg, #22c55e, #16a34a); color: #020617; font-weight: 600; cursor: pointer; }}
    button:hover {{ filter: brightness(1.05); }}
    .hint {{ font-size: 0.8rem; color: #9ca3af; }}
    .shell {{ margin-top: 2rem; white-space: pre-wrap; background: #020617; border-radius: 0.75rem; padding: 1rem 1.25rem; border: 1px solid #1f2937; max-width: 960px; width: 100%; overflow-x: auto; }}
    .tag {{ display: inline-block; font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 9999px; background: #1e293b; color: #e5e7eb; margin-right: 0.5rem; }}
    .loader-backdrop {{ position: fixed; inset: 0; background: rgba(15,23,42,0.8); display: none; align-items: center; justify-content: center; z-index: 50; }}
    .loader {{ display: flex; flex-direction: column; align-items: center; gap: 0.75rem; }}
    .loader-spinner {{ width: 42px; height: 42px; border-radius: 9999px; border: 4px solid #1e293b; border-top-color: #22c55e; animation: spin 0.8s linear infinite; }}
    .loader-text {{ font-size: 0.9rem; color: #e5e7eb; }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  </style>
</head>
<body>
  <div id="loader" class="loader-backdrop">
    <div class="loader">
      <div class="loader-spinner"></div>
      <div class="loader-text">Running the Digital Courtroom&hellip;</div>
    </div>
  </div>
  <h1>The Automaton Auditor</h1>
  <p class="hint">Run the Digital Courtroom against a Week 2 repo + report.</p>
  <form id="audit-form" method="post" action="/">
    <label>Username (used in report filename)
      <input type="text" name="username" placeholder="e.g. bnobody47" required />
    </label>
    <span class="hint">This will be used to name the generated report file.</span>

    <label>GitHub repository URL
      <input type="text" name="repo_url" placeholder="https://github.com/user/week2-repo" />
    </label>
    <span class="hint">Optional but recommended. Leave empty to run PDF-only audit.</span>

    <label>PDF path or URL
      <input type="text" name="pdf_input" placeholder="reports/interim_report.pdf or https://..." />
    </label>
    <span class="hint">Local path relative to this project, or a direct URL to a PDF. Leave empty to run repo-only audit.</span>

    <button id="submit-btn" type="submit">Run Audit</button>
  </form>

  {report_section}

  <script>
    const form = document.getElementById('audit-form');
    const loader = document.getElementById('loader');
    const submitBtn = document.getElementById('submit-btn');

    if (form && loader && submitBtn) {{
      form.addEventListener('submit', function() {{
        loader.style.display = 'flex';
        submitBtn.disabled = true;
        submitBtn.textContent = 'Running...';
      }});
    }}
  </script>
</body>
</html>
"""


def _download_pdf_if_url(pdf_input: str) -> Optional[Path]:
    if pdf_input.startswith("http://") or pdf_input.startswith("https://"):
        try:
            resp = requests.get(pdf_input, timeout=30)
            resp.raise_for_status()
        except Exception:
            return None
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(resp.content)
        tmp.flush()
        tmp.close()
        return Path(tmp.name)
    return Path(pdf_input)


def _run_graph(repo_url: Optional[str], pdf_path: Optional[Path]) -> str:
    initial_state: Dict[str, Any] = {
        "repo_url": repo_url,
        "pdf_path": str(pdf_path) if pdf_path else None,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None,
        "final_report_markdown": "",
    }
    result = compiled_graph.invoke(initial_state)
    return result.get("final_report_markdown", "") or "(No report generated.)"


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(HTML_PAGE.format(report_section=""))


@app.post("/", response_class=HTMLResponse)
def run_web_audit(
    username: str = Form(...),
    repo_url: str = Form(""),
    pdf_input: str = Form(""),
) -> HTMLResponse:
    repo = repo_url.strip() or None
    pdf_path: Optional[Path] = None
    pdf_input = pdf_input.strip()
    if pdf_input:
        pdf_path = _download_pdf_if_url(pdf_input)
        if pdf_path is None or not pdf_path.exists():
            return HTMLResponse(
                HTML_PAGE.format(
                    report_section=(
                        '<div class="shell"><span class="tag">error</span>'
                        "Failed to fetch or locate PDF from the given path/URL.</div>"
                    )
                ),
                status_code=400,
            )

    if not repo and not pdf_path:
        return HTMLResponse(
            HTML_PAGE.format(
                report_section=(
                    '<div class="shell"><span class="tag">error</span>'
                    "Please provide at least a repo URL or a PDF path/URL.</div>"
                )
            ),
            status_code=400,
        )

    markdown = _run_graph(repo, pdf_path)

    # Persist the report under audit/report_onself_generated/ with username prefix.
    out_dir = Path("audit") / "report_onself_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"audit_report_{username}.md"
    out_path.write_text(markdown, encoding="utf-8")

    escaped = (
        markdown.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    report_html = (
        f'<h2>Latest Audit Report</h2>'
        f'<div class="shell"><span class="tag">report</span>'
        f'<span class="hint">Saved to {out_path.as_posix()}</span>\n\n'
        f"{escaped}</div>"
    )
    return HTMLResponse(HTML_PAGE.format(report_section=report_html))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

