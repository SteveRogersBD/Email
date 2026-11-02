"""Validation helpers used by the UI and email workflow."""

from __future__ import annotations

import re
from pathlib import Path


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_email(value: str) -> bool:
    return bool(EMAIL_PATTERN.fullmatch(value.strip()))


def validate_required(value: str, label: str) -> str | None:
    return f"{label} is required." if not value.strip() else None


def validate_attachment(path: str | Path | None, max_size_mb: int = 10) -> str | None:
    if path is None or not str(path).strip():
        return None
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return "The selected attachment no longer exists."
    if file_path.suffix.lower() != ".pdf":
        return "Resume attachments must be PDF files."
    if file_path.stat().st_size > max_size_mb * 1024 * 1024:
        return f"The attachment must be {max_size_mb} MB or smaller."
    return None
