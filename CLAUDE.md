# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

The Qwen Code Proxy is a lightweight, Dockerized middleware that allows you to use the official Claude Code CLI and Opencode with the Qwen3-Coder-Plus backend (via Qwen Portal). The proxy acts as a translation layer, converting Anthropic API requests into OpenAI-compatible requests for the Qwen Portal.

## Architecture

The Qwen Code Proxy leverages LiteLLM as an open-source AI gateway that serves as an OpenAI-compatible proxy server. The architecture consists of:

1. **Python Application Wrapper** - Runs the main.py application that manages the LiteLLM proxy with retry and graceful shutdown mechanisms
2. **LiteLLM Proxy Server** - Runs inside a Docker container on port 3455
3. **API Translation Layer** - Converts between Anthropic and OpenAI API formats
4. **Credential Manager** - Securely accesses your Qwen OAuth credentials with thread-safe caching
5. **Model Router** - Routes all Claude model requests to Qwen3-Coder-Plus

Request Flow: `Claude / Opencode CLI → Local Proxy (3455) → LiteLLM Translation → Qwen Portal API → Response Back to CLI`

Key Components:
- **main.py**: Contains the ProxyRunner class which manages the LiteLLM proxy process, handles graceful shutdown, and implements retry logic
- **auth.py**: Manages secure API key retrieval and caching with thread-safe mechanisms
- **config.py**: Configuration management using Pydantic with environment variable support
- **config.yaml**: LiteLLM configuration for model routing and parameter handling
- **Dockerfile**: Multi-stage build using uv for dependency management
- **docker-compose.yml**: Docker orchestration with secure volume mounting for credentials

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

### Development Workflow

```bash
# Install dependencies with uv
uv sync

# Run the proxy directly with Python (for development)
uv run python main.py

# Run with custom configuration via environment variables
QWEN_LOG_LEVEL=DEBUG uv run python main.py

# Run LiteLLM directly for debugging (bypassing the Python wrapper)
uv run litellm --config config.yaml --port 3455 --host 0.0.0.0
```

### Building and Testing

```bash
# Rebuild the container after changes (uses uv for dependency management)
docker compose up -d --build

# Run with verbose logging
QWEN_LOG_LEVEL=DEBUG docker compose up

# Refresh credentials and restart
cd qwen-code-proxy  # Navigate to project directory
qwen "Hello" && docker compose restart
```

## Configuration

The proxy uses the following configuration options, which can be overridden via environment variables prefixed with `QWEN_`:

- `QWEN_CONFIG_FILE`: Path to the LiteLLM config file (default: config.yaml)
- `QWEN_PORT`: Port for the proxy to listen on (default: 3455)
- `QWEN_HOST`: Host for the proxy to bind to (default: 127.0.0.1)
- `QWEN_CREDS_PATH`: Path to the credentials file (default: ~/.qwen/oauth_creds.json)
- `QWEN_API_KEY_ENV_VAR`: Environment variable name for API key (default: QWEN_API_KEY)
- `QWEN_MAX_RETRIES`: Maximum number of retry attempts (default: 3)
- `QWEN_RETRY_DELAY`: Delay between retries in seconds (default: 5.0)
- `QWEN_LOG_LEVEL`: Logging level (default: INFO)

The config.yaml file maps all Claude model requests (claude-*) to the qwen3-coder-plus model and uses `drop_params: true` to remove Anthropic-specific parameters that aren't supported by the OpenAI-compatible Qwen API.

## Security

- Credentials are securely accessed from `~/.qwen/oauth_creds.json` with thread-safe caching
- The Docker container mounts credentials as read-only volumes for security
- The application runs as a non-root user inside the container
- API keys are stored in environment variables rather than configuration files