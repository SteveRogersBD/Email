"""Small Gmail API adapter with local OAuth token management."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from config import settings


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailService:
    def __init__(self, client_secret_file: Path | None = None, token_file: Path | None = None) -> None:
        self.client_secret_file = client_secret_file or settings.google_client_secret_file
        self.token_file = token_file or settings.google_token_file

    def _load_credentials(self) -> Credentials | None:
        if not self.token_file.exists():
            return None
        return Credentials.from_authorized_user_file(str(self.token_file), SCOPES)

    def authenticate(self) -> Credentials:
        credentials = self._load_credentials()
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self.token_file.write_text(credentials.to_json(), encoding="utf-8")
        elif not credentials or not credentials.valid:
            if not self.client_secret_file.exists():
                raise FileNotFoundError(
                    f"Google OAuth client file not found at {self.client_secret_file}. "
                    "Download a Desktop OAuth client JSON and place it there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(self.client_secret_file), SCOPES)
            credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
            self.token_file.write_text(credentials.to_json(), encoding="utf-8")
        return credentials

    def build_client(self) -> Resource:
        credentials = self.authenticate()
        return build("gmail", "v1", credentials=credentials, cache_discovery=False)

    def connected_email(self) -> str | None:
        if not self.token_file.exists():
            return None
        try:
            client = self.build_client()
            profile = client.users().getProfile(userId="me").execute()
            return profile.get("emailAddress")
        except Exception:
            return None

    def send_message(self, message: EmailMessage) -> str:
        client = self.build_client()
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        result: dict[str, Any] = client.users().messages().send(userId="me", body={"raw": raw}).execute()
        return str(result["id"])

    def disconnect(self) -> None:
        if self.token_file.exists():
            self.token_file.unlink()
