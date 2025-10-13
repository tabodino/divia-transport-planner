"""Application configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_format_console: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    log_format_file: str = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{name}:{function}:{line} - {message}"
    )
    log_rotation: str = "10 MB"
    log_retention: str = "1 week"
    log_compression: str = "zip"

    # GTFS Data
    gtfs_url: str = (
        "https://www.data.gouv.fr/api/1/datasets/r/e0dbd217-15cd-4e28-9459-211a27511a34"
    )

    # Paths
    data_dir: Path = Path("data")
    raw_data_dir: Path = data_dir / "raw"
    processed_data_dir: Path = data_dir / "processed"
    logs_dir: Path = Path("logs")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
