import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app

def test_read_main():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@patch.dict(os.environ, {}, clear=True)
def test_get_slack_status_not_configured():
    with TestClient(app) as client:
        response = client.get("/api/slack/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False
        assert data["is_connected"] is False
        assert data["bot_info"] is None
        assert "not set" in data["error"]

@patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token"})
@patch("app.main.SlackClient")
def test_get_slack_status_configured_and_connected(mock_slack_client_class):
    mock_instance = MagicMock()
    mock_instance.auth_test.return_value = {
        "ok": True,
        "url": "https://test.slack.com/",
        "team": "Test Team",
        "user": "test_bot",
        "team_id": "T123",
        "user_id": "U123",
        "bot_id": "B123"
    }
    mock_slack_client_class.return_value = mock_instance

    # Clear global state or patch global slack_client
    with patch("app.main.slack_client", None):
        with TestClient(app) as client:
            response = client.get("/api/slack/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_configured"] is True
            assert data["is_connected"] is True
            assert data["bot_info"]["user"] == "test_bot"
            assert data["error"] is None

@patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test-token"})
@patch("app.main.SlackClient")
def test_get_slack_status_configured_but_failed(mock_slack_client_class):
    mock_instance = MagicMock()
    mock_instance.auth_test.return_value = None
    mock_slack_client_class.return_value = mock_instance

    with patch("app.main.slack_client", None):
        with TestClient(app) as client:
            response = client.get("/api/slack/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_configured"] is True
            assert data["is_connected"] is False
            assert data["bot_info"] is None
            assert "unsuccessful" in data["error"]

@patch("app.main.slack_client")
def test_send_slack_msg_success(mock_client):
    mock_client.send_message.return_value = {"channel": "C123", "ts": "123.456", "text": "Hello channel"}
    
    with TestClient(app) as client:
        payload = {
            "target_id": "C123",
            "text": "Hello channel"
        }
        response = client.post("/api/slack/send", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["ts"] == "123.456"
        mock_client.send_message.assert_called_once_with(target_id="C123", text="Hello channel")

@patch("app.main.slack_client")
def test_send_slack_msg_thread_success(mock_client):
    mock_client.reply_to_thread.return_value = {"channel": "C123", "ts": "123.457", "text": "Hello thread"}
    
    with TestClient(app) as client:
        payload = {
            "target_id": "C123",
            "text": "Hello thread",
            "thread_ts": "123.456"
        }
        response = client.post("/api/slack/send", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_client.reply_to_thread.assert_called_once_with(channel_id="C123", thread_ts="123.456", text="Hello thread")

@patch("app.main.slack_client")
def test_send_slack_msg_failed_response(mock_client):
    mock_client.send_message.return_value = None
    
    with TestClient(app) as client:
        payload = {
            "target_id": "C123",
            "text": "Hello failed"
        }
        response = client.post("/api/slack/send", json=payload)
        assert response.status_code == 400
        assert "Failed to send message to Slack" in response.json()["detail"]


def test_db_tables_exist():
    # Verify tables are created on database engine
    from app.database import engine
    from sqlalchemy import inspect
    inspector = inspect(engine)
    assert "family_members" in inspector.get_table_names()
    assert "family_preferences" in inspector.get_table_names()


@patch.dict(os.environ, {}, clear=True)
def test_get_google_status_not_configured():
    with TestClient(app) as client:
        response = client.get("/api/google/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False
        assert data["authenticated_accounts"] == []


@patch.dict(os.environ, {
    "GOOGLE_CLIENT_ID": "mock-client-id",
    "GOOGLE_CLIENT_SECRET": "mock-client-secret",
    "GOOGLE_REDIRECT_URI": "mock-redirect-uri"
})
def test_get_google_status_configured_no_accounts():
    with TestClient(app) as client:
        response = client.get("/api/google/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is True
        assert data["authenticated_accounts"] == []


@patch.dict(os.environ, {
    "GOOGLE_CLIENT_ID": "mock-client-id",
    "GOOGLE_CLIENT_SECRET": "mock-client-secret",
    "GOOGLE_REDIRECT_URI": "mock-redirect-uri"
})
def test_get_google_status_configured_with_accounts():
    from app.models import FamilyMember
    from app.database import get_db

    mock_db = MagicMock()
    mock_member = FamilyMember(
        name="John Doe",
        email="john@example.com",
        google_refresh_token="mock-token",
        is_authenticated=True
    )
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_member]

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/google/status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_configured"] is True
            assert len(data["authenticated_accounts"]) == 1
            assert data["authenticated_accounts"][0]["email"] == "john@example.com"
            assert data["authenticated_accounts"][0]["name"] == "John Doe"
    finally:
        app.dependency_overrides.clear()


@patch.dict(os.environ, {
    "GOOGLE_CLIENT_ID": "fake-id",
    "GOOGLE_CLIENT_SECRET": "fake-secret",
    "GOOGLE_REDIRECT_URI": "http://localhost:4000/api/google/callback"
})
@patch("app.main.Flow.from_client_config")
def test_google_login_redirect(mock_from_client_config):
    mock_flow = MagicMock()
    mock_flow.authorization_url.return_value = ("https://google-consent-page.com", "state")
    mock_from_client_config.return_value = mock_flow
    
    with TestClient(app) as client:
        response = client.get("/api/google/login", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://google-consent-page.com"


@patch.dict(os.environ, {}, clear=True)
def test_google_login_not_configured():
    with TestClient(app) as client:
        response = client.get("/api/google/login")
        assert response.status_code == 400
        assert "Google OAuth is not configured in .env" in response.json()["detail"]


@patch.dict(os.environ, {
    "GOOGLE_CLIENT_ID": "fake-id",
    "GOOGLE_CLIENT_SECRET": "fake-secret",
    "GOOGLE_REDIRECT_URI": "http://localhost:4000/api/google/callback"
})
@patch("app.main.Flow.from_client_config")
@patch("app.main.build")
def test_google_callback_success(mock_build, mock_from_client_config):
    # Mocking OAuth exchange
    mock_flow = MagicMock()
    mock_credentials = MagicMock()
    mock_credentials.refresh_token = "fake-refresh-token"
    mock_credentials.token = "fake-access-token"
    mock_flow.credentials = mock_credentials
    mock_from_client_config.return_value = mock_flow
    
    # Mocking userinfo service
    mock_userinfo_service = MagicMock()
    mock_build.return_value = mock_userinfo_service
    mock_userinfo_service.userinfo().get().execute.return_value = {
        "email": "testuser@gmail.com",
        "name": "Test User"
    }
    
    try:
        with TestClient(app) as client:
            response = client.get("/api/google/callback?code=fake-code", follow_redirects=False)
            assert response.status_code == 307
            assert "google_success=true" in response.headers["location"]
    finally:
        from app.database import SessionLocal
        from app.models import FamilyMember
        db = SessionLocal()
        try:
            member = db.query(FamilyMember).filter(FamilyMember.email == "testuser@gmail.com").first()
            if member:
                db.delete(member)
                db.commit()
        finally:
            db.close()


@patch("app.main.build")
def test_get_google_emails_success(mock_build):
    from app.database import SessionLocal
    from app.models import FamilyMember
    db = SessionLocal()
    # Clean up first to avoid duplicates
    db.query(FamilyMember).filter(FamilyMember.email == "bob@gmail.com").delete()
    
    member = FamilyMember(name="Bob", email="bob@gmail.com", google_refresh_token="bob-refresh", is_authenticated=True)
    db.add(member)
    db.commit()
    db.close()
    
    # Mocking Gmail API build
    mock_gmail_service = MagicMock()
    mock_build.return_value = mock_gmail_service
    mock_gmail_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg1"}, {"id": "msg2"}]
    }
    mock_gmail_service.users().messages().get().execute.side_effect = [
        {"id": "msg1", "snippet": "Hey there!", "payload": {"headers": [{"name": "Subject", "value": "Hello"}, {"name": "From", "value": "Alice"}, {"name": "Date", "value": "Mon, 20 Jul 2026 10:00:00 GMT"}]}},
        {"id": "msg2", "snippet": "Meeting tomorrow", "payload": {"headers": [{"name": "Subject", "value": "Quick Sync"}, {"name": "From", "value": "Work"}, {"name": "Date", "value": "Mon, 20 Jul 2026 11:00:00 GMT"}]}}
    ]
    
    with TestClient(app) as client:
        response = client.get("/api/google/emails?email=bob@gmail.com")
        assert response.status_code == 200
        emails = response.json()
        assert len(emails) == 2
        assert emails[0]["subject"] == "Hello"
        assert emails[0]["snippet"] == "Hey there!"
        assert emails[0]["from"] == "Alice"
        assert emails[0]["date"] == "Mon, 20 Jul 2026 10:00:00 GMT"

    # Database cleanup
    db = SessionLocal()
    db.query(FamilyMember).filter(FamilyMember.email == "bob@gmail.com").delete()
    db.commit()
    db.close()


def test_get_google_emails_not_found():
    with TestClient(app) as client:
        response = client.get("/api/google/emails?email=nonexistent@gmail.com")
        assert response.status_code == 404
        assert "Authenticated family member not found" in response.json()["detail"]







