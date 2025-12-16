# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Qwen Code Proxy is a Dockerized middleware that acts as a translation layer between the Claude Code CLI and the Qwen3-Coder-Plus backend. It allows users to leverage the Claude Code CLI experience while using Qwen's models instead of consuming Anthropic API credits.

## Architecture

The system consists of:

- **main.py**: Entry point that reads Qwen OAuth credentials and starts the LiteLLM proxy
- **config.yaml**: LiteLLM configuration that routes all Claude model requests to Qwen3-Coder-Plus
- **Dockerfile**: Creates a Python container with LiteLLM dependencies
- **docker-compose.yml**: Orchestrates the container setup with secure credential mounting

The request flow: Claude CLI → Local Proxy (port 3455) → LiteLLM Translation → Qwen Portal API → Response Back to CLI

## Development Commands

### Running the Proxy

```bash
# Start the proxy service
docker compose up -d

# View proxy logs
docker compose logs -f qwen-proxy

# Stop the proxy service
docker compose down
```

### Development

```bash
# Rebuild and start the proxy service
docker compose up -d --build

# Access the container shell
docker exec -it qwen-proxy bash
```

### Testing

To test the proxy functionality:

1. Start the proxy with `docker compose up -d`
2. Set environment variables:

   ```bash
   export ANTHROPIC_BASE_URL="http://127.0.0.1:3455"
   export ANTHROPIC_API_KEY="sk-local-proxy-key"
   ```

3. Run Claude CLI commands to verify the proxy is working

## Key Configuration

- **Port**: The proxy runs on port 3455
- **Authentication**: Uses a master key `"sk-local-proxy-key"` for proxy access
- **Model Routing**: All Claude models are mapped to `openai/qwen3-coder-plus` via wildcard
- **Credential Path**: Expects Qwen credentials at `~/.qwen/oauth_creds.json`
- **Parameter Filtering**: `drop_params: true` removes Anthropic-specific parameters for Qwen compatibility

## Security Considerations

- The proxy mounts the `~/.qwen` directory as read-only for credential access
- Uses LiteLLM's parameter dropping feature to ensure API compatibility
- The master key is hardcoded in config.yaml and should be changed for production use
- All model requests are routed to the same Qwen3-Coder-Plus model
