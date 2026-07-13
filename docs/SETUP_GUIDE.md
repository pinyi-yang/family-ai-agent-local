# Setup & Run Guide: Family AI Agent

This guide walks you through setting up the required API tokens, configuring your local environment, and running the Family AI Agent.

## 1. Prerequisites
- **Python 3.9+**
- **Node.js 18+** (and npm)
- A **Google Cloud Platform (GCP)** account.
- A **WeChat Work (Enterprise WeChat)** account.
- A **Google AI Studio** account (for Gemini).

---

## 2. Environment Variables (.env)

You need to inject your secure API tokens into the backend. Create a `.env` file in the `backend/` directory:

```bash
cd backend
touch .env
```

Add the following structure to your `backend/.env` file:

```ini
# --- Google OAuth 2.0 Credentials ---
GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GOOGLE_REDIRECT_URI="http://localhost:4000/api/auth/callback"

# --- Gemini API ---
GEMINI_API_KEY="your-gemini-api-key"

# --- WeChat Work Webhook ---
WECHAT_WEBHOOK_URL="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key"
```

---

## 3. Obtaining the API Tokens

### A. Google Workspace (OAuth Credentials)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., "Family AI Agent").
3. Navigate to **APIs & Services > Credentials**.
4. Click **Create Credentials > OAuth client ID**.
5. Choose **Web application** as the application type.
6. Under **Authorized redirect URIs**, add exactly: `http://localhost:4000/api/auth/callback`.
7. Click Create. Copy the **Client ID** and **Client Secret** into your `.env` file.
8. *Note:* Ensure you enable the **Gmail API**, **Google Calendar API**, and **Google Drive API** in the "Library" section of the console.

### B. Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Get API key** and generate a new key.
3. Copy the key into `GEMINI_API_KEY` in your `.env` file.

### C. WeChat Work Webhook Setup
1. Download and sign up for **WeChat Work** (企业微信). You can create an organization for free as an individual.
2. Create a new Group Chat for your family.
3. Right-click the group chat (on desktop) or go to group settings and select **Add Group Robot** (添加群机器人).
4. Create a new robot and copy its **Webhook URL**.
5. Paste this URL into `WECHAT_WEBHOOK_URL` in your `.env` file.

---

## 4. Running the Application

Because this is a local-first application, you will need to start both the Backend (Python) and the Frontend (React) in separate terminal windows.

### Terminal 1: Start the Backend (FastAPI)
```bash
cd backend

# Create and activate virtual environment (if you haven't already)
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server (defaults to port 4000 based on our OAuth setup)
uvicorn app.main:app --reload --port 4000
```
*The backend API will be available at `http://localhost:4000`.*

### Terminal 2: Start the Frontend (React/Vite)
```bash
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```
*The frontend dashboard will be available at `http://localhost:3000` (or the port Vite specifies).*

## 5. Next Steps
Once both servers are running, open the Frontend URL in your browser to access the Family AI Agent Dashboard and begin the Google account linking process!