import json
import os
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
