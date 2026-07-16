# Family AI Agent Implementation Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a local-first Family AI Agent with a Python/FastAPI backend, React frontend, SQLite storage, and integrations with Google Workspace, Gemini, and WeChat Work.

**Architecture:** Local Monorepo with a distinct `backend/` and `frontend/` directory.

**Tech Stack:** Python 3 (FastAPI, SQLAlchemy, Pytest), Node.js (React, Vite), SQLite.

---

### Task 1: Initialize Python Backend and Health Check

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_main.py`
- Create: `backend/pytest.ini`

**Step 1: Write the failing test**

```python
# backend/tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_main.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app'"

**Step 3: Write minimal implementation**

```text
# backend/requirements.txt
fastapi
uvicorn
pytest
httpx
```

```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

```ini
# backend/pytest.ini
[pytest]
pythonpath = .
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pip install -r requirements.txt && python -m pytest tests/test_main.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/requirements.txt backend/app/main.py backend/tests/test_main.py backend/pytest.ini
git commit -m "feat(backend): initialize fastapi and health check endpoint"
```

---

### Task 2: Initialize React Frontend

**Files:**
- Create: `frontend/package.json` (via Vite)
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.test.tsx` (using vitest)

**Step 1: Write the failing test (or setup scaffolding to allow one)**

We will use `create-vite` to scaffold, then add a simple test.

```bash
# Note: we execute this as the first action before writing the test file directly
cd frontend && npm install vitest @testing-library/react @testing-library/jest-dom jsdom --save-dev
```

```typescript
# frontend/src/App.test.tsx
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders dashboard heading', () => {
  render(<App />);
  const headingElement = screen.getByText(/Family AI Agent Dashboard/i);
  expect(headingElement).toBeDefined();
});
```

**Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/App.test.tsx`
Expected: FAIL (Text not found in default Vite App.tsx)

**Step 3: Write minimal implementation**

```typescript
// frontend/src/App.tsx
import './App.css'

function App() {
  return (
    <div>
      <h1>Family AI Agent Dashboard</h1>
    </div>
  )
}

export default App
```

**Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/App.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/
git commit -m "feat(frontend): initialize react vite project and basic dashboard"
```

---

### Task 3: Backend Database Schema Setup (SQLite)

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/tests/test_database.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, FamilyMember

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_create_family_member():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    member = FamilyMember(name="Alice", email="alice@example.com")
    db.add(member)
    db.commit()
    db.refresh(member)
    assert member.id is not None
    assert member.name == "Alice"
    db.close()
    Base.metadata.drop_all(bind=engine)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_database.py -v`
Expected: FAIL with "ImportError: cannot import name 'Base'"

**Step 3: Write minimal implementation**

```python
# backend/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./family.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
```

```python
# backend/app/models.py
from sqlalchemy import Column, String, Integer, Boolean, Text
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    google_refresh_token = Column(String, nullable=True)
    is_authenticated = Column(Boolean, default=False)

class FamilyPreferences(Base):
    __tablename__ = "family_preferences"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_type = Column(String)
    sub_type = Column(String)
    lead_time_days = Column(Integer)
    preferred_season = Column(String, nullable=True)
    preferences_summary = Column(Text, nullable=True)
```

*(Note: Add `sqlalchemy` to `requirements.txt` before running the test)*

**Step 4: Run test to verify it passes**

Run: `cd backend && echo "sqlalchemy" >> requirements.txt && pip install -r requirements.txt && python -m pytest tests/test_database.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/database.py backend/app/models.py backend/tests/test_database.py backend/requirements.txt
git commit -m "feat(backend): implement sqlite database models for family members and preferences"
```

---

### Task 4: Slack SDK Integration

**Files:**
- Create: `backend/app/services/slack_service.py`
- Create / Update: `backend/tests/test_main.py`

**Step 1: Write the Slack service implementation**

```python
# backend/app/services/slack_service.py
import os
import logging
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SlackClient:
    def __init__(self):
        token = os.getenv("SLACK_BOT_TOKEN")
        if not token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is not set.")
        self.client = WebClient(token=token)

    def send_message(self, target_id: str, text: str) -> Optional[dict]:
        try:
            response = self.client.chat_postMessage(channel=target_id, text=text)
            return response.data
        except SlackApiError as e:
            logger.error(f"Error sending message to Slack: {e.response['error']}")
            return None
```

**Step 2: Run backend tests to verify connectivity & Mock routing**

Run: `cd backend && python -m pytest tests/test_main.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/app/services/slack_service.py backend/tests/test_main.py
git commit -m "feat(backend): add slack sdk integration service"
```
