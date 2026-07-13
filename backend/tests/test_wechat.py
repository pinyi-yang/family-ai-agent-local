import pytest
from unittest.mock import patch, MagicMock
from app.services.wechat import send_wechat_message

@patch('httpx.post')
def test_send_wechat_message(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"errcode": 0, "errmsg": "ok"}
    mock_post.return_value = mock_response

    result = send_wechat_message("dummy_webhook_url", "Test Message")
    
    assert result == True
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs["json"]["msgtype"] == "markdown"
    assert "Test Message" in kwargs["json"]["markdown"]["content"]