from unittest.mock import Mock, patch

import pytest

from services.gmail_service import GmailService


def test_valid_send_only_token_is_connected_without_profile_request(tmp_path):
    token = tmp_path / "token.json"
    token.touch()
    service = GmailService(token_file=token)
    credentials = Mock(valid=True, expired=False, account="")
    with patch.object(service, "_load_credentials", return_value=credentials), patch.object(service, "build_client") as build:
        assert service.is_connected()
        assert service.connected_email() is None
        build.assert_not_called()


def test_missing_token_is_disconnected_and_sending_never_starts_oauth(tmp_path):
    service = GmailService(token_file=tmp_path / "missing.json")
    assert not service.is_connected()
    with patch("services.gmail_service.InstalledAppFlow.from_client_secrets_file") as flow:
        with pytest.raises(RuntimeError, match="Connect Gmail"):
            service.build_client()
        flow.assert_not_called()


def test_refresh_error_is_reported_instead_of_hidden(tmp_path):
    token = tmp_path / "token.json"
    token.touch()
    service = GmailService(token_file=token)
    credentials = Mock(valid=False, expired=True, refresh_token="test-token")
    credentials.refresh.side_effect = RuntimeError("Refresh failed")
    with patch.object(service, "_load_credentials", return_value=credentials):
        with pytest.raises(RuntimeError, match="Refresh failed"):
            service.is_connected()
