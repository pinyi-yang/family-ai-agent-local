import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Absolute path load of backend/.env
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
load_dotenv(dotenv_path=os.path.join(backend_dir, ".env"))

from app.services.slack_service import SlackClient
from app.database import Base, engine, get_db
import app.models

# Auto-create SQLite database tables on startup
Base.metadata.create_all(bind=engine)

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


@app.get("/api/google/status")
def get_google_status(db = Depends(get_db)):
    """Checks Google Workspace integration status and returns authenticated accounts."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    is_configured = bool(client_id and client_secret and redirect_uri)
    
    accounts = []
    if is_configured:
        from app.models import FamilyMember
        members = db.query(FamilyMember).filter(
            FamilyMember.google_refresh_token.isnot(None),
            FamilyMember.is_authenticated == True
        ).all()
        accounts = [{"email": m.email, "name": m.name} for m in members]
        
    return {
        "is_configured": is_configured,
        "authenticated_accounts": accounts
    }


@app.get("/api/google/login")
def google_login():
    """Generates the Google OAuth authorization URL and redirects the user."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not (client_id and client_secret and redirect_uri):
        raise HTTPException(status_code=400, detail="Google OAuth is not configured in .env")
        
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/calendar.readonly"
    ]
    
    flow = Flow.from_client_config(client_config, scopes=scopes)
    flow.redirect_uri = redirect_uri
    
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    
    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key="google_code_verifier",
        value=flow.code_verifier,
        httponly=True,
        max_age=600,
        samesite="lax"
    )
    return response


@app.get("/api/google/callback")
@app.get("/api/auth/callback")
def google_callback(code: str, db = Depends(get_db), google_code_verifier: Optional[str] = Cookie(None)):
    """Receives OAuth callback, exchanges authorization code, and registers/updates user."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/calendar.readonly"
    ]
    
    flow = Flow.from_client_config(client_config, scopes=scopes)
    flow.redirect_uri = redirect_uri
    
    if google_code_verifier:
        flow.code_verifier = google_code_verifier
        
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch token: {str(e)}")
        
    credentials = flow.credentials
    
    try:
        # Build userinfo service to get email
        userinfo_service = build("oauth2", "v2", credentials=credentials)
        user_info = userinfo_service.userinfo().get().execute()
        email = user_info.get("email")
        name = user_info.get("name", "Google User")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user info: {str(e)}")
        
    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from Google")
        
    from app.models import FamilyMember
    member = db.query(FamilyMember).filter(FamilyMember.email == email).first()
    
    if member:
        if credentials.refresh_token:
            member.google_refresh_token = credentials.refresh_token
        member.name = name
        member.is_authenticated = True
    else:
        member = FamilyMember(
            name=name,
            email=email,
            google_refresh_token=credentials.refresh_token,
            is_authenticated=True
        )
        db.add(member)
        
    db.commit()
    
    return RedirectResponse(url="http://localhost:5173/tests?google_success=true")


from google.oauth2.credentials import Credentials

@app.get("/api/google/emails")
def get_google_emails(email: str, db = Depends(get_db)):
    from app.models import FamilyMember
    member = db.query(FamilyMember).filter(FamilyMember.email == email).first()
    if not member or not member.google_refresh_token:
        raise HTTPException(status_code=404, detail="Authenticated family member not found or missing credentials.")
        
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    creds = Credentials(
        token=None,  # Will trigger refresh automatically if needed
        refresh_token=member.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    
    try:
        gmail = build("gmail", "v1", credentials=creds)
        results = gmail.users().messages().list(userId="me", maxResults=5).execute()
        messages = results.get("messages", [])
        
        emails_list = []
        for msg in messages:
            msg_data = gmail.users().messages().get(userId="me", id=msg["id"], format="full").execute()
            snippet = msg_data.get("snippet", "")
            headers = msg_data.get("payload", {}).get("headers", [])
            
            subject = "No Subject"
            sender = "Unknown"
            date = ""
            for h in headers:
                if h["name"].lower() == "subject":
                    subject = h["value"]
                elif h["name"].lower() == "from":
                    sender = h["value"]
                elif h["name"].lower() == "date":
                    date = h["value"]
                    
            emails_list.append({
                "id": msg["id"],
                "subject": subject,
                "from": sender,
                "date": date,
                "snippet": snippet
            })
        return emails_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Gmail messages: {str(e)}")


@app.get("/api/google/calendar")
def get_google_calendar(email: str, db = Depends(get_db)):
    from app.models import FamilyMember
    member = db.query(FamilyMember).filter(FamilyMember.email == email).first()
    if not member or not member.google_refresh_token:
        raise HTTPException(status_code=404, detail="Authenticated family member not found or missing credentials.")
        
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    creds = Credentials(
        token=None,
        refresh_token=member.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    
    try:
        calendar = build("calendar", "v3", credentials=creds)
        # Get current time to get upcoming events
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        
        results = calendar.events().list(
            calendarId="primary",
            timeMin=now_iso,
            maxResults=5,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        
        items = results.get("items", [])
        events_list = []
        for item in items:
            events_list.append({
                "id": item.get("id"),
                "summary": item.get("summary", "No Title"),
                "start": item.get("start", {}).get("dateTime") or item.get("start", {}).get("date", ""),
                "end": item.get("end", {}).get("dateTime") or item.get("end", {}).get("date", ""),
                "link": item.get("htmlLink", "")
            })
        return events_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Google Calendar events: {str(e)}")





