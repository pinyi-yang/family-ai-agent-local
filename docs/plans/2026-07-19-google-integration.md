# Google Workspace Integration Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Google OAuth authentication, token storage, and Gmail/Calendar API integration in the Family AI Agent, with a dedicated "Tests" page in the frontend housing both Slack and Google tests.

**Architecture:** 
1. **OAuth Flow:** A backend-driven OAuth 2.0 flow using `google-auth-oauthlib`. The frontend initiates authentication by redirecting the user's browser to `/api/google/login`. The backend generates the authorization URL with `offline` access to obtain a refresh token. Upon consent, Google redirects the browser to `/api/google/callback`, where the backend exchanges the code, fetches user profile (email and name), stores/updates the credentials in the SQLite database, and redirects back to the frontend with a success indicator.
2. **Database Integration:** SQLite database tables (`family_members`) are created on startup. The `FamilyMember` record storing `google_refresh_token` is retrieved on demand to initialize authenticated Google clients using automatic token refreshing.
3. **API Access:** Expose read-only API endpoints for listing a user's recent emails and calendar events. These endpoints authenticate via the stored refresh token.
4. **Frontend Layout:** Refactor the main application layout to introduce a "Tests" tab. Inside the "Tests" view, create sub-navigation for "Slack Integration Test" and a new "Google Workspace Test".

**Tech Stack:**
- **Backend:** FastAPI, SQLite + SQLAlchemy, `google-api-python-client`, `google-auth-oauthlib`, `pytest`.
- **Frontend:** React 19, TypeScript, Vitest.

---

### Task 1: Add Dependencies and Database Initialization

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/database.py`
- Modify: `backend/app/main.py`

**Step 1: Write the failing test**
Create a test in `backend/tests/test_main.py` to ensure the DB tables are created and `get_db` works.

```python
from app.database import engine, Base
import os

def test_db_tables_exist():
    # Verify tables are created on database engine
    from sqlalchemy import inspect
    inspector = inspect(engine)
    assert "family_members" in inspector.get_table_names()
    assert "family_preferences" in inspector.get_table_names()
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_main.py -k test_db_tables_exist -v`
Expected: Fail because tables are not yet created automatically.

**Step 3: Write minimal implementation**
1. Add to `backend/requirements.txt`:
   ```text
   google-api-python-client
   google-auth-oauthlib
   ```
2. In `backend/app/database.py`, implement `get_db` dependency:
   ```python
   def get_db():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```
3. In `backend/app/main.py`, import `Base` and `engine` and run `Base.metadata.create_all(bind=engine)` to ensure tables are created on app startup.

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_main.py -k test_db_tables_exist -v`
Expected: Pass

**Step 5: Commit**
```bash
git add backend/requirements.txt backend/app/database.py backend/app/main.py
git commit -m "chore(backend): add google dependencies and database auto-creation"
```

---

