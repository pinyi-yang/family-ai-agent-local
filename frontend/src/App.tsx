import { useState } from "react";
import SlackTest from "./SlackTest";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "slack">("dashboard");

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
            className={`nav-link ${activeTab === "slack" ? "active" : ""}`}
            onClick={() => setActiveTab("slack")}
          >
            Slack Integration Test
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
                <h3>💬 Slack Integration</h3>
                <p>Proactive family notifications and summaries via Slack WebClient.</p>
                <button className="btn btn-primary" onClick={() => setActiveTab("slack")}>
                  Manage Slack Bot
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "slack" && <SlackTest />}
      </main>
    </div>
  );
}

export default App;
