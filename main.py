import json
import os
import subprocess
import sys


# 1. Get API key only from oauth_creds.json
def get_api_key():
    # Read from ~/.qwen/oauth_creds.json
    oauth_file = os.path.expanduser("~/.qwen/oauth_creds.json")
    if os.path.exists(oauth_file):
        try:
            with open(oauth_file) as f:
                creds = json.load(f)
                return creds.get('access_token')
        except Exception as e:
            print(f"Error reading oauth file: {e}")
            return None

    print("Error: ~/.qwen/oauth_creds.json file not found")
    return None


# 2. Check if key exists
api_key = get_api_key()
if not api_key:
    print("Error: QWEN_API_KEY not found in ~/.qwen/oauth_creds.json")
    sys.exit(1)

# Set the API key in the environment for litellm to use
os.environ["QWEN_API_KEY"] = api_key

# 3. Command to run LiteLLM Proxy
# Using subprocess for better security and control
cmd = ["litellm", "--config", "config.yaml", "--port", "3455"]
# cmd = ["litellm", "--config", "config.yaml", "--port", "3455", "--detailed_debug"]

print("🚀 Starting Qwen Proxy on http://127.0.0.1:3455")
print("🔗 Target: portal.qwen.ai (Model: qwen3-coder-plus)")

try:
    # Safe to use subprocess.run as cmd is hardcoded with no user input
    subprocess.run(cmd, check=True)  # noqa: S603
except subprocess.CalledProcessError as e:
    print(f"Error running LiteLLM proxy: {e}")
    sys.exit(1)
except KeyboardInterrupt:
    print("\nProxy stopped by user")
    sys.exit(0)
