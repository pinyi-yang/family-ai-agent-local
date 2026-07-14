from .client import WeChatBot
from .types import IncomingMessage
import httpx

def send_wechat_message(webhook_url: str, message: str) -> bool:
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": message
        }
    }
    
    try:
        response = httpx.post(webhook_url, json=payload, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        return data.get("errcode") == 0
    except Exception:
        return False

__all__ = ["IncomingMessage", "WeChatBot", "send_wechat_message"]
