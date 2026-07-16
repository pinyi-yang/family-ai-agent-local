# Family AI Agent

**Family AI Agent** is a privacy-first, locally-hosted application designed to coordinate, plan, and remind family members about key recurring and seasonal events (e.g., summer camps, health checkups, travel). 

It securely integrates with multiple family members' Google Workspace accounts, utilizes Google Gemini to learn historical scheduling habits, and sends proactive notifications and daily summaries to a shared Slack channel.

---

## 🏗️ Architecture
This project is structured as a **Local Monorepo**:

- **Backend (`/backend`)**: Built with **Python 3 and FastAPI**. Handles local SQLite database interactions, Google OAuth loops, Gemini AI data extraction, and the APScheduler background tasks.
- **Frontend (`/frontend`)**: Built with **React and Vite**. Serves as the local dashboard to link Google accounts and view learned family scheduling profiles.
- **Database**: Local **SQLite** (`family.db`) to store encrypted refresh tokens and analyzed preferences securely on your machine.
- **Notifications**: Uses the official **Slack WebClient** to securely publish updates and daily morning digests to a family Slack workspace channel.

---

## 📚 Documentation
Detailed documentation on the app's expectations, design, and execution plans can be found in the `docs/` folder:

- [App Expectations & Requirements](docs/APP_EXPECTATIONS.md) - The high-level behaviors and features of the agent.
- [System Design Document](docs/plans/2026-07-12-family-agent-design.md) - The architectural choices and data flow.
- [Setup & Run Guide](docs/SETUP_GUIDE.md) - Instructions on running the app, getting API keys (Google/Gemini), and setting up the Slack integration.

---

## 🚀 Quick Start

To run the application locally, you will need API tokens for Google OAuth, Gemini, and Slack. 

**👉 See the [Setup & Run Guide](docs/SETUP_GUIDE.md) for full instructions.**

### Briefly:
1. Copy API tokens into `backend/.env`.
2. Start the Backend:
   ```bash
   cd backend
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 4000
   ```
3. Start the Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
