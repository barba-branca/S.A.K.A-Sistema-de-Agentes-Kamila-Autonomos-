from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Centralized configuration for S.A.K.A.
    """

    # Environment
    ENV: str = Field(default="development", description="Environment (development, production)")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # API Keys
    INTERNAL_API_KEY: str = Field(..., description="Internal API Key for agent communication")

    # Service URLs
    SENTINEL_URL: str = Field(..., description="URL for Sentinel Agent")
    CRONOS_URL: str = Field(..., description="URL for Cronos Agent")
    ORION_URL: str = Field(..., description="URL for Orion Agent")
    KAMILA_URL: str = Field(..., description="URL for Kamila Agent")

    # Timeouts (Optimization: Configurable timeouts)
    DEFAULT_TIMEOUT: float = Field(default=20.0, description="Default HTTP timeout")
    KAMILA_TIMEOUT: float = Field(default=30.0, description="Timeout for Kamila decision")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Ignore extra fields in .env
    )

settings = Settings()
