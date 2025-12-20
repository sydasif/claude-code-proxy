# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Qwen Code Proxy - a lightweight, Dockerized middleware that allows you to use the official Claude Code CLI with the Qwen3-Coder-Plus backend (via Qwen Portal). The proxy acts as a translation layer, converting Anthropic API requests into OpenAI-compatible requests for the Qwen Portal.

## Architecture

The proxy leverages LiteLLM as an open-source AI gateway that serves as an OpenAI-compatible proxy server. The architecture consists of:

- **LiteLLM Proxy Server** - Runs inside a Docker container on port 3455
- **API Translation Layer** - Converts between Anthropic and OpenAI API formats
- **Credential Manager** - Securely accesses your Qwen OAuth credentials from `~/.qwen/oauth_creds.json`
- **Model Router** - Routes all Claude model requests to Qwen3-Coder-Plus

Request Flow: `Claude CLI → Local Proxy (3455) → LiteLLM Translation → Qwen Portal API → Response Back to CLI`

Core Files:
- `main.py` - Main application entry point with proxy runner logic
- `auth.py` - Handles credential retrieval and caching with thread-safe mechanisms
- `config.py` - Configuration management using Pydantic
- `config.yaml` - LiteLLM configuration for model routing and parameter dropping
- `Dockerfile` - Container definition for the proxy service
- `docker-compose.yml` - Docker orchestration with secure volume mounting for credentials

## Development Commands

### Running the Proxy
```bash
# Start the proxy in the background using Docker Compose
docker compose up -d

# View logs to confirm the proxy is running
docker compose logs -f

# Stop the proxy
docker compose down
```

### Using with Claude Code CLI
```bash
# Set environment variables to use the proxy
export ANTHROPIC_BASE_URL="http://127.0.0.1:3455"
```

### Building and Testing
```bash
# Rebuild the container after changes (uses uv for dependency management)
docker compose up -d --build

# Run with verbose logging
QWEN_LOG_LEVEL=DEBUG docker compose up

# Run the proxy directly with Python (for development)
uv run python main.py

# Run LiteLLM directly for debugging (bypassing the Python wrapper)
uv run litellm --config config.yaml --port 3455 --host 0.0.0.0
```

### Docker with uv (Dependency Management)
The Docker setup now uses uv for dependency management following best practices:

- **Multi-stage build**: Dependencies are installed in a builder stage with uv, then copied to the runtime stage
- **uv.lock integration**: Dependencies are installed directly from `pyproject.toml` and `uv.lock` (not requirements.txt)
- **Bytecode compilation**: Enabled for better runtime performance
- **Security**: Non-root user is used in the container
- **Optimization**: .dockerignore file excludes unnecessary files during build
- **Build optimization**: The .dockerignore file prevents unnecessary files (like .git, __pycache__, .venv, logs, etc.) from being copied into the Docker image, reducing build time and image size

```dockerfile
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

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=app:app /app/.venv ./.venv

# Activate virtual environment
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Copy all application files using .dockerignore to exclude unnecessary files
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Expose the port
EXPOSE 3455

# Run the proxy
CMD ["python", "main.py"]
```

### Development Workflow
1. Make changes to the Python files (main.py, auth.py, config.py)
2. Rebuild the container: `docker compose up -d --build` (uses uv for dependency management)
3. Restart the proxy: `docker compose restart`
4. Test with Claude CLI using the proxy endpoint

## Key Configuration

The proxy explicitly maps specific Claude models (sonnet, opus, haiku) to `qwen3-coder-plus` in `config.yaml`. The `drop_params: true` setting is critical as it removes Anthropic-specific parameters (like `thinking` or `betas`) that would cause errors with OpenAI/Qwen endpoints.

Credentials are securely accessed from `~/.qwen/oauth_creds.json` with thread-safe caching implemented in `auth.py`. The application includes retry logic with configurable maximum attempts and delay between retries, as well as graceful shutdown handling for clean process termination.

## Important Notes

- The proxy drops Anthropic-specific parameters to maintain compatibility with Qwen APIs
- Credentials are mounted as read-only volumes in the Docker container for security
- The proxy supports graceful shutdown and retry mechanisms with configurable attempts and delays
- All Claude model requests (Sonnet, Opus, etc.) are mapped to `qwen3-coder-plus`
- Configuration settings can be customized via environment variables prefixed with `QWEN_`
- **uv Integration**: The project now uses uv exclusively for dependency management in both development and Docker builds (requirements.txt has been removed in favor of pyproject.toml and uv.lock)
