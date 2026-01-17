# Qwen Code Proxy

A lightweight, Dockerized middleware that allows you to use the official **[Claude Code CLI](https://github.com/anthropics/claude-code)** and [Opencode](https://opencode.ai/) with the **Qwen3-Coder-Plus** backend (via Qwen Portal).

This proxy acts as a translation layer, converting API requests into OpenAI-compatible requests for the Qwen Portal, allowing you to use the advanced CLI workflow.

## 🚀 Features

* **Model Translation:** Seamlessly routes to **Qwen3-Coder-Plus**.
* **Protocol Adaptation:** Automatically handles API differences (strips unsupported parameters like `thinking` blocks using LiteLLM).
* **Credential Integration:** Securely mounts your existing local Qwen OAuth credentials (`~/.qwen/oauth_creds.json`) into the container.
* **Dockerized:** Runs in a lightweight Python container with no dependency pollution on your host machine.
* **API Compatibility:** Handles translation between Anthropic and OpenAI API formats transparently.

## 🏗️ Architecture

The Qwen Code Proxy leverages **LiteLLM**, an open-source AI gateway that serves as an OpenAI-compatible proxy server for calling 100+ LLMs through a unified interface. The architecture consists of:

### Core Components

1. **Python Application Wrapper** - Runs the main.py application that manages the LiteLLM proxy with retry and graceful shutdown mechanisms
2. **LiteLLM Proxy Server** - Runs inside a Docker container on port 3455
3. **API Translation Layer** - Converts between Anthropic and OpenAI API formats
4. **Credential Manager** - Securely accesses your Qwen OAuth credentials with thread-safe caching
5. **Model Router** - Routes all Claude model requests to Qwen3-Coder-Plus

### Request Flow

```text
Claude / Opencode CLI → Local Proxy (3455) → LiteLLM Translation → Qwen Portal API → Response Back to CLI
```

### Technical Details

* **Model Aliasing**: All model requests are mapped to `qwen3-coder-plus`
* **Parameter Filtering**: Anthropic-specific parameters like `thinking` and `betas` are automatically dropped
* **Response Standardization**: Qwen responses are formatted to match Anthropic API responses
* **Credential Caching**: API keys are cached with file modification monitoring to avoid unnecessary reads
* **Retry Mechanism**: Automatic retry logic with configurable attempts and delays
* **Graceful Shutdown**: Signal handling for proper process termination

## 📋 Prerequisites

1. **Docker & Docker Compose**: Installed and running.
2. **Claude Code CLI**: Installed on your host machine (Claude Console Auth).

    ```bash
    # claued-code CLI installation
    npm install -g @anthropic-ai/claude-code

    # opencode installation
    npm install -g opencode-ai
    ```

3. **Qwen Credentials**: You must be logged into the Qwen tools on your machine. The proxy expects to find your credentials at `~/.qwen/oauth_creds.json`.

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

To use the proxy, you need to configure the Claude CLI to point to your localhost instead of Anthropic's servers.

### For Claude CLI

Add the following to your Claude CLI configuration file (`~/.claude/settings.json`):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:3455"
  }
}
```

### For Opencode CLI

Add the following to your Opencode CLI configuration file (`~/.config/opencode/opencode.json`):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "litellm": {
      "name": "litellm",
      "options": {
        "baseURL": "http://127.0.0.1:3455",
      },
      "models": {
        "openai/qwen3-coder-plus": {
          "name": "openai/qwen3-coder-plus",
        }
      }
    }
  }
}
```

### Start a Session

Now, simply type `claude` to start a session using the Qwen backend.

## 🚨 Limitations & Considerations

* **Feature Parity**: Some Anthropic-specific features may not be fully supported by Qwen
* **Rate Limits**: Subject to Qwen Portal's rate limits and usage policies
* **Offline Access**: Requires internet connectivity to reach Qwen Portal API

## 🛠️ Development

For development purposes, you can run the proxy directly without Docker:

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

* **Q: How do I view the server logs?**
* A: Run `docker compose logs -f`. This is useful for debugging connection issues or verifying that requests are hitting the Qwen API.

* **Q: How do I update the project?**
* A: Pull the latest changes (if any), then rebuild the container:

```bash
docker compose up -d --build
```

* **Q: I'm getting API errors or authentication issues, how can I refresh my token?**
* A: If you encounter API errors, try refreshing your token by navigating to the project folder and running:

```bash
cd qwen-code-proxy  # Navigate to project directory
qwen "Hello" && docker compose restart
```

This will restart the proxy container and refresh the token from your credentials file. The proxy implements thread-safe caching with file modification monitoring, automatically picking up updated tokens when the credentials file changes.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

* [LiteLLM](https://litellm.ai/) for providing the API translation and proxy infrastructure
* Anthropic for the excellent Claude Code CLI
* Opencode for their open-source CLI tool
* Alibaba Cloud for the Qwen3-Coder-Plus model and API access
