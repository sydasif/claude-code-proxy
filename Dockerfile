# Multi-stage build
# Stage 1: Install dependencies with uv
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim as builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --locked --no-dev --compile-bytecode

# Stage 2: Runtime
FROM python:3.12-slim

# Install minimal runtime dependencies and create user
RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash --uid 1000 app

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=app:app /app/.venv ./.venv

# Activate virtual environment
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random

# Copy all application files using .dockerignore to exclude unnecessary files
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Expose the port
EXPOSE 3455

# Use dumb-init to handle signals properly and run the proxy
ENTRYPOINT ["dumb-init", "--"]
CMD ["python", "main.py"]