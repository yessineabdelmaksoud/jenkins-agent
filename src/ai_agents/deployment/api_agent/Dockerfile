# Build from the repository root (the build context must contain pyproject.toml and src/):
#   docker build -f src/ai_agents/deployment/api_agent/Dockerfile -t jenkins-agent .
#   docker run --env-file .env -p 8000:8000 jenkins-agent
# Secrets are passed at run time; .env is never copied into the image (see .dockerignore).
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install Poetry and the runtime dependencies only (poetry.lock needs Poetry 2.x).
# --no-root: the project itself is used from /app/src via PYTHONPATH.
RUN pip install --no-cache-dir "poetry>=2.1,<3" && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-root --no-interaction --no-ansi && \
    rm -rf /root/.cache/pypoetry

# Copy source code
COPY src/ ./src/

# Set Python path; per-job retry counters live here (mount a volume to keep them)
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    JENKINS_AGENT_STATE_DIR=/app/.jenkins_agent

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the API server
CMD ["python", "src/ai_agents/deployment/api_agent/start_api.py"]
