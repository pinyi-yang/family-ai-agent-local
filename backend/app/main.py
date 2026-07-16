import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Absolute path load of backend/.env
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(backend_dir, ".env"))

from app.services.slack_service import SlackClient

# Initialize Slack Client gracefully
slack_client = None
try:
    slack_client = SlackClient()
    print(">>> [Backend] SlackClient initialized successfully.")
except Exception as e:
    print(f">>> [Backend] WARNING: SlackClient initialization failed (probably missing SLACK_BOT_TOKEN): {e}")

app = FastAPI()

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In local YOLO dev mode, allowing all origins is safe and robust
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SlackMessageRequest(BaseModel):
    target_id: str
    text: str
    thread_ts: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/slack/status")
async def get_slack_status():
    """Checks Slack integration configuration and connection status."""
    print(">>> [Backend] GET /api/slack/status request received")
    token = os.getenv("SLACK_BOT_TOKEN")
    is_configured = token is not None and len(token.strip()) > 0
    
    if not is_configured:
        return {
            "is_configured": False,
            "is_connected": False,
            "bot_info": None,
            "error": "SLACK_BOT_TOKEN is not set in environment variables."
        }
    
    # Try testing the token/connection
    try:
        # Re-initialize client if it wasn't initialized
        global slack_client
        if slack_client is None:
            slack_client = SlackClient()
            
        bot_info = slack_client.auth_test()
        if bot_info:
            return {
                "is_configured": True,
                "is_connected": True,
                "bot_info": bot_info,
                "error": None
            }
        else:
            return {
                "is_configured": True,
                "is_connected": False,
                "bot_info": None,
                "error": "Slack auth test returned unsuccessful response."
            }
    except Exception as e:
        return {
            "is_configured": True,
            "is_connected": False,
            "bot_info": None,
            "error": str(e)
        }

@app.post("/api/slack/send")
async def send_slack_msg(req: SlackMessageRequest):
    """Sends a text message to a Slack channel or user, optionally as a thread reply."""
    print(f">>> [Backend] POST /api/slack/send request received for target={req.target_id}")
    
    global slack_client
    if slack_client is None:
        try:
            slack_client = SlackClient()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Slack client is not initialized and failed to start: {str(e)}"
            )
            
    try:
        if req.thread_ts:
            response = slack_client.reply_to_thread(
                channel_id=req.target_id,
                thread_ts=req.thread_ts,
                text=req.text
            )
        else:
            response = slack_client.send_message(
                target_id=req.target_id,
                text=req.text
            )
            
        if response:
            return {"status": "success", "data": response}
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to send message to Slack. Check backend logs for API errors."
            )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Exception while sending message: {str(e)}")
