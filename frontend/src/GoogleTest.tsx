import { useState, useEffect, useRef, useCallback } from "react";

const API_BASE_URL = "http://localhost:4000";

interface AuthenticatedAccount {
  email: string;
  name: string;
}

interface GoogleEmail {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
}

interface GoogleEvent {
  id: string;
  summary: string;
  start: string;
  end: string;
  link: string;
}

export default function GoogleTest() {
  const [isConfigured, setIsConfigured] = useState<boolean>(false);
  const [authenticatedAccounts, setAuthenticatedAccounts] = useState<AuthenticatedAccount[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<string>("");
  const [checking, setChecking] = useState<boolean>(false);
  const [statusError, setStatusError] = useState<string | null>(null);

  // Success Banner
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Email and Calendar States
  const [emails, setEmails] = useState<GoogleEmail[]>([]);
  const [loadingEmails, setLoadingEmails] = useState<boolean>(false);
  const [emailsError, setEmailsError] = useState<string | null>(null);

  const [events, setEvents] = useState<GoogleEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState<boolean>(false);
  const [eventsError, setEventsError] = useState<string | null>(null);

  // System logs
  const [logs, setLogs] = useState<string[]>([]);
  const hasCheckedStatusRef = useRef<boolean>(false);

  const addLog = useCallback((msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [`[${timestamp}] ${msg}`, ...prev]);
  }, []);

  // Check URL params for success redirect
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("google_success") === "true") {
      setSuccessBanner("🎉 Google account connected successfully!");
      addLog("Authentication redirect detected: account linked successfully!");
      
      // Clean up URL query parameters
      const newUrl = window.location.pathname + window.location.hash;
      window.history.replaceState({}, document.title, newUrl);
    }
  }, [addLog]);

  const checkGoogleStatus = useCallback(async () => {
    setChecking(true);
    setStatusError(null);
    try {
      addLog("Checking Google OAuth configuration and status...");
      const response = await fetch(`${API_BASE_URL}/api/google/status`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to fetch status`);
      }
      const data = await response.json();
      setIsConfigured(data.is_configured);
      setAuthenticatedAccounts(data.authenticated_accounts || []);
      
      if (data.authenticated_accounts && data.authenticated_accounts.length > 0) {
        // Default to first email if none currently selected
        setSelectedEmail((current) => current || data.authenticated_accounts[0].email);
        addLog(`Found ${data.authenticated_accounts.length} authenticated Google account(s).`);
      } else if (data.is_configured) {
        addLog("Google integration is configured but no accounts are authenticated yet.");
      } else {
        addLog("Google OAuth is not configured. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI in your backend .env.");
      }
    } catch (err: any) {
      addLog(`Error checking status: ${err.message}`);
      setStatusError(err.message);
    } finally {
      setChecking(false);
    }
  }, [addLog]);

  // Check on mount
  useEffect(() => {
    if (!hasCheckedStatusRef.current) {
      hasCheckedStatusRef.current = true;
      checkGoogleStatus();
    }
  }, [checkGoogleStatus]);

  // Connect Google account (redirect)
  const handleConnectAccount = () => {
    addLog("Redirecting to Google login authorization endpoint...");
    window.location.href = `${API_BASE_URL}/api/google/login`;
  };

  // Fetch Emails
  const fetchEmails = useCallback(async () => {
    if (!selectedEmail) return;
    setLoadingEmails(true);
    setEmailsError(null);
    addLog(`Fetching Gmail messages for ${selectedEmail}...`);
    try {
      const response = await fetch(`${API_BASE_URL}/api/google/emails?email=${encodeURIComponent(selectedEmail)}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to fetch emails`);
      }
      const data = await response.json();
      setEmails(data);
      addLog(`Successfully retrieved ${data.length} Gmail messages.`);
    } catch (err: any) {
      addLog(`Error fetching emails: ${err.message}`);
      setEmailsError(err.message);
    } finally {
      setLoadingEmails(false);
    }
  }, [selectedEmail, addLog]);

  // Fetch Calendar
  const fetchCalendar = useCallback(async () => {
    if (!selectedEmail) return;
    setLoadingEvents(true);
    setEventsError(null);
    addLog(`Fetching upcoming Google Calendar events for ${selectedEmail}...`);
    try {
      const response = await fetch(`${API_BASE_URL}/api/google/calendar?email=${encodeURIComponent(selectedEmail)}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to fetch calendar`);
      }
      const data = await response.json();
      setEvents(data);
      addLog(`Successfully retrieved ${data.length} upcoming calendar events.`);
    } catch (err: any) {
      addLog(`Error fetching calendar events: ${err.message}`);
      setEventsError(err.message);
    } finally {
      setLoadingEvents(false);
    }
  }, [selectedEmail, addLog]);

  // Trigger automated fetches when selected email changes
  useEffect(() => {
    if (selectedEmail) {
      fetchEmails();
      fetchCalendar();
    } else {
      setEmails([]);
      setEvents([]);
    }
  }, [selectedEmail, fetchEmails, fetchCalendar]);

  return (
    <div className="wechat-test-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2 className="title" style={{ margin: 0 }}>Google Workspace Testing Tool</h2>
        <button 
          className="btn btn-secondary" 
          onClick={checkGoogleStatus} 
          disabled={checking}
        >
          {checking ? "Checking..." : "🔄 Refresh Status"}
        </button>
      </div>

      {successBanner && (
        <div className="result-alert success" style={{ marginBottom: "20px" }}>
          {successBanner}
          <button 
            style={{ float: "right", background: "none", border: "none", cursor: "pointer", fontSize: "16px", color: "inherit" }}
            onClick={() => setSuccessBanner(null)}
          >
            ×
          </button>
        </div>
      )}

      <div className="layout-grid">
        {/* Left Column: Connection Info & Account Selector */}
        <div className="column">
          <div className="card">
            <h3>🔑 Google Integration Status</h3>
            {isConfigured ? (
              <div className="status-badge logged-in">
                <span>🟢 Environment Configured</span>
                <p style={{ fontSize: "14px", marginTop: "10px", lineHeight: "1.5" }}>
                  Google API credentials are set in <code>.env</code>. Ready to connect and fetch user calendar and email resources.
                </p>
                <button 
                  className="btn btn-primary" 
                  onClick={handleConnectAccount}
                  style={{ marginTop: "10px", width: "100%" }}
                >
                  🔌 Connect Google Account
                </button>
              </div>
            ) : (
              <div className="status-badge logged-out">
                <span>🔴 Not Configured</span>
                <p style={{ fontSize: "13px", marginTop: "10px", marginBottom: 0 }}>
                  Google Client credentials are missing from your backend <code>.env</code>.
                </p>
              </div>
            )}
            {statusError && (
              <div className="result-alert error" style={{ marginTop: "12px" }}>
                Status Error: {statusError}
              </div>
            )}
          </div>

          <div className="card">
            <h3>👤 Selected Account</h3>
            {authenticatedAccounts.length > 0 ? (
              <div className="form-group" style={{ marginBottom: 0 }}>
                <label htmlFor="account-select">Select authenticated user:</label>
                <select
                  id="account-select"
                  className="form-control"
                  style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "1px solid var(--border)", background: "var(--bg)", color: "var(--text)" }}
                  value={selectedEmail}
                  onChange={(e) => setSelectedEmail(e.target.value)}
                >
                  {authenticatedAccounts.map((account) => (
                    <option key={account.email} value={account.email}>
                      {account.name} ({account.email})
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <p className="subtitle" style={{ margin: 0, fontStyle: "italic" }}>
                No accounts authenticated. Click "Connect Google Account" to authorize a user.
              </p>
            )}
          </div>

          {!isConfigured && (
            <div className="card qr-card" style={{ padding: "20px" }}>
              <h3>ℹ️ Google OAuth Setup Guide</h3>
              <p className="subtitle" style={{ fontSize: "14px", lineHeight: "1.6" }}>
                Ensure you have created a <strong>Desktop Application</strong> or <strong>Web Application</strong> credential in Google Cloud Console and added the details to your <code>.env</code> file:
              </p>
              <pre style={{ background: "#272822", color: "#f8f8f2", padding: "12px", borderRadius: "6px", fontSize: "11px", overflowX: "auto" }}>
{`GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="GOCSPX-your-secret"
GOOGLE_REDIRECT_URI="http://localhost:4000/api/google/callback"`}
              </pre>
            </div>
          )}

          <div className="card logs-card" style={{ marginTop: "20px" }}>
            <h3>📋 System Log Output</h3>
            <div className="console-log" style={{ maxHeight: "180px" }}>
              {logs.map((log, index) => (
                <div key={index} className="log-line">{log}</div>
              ))}
              {logs.length === 0 && <div className="log-line empty">Monitoring Google Workspace status...</div>}
            </div>
          </div>
        </div>

        {/* Right Column: Gmail & Calendar view */}
        <div className="column">
          {selectedEmail ? (
            <>
              {/* Gmail List */}
              <div className="card" style={{ minHeight: "220px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
                  <h3 style={{ margin: 0 }}>📧 Recent Emails (Gmail)</h3>
                  <button 
                    className="btn btn-secondary" 
                    onClick={fetchEmails} 
                    disabled={loadingEmails}
                    style={{ padding: "4px 10px", fontSize: "13px" }}
                  >
                    {loadingEmails ? "Fetching..." : "🔄 Refresh"}
                  </button>
                </div>

                {loadingEmails ? (
                  <p className="subtitle" style={{ fontStyle: "italic" }}>Loading messages...</p>
                ) : emailsError ? (
                  <div className="result-alert error">
                    Error loading emails: {emailsError}
                  </div>
                ) : emails.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {emails.map((email) => (
                      <div key={email.id} style={{ padding: "12px", border: "1px solid var(--border)", borderRadius: "8px", background: "var(--social-bg)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", fontWeight: "600", color: "var(--text-h)" }}>
                          <span>Subject: {email.subject}</span>
                          <span style={{ fontSize: "11px", color: "var(--text)", fontWeight: "normal" }}>{email.date}</span>
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--text)", marginTop: "4px" }}>
                          <strong>From:</strong> {email.from}
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--text)", fontStyle: "italic", marginTop: "6px", borderLeft: "2px solid var(--border)", paddingLeft: "8px" }}>
                          {email.snippet}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="subtitle" style={{ fontStyle: "italic" }}>No messages found in this inbox.</p>
                )}
              </div>

              {/* Calendar Events */}
              <div className="card" style={{ minHeight: "220px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
                  <h3 style={{ margin: 0 }}>📅 Upcoming Events (Google Calendar)</h3>
                  <button 
                    className="btn btn-secondary" 
                    onClick={fetchCalendar} 
                    disabled={loadingEvents}
                    style={{ padding: "4px 10px", fontSize: "13px" }}
                  >
                    {loadingEvents ? "Fetching..." : "🔄 Refresh"}
                  </button>
                </div>

                {loadingEvents ? (
                  <p className="subtitle" style={{ fontStyle: "italic" }}>Loading schedule...</p>
                ) : eventsError ? (
                  <div className="result-alert error">
                    Error loading calendar: {eventsError}
                  </div>
                ) : events.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {events.map((event) => (
                      <div key={event.id} style={{ padding: "12px", border: "1px solid var(--border)", borderRadius: "8px", background: "var(--social-bg)" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", fontWeight: "600", color: "var(--text-h)" }}>
                          <span>Event: {event.summary}</span>
                          {event.link && (
                            <a href={event.link} target="_blank" rel="noopener noreferrer" style={{ fontSize: "12px", color: "var(--accent)" }}>
                              View ↗
                            </a>
                          )}
                        </div>
                        <div style={{ fontSize: "12px", color: "var(--text)", marginTop: "6px" }}>
                          📅 <strong>Time:</strong> {new Date(event.start).toLocaleString()} - {new Date(event.end).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="subtitle" style={{ fontStyle: "italic" }}>No upcoming events scheduled on the primary calendar.</p>
                )}
              </div>
            </>
          ) : (
            <div className="card" style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "300px", color: "var(--text)" }}>
              <p style={{ fontStyle: "italic" }}>Please connect or select an authenticated account on the left pane to view Google resources.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
