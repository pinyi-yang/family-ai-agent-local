# WeChat QR Client Integration Plan

> **For Gemini:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Integrate the WeChat iLink QR-code client into the FastAPI backend, expose HTTP API endpoints for authentication and message sending, and build a beautiful test page in the React frontend to scan the QR code, log in, and test sending messages.

**Architecture:**
1. Complete the missing type definitions in `backend/app/services/wechat/types.py` to resolve import errors.
2. Initialize a global `WeChatBot` instance in the FastAPI backend that runs its poll loop in the background.
3. Expose non-blocking REST API endpoints for QR generation, polling status, fetching active sessions, and sending messages.
4. Implement frontend UI component for scanning QR codes, displaying login status, viewing active sessions, and sending messages.

**Tech Stack:** FastAPI, aiohttp, Python, React (TypeScript), CSS.

---

### Task 1: Complete Type Definitions and Verify Core Imports

**Files:**
- Modify: `backend/app/services/wechat/types.py`
- Modify: `backend/requirements.txt`

**Step 1: Write type definitions and add aiohttp**

We will write the complete types to `backend/app/services/wechat/types.py` and add `WeChatMessage = WeixinMessage` as a backward compatibility alias because `client.py` references `WeChatMessage`.
We will also append `aiohttp` to `backend/requirements.txt`.

**Step 2: Install dependencies**

Run: `cd backend && source venv/bin/activate && pip install -r requirements.txt`
Expected: Successful installation of `aiohttp`.

**Step 3: Run baseline tests to verify import errors are resolved**

Run: `cd backend && source venv/bin/activate && pytest -v`
Expected: Pytest runs and passes (or fails only on the old `send_wechat_message` test, but imports succeed).

---

### Task 2: Implement WeChat Bot Lifetime and FastAPI API Endpoints

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/wechat.py`

**Step 1: Update `backend/app/services/wechat.py`**

We will update the original `wechat.py` to export a unified helper that can either use the `WeChatBot` global instance or fall back to the webhook.

**Step 2: Mount WeChat Bot and Endpoints in `backend/app/main.py`**

We will:
- Set up a Lifespan context manager to start and stop the `WeChatBot` background task cleanly.
- Define endpoints:
  - `GET /api/wechat/qr`: Fetches a fresh QR code from WeChat API.
  - `GET /api/wechat/status?qrcode=<qrcode>`: Polls the QR code status. If confirmed, saves the credentials.
  - `GET /api/wechat/sessions`: Lists all cached contact sessions (`user_id` -> `context_token`) that have interacted with the bot.
  - `POST /api/wechat/send`: Sends a message to a user. If `context_token` is not supplied, it uses the cached in-memory one.

---

### Task 3: Write Backend Unit Tests for WeChat Endpoints

**Files:**
- Modify: `backend/tests/test_wechat.py`

**Step 1: Update WeChat tests**

We will write unit tests for the endpoints and mock the underlying api calls (`fetch_qr_code`, `poll_qr_status`, `send_message`, etc.) to verify:
- QR code fetching endpoint.
- QR status polling endpoint.
- Send message endpoint.
We will run `pytest -v` to ensure all tests pass.

---

### Task 4: Create React Frontend WeChat Test Page

**Files:**
- Create: `frontend/src/WeChatTest.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/App.css`

**Step 1: Implement the UI Component**

Create `frontend/src/WeChatTest.tsx` with:
- QR Code display (using an `<img>` tag showing the Base64 QR code returned by `/api/wechat/qr`).
- Real-time polling of login status.
- Session List displaying active users/conversations.
- Message input and Send button.

**Step 2: Add Route / Component to App.tsx**

Modify `frontend/src/App.tsx` to render the `WeChatTest` page under a dedicated tab or section.

**Step 3: Add Styles to App.css**

Add CSS definitions to make the page visually modern, aligned with the YOLO/new application mandates.

---

### Task 5: End-to-End Verification

**Step 1: Build Frontend and Backend**

- Build frontend: `cd frontend && npm run build`
- Run linting: `cd frontend && npm run lint`
- Run frontend tests: `cd frontend && npm run test`
- Run backend tests: `cd backend && source venv/bin/activate && pytest`

**Expected:** All tests pass, build compiles successfully.
