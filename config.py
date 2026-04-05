"""Configuration helpers for the application."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _load_env_file() -> None:
    """Load environment variables from a local .env file if present."""
    load_dotenv(override=False)


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    @property
    def database_url(self) -> str:
        return (
            "mysql+mysqlconnector://"
            f"{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )


def load_settings() -> Settings:
    _load_env_file()
    return Settings(
        db_host=os.getenv("DB_HOST", "127.0.0.1"),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_user=os.getenv("DB_USER", "root"),
        db_password=os.getenv("DB_PASSWORD", ""),
        db_name=os.getenv("DB_NAME", "reservations_db"),
    )
