# Family AI Agent - Project Instructions

This file contains the foundational architectural decisions, conventions, and workflows for the `family-ai-agent-local` repository. The Gemini AI agent will read this file automatically at the start of every session to ensure consistency.

## 🏗️ Architecture & Tech Stack
This project is a **Local Monorepo** designed to run exclusively on the user's local machine (`localhost`). It consists of two main parts:

1. **Backend (`/backend`)**:
   - **Language:** Python 3.9+
   - **Framework:** FastAPI
   - **Database:** SQLite with SQLAlchemy ORM
   - **Testing:** `pytest`
   - **Key Integrations:** Google Workspace API (OAuth loopback), Google GenAI SDK (Gemini), `slack-sdk` (for Slack Integration).
   - **Execution:** Runs on `localhost:4000`. Requires activating the virtual environment (`venv`).

2. **Frontend (`/frontend`)**:
   - **Language:** TypeScript
   - **Framework:** React 19 scaffolded via Vite
   - **Styling:** Vanilla CSS (Do NOT use TailwindCSS unless explicitly requested).
   - **Testing:** `vitest` + `@testing-library/react` + `jsdom`.
   - **Execution:** Runs on Vite's default local port (usually `3000` or `5173`).

---

## 🛠️ Development Conventions & Rules

### 1. Test-Driven Development (TDD) is Mandatory
Whenever implementing a new feature or fixing a bug, you MUST follow the TDD lifecycle:
1. **Red:** Write a failing test first. Verify it fails.
2. **Green:** Write the minimal implementation required to make the test pass.
3. **Refactor:** Clean up the code while ensuring tests remain green.

### 2. Testing Commands
Always use the following commands to run test suites:
- **Backend:** `cd backend && source venv/bin/activate && pytest -v`
- **Frontend:** `cd frontend && npm run test`

### 3. Database Management
- Always use **SQLite**. 
- Database files (`*.db`) are ignored in version control (`.gitignore`).
- For testing database logic, use an in-memory SQLite database or a temporary test database that is deleted after the test suite runs.

### 4. API & Integration Guidelines
- **Google OAuth:** Must follow the desktop/loopback IP address flow.
- **Slack Notifications:** We use the official Slack WebClient (`slack-sdk`) to securely broadcast updates, event schedules, and daily summaries to a designated Slack channel in the workspace. Ensure `SLACK_BOT_TOKEN` is set in the environment variables.
- **Gemini Prompts:** Prefer using Gemini's "Structured Outputs" (JSON Schema / Pydantic models) when analyzing emails and extracting calendar events to ensure predictable parsing.

### 5. Git Workflow
- Keep commits small, atomic, and conventionally formatted (e.g., `feat(backend): ...`, `fix(frontend): ...`, `chore: ...`).
- Never commit `.env` files or hardcoded credentials.