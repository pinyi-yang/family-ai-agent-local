# Family AI Agent - App Expectations & Requirements

This document captures the formal requirements and behavioral specifications for the local Family AI Agent application.

## 🎯 Purpose
The Family AI Agent is a local-first helper designed to coordinate, plan, and remind family members about key recurring and seasonal events (e.g., summer camps, routine health checks, vacations). It operates securely on a local machine, interfacing with family members' Google Workspace accounts, analyzing scheduling preferences via Gemini, and sending updates/reminders to a shared Slack channel.

---

## ⚙️ Key Behavior & Phases

### 1. Initialization Phase (`Init`)
*   **Multi-Account Authentication (Google OAuth 2.0):**
    *   Securely request and store credentials for multiple family members.
    *   Scopes required: Gmail (readonly), Google Calendar (read/write), Google Drive (readonly/file scope).
*   **Historical Data Retrieval:**
    *   Query Gmail threads, Calendar events, and Google Drive files for the **last 2 years** looking for keywords/metadata related to family events (e.g., "summer camp", "health check", "vaccine", "pediatrician", "flight", "itinerary", "booking").
*   **Preference & Pattern Learning (Gemini Analysis):**
    *   Utilize Gemini to analyze the retrieved 2-year history.
    *   Identify custom family scheduling patterns:
        *   *Planning Lead-Times:* How long in advance they book summer camps (e.g., 4 months ahead) or schedule health checks (e.g., 2 weeks ahead).
        *   *Activity Preferences:* Preferred camp providers, dental offices, travel destinations, etc.
    *   Save these structured preferences locally as the family's "Coordinating Profile" for future trigger evaluation.

---

### 2. Operational Phase (`After Init` / Daily Lifecycle)
The app runs a daily background task (cron/interval) that performs two key checks:

*   **Email-to-Calendar Automation:**
    *   Monitor incoming emails of family members.
    *   If a new email is classified by Gemini as a key family event (e.g., camp confirmation, appointment confirmation):
        *   Extract critical event details (date, time, location, confirmation number, requirements).
        *   Automatically create a matching Google Calendar event with the parsed details.
*   **Daily Slack Notification & Contextual Briefing:**
    *   Send a daily morning digest to the Slack family channel containing:
        *   *Today's/Upcoming Events:* Detailed list of today's key schedules.
        *   *Short Notices:* Useful reminders parsed from attachments or descriptions (e.g., "Bring water bottle and swimsuit for summer camp today", "Check-in open for flight tomorrow").
    *   *No-Noise Policy:* If no events or notices exist for the day, **do not** send any Slack message.
*   **Proactive Scheduling Reminders & Search Integration:**
    *   Check recursive events against learned lead-times (from the Init phase).
    *   *Trigger:* If a recursive event (e.g., annual dental checkup usually booked in August) has not been scheduled, and the current date is past the typical lead-time threshold (e.g., it is now July and no appointment is on the calendar):
        *   Trigger Gemini to research potential recommendations based on learned family preferences (e.g., search local dentists or camps).
        *   Include custom, highly-relevant recommendations directly in the daily Slack message to prompt action.

---

## 🔌 Technical Touchpoints
1.  **Backend (Local Host):** Manages OAuth redirection, background schedulers, database, Gemini API orchestrator, and Slack hook.
2.  **Frontend (Local Host):** Interactive dashboard for family profiles setup, authentication management, profile review, and notification logs.
3.  **Local Database:** A secure local database (e.g., SQLite) to hold OAuth credentials (refresh tokens), learned preferences, execution logs, and notification queue.
4.  **Slack Gateway:** Integration layer to send notifications to Slack workspace channels or direct messages.
