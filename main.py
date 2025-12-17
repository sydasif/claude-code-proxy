import os
import subprocess
import sys

from auth import get_api_key


def run_proxy():
    # 1. Extract Key
    api_key = get_api_key()
    if not api_key:
        sys.exit(1)

    # 2. Prepare Environment for LiteLLM
    # We copy the current environment and add the key
    current_env = os.environ.copy()
    current_env["QWEN_API_KEY"] = api_key

    # 3. Command to run LiteLLM Proxy
    cmd = ["litellm", "--config", "config.yaml", "--port", "3455"]

    print("🚀 Starting Qwen Proxy on http://0.0.0.0:3455")

    try:
        # We pass 'env=current_env' explicitly
        # The command is hardcoded and doesn't accept untrusted input
        result = subprocess.run(cmd, check=True, env=current_env)  # noqa: S603
    except subprocess.CalledProcessError as e:
        print(f"Error running LiteLLM proxy: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nProxy stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    run_proxy()
