"""Application configuration and filesystem paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")


def _database_url() -> str:
    configured = os.getenv("DATABASE_URL", "sqlite:///data/outreach.db")
    if configured.startswith("sqlite:///") and not configured.startswith("sqlite:////"):
        relative_path = configured.removeprefix("sqlite:///")
        return f"sqlite:///{(ROOT_DIR / relative_path).resolve()}"
    return configured


@dataclass(frozen=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / os.getenv("APP_DATA_DIR", "data")
    upload_dir: Path = ROOT_DIR / os.getenv("UPLOAD_DIR", "uploads")
    database_url: str = _database_url()
    google_client_secret_file: Path = ROOT_DIR / os.getenv(
        "GOOGLE_CLIENT_SECRET_FILE", "credentials.json"
    )
    google_token_file: Path = ROOT_DIR / os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    max_attachment_size_mb: int = int(os.getenv("MAX_ATTACHMENT_SIZE_MB", "10"))

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
