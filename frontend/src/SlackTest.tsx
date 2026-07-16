import { useState, useEffect, useRef } from "react";

const API_BASE_URL = "http://localhost:4000";

interface BotInfo {
  ok: boolean;
  url: string;
  team: string;
  user: string;
  team_id: string;
  user_id: string;
  bot_id: string;
}

export default function SlackTest() {
  const [isConfigured, setIsConfigured] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [botInfo, setBotInfo] = useState<BotInfo | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [checking, setChecking] = useState<boolean>(false);

  // Message Sending States
  const [targetId, setTargetId] = useState<string>("");
  const [messageText, setMessageText] = useState<string>("");
  const [threadTs, setThreadTs] = useState<string>("");
  const [sending, setSending] = useState<boolean>(false);
  const [sendResult, setSendResult] = useState<{ success: boolean; message: string } | null>(null);

  // Logging / Console feedback
  const [logs, setLogs] = useState<string[]>([]);
  const hasCheckedStatusRef = useRef<boolean>(false);

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [`[${timestamp}] ${msg}`, ...prev]);
  };

  // Check Slack status from backend
  const checkSlackStatus = async () => {
    setChecking(true);
    try {
      addLog("Checking Slack bot configuration and status...");
      const response = await fetch(`${API_BASE_URL}/api/slack/status`);
      if (!response.ok) {
        const text = await response.text().catch(() => "");
        throw new Error(`HTTP ${response.status}: ${text || "Failed to fetch status"}`);
      }
      const data = await response.json();

      setIsConfigured(data.is_configured);
      setIsConnected(data.is_connected);
      setBotInfo(data.bot_info);
      setStatusError(data.error);

      if (data.is_connected && data.bot_info) {
        addLog(`Slack connected! Bot: @${data.bot_info.user} in workspace "${data.bot_info.team}".`);
      } else if (data.is_configured) {
        addLog(`Slack token is configured but connection test failed: ${data.error || "unknown error"}.`);
      } else {
        addLog("Slack integration is not configured. Please set SLACK_BOT_TOKEN in your backend environment variables.");
      }
    } catch (error: any) {
      addLog(`Error checking status: ${error.message}`);
      setStatusError(error.message);
    } finally {
      setChecking(false);
    }
  };

  // Send Message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetId.trim()) {
      alert("Please enter a Target Channel or User ID.");
      return;
    }
    if (!messageText.trim()) {
      alert("Please enter message content.");
      return;
    }

    setSending(true);
    setSendResult(null);
    addLog(`Sending message to target "${targetId}"...`);

    try {
      const response = await fetch(`${API_BASE_URL}/api/slack/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_id: targetId,
          text: messageText,
          thread_ts: threadTs.trim() || undefined,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setSendResult({ success: true, message: "Message sent successfully!" });
        addLog(`Message successfully sent to ${targetId}. TS: ${data.data?.ts || "N/A"}`);
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

  // Check initial status on mount
  useEffect(() => {
    if (!hasCheckedStatusRef.current) {
      hasCheckedStatusRef.current = true;
      checkSlackStatus();
    }
  }, []);

  return (
    <div className="wechat-test-container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h2 className="title" style={{ margin: 0 }}>Slack Integration Testing Tool</h2>
        <button 
          className="btn btn-secondary" 
          onClick={checkSlackStatus} 
          disabled={checking}
        >
          {checking ? "Checking..." : "🔄 Refresh Connection"}
        </button>
      </div>

      <div className="layout-grid">
        {/* Left Column: Connection Info & Config */}
        <div className="column">
          <div className="card">
            <h3>🤖 Slack Bot Status</h3>
            {isConfigured ? (
              isConnected ? (
                <div className="status-badge logged-in">
                  <span>🟢 Connected</span>
                  <div style={{ marginTop: "10px", fontSize: "14px", lineHeight: "1.5" }}>
                    <strong>Workspace:</strong> {botInfo?.team}<br />
                    <strong>Bot Name:</strong> @{botInfo?.user}<br />
                    <strong>Bot User ID:</strong> {botInfo?.user_id}
                  </div>
                </div>
              ) : (
                <div className="status-badge logged-out" style={{ background: "#fff3cd", border: "1px solid #ffeeba", color: "#856404" }}>
                  <span>⚠️ Misconfigured or Connection Failed</span>
                  <p style={{ fontSize: "13px", marginTop: "5px", marginBottom: 0 }}>
                    Token is set, but test connection failed: <code>{statusError}</code>
                  </p>
                </div>
              )
            ) : (
              <div className="status-badge logged-out">
                <span>🔴 Not Configured</span>
                <p style={{ fontSize: "13px", marginTop: "5px", marginBottom: 0 }}>
                  <code>SLACK_BOT_TOKEN</code> is missing from environment.
                </p>
              </div>
            )}
          </div>

          <div className="card qr-card" style={{ padding: "20px" }}>
            <h3>ℹ️ Configuration Guide</h3>
            <p className="subtitle" style={{ fontSize: "14px", lineHeight: "1.6" }}>
              To connect your Slack Workspace, ensure you have set up your app in Slack and have added the token to your local <code>.env</code> file:
            </p>
            <pre style={{ background: "#272822", color: "#f8f8f2", padding: "12px", borderRadius: "6px", fontSize: "13px", overflowX: "auto" }}>
              SLACK_BOT_TOKEN="xoxb-your-bot-token"
            </pre>
            <p className="subtitle" style={{ fontSize: "14px", lineHeight: "1.6", marginTop: "10px" }}>
              Make sure your Slack Bot Token has the <code>chat:write</code> OAuth scope configured on the Slack developer portal.
            </p>
          </div>
        </div>

        {/* Right Column: Message Composer and Logs */}
        <div className="column">
          <div className="card message-card">
            <h3>✉️ Send Test Message</h3>

            <form onSubmit={handleSendMessage} className="message-form">
              <div className="form-group">
                <label>Target Channel ID or User ID:</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. C12345678 or U12345678"
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Thread Timestamp (Optional):</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g. 1718292834.123456"
                  value={threadTs}
                  onChange={(e) => setThreadTs(e.target.value)}
                />
                <span className="hint-text">If provided, the message will be posted as a reply to that message thread.</span>
              </div>

              <div className="form-group">
                <label>Message Content:</label>
                <textarea
                  className="form-control text-area"
                  rows={4}
                  placeholder="Type your Slack test message here..."
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary submit-btn"
                disabled={sending || !isConfigured || !isConnected}
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
              {logs.length === 0 && <div className="log-line empty">Console ready. Monitoring Slack status & messages...</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