### Task 2: Implement Google Status Endpoint `/api/google/status`

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_main.py`

**Step 1: Write the failing test**
In `backend/tests/test_main.py`:
```python
@patch.dict(os.environ, {}, clear=True)
def test_get_google_status_not_configured():
    with TestClient(app) as client:
        response = client.get("/api/google/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False
        assert data["authenticated_accounts"] == []
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_main.py -k test_get_google_status_not_configured -v`
Expected: FAIL with 404 (Not Found).

**Step 3: Write minimal implementation**
In `backend/app/main.py`:
1. Check if `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` are configured in `.env`.
2. Add route `/api/google/status`:
   ```python
   @app.get("/api/google/status")
   def get_google_status(db = Depends(get_db)):
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
   ```
   *(Note: Ensure imports for `Depends` and `get_db` are added).*

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_main.py -k test_get_google_status -v`
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/main.py backend/tests/test_main.py
git commit -m "feat(backend): implement google status endpoint"
```

---

### Task 3: Implement Google Login Endpoint `/api/google/login`

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_main.py`

**Step 1: Write the failing test**
In `backend/tests/test_main.py`:
```python
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
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_main.py -k test_google_login_redirect -v`
Expected: FAIL with 404.

**Step 3: Write minimal implementation**
In `backend/app/main.py`:
1. Implement the `/api/google/login` endpoint. It uses `google_auth_oauthlib.flow.Flow` to construct the authorization URL with appropriate scopes:
   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/userinfo.profile`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/calendar.readonly`
2. Configure `access_type="offline"` and `prompt="consent"` to ensure a refresh token is returned.
3. Code:
   ```python
   from fastapi.responses import RedirectResponse
   from google_auth_oauthlib.flow import Flow

   @app.get("/api/google/login")
   def google_login():
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
       return RedirectResponse(url=auth_url)
   ```

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_main.py -k test_google_login_redirect -v`
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/main.py backend/tests/test_main.py
git commit -m "feat(backend): implement google login oauth initialization"
```

---

### Task 4: Implement Google Callback Endpoint `/api/google/callback`

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_main.py`

**Step 1: Write the failing test**
In `backend/tests/test_main.py`:
```python
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
    
    with TestClient(app) as client:
        response = client.get("/api/google/callback?code=fake-code", follow_redirects=False)
        assert response.status_code == 307
        assert "google_success=true" in response.headers["location"]
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_main.py -k test_google_callback_success -v`
Expected: FAIL with 404.

**Step 3: Write minimal implementation**
In `backend/app/main.py`:
1. Implement `/api/google/callback` endpoint:
   - Create Flow object.
   - Fetch token using `flow.fetch_token(code=code)`.
   - Extract `credentials`. If `credentials.refresh_token` is missing (can happen if user didn't consent fully, but since we use `prompt="consent"`, we should get it), log a warning or handle gracefully.
   - Call Google Userinfo API to fetch user's email and name.
   - Look up user in database by email.
   - If user exists, update `google_refresh_token` (if provided) and set `is_authenticated = True`.
   - If user does not exist, create a new `FamilyMember` with name, email, `google_refresh_token`, and `is_authenticated = True`.
   - Commit DB changes.
   - Redirect to `http://localhost:5173/tests?google_success=true`.
2. Code:
   ```python
   from googleapiclient.discovery import build

   @app.get("/api/google/callback")
   def google_callback(code: str, db = Depends(get_db)):
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
   ```

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_main.py -k test_google_callback_success -v`
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/main.py backend/tests/test_main.py
git commit -m "feat(backend): implement google auth callback and database sync"
```

---

### Task 5: Implement Google Email List Endpoint `/api/google/emails`

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_main.py`

**Step 1: Write the failing test**
In `backend/tests/test_main.py`:
```python
@patch("app.main.build")
def test_get_google_emails_success(mock_build, db_session_fixture):
    # Set up active FamilyMember with refresh token in db
    from app.models import FamilyMember
    member = FamilyMember(name="Bob", email="bob@gmail.com", google_refresh_token="bob-refresh", is_authenticated=True)
    db_session_fixture.add(member)
    db_session_fixture.commit()
    
    # Mocking Gmail API build
    mock_gmail_service = MagicMock()
    mock_build.return_value = mock_gmail_service
    mock_gmail_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg1"}, {"id": "msg2"}]
    }
    mock_gmail_service.users().messages().get().execute.side_effect = [
        {"id": "msg1", "snippet": "Hey there!", "payload": {"headers": [{"name": "Subject", "value": "Hello"}, {"name": "From", "value": "Alice"}]}},
        {"id": "msg2", "snippet": "Meeting tomorrow", "payload": {"headers": [{"name": "Subject", "value": "Quick Sync"}, {"name": "From", "value": "Work"}]}}
    ]
    
    with TestClient(app) as client:
        response = client.get("/api/google/emails?email=bob@gmail.com")
        assert response.status_code == 200
        emails = response.json()
        assert len(emails) == 2
        assert emails[0]["subject"] == "Hello"
        assert emails[0]["snippet"] == "Hey there!"
```
*(Note: Create a simple fixture for database session if not already available, or retrieve from SessionLocal and clear after).*

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_main.py -k test_get_google_emails -v`
Expected: FAIL with 404.

**Step 3: Write minimal implementation**
In `backend/app/main.py`:
1. Implement the `/api/google/emails` endpoint.
2. It fetches the `FamilyMember` by email from the DB, takes their `google_refresh_token`, and initializes a `google.oauth2.credentials.Credentials` object with the token.
3. Uses `build("gmail", "v1", credentials=creds)` to fetch the message list (limit 5) and metadata for each message.
4. Code:
   ```python
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
   ```

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_main.py -k test_get_google_emails -v`
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/main.py backend/tests/test_main.py
git commit -m "feat(backend): implement gmail list retrieval endpoint"
```

---

