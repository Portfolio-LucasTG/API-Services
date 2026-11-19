"""Seeder settings, read from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment configuration; empty variables count as unset (``DATASET_PATH=``)."""

    model_config = SettingsConfigDict(env_ignore_empty=True)

    database_url: str
    dataset_path: Path | None = None
    kaggle_dataset: str = "uciml/iris"
    seed_allow_fallback: bool = True
    log_level: str = "INFO"
