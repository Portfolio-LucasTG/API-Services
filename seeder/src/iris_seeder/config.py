"""Seeder settings, read from environment variables."""

from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Environment configuration; empty variables count as unset (``DATASET_PATH=``)."""

    model_config = SettingsConfigDict(env_ignore_empty=True)

    database_url: str
    dataset_path: Path | None = None
    kaggle_dataset: str = "uciml/iris"
    seed_allow_fallback: bool = True
    log_level: LogLevel = "INFO"

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: object) -> object:
        """Accept ``info`` as well as ``INFO``."""
        return value.strip().upper() if isinstance(value, str) else value
