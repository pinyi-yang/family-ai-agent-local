import { useState, useEffect, useRef } from "react";

const API_BASE_URL = "http://localhost:4000";

interface ChatSession {
  user_id: string;
  context_token: string;
}

export default function WeChatTest() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [botUserId, setBotUserId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  
  // QR Login States
  const [qrToken, setQrToken] = useState<string | null>(null);
  const [qrImg, setQrImg] = useState<string | null>(null);
  const [qrStatus, setQrStatus] = useState<string | null>(null);
  
  // Message Sending States
  const [targetUserId, setTargetUserId] = useState<string>("");
  const [explicitContextToken, setExplicitContextToken] = useState<string>("");
  const [messageText, setMessageText] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);
  const [sendResult, setSendResult] = useState<{ success: boolean; message: string } | null>(null);
  
  // Logging / Console feedback
  const [logs, setLogs] = useState<string[]>([]);
  const pollTimerRef = useRef<any>(null);
  const pollingActiveRef = useRef<string | null>(null);
  const hasCheckedStatusRef = useRef<boolean>(false);

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [`[${timestamp}] ${msg}`, ...prev]);
  };

  // 1. Initial Status Check
  const checkInitialStatus = async () => {
    if (hasCheckedStatusRef.current) return;
    hasCheckedStatusRef.current = true;
    try {
      addLog("Checking WeChat login status...");
      const response = await fetch(`${API_BASE_URL}/api/wechat/sessions`);
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(`HTTP ${response.status}: ${text || "Failed to fetch sessions status"}`);
      }
      const data = await response.json();
      
      setIsLoggedIn(data.is_logged_in);
      setBotUserId(data.user_id);
      
      if (data.is_logged_in) {
        setSessions(data.sessions);
        addLog(`Bot is already logged in as: ${data.user_id}. Loaded ${data.sessions.length} active sessions.`);
      } else {
        addLog("Bot is not logged in. You can generate a QR code to log in.");
      }
    } catch (error: any) {
      addLog(`Error checking initial status: ${error.message}`);
    }
  };

  // 2. Fetch Fresh QR Code
  const fetchNewQrCode = async () => {
    try {
      addLog("Fetching new WeChat login QR code...");
      const response = await fetch(`${API_BASE_URL}/api/wechat/qr`);
      if (!response.ok) {
        let errMsg = `HTTP ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errMsg += `: ${errData.detail}`;
        } catch {
          const text = await response.text().catch(() => "");
          if (text) errMsg += `: ${text}`;
        }
        throw new Error(errMsg);
      }
      const data = await response.json();
      
      setQrToken(data.qrcode);
      setQrImg(data.qrcode_img_content);
      setQrStatus("wait");
      addLog(`QR Code successfully loaded (Token: ${data.qrcode.substring(0, 8)}...). Please scan with WeChat.`);
    } catch (error: any) {
      addLog(`Error fetching QR code: ${error.message}`);
    }
  };

  // 3. Sequential Status Polling (Condition-Based Waiting)
  const pollStatus = async (token: string) => {
    if (pollingActiveRef.current !== token || isLoggedIn) return;

    try {
      const response = await fetch(`${API_BASE_URL}/api/wechat/status?qrcode=${encodeURIComponent(token)}`);
      
      // Check if we are still active after the fetch resolves
      if (pollingActiveRef.current !== token) return;

      if (!response.ok) {
        let errMsg = `HTTP ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errMsg += `: ${errData.detail}`;
        } catch {
          const text = await response.text().catch(() => "");
          if (text) errMsg += `: ${text}`;
        }
        throw new Error(errMsg);
      }
      const data = await response.json();
      
      setQrStatus(data.status);
      
      if (data.status === "confirmed") {
        addLog(`Login confirmed! Logged in as user ID: ${data.user_id}`);
        setIsLoggedIn(true);
        setBotUserId(data.user_id);
        // Clear QR states
        setQrToken(null);
        setQrImg(null);
        pollingActiveRef.current = null;
        // Refresh sessions
        refreshSessions();
        return;
      } else if (data.status === "scaned") {
        addLog("QR code scanned. Waiting for confirmation in WeChat app...");
      } else if (data.status === "expired") {
        addLog("QR code has expired. Generating a new one...");
        pollingActiveRef.current = null;
        fetchNewQrCode();
        return;
      }
      
      // Schedule next poll ONLY after this long poll completes, and only if still active
      if (pollingActiveRef.current === token) {
        pollTimerRef.current = setTimeout(() => pollStatus(token), 1500);
      }
    } catch (error: any) {
      addLog(`Error polling QR status: ${error.message}`);
      // Retry after an error delay if still active
      if (pollingActiveRef.current === token) {
        pollTimerRef.current = setTimeout(() => pollStatus(token), 4000);
      }
    }
  };

  // 4. Refresh Sessions
  const refreshSessions = async () => {
    try {
      addLog("Refreshing active conversations list...");
      const response = await fetch(`${API_BASE_URL}/api/wechat/sessions`);
      if (!response.ok) throw new Error("Failed to fetch sessions list");
      const data = await response.json();
      
      setIsLoggedIn(data.is_logged_in);
      setBotUserId(data.user_id);
      setSessions(data.sessions);
      addLog(`Conversations list updated. Total: ${data.sessions.length} active chats.`);
    } catch (error: any) {
      addLog(`Error refreshing sessions: ${error.message}`);
    }
  };

  // 5. Send Message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUserId) {
      alert("Please select or enter a Target User ID.");
      return;
    }
    if (!messageText.trim()) {
      alert("Please enter message content.");
      return;
    }
    
    setSending(true);
    setSendResult(null);
    addLog(`Sending message to ${targetUserId}...`);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/wechat/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: targetUserId,
          text: messageText,
          context_token: explicitContextToken || undefined,
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setSendResult({ success: true, message: "Message sent successfully!" });
        addLog(`Message sent to ${targetUserId} successfully.`);
        setMessageText(""); // Clear input on success
      } else {
        setSendResult({ success: false, message: data.detail || "Failed to send message." });
        addLog(`Failed to send message: ${data.detail}`);
      }
    } catch (error: any) {
      setSendResult({ success: false, message: error.message });
      addLog(`Network error sending message: ${error.message}`);
    } finally {
      setSending(false);
    }
  };

  // 6. Log Out
  const handleLogout = async () => {
    if (!window.confirm("Are you sure you want to log out the bot?")) return;
    
    addLog("Logging out WeChat bot...");
    try {
      const response = await fetch(`${API_BASE_URL}/api/wechat/logout`, { method: "POST" });
      if (!response.ok) throw new Error("Logout request failed");
      
      setIsLoggedIn(false);
      setBotUserId(null);
      setSessions([]);
      setTargetUserId("");
      setExplicitContextToken("");
      addLog("Successfully logged out. Initiating new QR code fetch...");
      fetchNewQrCode();
    } catch (error: any) {
      addLog(`Error logging out: ${error.message}`);
    }
  };

  // Set up sequential polling on qrToken change
  useEffect(() => {
    if (qrToken) {
      addLog("Starting sequential status polling loop...");
      pollingActiveRef.current = qrToken;
      pollStatus(qrToken);
    } else {
      pollingActiveRef.current = null;
    }
    return () => {
      pollingActiveRef.current = null;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [qrToken]);

  // Check initial status on mount
  useEffect(() => {
    checkInitialStatus();
    return () => {
      pollingActiveRef.current = null;
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, []);

  return (
    <div className="wechat-test-container">
      <h2 className="title">WeChat QR-Client Testing Tool</h2>
      
      <div className="layout-grid">
        {/* Left Column: Auth and Sessions */}
        <div className="column">
          <div className="card">
            <h3>🤖 Bot Status</h3>
            {isLoggedIn ? (
              <div className="status-badge logged-in">
                <span>🟢 Logged In</span>
                <span className="user-id">Account ID: {botUserId}</span>
                <button className="btn btn-secondary logout-btn" onClick={handleLogout}>Log Out</button>
              </div>
            ) : (
              <div className="status-badge logged-out">
                <span>🔴 Logged Out</span>
              </div>
            )}
          </div>

          {!isLoggedIn && (
            <div className="card qr-card">
              <h3>📱 Scan to Authenticate</h3>
              {qrImg ? (
                <>
                  <p className="subtitle">Scan this QR code with the WeChat app to authorize this local bot instance.</p>
                  
                  <div className="qr-container">
                    <img 
                      src={qrImg.startsWith("http") || qrImg.startsWith("data:") ? qrImg : `${API_BASE_URL}${qrImg}`} 
                      alt="WeChat Authentication QR Code" 
                      className="qr-image" 
                      referrerPolicy="no-referrer"
                    />
                    <div className="qr-status-indicator">
                      Status: <strong className={`status-${qrStatus}`}>{qrStatus?.toUpperCase()}</strong>
                    </div>
                  </div>
                  
                  <button className="btn btn-primary" onClick={fetchNewQrCode}>Generate Fresh QR Code</button>
                </>
              ) : (
                <div className="qr-placeholder" style={{ textAlign: "center", padding: "20px 0" }}>
                  <p className="subtitle" style={{ marginBottom: "20px" }}>Click below to retrieve a login QR code from WeChat iLink.</p>
                  <button className="btn btn-primary" onClick={fetchNewQrCode}>Generate Login QR Code</button>
                </div>
              )}
            </div>
          )}

          {isLoggedIn && (
            <div className="card sessions-card">
              <div className="card-header">
                <h3>💬 Active Conversations</h3>
                <button className="btn btn-icon" onClick={refreshSessions} title="Refresh Sessions">🔄</button>
              </div>
              <p className="subtitle">These users have previously sent messages to the bot. Select one to compose a reply.</p>
              
              {sessions.length === 0 ? (
                <div className="empty-state">
                  <p>No active conversations found.</p>
                  <p className="hint">Send a message to the WeChat bot first to establish a chat context session!</p>
                </div>
              ) : (
                <div className="session-list">
                  {sessions.map((session, idx) => (
                    <div 
                      key={idx} 
                      className={`session-item ${targetUserId === session.user_id ? "active" : ""}`}
                      onClick={() => {
                        setTargetUserId(session.user_id);
                        setExplicitContextToken(session.context_token);
                        addLog(`Selected active chat for user: ${session.user_id}`);
                      }}
                    >
                      <div className="avatar">👤</div>
                      <div className="info">
                        <span className="uid">{session.user_id}</span>
                        <span className="token-preview">Token: {session.context_token.substring(0, 16)}...</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Message Composer and Logs */}
        <div className="column">
          <div className="card message-card">
            <h3>✉️ Send Test Message</h3>
            
            <form onSubmit={handleSendMessage} className="message-form">
              <div className="form-group">
                <label>Target User ID:</label>
                <input 
                  type="text" 
                  className="form-control"
                  placeholder="e.g. o3A8B..."
                  value={targetUserId}
                  onChange={(e) => setTargetUserId(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Explicit Context Token (Optional):</label>
                <input 
                  type="text" 
                  className="form-control"
                  placeholder="Only required if not in Active Conversations list"
                  value={explicitContextToken}
                  onChange={(e) => setExplicitContextToken(e.target.value)}
                />
                <span className="hint-text">If left blank, the bot will look up the token in its local memory context cache.</span>
              </div>

              <div className="form-group">
                <label>Message Content:</label>
                <textarea 
                  className="form-control text-area"
                  rows={4}
                  placeholder="Type your test message here..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                />
              </div>

              <button 
                type="submit" 
                className="btn btn-primary submit-btn" 
                disabled={sending || !isLoggedIn}
              >
                {sending ? "Sending..." : "Send Message"}
              </button>
            </form>

            {sendResult && (
              <div className={`result-alert ${sendResult.success ? "success" : "error"}`}>
                {sendResult.success ? "✅ Success: " : "❌ Error: "}{sendResult.message}
              </div>
            )}
          </div>

          <div className="card logs-card">
            <h3>📋 System Log Output</h3>
            <div className="console-log">
              {logs.map((log, index) => (
                <div key={index} className="log-line">{log}</div>
              ))}
              {logs.length === 0 && <div className="log-line empty">Console ready. Monitoring auth & session actions...</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
