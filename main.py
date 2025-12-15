import json
import os
import subprocess
import sys
from pathlib import Path


def get_api_key():
    # 1. Check for the path passed via Docker Environment variables
    # Default to local home dir if running outside Docker
    default_path = Path.expanduser(Path("~/.qwen/oauth_creds.json"))
    oauth_file = Path(os.environ.get("QWEN_CREDS_PATH", str(default_path)))

    print(f"🔍 Looking for credentials at: {oauth_file}")

    if oauth_file.exists():
        try:
            with oauth_file.open() as f:
                creds = json.load(f)
                token = creds.get('access_token')
                if token:
                    return token
                print("Error: 'access_token' is missing in the JSON file.")
        except Exception as e:
            print(f"Error reading oauth file: {e}")
    else:
        print(f"Error: Credentials file not found at {oauth_file}")

    return None


# 2. Extract Key
api_key = get_api_key()
if not api_key:
    sys.exit(1)

# 3. Prepare Environment for LiteLLM
# We copy the current environment and add the key
current_env = os.environ.copy()
current_env["QWEN_API_KEY"] = api_key

# 4. Command to run LiteLLM Proxy
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
