import os
import subprocess
import sys
import signal
import logging
import time
from typing import Optional

from auth import get_api_key
from config import get_settings


def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


class ProxyRunner:
    def __init__(self, settings):
        self.settings = settings
        self.process = None
        self.running = False

    def run_proxy(self):
        """Start the LiteLLM proxy with proper error handling and graceful shutdown."""
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
            "--config", self.settings.config_file,
            "--port", str(self.settings.port),
            "--host", self.settings.host
        ]

        logging.info(f"🚀 Starting Qwen Proxy on {self.settings.host}:{self.settings.port}")

        try:
            # Using Popen for better control over the process
            self.process = subprocess.Popen(
                cmd,
                env=current_env,
                stdout=sys.stdout,
                stderr=sys.stderr
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
                    self.process.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
                except subprocess.TimeoutExpired:
                    logging.warning("Process did not terminate gracefully, killing it")
                    self.process.kill()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logging.info(f"\nReceived signal {signum}, shutting down proxy...")
        self.running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
            except subprocess.TimeoutExpired:
                logging.warning("Process did not terminate gracefully, killing it")
                self.process.kill()
        # Don't call sys.exit here to allow finally block to execute in run_proxy

    def run_with_retry(self):
        """Run the proxy with retry logic."""
        for attempt in range(self.settings.max_retries + 1):
            try:
                self.run_proxy()
                return  # Success, exit the method
            except SystemExit as e:
                if e.code == 0:
                    # Normal exit
                    return
                elif attempt < self.settings.max_retries:
                    logging.warning(f"Proxy failed, attempt {attempt + 1}/{self.settings.max_retries}. Retrying in {self.settings.retry_delay}s...")
                    time.sleep(self.settings.retry_delay)
                else:
                    logging.error(f"Proxy failed after {self.settings.max_retries} retries")
                    raise
            except Exception as e:
                # Handle other exceptions that might occur during proxy run
                if attempt < self.settings.max_retries:
                    logging.warning(f"Proxy failed with error: {e}, attempt {attempt + 1}/{self.settings.max_retries}. Retrying in {self.settings.retry_delay}s...")
                    time.sleep(self.settings.retry_delay)
                else:
                    logging.error(f"Proxy failed after {self.settings.max_retries} retries: {e}")
                    raise


def main():
    # Load settings
    settings = get_settings()

    # Setup logging with configured level
    setup_logging(settings.log_level)

    runner = ProxyRunner(settings)
    runner.run_with_retry()


if __name__ == "__main__":
    main()
