import { useState } from "react";
import WeChatTest from "./WeChatTest";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "wechat">("dashboard");

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo-section">
          <span className="logo-icon">🏡</span>
          <h1>Family AI Agent</h1>
        </div>
        <nav className="app-nav">
          <button 
            className={`nav-link ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            Dashboard
          </button>
          <button 
            className={`nav-link ${activeTab === "wechat" ? "active" : ""}`}
            onClick={() => setActiveTab("wechat")}
          >
            WeChat Client Test
          </button>
        </nav>
      </header>

      <main className="app-main-content">
        {activeTab === "dashboard" && (
          <div className="dashboard-view">
            <div className="card hero-card">
              <h2>Welcome to your Family AI Agent!</h2>
              <p>
                Your personal workspace is initialized. The local backend is running at{" "}
                <code>http://localhost:4000</code> and ready to manage family preferences,
                Google calendar events, and notifications.
              </p>
            </div>
            
            <div className="dashboard-grid">
              <div className="card feature-card">
                <h3>📅 Google Workspace</h3>
                <p>Authenticates dynamically and syncs calendar schedules automatically.</p>
                <div className="badge">Configured</div>
              </div>

              <div className="card feature-card">
                <h3>💬 WeChat Integration</h3>
                <p>WeChat iLink QR authentication client for real-time proactive notices.</p>
                <button className="btn btn-primary" onClick={() => setActiveTab("wechat")}>
                  Manage WeChat Bot
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "wechat" && <WeChatTest />}
      </main>
    </div>
  );
}

export default App;