### Task 6: Implement Google Calendar List Endpoint `/api/google/calendar`

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_main.py`

**Step 1: Write the failing test**
In `backend/tests/test_main.py`:
```python
@patch("app.main.build")
def test_get_google_calendar_success(mock_build, db_session_fixture):
    # Setup FamilyMember
    from app.models import FamilyMember
    # Re-use Bob or create bob2
    member = db_session_fixture.query(FamilyMember).filter_by(email="bob@gmail.com").first()
    if not member:
        member = FamilyMember(name="Bob", email="bob@gmail.com", google_refresh_token="bob-refresh", is_authenticated=True)
        db_session_fixture.add(member)
        db_session_fixture.commit()
        
    # Mocking Calendar API build
    mock_cal_service = MagicMock()
    mock_build.return_value = mock_cal_service
    mock_cal_service.events().list().execute.return_value = {
        "items": [
            {
                "id": "evt1",
                "summary": "Family Dinner",
                "start": {"dateTime": "2026-07-20T18:00:00Z"},
                "end": {"dateTime": "2026-07-20T19:00:00Z"}
            }
        ]
    }
    
    with TestClient(app) as client:
        response = client.get("/api/google/calendar?email=bob@gmail.com")
        assert response.status_code == 200
        events = response.json()
        assert len(events) == 1
        assert events[0]["summary"] == "Family Dinner"
```

**Step 2: Run test to verify it fails**
Run: `pytest backend/tests/test_main.py -k test_get_google_calendar -v`
Expected: FAIL with 404.

**Step 3: Write minimal implementation**
In `backend/app/main.py`:
1. Implement `/api/google/calendar` endpoint.
2. It fetches the family member, instantiates credentials with refresh token, and calls `calendar.events().list(calendarId="primary", maxResults=5)` to fetch recent/upcoming events.
3. Code:
   ```python
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
   ```

**Step 4: Run test to verify it passes**
Run: `pytest backend/tests/test_main.py -k test_get_google_calendar -v`
Expected: PASS

**Step 5: Commit**
```bash
git add backend/app/main.py backend/tests/test_main.py
git commit -m "feat(backend): implement calendar list retrieval endpoint"
```

---

### Task 7: Move SlackTest and Introduce GoogleTest into a Dedicated "Tests" Page

**Files:**
- Create: `frontend/src/GoogleTest.tsx`
- Modify: `frontend/src/App.tsx`

**Step 1: Write the failing test**
Create a test in `frontend/src/App.test.tsx` (or modify it) to verify that we have a Tests tab and clicking it reveals sub-navigation for Slack Test and Google Test.

**Step 2: Run test to verify it fails**
Run: `cd frontend && npm run test`
Expected: FAIL due to missing Tests tab.

**Step 3: Write minimal implementation**
1. Move `SlackTest` logic if needed, or keep it in `frontend/src/SlackTest.tsx`.
2. Create `frontend/src/GoogleTest.tsx` with fields:
   - Config check (Is Google Configured in `.env`?)
   - Connect Account button (redirects `window.location.href` to `http://localhost:4000/api/google/login`).
   - Authenticated Accounts dropdown: lets user select from currently authenticated accounts (emails) returned by `/api/google/status`.
   - "Fetch Data" button to fetch emails and calendar events.
   - List layout of last 5 emails and last 5 calendar events.
3. In `frontend/src/App.tsx`, update active tab choices to: `dashboard` and `tests`.
4. In `tests` tab view, render sub-tabs: "Slack Test" and "Google Test".

**Step 4: Run test to verify it passes**
Run: `cd frontend && npm run test`
Expected: PASS

**Step 5: Commit**
```bash
git add frontend/src/App.tsx frontend/src/GoogleTest.tsx
git commit -m "feat(frontend): refactor navigation and implement GoogleTest component"
```

---

### Task 8: End-to-End Validation and Code Review

**Step 1: Perform complete manual verification**
1. Startup FastAPI Backend: `cd backend && source venv/bin/activate && uvicorn app.main:app --port 4000 --reload`
2. Startup Frontend: `cd frontend && npm run dev`
3. Open browser to `http://localhost:5173/tests`
4. Verify SlackTest and GoogleTest tabs display correctly.
5. Check if environment parameters check is fully operational.
6. Verify OAuth callback logic behaves as expected.

**Step 2: Submit for code review**
Using @code-reviewer to ensure the implementation is robust, correct, and follows all conventions.
