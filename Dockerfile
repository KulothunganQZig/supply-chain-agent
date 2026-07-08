# Supply Chain Visibility Agent — container image for Azure Container Apps.
#
# Serves the FastAPI app (src/api.py) on :8000. SQLite is generated + seeded at
# build time and baked in, so the container runs statelessly (the "run the
# pipeline" demo needs no external DB). Azure SQL is a later migration step.
#
# LLM path: in Azure the app authenticates as the Container App's Managed
# Identity (DefaultAzureCredential); no key is baked in. Run locally without
# Azure creds and the LLM hooks fall back to their deterministic path.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies + the project. Source is copied before install (so the
# declared packages exist for setuptools); a code change re-runs the install,
# acceptable for this image's cadence.
COPY pyproject.toml ./
COPY src/ ./src/
COPY mock_data/ ./mock_data/
RUN pip install .

# Generate mock JSON and seed the baked-in SQLite database at build time.
RUN python -m mock_data.generate && python -m mock_data.seed_db

EXPOSE 8000

# Honor $PORT if Container Apps injects one; default 8000.
CMD ["sh", "-c", "uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
