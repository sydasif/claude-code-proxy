import os
import subprocess
import sys

from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# 2. Check if key exists
if not os.getenv("QWEN_API_KEY"):
    print("Error: QWEN_API_KEY not found in .env file")
    sys.exit(1)

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
