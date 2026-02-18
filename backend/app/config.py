"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://swag:devpassword@localhost:5432/swag"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Mollie
    mollie_api_key: str = ""

    # POD Providers
    prodigi_api_key: str = ""
    printful_api_token: str = ""
    pod_sandbox_mode: bool = True

    # Flow Service (TBFF revenue split → bonding curve)
    flow_service_url: str = ""
    flow_id: str = ""
    flow_funnel_id: str = ""
    flow_revenue_split: float = 0.5  # fraction of margin routed to flow (0.0-1.0)

    # Auth
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Paths
    designs_path: str = "/app/designs"
    config_path: str = "/app/config"
    spaces_path: str = "/app/spaces"

    # App
    app_name: str = "rSwag"
    debug: bool = False

    @property
    def designs_dir(self) -> Path:
        return Path(self.designs_path)

    @property
    def config_dir(self) -> Path:
        return Path(self.config_path)

    @property
    def spaces_dir(self) -> Path:
        return Path(self.spaces_path)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
