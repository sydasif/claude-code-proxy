import json
import os
import time
from pathlib import Path
import logging
from typing import Optional
import threading


# Global cache for the API key
_cached_token = None
_last_modified_time = 0
_cache_lock = threading.Lock()


def get_api_key() -> Optional[str]:
    """
    Retrieve the API key from the credentials file with thread-safe caching.
    Returns the cached token if file hasn't changed, otherwise reads the file.
    """
    global _cached_token, _last_modified_time

    # 1. Check for the path passed via Docker Environment variables
    # Default to local home dir if running outside Docker
    default_path = Path.expanduser(Path("~/.qwen/oauth_creds.json"))
    oauth_file = Path(os.environ.get("QWEN_CREDS_PATH", str(default_path)))

    logging.info(f"🔍 Looking for credentials at: {oauth_file}")

    if not oauth_file.exists():
        logging.error(f"Error: Credentials file not found at {oauth_file}")
        return None

    # Use lock for thread-safe access to cache
    with _cache_lock:
        # Check if file has been modified since last read
        try:
            current_modified_time = oauth_file.stat().st_mtime
            if (_cached_token is not None and
                current_modified_time <= _last_modified_time):
                # Return cached token if file hasn't changed
                return _cached_token

            # File has been modified or token not cached, read it
            with oauth_file.open('r') as f:
                creds = json.load(f)
                token = creds.get('access_token')

                if not token:
                    logging.error("Error: 'access_token' is missing in the JSON file.")
                    return None

                # Validate token format (basic check)
                if not isinstance(token, str) or len(token.strip()) == 0:
                    logging.error("Error: Invalid token format in credentials file.")
                    return None

                # Update cache
                _cached_token = token
                _last_modified_time = current_modified_time

                logging.info("Successfully loaded and cached API key")
                return token

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON from oauth file: {e}")
            return None
        except PermissionError:
            logging.error(f"Permission denied accessing credentials file: {oauth_file}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error reading oauth file: {e}")
            return None
