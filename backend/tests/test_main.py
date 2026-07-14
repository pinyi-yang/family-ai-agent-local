import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app, bot

def test_read_main():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@patch("app.main.fetch_qr_code", new_callable=AsyncMock)
def test_get_wechat_qr(mock_fetch):
    mock_fetch.return_value = {
        "qrcode": "test_qr_token",
        "qrcode_img_content": "https://liteapp.weixin.qq.com/some-image-url"
    }
    
    with TestClient(app) as client:
        response = client.get("/api/wechat/qr")
        assert response.status_code == 200
        data = response.json()
        assert data["qrcode"] == "test_qr_token"
        assert data["qrcode_img_content"] == "/api/wechat/qr_image?url=https%3A//liteapp.weixin.qq.com/some-image-url"
        mock_fetch.assert_called_once_with(bot._base_url)

@patch("httpx.AsyncClient.get")
def test_get_qr_image_proxy(mock_get):
    # Setup mock response for httpx.AsyncClient.get
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake_binary_image_content"
    mock_response.headers = {"content-type": "image/png"}
    mock_get.return_value = mock_response

    with TestClient(app) as client:
        response = client.get("/api/wechat/qr_image?url=https%3A//liteapp.weixin.qq.com/some-image-url")
        assert response.status_code == 200
        assert response.content == b"fake_binary_image_content"
        assert response.headers["content-type"] == "image/png"
        mock_get.assert_called_once()

@patch("app.main.poll_qr_status", new_callable=AsyncMock)
@patch("app.main._save_credentials_sync")
@patch("app.main.bot._run_loop", new_callable=AsyncMock)
def test_check_wechat_status_waiting(mock_run_loop, mock_save, mock_poll):
    mock_poll.return_value = {
        "status": "wait"
    }
    
    with TestClient(app) as client:
        response = client.get("/api/wechat/status?qrcode=test_qr")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "wait"
        assert data["user_id"] is None
        mock_save.assert_not_called()

@patch("app.main.poll_qr_status", new_callable=AsyncMock)
@patch("app.main._save_credentials_sync")
@patch("app.main.asyncio.create_task")
def test_check_wechat_status_confirmed(mock_create_task, mock_save, mock_poll):
    mock_poll.return_value = {
        "status": "confirmed",
        "bot_token": "mock_token",
        "ilink_bot_id": "mock_bot_id",
        "ilink_user_id": "mock_user_id",
        "baseurl": "https://custom.base.url"
    }
    
    with TestClient(app) as client:
        # Reset bot loop mock state
        bot._loop = None
        response = client.get("/api/wechat/status?qrcode=test_qr")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["user_id"] == "mock_user_id"
        
        # Verify credentials saved
        mock_save.assert_called_once()
        assert bot._credentials is not None
        assert bot._credentials.token == "mock_token"
        assert bot._credentials.account_id == "mock_bot_id"
        assert bot._credentials.user_id == "mock_user_id"
        assert bot._base_url == "https://custom.base.url"
        
        # Verify background loop started
        mock_create_task.assert_called_once()

def test_get_wechat_sessions_logged_out():
    bot._credentials = None
    bot._context_tokens = {}
    
    with TestClient(app) as client:
        response = client.get("/api/wechat/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["is_logged_in"] is False
        assert data["user_id"] is None
        assert data["sessions"] == []

def test_get_wechat_sessions_logged_in_with_data():
    from app.services.wechat.auth import Credentials
    bot._credentials = Credentials(
        token="token123",
        base_url="https://base",
        account_id="account123",
        user_id="user123"
    )
    bot._context_tokens = {
        "chat_user_1": "token_abc",
        "chat_user_2": "token_def"
    }
    
    with TestClient(app) as client:
        response = client.get("/api/wechat/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["is_logged_in"] is True
        assert data["user_id"] == "user123"
        assert len(data["sessions"]) == 2
        assert {"user_id": "chat_user_1", "context_token": "token_abc"} in data["sessions"]
        assert {"user_id": "chat_user_2", "context_token": "token_def"} in data["sessions"]

@patch("app.main.bot._send_text", new_callable=AsyncMock)
def test_send_wechat_msg_with_cached_token(mock_send_text):
    bot._context_tokens = {
        "user_x": "cached_token_x"
    }
    
    with TestClient(app) as client:
        payload = {
            "user_id": "user_x",
            "text": "Hello world"
        }
        response = client.post("/api/wechat/send", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        mock_send_text.assert_called_once_with("user_x", "Hello world", "cached_token_x")

@patch("app.main.bot._send_text", new_callable=AsyncMock)
def test_send_wechat_msg_with_explicit_token(mock_send_text):
    bot._context_tokens = {}
    
    with TestClient(app) as client:
        payload = {
            "user_id": "user_y",
            "text": "Hello explicit",
            "context_token": "explicit_token_y"
        }
        response = client.post("/api/wechat/send", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        mock_send_text.assert_called_once_with("user_y", "Hello explicit", "explicit_token_y")
        assert bot._context_tokens["user_y"] == "explicit_token_y"

def test_send_wechat_msg_missing_token():
    bot._context_tokens = {}
    
    with TestClient(app) as client:
        payload = {
            "user_id": "user_z",
            "text": "Hello missing"
        }
        response = client.post("/api/wechat/send", json=payload)
        assert response.status_code == 400
        assert "No cached context token found" in response.json()["detail"]

@patch("app.main.bot_task", None)
@patch("app.main.clear_credentials", new_callable=AsyncMock)
def test_logout_wechat(mock_clear):
    from app.services.wechat.auth import Credentials
    bot._credentials = Credentials(
        token="token123",
        base_url="https://base",
        account_id="account123",
        user_id="user123"
    )
    bot._context_tokens = {"user_a": "token_a"}
    bot.stop = MagicMock()
    
    with TestClient(app) as client:
        response = client.post("/api/wechat/logout")
        assert response.status_code == 200
        assert response.json() == {"status": "success"}
        
        bot.stop.assert_called_once()
        mock_clear.assert_called_once_with(bot._token_path)
        assert bot._credentials is None
        assert bot._context_tokens == {}
        assert bot._cursor == ""
