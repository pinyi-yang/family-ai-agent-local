# Google Workspace API Integration Guide
This guide outlines the best architectural patterns for authenticating users and accessing **Gmail**, **Google Calendar**, and **Google Drive** across three types of applications: Local Desktop/CLI Apps, Hosted Web Apps, and Mobile Apps.

---

## 1. Local App (Desktop / Localhost Dev Tool)
*When your frontend and backend both run on the user's local machine (`localhost` or `127.0.0.1`).*

### Architectural Pattern
*   **OAuth Client Type:** Desktop Application.
*   **Flow:** Authorization Code Flow with Loopback IP Address (RFC 8252).

```
┌──────────────┐         1. Start temporary HTTP server         ┌────────────────┐
│              ├───────────────────────────────────────────────>│                │
│              │                                                │                │
│  Local App   │         2. Open default browser to Google      │ Google OAuth   │
│   Backend    ├───────────────────────────────────────────────>│ Consent Screen │
│ (localhost)  │                                                │                │
│              │<───────────────────────────────────────────────┤                │
│              │         3. Redirect with Auth Code to Loopback │                │
└──────────────┘                                                └────────────────┘
```

### Implementation Steps
1.  **Spin up a Temporary Server:** Start a lightweight, temporary HTTP server on a random open port on loopback (e.g., `http://127.0.0.1:53213`).
2.  **Open Browser:** Programmatically open the user's default web browser to the Google OAuth consent URL. Include your loopback URI as the `redirect_uri`.
3.  **Capture Code:** When the user consents, Google redirects to `http://127.0.0.1:53213/?code=AUTHORIZATION_CODE`. Capture the code and send a nice "Success! You can close this window" HTML page to the browser.
4.  **Exchange & Close:** Stop the temporary local server, exchange the authorization code for an `access_token` and `refresh_token` securely from your backend code.
5.  **Storage:** Store the `refresh_token` in a secure local database, or utilize the native system keychain (macOS Keychain, Windows Credential Manager).

---

## 2. Web App (Hosted SaaS / Public Web Application)
*When you host a web-accessible application with a distinct frontend and backend server.*

### Architectural Pattern
*   **OAuth Client Type:** Web Application.
*   **Flow:** Authorization Code Flow (Backend-to-Backend exchange).

```
┌──────────┐      1. Directs user to Google Consent Screen     ┌──────────┐
│          ├──────────────────────────────────────────────────>│          │
│          │                                                   │          │
│ Frontend │      3. Redirect with Auth Code to Backend URL    │  Google  │
│ Browser  │<──────────────────────────────────────────────────┤  OAuth   │
│          │                                                   │          │
│          │──────────────────────────────────────────────────>│          │
└────┬─────┘      2. User Consents                             └────┬─────┘
     │                                                              │
     │ 4. Forward Auth Code                                         │ 5. Code + Client Secret
     ▼                                                              ▼
┌──────────┐                                                   ┌──────────┐
│ App      ├──────────────────────────────────────────────────>│ Google   │
│ Backend  │<──────────────────────────────────────────────────┤ Token    │
│ Server   │      6. Returns Access & Refresh Tokens           │ Endpoint │
└──────────┘                                                   └──────────┘
```

### Implementation Steps
1.  **Initiate Flow:** The frontend redirects the user (or opens a popup) to the Google OAuth consent screen.
2.  **Receive Callback:** Set your Google Cloud OAuth Redirect URI to your hosted backend API callback endpoint (e.g., `https://api.yourdomain.com/auth/google/callback`).
3.  **Exchange Securely:** The backend handles the callback request, extracts the authorization code, and sends it to Google's token exchange endpoint along with your **Client Secret**.
4.  **Token Storage:** Save the encrypted `refresh_token` in your database associated with the user's account. Do *not* send the refresh token to the frontend client.
5.  **Secure Proxy:** Create dedicated endpoints on your API backend (e.g., `/api/google/drive/files`). When the frontend requests them, your backend retrieves Google APIs using the stored token and passes the result back to the frontend.

---

## 3. Mobile App (iOS / Android)
*When building native (Swift, Kotlin) or cross-platform (React Native, Flutter) apps.*

### Architectural Pattern
*   **OAuth Client Type:** iOS / Android (Register separate credentials for each OS).
*   **Flow:** Authorization Code Flow with **PKCE** (Proof Key for Code Exchange) using standard system secure browsers (e.g., `ASWebAuthenticationSession` on iOS or `Custom Tabs` on Android).

### Implementation Steps
1.  **Avoid Embedded WebViews:** Google blocks standard WebViews (`WKWebView`, `Android WebView`) for security. You must use the official **Google Sign-In SDK** or standard OAuth libraries (e.g., `react-native-app-auth` or `flutter_appauth`) which utilize platform-secure browser environments.
2.  **Redirect with Custom Schemes:** Configure your redirect URI to use a custom app scheme (e.g., `com.mycompany.app:/oauth2callback`) or Universal/App Links so the OS opens your app automatically when authentication finishes.
3.  **Token Strategy:**
    *   **Backend-Driven (Recommended):** Acquire an ID Token or temporary Auth Code in the app, send it to your backend, and let the backend manage Google API operations.
    *   **Standalone Mobile App:** Store tokens locally using native secure storage (`Keychain` on iOS, `EncryptedSharedPreferences` on Android) and perform direct API requests using client libraries.

---

## 💡 Key Developer Guidelines & Best Practices

### 1. Scope Strategy & The "Restricted Scopes" Warning
Google classifies scopes into **Sensitive** and **Restricted** tiers:
*   **Gmail & Drive** are mostly **Restricted Scopes** (e.g., `.../auth/drive`, `.../auth/gmail.readonly`).
*   **Implication:** If your app is public-facing and requests Restricted Scopes, you must undergo a strict, annual third-party security verification process (CASA Assessment), which can be costly and time-consuming.
*   **Alternative for Drive:** Use the scope `https://www.googleapis.com/auth/drive.file`. This scope only grants your app access to files that *your app itself created* or files explicitly opened by the user via the Google Drive picker. This is a **Sensitive** scope, which bypasses the restrictive CASA assessment.
*   **Alternative for Calendar:** Google Calendar scopes are generally **Sensitive** rather than Restricted, making verification much simpler.

### 2. Auto-refreshing Token Pattern
Do not write custom request logic to handle expired access tokens. Use the official client libraries (e.g., `google-auth-library` and `@googleapis/drive` in Node.js, `google-api-python-client` in Python). 
Once instantiated with a `refresh_token` and client credentials, they handle automatic token rotation, retries, and rate-limiting out of the box.

### 3. Google API Libraries Setup (Node.js Example)
```javascript
const { google } = require('googleapis');

// Create the OAuth2 client
const oauth2Client = new google.auth.OAuth2(
  YOUR_CLIENT_ID,
  YOUR_CLIENT_SECRET,
  YOUR_REDIRECT_REDIRECT_URI
);

// Set credentials (usually retrieved from your database)
oauth2Client.setCredentials({
  refresh_token: USER_REFRESH_TOKEN
});

// Access Calendar API
const calendar = google.calendar({ version: 'v3', auth: oauth2Client });
const response = await calendar.events.list({
  calendarId: 'primary',
  timeMin: new Date().toISOString(),
  maxResults: 10,
  singleEvents: true,
  orderBy: 'startTime',
});
```
