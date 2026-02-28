# The Automaton Auditor – containerized runtime
# Build: docker build -t automaton-auditor .
# Run:   docker run -p 8000:8000 --env-file .env automaton-auditor

FROM python:3.11-slim

# Git required for repo cloning
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY rubric/ ./rubric/
COPY main.py ./

# Optional: include reports/ and scripts/ for PDF/audit paths
COPY reports/ ./reports/
COPY scripts/ ./scripts/

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Web UI by default; override to run CLI, e.g.:
#   docker run --rm --env-file .env automaton-auditor python -m src.cli --repo-url "..." --output /tmp/audit.md
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
