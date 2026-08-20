# syntax=docker/dockerfile:1
# Adapted from livekit/agents' examples/inference/Dockerfile.
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /usr/local/bin/uv

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/app" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
USER appuser

COPY pyproject.toml ./
RUN uv sync --no-cache
ENV PATH="/app/.venv/bin:${PATH}"

RUN python -m livekit.agents download-files

COPY . .

CMD ["python", "agent.py", "start"]
