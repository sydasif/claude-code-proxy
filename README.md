# Qwen Code Proxy

A lightweight, Dockerized middleware that allows you to use the official **[Claude Code CLI](https://github.com/anthropics/claude-code)** with the **Qwen3-Coder-Plus** backend (via Qwen Portal).

This proxy acts as a translation layer, converting Anthropic API requests into OpenAI-compatible requests for the Qwen Portal, allowing you to use the advanced Claude CLI workflow without consuming Anthropic API credits.

## 🚀 Features

* **Model Translation:** Seamlessly routes Claude Code requests (Sonnet, Opus, etc.) to **Qwen3-Coder-Plus**.
* **Protocol Adaptation:** Automatically handles API differences (strips unsupported parameters like `thinking` blocks using LiteLLM).
* **Credential Integration:** Securely mounts your existing local Qwen OAuth credentials (`~/.qwen/oauth_creds.json`) into the container.
* **Dockerized:** Runs in a lightweight Python container with no dependency pollution on your host machine.
* **API Compatibility:** Handles translation between Anthropic and OpenAI API formats transparently.
* **Parameter Filtering:** Removes Anthropic-specific parameters that would cause errors with Qwen endpoints.

## 🏗️ Architecture

The Qwen Code Proxy leverages **LiteLLM**, an open-source AI gateway that serves as an OpenAI-compatible proxy server for calling 100+ LLMs through a unified interface. The architecture consists of:

### Core Components

1. **Python Application Wrapper** - Runs the main.py application that manages the LiteLLM proxy with retry and graceful shutdown mechanisms
2. **LiteLLM Proxy Server** - Runs inside a Docker container on port 3455
3. **API Translation Layer** - Converts between Anthropic and OpenAI API formats
4. **Credential Manager** - Securely accesses your Qwen OAuth credentials with thread-safe caching
5. **Model Router** - Routes all Claude model requests to Qwen3-Coder-Plus

### Request Flow

```
Claude CLI → Local Proxy (3455) → LiteLLM Translation → Qwen Portal API → Response Back to CLI
```

### Technical Details

* **Model Aliasing**: All model requests (Sonnet, Opus, etc.) are mapped to `qwen3-coder-plus`

* **Parameter Filtering**: Anthropic-specific parameters like `thinking` and `betas` are automatically dropped
* **Response Standardization**: Qwen responses are formatted to match Anthropic API responses
* **Credential Caching**: API keys are cached with file modification monitoring to avoid unnecessary reads
* **Retry Mechanism**: Automatic retry logic with configurable attempts and delays
* **Graceful Shutdown**: Signal handling for proper process termination

## 📋 Prerequisites

1. **Docker & Docker Compose**: Installed and running.
2. **Claude Code CLI**: Installed on your host machine (Claude Console Auth).

    ```bash
    npm install -g @anthropic-ai/claude-code
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

### Option 1: Temporary Session (Current Terminal)

Run these commands in your terminal before starting Claude:

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:3455"
```

### Option 2: Permanent Alias (Recommended)

Add to your shell configuration (`~/.bashrc` or `~/.zshrc`) to easily toggle between the real API and the Qwen proxy.

```bash
# Add to .bashrc or .zshrc
export ANTHROPIC_BASE_URL="http://127.0.0.1:3455"
```

Now, simply type `claude` to start a session using the Qwen backend.

## ⚙️ Configuration

The routing logic is defined in `config.yaml`, while application settings can be configured through environment variables.

### Application Settings (Environment Variables)

The following environment variables can be used to configure the proxy application:

* `QWEN_CREDS_PATH` - Path to the Qwen credentials file (default: `~/.qwen/oauth_creds.json`)
* `QWEN_LOG_LEVEL` - Logging level (default: `INFO`)
* `QWEN_MAX_RETRIES` - Maximum number of retry attempts (default: `3`)
* `QWEN_RETRY_DELAY` - Delay between retries in seconds (default: `5.0`)

### Default Routing

By default, the proxy uses a wildcard (`*`) strategy. This means **any** model requested by the Claude CLI (whether it asks for `claude-3-5-sonnet` or `claude-opus`) will be routed to `qwen3-coder-plus`.

```yaml
model_list:
  - model_name: "*"
    litellm_params:
      model: openai/qwen3-coder-plus
      api_base: "https://portal.qwen.ai/v1"
      api_key: os.environ/QWEN_API_KEY

litellm_settings:
  drop_params: true  # Essential for API compatibility
```

### Parameter Dropping

The setting `drop_params: true` is critical. The Claude CLI sends Anthropic-specific parameters (like `thinking` or `betas`) that cause errors with standard OpenAI/Qwen endpoints. This setting automatically removes them before forwarding the request.

## 🔐 Security

* **Credential Isolation**: Qwen credentials are mounted as read-only volumes into the container
* **Network Isolation**: The proxy runs locally and only accepts connections from the host
* **Parameter Sanitization**: Unsupported parameters are filtered out before reaching the Qwen API
* **Access Control**: Master key authentication ensures only authorized requests are processed

## 🚨 Limitations & Considerations

* **Model Identity**: Claude may report itself as "Claude Opus" due to system prompts injected by the CLI, but responses come from Qwen3-Coder-Plus
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

* **Q: Claude says "I am powered by Claude Opus" in the chat.**
* A: The Claude CLI injects a system prompt instructing the model to identify itself as Claude. Since Qwen3-Coder-Plus is highly capable of following instructions, it adheres to this persona. You are still using the Qwen backend.

* **Q: How do I view the server logs?**
* A: Run `docker compose logs -f qwen-proxy`. This is useful for debugging connection issues or verifying that requests are hitting the Qwen API.

* **Q: How do I update the project?**
* A: Pull the latest changes (if any), then rebuild the container:

```bash
docker compose up -d --build
```

* **Q: Why does the proxy need to drop certain parameters?**
* A: Anthropic-specific parameters like `thinking` blocks or `betas` are not supported by the Qwen API and would cause errors if passed through.

* **Q: I'm getting API errors or authentication issues, how can I refresh my token?**
* A: If you encounter API errors, try refreshing your token by navigating to the project folder and running:

```bash
cd /path/to/qwen-code-proxy  # Navigate to project directory
qwen "Hello" && docker compose restart
```

This will restart the proxy container and refresh the token from your credentials file. The proxy monitors the credentials file for changes and will automatically pick up updated tokens.

## 🤝 Contributing

Contributions are welcome! Feel free to submit issues, feature requests, or pull requests to improve the proxy functionality.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

* [LiteLLM](https://litellm.ai/) for providing the API translation and proxy infrastructure
* Anthropic for the excellent Claude Code CLI
* Alibaba Cloud for the Qwen3-Coder-Plus model and API access
