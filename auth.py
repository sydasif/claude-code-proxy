"""
Authentication module for the Qwen Code Proxy application.

This module handles secure API key retrieval and caching with thread-safe mechanisms.
It reads credentials from the user's OAuth credentials file and provides caching
to avoid repeated file I/O operations.
"""

import json
import logging
import os
import threading
from pathlib import Path


class TokenManager:
    """Thread-safe token manager with caching and file modification tracking.

    This class manages the retrieval and caching of API tokens from the credentials file.
    It implements thread-safe access to cached tokens and checks for file modifications
    to ensure the token is always up-to-date. The class uses a lock to prevent race
    conditions when accessing the cache from multiple threads.

    Attributes:
        _cached_token: The currently cached API token string, or None if not cached
        _last_modified_time: The timestamp of the last file modification that was cached
        _cache_lock: A threading lock for thread-safe access to the cache
    """

    def __init__(self):
        """Initialize the TokenManager with empty cache and a thread lock.

        Sets up the initial state with no cached token, zero modification time,
        and creates a threading lock for thread-safe operations.
        """
        self._cached_token: str | None = None
        self._last_modified_time: float = 0
        self._cache_lock = threading.Lock()

    def get_api_key(self) -> str | None:
        """Retrieve the API key from the credentials file with thread-safe caching.

        This method implements a smart caching mechanism that checks if the credentials
        file has been modified since the last read. If the file hasn't changed, it
        returns the cached token to avoid unnecessary file I/O. If the file has been
        modified or no token is cached, it reads the file, validates the token format,
        updates the cache, and returns the token.

        The method handles various error conditions including:
        - Missing credentials file
        - Invalid JSON format in the credentials file
        - Missing 'access_token' field in the JSON
        - Invalid token format (empty or non-string values)
        - Permission errors when accessing the file

        The path to the credentials file is determined by the QWEN_CREDS_PATH environment
        variable, or defaults to ~/.qwen/oauth_creds.json if not set.

        Returns:
            Optional[str]: The API token string if successfully retrieved and validated,
                None if any error occurs during the process
        """
        # Check for the path passed via Docker Environment variables
        # Default to local home dir if running outside Docker
        default_path = Path.expanduser(Path("~/.qwen/oauth_creds.json"))
        oauth_file = Path(os.environ.get("QWEN_CREDS_PATH", str(default_path)))

        # Change to debug level to reduce log noise
        logging.debug(f"🔍 Looking for credentials at: {oauth_file}")

        if not oauth_file.exists():
            logging.error(f"Error: Credentials file not found at {oauth_file}")
            return None

        # Use lock for thread-safe access to cache
        with self._cache_lock:
            # Check if file has been modified since last read
            try:
                current_modified_time = oauth_file.stat().st_mtime
                if (
                    self._cached_token is not None
                    and current_modified_time <= self._last_modified_time
                ):
                    # Return cached token if file hasn't changed
                    return self._cached_token

                # File has been modified or token not cached, read it
                with oauth_file.open("r") as f:
                    creds = json.load(f)
                    token = creds.get("access_token")

                if not token:
                    logging.error("Error: 'access_token' is missing in the JSON file.")
                    return None

                # Validate token format (basic check)
                if not isinstance(token, str) or len(token.strip()) == 0:
                    logging.error("Error: Invalid token format in credentials file.")
                    return None

                # Update cache
                self._cached_token = token
                self._last_modified_time = current_modified_time

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


# Global instance
_token_manager = TokenManager()


def get_api_key() -> str | None:
    """Public interface for getting API key from the global token manager.

    This function provides access to the API key through the global TokenManager
    instance, which handles all the complexity of file reading, caching, and
    thread safety. It's the main entry point for other modules to retrieve
    the API key without directly interacting with the TokenManager class.

    Returns:
        str | None: The API token string if successfully retrieved from the
            credentials file, None if any error occurs during the process
    """
    return _token_manager.get_api_key()

