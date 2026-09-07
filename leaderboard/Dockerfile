# Build context is the repository root, not this directory: the image needs
# toolkit_core, which lives next to the service.
#   docker build -f leaderboard/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

COPY leaderboard/requirements.txt .
RUN  pip install --no-cache-dir -r requirements.txt

# Editable, so mounting ./toolkit_core over it during development is enough to
# pick up changes without a rebuild.
COPY toolkit_core /toolkit_core
RUN  pip install --no-cache-dir -e /toolkit_core

COPY leaderboard/ .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
