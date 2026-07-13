# System Design: Family AI Agent (Local)

**Date:** July 12, 2026
**Architecture Style:** Local Monorepo (Python/FastAPI Backend + React/Vite Frontend)

## 1. Overview
The Family AI Agent is a privacy-first, locally-hosted application designed to coordinate, plan, and remind family members about key recurring and seasonal events. It integrates with multiple Google Workspace accounts, uses Gemini for deep historical scheduling analysis, and sends summaries and proactive alerts via a WeChat Work Webhook.

## 2. Technology Stack
*   **Backend:** Python 3 (FastAPI, Uvicorn). Selected for superior data manipulation capabilities and native integration with Google/GenAI SDKs.
*   **Frontend:** React (TypeScript) + Vite + Vanilla CSS. Provides a local dashboard for managing users and viewing logs.
*   **Database:** SQLite (via SQLAlchemy). A single local file (`family.db`) to store encrypted credentials and analyzed profiles.
*   **AI Engine:** Google Gemini (`gemini-2.5-flash` or `gemini-2.5-pro`) using structured JSON schema extraction.
*   **Notification Channel:** WeChat Work Group Webhook (Official, free, and stable approach compared to personal WeChat automation).

## 3. Core Workflows

### 3.1. Authentication (Google OAuth Loopback)
To authenticate users locally without a public domain:
1.  The React frontend initiates the OAuth flow, opening the system browser.
2.  Google redirects to a fixed local port (e.g., `http://localhost:4000/api/auth/callback`).
3.  FastAPI exchanges the code for a `refresh_token`, encrypts it, and saves it in SQLite.

### 3.2. Initialization (Init) & Profile Extraction
Triggered manually via the dashboard once the user confirms **all family members have been linked**.

**Two-Pass Gemini Analysis Pipeline:**
*   **Data Fetch:** Fetch the last 2 years of Gmail, Calendar events, and Drive metadata for *all* linked accounts.
*   **Pass 1 (Triage):** Gemini categorizes key emails into hierarchical buckets (e.g., `Type: Health` -> `Sub-Type: Dental` or `Type: Travel` -> `Sub-Type: Summer Trip`).
*   **Pass 2 (Deep Pattern Analysis):** For each specific sub-group, Gemini analyzes the chronological data to determine:
    *   Typical lead time (days between booking and the event).
    *   Preferred seasons/months.
    *   Preferred providers/locations.
*   **Storage & Broadcast:** These hierarchical profiles are saved to the database, and a detailed "Welcome Summary" is posted to the WeChat group.

### 3.3. Daily Operational Cycle (After Init)
Managed by a background scheduler (`APScheduler`) running daily (e.g., at 7:00 AM).

1.  **Email-to-Calendar Sync:**
    *   Fetch emails from the last 24 hours.
    *   Gemini identifies new key event confirmations.
    *   Backend automatically creates corresponding Google Calendar events.
2.  **Proactive Reminders (Lead Time Checks):**
    *   Compare current date against learned profiles.
    *   *Example:* If a "Health -> Dental" check is usually booked 30 days ahead of August, and it is now July with no event found, trigger a reminder.
    *   Gemini optionally uses web search to provide custom recommendations (e.g., nearby highly-rated dentists) based on the profile.
3.  **WeChat Digest Dispatch:**
    *   Compile today's events, short notices extracted from emails, and any proactive recommendations.
    *   Send via HTTP POST to the WeChat Work Webhook.
    *   *No-Noise Policy:* If there are no events and no recommendations, skip sending the message.

## 4. Database Schema Outline (SQLAlchemy)

*   **`FamilyMember`:** `id`, `name`, `email`, `google_refresh_token`, `is_authenticated`.
*   **`FamilyPreferences`:** `id`, `event_type` (e.g., Health), `sub_type` (e.g., Dental), `lead_time_days`, `preferred_season`, `preferences_summary`.
*   **`ExecutionLogs`:** `id`, `timestamp`, `task_name`, `status`, `message`.
