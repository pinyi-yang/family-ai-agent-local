# Setup & Run Guide: Family AI Agent

This guide walks you through setting up the required API tokens, configuring your local environment, and running the Family AI Agent.

## 1. Prerequisites
- **Python 3.9+**
- **Node.js 18+** (and npm)
- A **Google Cloud Platform (GCP)** account.
- A **Slack Workspace** (with permissions to create a Slack App).
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

# --- Slack Bot Configuration ---
SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"
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

### C. Slack Bot Token Setup
1. Go to the [Slack API Portal](https://api.slack.com/apps).
2. Click **Create New App** -> Select **From scratch**.
3. Enter your App Name (e.g., "Family AI Agent") and select your target family workspace.
4. Go to **OAuth & Permissions** under Features.
5. Scroll down to **Scopes > Bot Token Scopes**, and add the `chat:write` scope (allowing the bot to post messages).
6. Scroll up and click **Install to Workspace**, then authorize the app.
7. Copy the generated **Bot User OAuth Token** (starts with `xoxb-`) and paste it as `SLACK_BOT_TOKEN` in your backend `.env` file.
8. Invite your new bot to any Slack channel you wish to send notifications to (e.g., type `/invite @FamilyAgent` or right-click the channel, select Integrations -> Add an App).

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
