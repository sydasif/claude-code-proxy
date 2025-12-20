"""
Configuration management for the Qwen Proxy application.
Uses Pydantic for validation and type safety.
"""

import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings with validation."""

    # Proxy settings
    config_file: str = Field(
        default="config.yaml", description="Path to the LiteLLM config file"
    )
    port: int = Field(
        default=3455, ge=1024, le=65535, description="Port for the proxy to listen on"
    )
    host: str = Field(default="0.0.0.0", description="Host for the proxy to bind to")

    # Authentication settings
    creds_path: str | None = Field(
        default=None, description="Path to the credentials file"
    )
    api_key_env_var: str = Field(
        default="QWEN_API_KEY", description="Environment variable name for API key"
    )

    # Retry settings
    max_retries: int = Field(
        default=3, ge=0, le=10, description="Maximum number of retry attempts"
    )
    retry_delay: float = Field(
        default=5.0, ge=0.1, le=60.0, description="Delay between retries in seconds"
    )

    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")

    class Config:
        env_prefix = "QWEN_"
        case_sensitive = False
        extra = "forbid"


def get_settings() -> Settings:
    """Get application settings from environment variables and defaults."""
    # Set default creds path if not provided
    creds_path = os.environ.get("QWEN_CREDS_PATH")
    if not creds_path:
        default_path = Path.expanduser(Path("~/.qwen/oauth_creds.json"))
        os.environ["QWEN_CREDS_PATH"] = str(default_path)

    return Settings()
