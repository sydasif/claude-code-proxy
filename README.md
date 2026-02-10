# Qwen Code Proxy

A lightweight, Dockerized middleware that lets you use the official **[Claude Code CLI](https://github.com/anthropics/claude-code)** and **[Opencode](https://opencode.ai/)** with the **Qwen3-Coder-Plus** backend (via _Qwen Portal_).

## 🚀 Features

- **Model Translation:** Seamlessly routes to **Qwen3-Coder-Plus**.
- **Credential Integration:** Securely mounts your existing local Qwen OAuth credentials (`~/.qwen/oauth_creds.json`) into the container.
- **Dockerized:** Runs in a lightweight Python container with no dependency pollution on your host machine.

## 🏗️ Architecture

The Qwen Code Proxy leverages **LiteLLM**, an open-source AI gateway that provides a unified proxy interface for 100+ LLMs.

### Core Components

1. **Python Application Wrapper** - Runs `main.py` and manages the LiteLLM proxy with retry logic and graceful shutdown
2. **LiteLLM Proxy Server** - Runs inside a Docker container on port `3455`
3. **Credential Manager** - Securely accesses Qwen OAuth credentials with thread-safe caching

### Request Flow

```bash
`claude` / `opencode` → Local Proxy (`3455`) → LiteLLM Translation → Qwen Portal API → Response Back to CLI
```

### Technical Details

- **Parameter Filtering**: Anthropic-specific parameters like `thinking` and `betas` are automatically dropped
- **Credential Caching**: API keys are cached with file modification monitoring to avoid unnecessary reads
- **Retry Mechanism**: Automatic retries with configurable attempts and delays
- **Graceful Shutdown**: Signal handling for clean process termination

## 📋 Prerequisites

1. **Docker & Docker Compose**: Installed and running.
2. **Claude Code CLI**: Installed on your host machine (_Claude Console Auth_).
3. **Opencode CLI**: Installed on your host machine (_Zen Auth_).

```bash
# claude-code CLI installation
npm install -g @anthropic-ai/claude-code

# opencode installation
npm install -g opencode-ai
```

**Qwen Credentials**: You must be logged into the Qwen CLI on your machine.

## 🛠️ Installation & Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd qwen-code-proxy
   ```

2. **Start the Proxy:**
   Run the Docker container in the background. This will build the image and start the LiteLLM proxy on port `3455`.

   ```bash
   docker compose up -d
   ```

3. **Verify Status:**
   Ensure the container is running and listening:

   ```bash
   docker compose logs -f
   ```

   You should see `🚀 Starting Qwen Proxy on http://0.0.0.0:3455`.

## 💻 Usage

To use the proxy, configure the Claude CLI to point to localhost instead of Anthropic's servers.

### For Claude CLI

Add the following to your Claude CLI configuration file (`~/.claude/settings.json`):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:3455"
  }
}
```

> When you run `claude`, it will ask you to log in. Use console auth.

### For Opencode CLI

Add the following to your Opencode CLI configuration file (`~/.config/opencode/opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "litellm": {
      "name": "litellm",
      "options": {
        "baseURL": "http://127.0.0.1:3455"
      },
      "models": {
        "openai/qwen3-coder-plus": {
          "name": "openai/qwen3-coder-plus"
        }
      }
    }
  }
}
```

> When you run `opencode`, it will ask you to log in. Use Zen auth.  
> After login, use `/connect`, select litellm, and enter a dummy API key (`sk-xxx`) to connect.

## 🚨 Limitations & Considerations

- **Feature Parity**: Some Anthropic-specific features may not be fully supported by Qwen
- **Rate Limits**: Subject to Qwen Portal's rate limits and usage policies
- **Offline Access**: Requires internet connectivity to reach Qwen Portal API

## 🛠️ Development

For development, you can run the proxy directly without Docker:

```bash
# Install dependencies with uv
uv sync

# Run the proxy directly with Python
uv run python main.py

# Run with custom configuration via environment variables
QWEN_LOG_LEVEL=DEBUG uv run python main.py
```

This approach is useful for debugging and development, bypassing the Docker container for faster iteration cycles.

## ❓ FAQ

- **Q: How do I view the server logs?**  
  A: Run `docker compose logs -f`. This is useful for debugging connection issues or verifying that requests are hitting the Qwen API.

- **Q: How do I update the project?**  
  A: Pull the latest changes (if any), then rebuild the container:

```bash
docker compose up -d --build
```

- **Q: I'm getting API errors or authentication issues. How can I refresh my token?**  
  A: If you encounter API errors, refresh your token by navigating to the project folder and running:

```bash
cd qwen-code-proxy  # Navigate to project directory
qwen "Hello" && docker compose restart
```

This restarts the proxy container and refreshes the token from your credentials file. The proxy uses thread-safe caching with file modification monitoring, so it automatically picks up updated tokens when the credentials file changes.

## 📄 License

Only use for personal and non-commercial purposes. Do not use for any illegal or unauthorized purpose.

## 🙏 Acknowledgments

- [LiteLLM](https://litellm.ai/) for providing the API translation and proxy infrastructure
- Anthropic for the excellent Claude Code CLI
- Opencode for their open-source CLI tool
- Alibaba Cloud for the Qwen3-Coder-Plus model and API access
