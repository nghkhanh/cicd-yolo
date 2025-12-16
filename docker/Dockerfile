# syntax=docker/dockerfile:1

################################
# BUILDER-BASE
# Used to build deps + create our virtual environment
################################

FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy


RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy files first to avoid permission issues with bind mounts
COPY uv.lock README.md pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY ./src /app/src

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

################################
# RUNTIME
# Setup user, utilities and copy the virtual environment only
################################
FROM python:3.11-slim-bookworm AS runtime

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* 

RUN useradd -m -u 1000 user

WORKDIR /app

COPY --from=builder --chown=1000 /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

USER user

RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"


CMD ["uvicorn", "cicd_yolo.model:app", "--host", "0.0.0.0", "--port", "8001"]
