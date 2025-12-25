"""
Configuration management for the Qwen Proxy application.
Uses Pydantic for validation and type safety.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and environment variable support.

    This class defines all configurable parameters for the Qwen Proxy application
    with proper validation, type hints, and environment variable mapping.

    Attributes:
        config_file: Path to the LiteLLM configuration file
        port: Port number for the proxy to listen on (1024-65535)
        host: Host address for the proxy to bind to
        creds_path: Optional path to the credentials file
        api_key_env_var: Environment variable name for storing API key
        max_retries: Maximum number of retry attempts for proxy operations
        retry_delay: Delay in seconds between retry attempts
        log_level: Logging level for the application (DEBUG, INFO, WARNING, ERROR)
    """

    # Proxy settings
    config_file: str = Field(
        default="config.yaml", description="Path to the LiteLLM config file"
    )
    port: int = Field(
        default=3455, ge=1024, le=65535, description="Port for the proxy to listen on"
    )
    host: str = Field(default="127.0.0.1", description="Host for the proxy to bind to")

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

    model_config = SettingsConfigDict(
        env_prefix="QWEN_",
        case_sensitive=False,
        extra="forbid"
    )


def get_settings() -> Settings:
    """Get application settings from environment variables and defaults.

    This function creates and returns a Settings instance, automatically
    loading configuration values from environment variables (prefixed with
    QWEN_) or using the defined defaults if not provided.

    Returns:
        Settings: A validated settings instance with all configuration values
    """
    return Settings()
