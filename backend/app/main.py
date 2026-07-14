import asyncio
from contextlib import asynccontextmanager
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.wechat.client import WeChatBot
from app.services.wechat.auth import (
    Credentials,
    load_credentials,
    clear_credentials,
    _save_credentials_sync,
)
from app.services.wechat.api import fetch_qr_code, poll_qr_status

# Initialize global WeChatBot instance
bot = WeChatBot()
bot_task: Optional[asyncio.Task] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task
    print(">>> [Backend] Lifespan starting: checking stored WeChat credentials...")
    try:
        credentials = await load_credentials(bot._token_path)
        if credentials is not None:
            print(f">>> [Backend] Found stored credentials for user {credentials.user_id}. Starting polling loop...")
            bot._credentials = credentials
            bot._base_url = credentials.base_url
            bot_task = asyncio.create_task(bot._run_loop())
        else:
            print(">>> [Backend] No stored credentials found.")
    except Exception as e:
        import traceback
        print(">>> [Backend] ERROR in lifespan startup loading credentials:")
        traceback.print_exc()
    yield
    # Clean up on shutdown
    print(">>> [Backend] Lifespan shutting down: stopping WeChatBot...")
    bot.stop()
    if bot_task is not None and not bot_task.done():
        try:
            await bot_task
        except asyncio.CancelledError:
            pass

app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In local YOLO dev mode, allowing all origins is safe and robust
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SendMessageRequest(BaseModel):
    user_id: str
    text: str
    context_token: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/wechat/qr")
async def get_wechat_qr():
    """Fetches a dynamic WeChat login QR code and returns it."""
    print(">>> [Backend] GET /api/wechat/qr request received")
    try:
        print(f">>> [Backend] Calling fetch_qr_code with base_url={bot._base_url}")
        qr = await asyncio.wait_for(fetch_qr_code(bot._base_url), timeout=10.0)
        print(f">>> [Backend] fetch_qr_code success! QR Token: {qr.get('qrcode')}")
        return {
            "qrcode": qr["qrcode"],
            "qrcode_img_content": qr["qrcode_img_content"],
            "is_static": False
        }
    except asyncio.TimeoutError:
        print(">>> [Backend] ERROR: fetch_qr_code timed out after 10 seconds!")
        raise HTTPException(status_code=504, detail="Request to WeChat API timed out.")
    except Exception as e:
        import traceback
        print(">>> [Backend] ERROR: Exception in get_wechat_qr:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch QR code: {str(e)}")

@app.get("/api/wechat/status")
async def check_wechat_status(qrcode: str = Query(..., description="The QR code token to poll")):
    """Polls the status of the QR code scan and saves credentials on confirmation."""
    global bot_task
    print(f">>> [Backend] GET /api/wechat/status request received for qrcode={qrcode}")
    try:
        print(f">>> [Backend] Polling QR status for qrcode={qrcode} with base_url={bot._base_url}")
        # Add a 40 second timeout to accommodate WeChat server-side 30-second long-polling
        status = await asyncio.wait_for(poll_qr_status(bot._base_url, qrcode), timeout=40.0)
        
        # LOG AUTH RESPONSE AFTER SCAN AT BACKEND
        print(f">>> [Backend] QR status polled successfully. RAW AUTH RESPONSE: {status}")
        
        if status["status"] == "confirmed":
            token = status.get("bot_token")
            account_id = status.get("ilink_bot_id")
            user_id = status.get("ilink_user_id")
            
            if not token or not account_id or not user_id:
                print(">>> [Backend] ERROR: QR confirmed but missing credentials in response!")
                raise HTTPException(status_code=500, detail="QR login confirmed, but no credentials returned.")
            
            credentials = Credentials(
                token=token,
                base_url=status.get("baseurl") or bot._base_url,
                account_id=account_id,
                user_id=user_id,
            )
            
            # Save credentials to home directory securely
            print(">>> [Backend] Saving confirmed credentials securely...")
            await asyncio.to_thread(_save_credentials_sync, credentials, bot._token_path)
            
            # Set bot credentials and start background task if not running
            bot._credentials = credentials
            bot._base_url = credentials.base_url
            
            if bot._loop is None:
                print(">>> [Backend] Starting bot background poll loop task...")
                bot_task = asyncio.create_task(bot._run_loop())
                
        return {
            "status": status["status"],
            "user_id": status.get("ilink_user_id") if status["status"] == "confirmed" else None
        }
    except asyncio.TimeoutError:
        print(">>> [Backend] ERROR: poll_qr_status timed out after 10 seconds!")
        raise HTTPException(status_code=504, detail="Status check request timed out.")
    except Exception as e:
        import traceback
        print(">>> [Backend] ERROR: Exception in check_wechat_status:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to check QR status: {str(e)}")

@app.get("/api/wechat/sessions")
async def get_wechat_sessions():
    """Lists cached active conversations and overall bot status."""
    print(">>> [Backend] GET /api/wechat/sessions request received")
    try:
        is_logged_in = bot._credentials is not None
        sessions = [
            {"user_id": user_id, "context_token": context_token}
            for user_id, context_token in bot._context_tokens.items()
        ]
        return {
            "is_logged_in": is_logged_in,
            "user_id": bot._credentials.user_id if is_logged_in and bot._credentials else None,
            "sessions": sessions,
        }
    except Exception as e:
        import traceback
        print(">>> [Backend] ERROR in get_wechat_sessions:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/wechat/send")
async def send_wechat_msg(req: SendMessageRequest):
    """Sends a text message to a user. Uses cached context token if not provided."""
    print(f">>> [Backend] POST /api/wechat/send request received for user={req.user_id}")
    context_token = req.context_token or bot._context_tokens.get(req.user_id)
    if not context_token:
        print(f">>> [Backend] ERROR: No cached context token found for user {req.user_id}")
        raise HTTPException(
            status_code=400,
            detail=f"No cached context token found for user {req.user_id}. Send a message to the bot first."
        )
    
    try:
        print(f">>> [Backend] Direct-sending text message to user={req.user_id} using token={context_token[:16]}...")
        await asyncio.wait_for(bot._send_text(req.user_id, req.text, context_token), timeout=10.0)
        # Update cached context token mapping
        bot._context_tokens[req.user_id] = context_token
        print(">>> [Backend] Message sent successfully!")
        return {"status": "success"}
    except asyncio.TimeoutError:
        print(">>> [Backend] ERROR: send message request timed out after 10 seconds!")
        raise HTTPException(status_code=540, detail="Send message timed out.")
    except Exception as e:
        import traceback
        print(">>> [Backend] ERROR: Exception in send_wechat_msg:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.post("/api/wechat/logout")
async def logout_wechat():
    """Logs out the bot, stops background polling, and deletes stored credentials."""
    global bot_task
    print(">>> [Backend] POST /api/wechat/logout request received")
    try:
        bot.stop()
        if bot_task is not None:
            try:
                await bot_task
            except asyncio.CancelledError:
                pass
            bot_task = None
            
        await clear_credentials(bot._token_path)
        bot._credentials = None
        bot._cursor = ""
        bot._context_tokens.clear()
        print(">>> [Backend] WeChatBot successfully logged out and credentials cleared.")
        return {"status": "success"}
    except Exception as e:
        import traceback
        print(">>> [Backend] ERROR in logout_wechat:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
