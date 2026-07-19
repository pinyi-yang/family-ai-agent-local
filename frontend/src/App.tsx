import { useState, useEffect } from "react";
import SlackTest from "./SlackTest";
import GoogleTest from "./GoogleTest";
import "./App.css";

function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "tests">("dashboard");
  const [activeSubTab, setActiveSubTab] = useState<"slack" | "google">("slack");

  // Keep 'tests' tab active and auto-select Google if returning from callback redirect
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("google_success") === "true") {
      setActiveTab("tests");
      setActiveSubTab("google");
    }
  }, []);

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
            className={`nav-link ${activeTab === "tests" ? "active" : ""}`}
            onClick={() => setActiveTab("tests")}
          >
            Integration Tests
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
                <button className="btn btn-primary" onClick={() => { setActiveTab("tests"); setActiveSubTab("google"); }}>
                  Manage Google Auth
                </button>
              </div>

              <div className="card feature-card">
                <h3>💬 Slack Integration</h3>
                <p>Proactive family notifications and summaries via Slack WebClient.</p>
                <button className="btn btn-primary" onClick={() => { setActiveTab("tests"); setActiveSubTab("slack"); }}>
                  Manage Slack Bot
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "tests" && (
          <div className="tests-container">
            <div className="tests-header" style={{ marginBottom: "24px", borderBottom: "1px solid var(--border)", paddingBottom: "12px", display: "flex", gap: "12px" }}>
              <button
                className={`nav-link ${activeSubTab === "slack" ? "active" : ""}`}
                style={{ fontSize: "14px", padding: "6px 14px" }}
                onClick={() => setActiveSubTab("slack")}
              >
                💬 Slack Bot Test
              </button>
              <button
                className={`nav-link ${activeSubTab === "google" ? "active" : ""}`}
                style={{ fontSize: "14px", padding: "6px 14px" }}
                onClick={() => setActiveSubTab("google")}
              >
                📅 Google Workspace Test
              </button>
            </div>

            {activeSubTab === "slack" && <SlackTest />}
            {activeSubTab === "google" && <GoogleTest />}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
