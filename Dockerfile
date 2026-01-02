# 1. Build Stage
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Install dependencies into a virtual environment
RUN uv sync --frozen --no-cache --no-dev

# 2. Runtime Stage
FROM python:3.12-slim-bookworm
WORKDIR /app

# Install curl for healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy the environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy Application Code
COPY engine.py main_ui.py .env ./

# MLOps: Copy the pre-indexed Vector DB so the container starts instantly
# (Ensure you have committed data/chroma_db or generated it locally first)
COPY data/ ./data/

# Expose Streamlit Port
EXPOSE 8501

# Healthcheck to ensure UI is up
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the App
ENTRYPOINT ["streamlit", "run", "main_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]