"""
Main module for the Qwen Code Proxy application.

This module contains the ProxyRunner class which manages the LiteLLM proxy process,
handles graceful shutdown, and implements retry logic for robust operation.
"""

import logging
import os
import signal
import subprocess
import sys
import time

from auth import get_api_key
from config import get_settings


def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration with the specified log level.

    Args:
        log_level: The logging level to use (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            Defaults to "INFO".
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


class ProxyRunner:
    """Manages the LiteLLM proxy process with graceful shutdown and retry logic.

    This class handles starting, stopping, and monitoring the LiteLLM proxy process,
    including signal handling for graceful shutdown and retry mechanisms for
    robust operation.

    Attributes:
        settings: Configuration settings for the proxy
        process: The subprocess instance running the LiteLLM proxy
        running: Boolean indicating if the proxy is currently running
        shutdown_requested: Boolean flag to track shutdown requests
    """

    def __init__(self, settings):
        """Initialize the ProxyRunner with the given settings.

        Args:
            settings: Configuration settings for the proxy
        """
        self.settings = settings
        self.process = None
        self.running = False
        self.shutdown_requested = False  # New flag to track shutdown requests

    def run_proxy(self):
        """Start the LiteLLM proxy process with proper error handling and graceful shutdown.

        This method initializes the LiteLLM proxy subprocess with the configured settings,
        sets up signal handlers for graceful shutdown, and manages the process lifecycle.
        It handles API key retrieval, environment setup, and process monitoring.

        The method will:
        1. Set up signal handlers for SIGINT and SIGTERM
        2. Retrieve the API key from the credentials file
        3. Prepare the environment with the API key
        4. Start the LiteLLM proxy subprocess
        5. Monitor the process and handle termination gracefully

        Raises:
            SystemExit: If the proxy process exits with a non-zero return code
                or if API key retrieval fails
        """
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # 1. Extract Key
        api_key = get_api_key()
        if not api_key:
            logging.error("Failed to retrieve API key")
            sys.exit(1)

        # 2. Prepare Environment for LiteLLM
        # We copy the current environment and add the key
        current_env = os.environ.copy()
        current_env[self.settings.api_key_env_var] = api_key

        # 3. Command to run LiteLLM Proxy
        cmd = [
            "litellm",
            "--config",
            self.settings.config_file,
            "--port",
            str(self.settings.port),
            "--host",
            self.settings.host,
        ]

        logging.info(
            f"🚀 Starting Qwen Proxy on {self.settings.host}:{self.settings.port}"
        )

        try:
            # Using Popen for better control over the process
            # The command is constructed from trusted configuration values only
            # and does not include any user input, making it safe from injection
            self.process = subprocess.Popen(  # noqa: S603
                cmd, env=current_env, stdout=sys.stdout, stderr=sys.stderr
            )
            self.running = True

            # Wait for the process to complete
            return_code = self.process.wait()

            if return_code != 0:
                logging.error(f"LiteLLM proxy exited with return code: {return_code}")
                sys.exit(return_code)
            else:
                logging.info("LiteLLM proxy exited normally")

        except subprocess.SubprocessError as e:
            logging.error(f"Subprocess error running LiteLLM proxy: {e}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error running LiteLLM proxy: {e}")
            sys.exit(1)
        finally:
            self.running = False
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(
                        timeout=5
                    )  # Wait up to 5 seconds for graceful termination
                except subprocess.TimeoutExpired:
                    logging.warning("Process did not terminate gracefully, killing it")
                    self.process.kill()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals (SIGINT, SIGTERM) gracefully.

        This method is called when the process receives a shutdown signal.
        It sets the shutdown flag, terminates the proxy process if running,
        and waits for graceful termination before allowing the process to exit.

        Args:
            signum: The signal number received (SIGINT or SIGTERM)
            frame: The current stack frame (unused)
        """
        logging.info(f"\nReceived signal {signum}, shutting down proxy...")
        self.shutdown_requested = True  # Set the shutdown flag
        self.running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(
                    timeout=5
                )  # Wait up to 5 seconds for graceful termination
            except subprocess.TimeoutExpired:
                logging.warning("Process did not terminate gracefully, killing it")
                self.process.kill()
        # Don't call sys.exit here to allow finally block to execute in run_proxy

    def run_with_retry(self):
        """Run the proxy process with retry logic for robust operation.

        This method attempts to run the proxy process up to max_retries times
        in case of failures. It handles different types of exceptions and
        provides appropriate logging and delays between retry attempts.
        The method respects shutdown requests and will terminate early if
        a shutdown signal is received.

        The retry logic handles:
        - SystemExit exceptions (normal and error exits)
        - KeyboardInterrupt (Ctrl+C)
        - Other exceptions with configurable delay between attempts

        Raises:
            Exception: If all retry attempts are exhausted and the proxy
                still fails to start/run properly
        """
        for attempt in range(self.settings.max_retries + 1):
            if self.shutdown_requested:  # Check if shutdown was requested
                return
            try:
                self.run_proxy()
                if self.shutdown_requested:  # Check again after run_proxy completes
                    return
                return  # Success, exit the method
            except SystemExit as e:
                if e.code == 0:
                    # Normal exit
                    return
                elif self.shutdown_requested:
                    # Shutdown requested during execution
                    return
                elif attempt < self.settings.max_retries:
                    logging.warning(
                        f"Proxy failed, attempt {attempt + 1}/{self.settings.max_retries}. "
                        f"Retrying in {self.settings.retry_delay}s..."
                    )
                    time.sleep(self.settings.retry_delay)
                else:
                    logging.error(
                        f"Proxy failed after {self.settings.max_retries} retries"
                    )
                    raise
            except KeyboardInterrupt:
                # Handle Ctrl+C explicitly
                logging.info("Keyboard interrupt received, shutting down...")
                return
            except Exception as e:
                if self.shutdown_requested:
                    return
                if attempt < self.settings.max_retries:
                    logging.warning(
                        f"Proxy failed with error: {e}, attempt {attempt + 1}/{self.settings.max_retries}. "
                        f"Retrying in {self.settings.retry_delay}s..."
                    )
                    time.sleep(self.settings.retry_delay)
                else:
                    logging.error(
                        f"Proxy failed after {self.settings.max_retries} retries: {e}"
                    )
                    raise


def main():
    """Main entry point for the Qwen Code Proxy application.

    This function initializes the application by loading settings,
    setting up logging, creating a ProxyRunner instance, and starting
    the proxy with retry logic. It serves as the primary entry point
    when the script is executed directly.
    """
    # Load settings
    settings = get_settings()

    # Setup logging with configured level
    setup_logging(settings.log_level)

    runner = ProxyRunner(settings)
    runner.run_with_retry()


if __name__ == "__main__":
    main()
