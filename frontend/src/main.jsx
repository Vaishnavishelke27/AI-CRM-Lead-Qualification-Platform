import React, { lazy, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { Activity, BriefcaseBusiness, Mail, RefreshCw, UserRound } from "lucide-react";
import { AuthPanel } from "./components/AuthPanel";
import { CRMProvider, useCRM } from "./context/CRMContext";
import { EmailComposer } from "./components/EmailComposer";
import { LeadDashboard } from "./components/LeadDashboard";
import { LeadDetail } from "./components/LeadDetail";
import { LeadForm } from "./components/LeadForm";
import { LeadTable } from "./components/LeadTable";
import { TaskManagement } from "./components/TaskManagement";
import "./styles.css";

const AnalyticsDashboard = lazy(() =>
  import("./components/AnalyticsDashboard").then((module) => ({ default: module.AnalyticsDashboard })),
);

function AnalyticsPlaceholder({ message = "Loading analytics…" }) {
  return (
    <section className="panel" aria-busy={message.startsWith("Loading")}>
      <div className="panel-heading">
        <div>
          <h2>Analytics</h2>
          <p>{message}</p>
        </div>
      </div>
    </section>
  );
}

function AppShell() {
  const { health, loading, error, refresh, setError, user } = useCRM();

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Activity size={24} />
          <span>AI CRM</span>
        </div>
        <nav>
          <a className="active" href="#leads">
            <UserRound size={18} /> Leads
          </a>
          <a href="#tasks">
            <BriefcaseBusiness size={18} /> Tasks
          </a>
          <a href="#emails">
            <Mail size={18} /> Emails
          </a>
        </nav>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Pipeline</p>
            <h1>Lead Command Center</h1>
          </div>
          <div className="topbar-actions">
            <div className={`status ${health}`}>API {health}</div>
            <button type="button" className="secondary-button" onClick={refresh}>
              <RefreshCw size={16} />
              {loading ? "Loading" : "Refresh"}
            </button>
          </div>
        </header>

        {error && (
          <div className="alert" role="alert">
            <span>{error}</span>
            <button type="button" className="link-button" onClick={() => setError("")}>
              Dismiss
            </button>
          </div>
        )}

        <LeadDashboard />
        {user ? (
          <Suspense fallback={<AnalyticsPlaceholder />}>
            <AnalyticsDashboard />
          </Suspense>
        ) : (
          <AnalyticsPlaceholder message="Log in to view CRM analytics" />
        )}

        <div className="crm-grid">
          <div className="primary-column">
            <LeadTable />
            <LeadDetail />
          </div>
          <div className="side-column">
            <AuthPanel />
            <LeadForm />
            <TaskManagement />
            <EmailComposer />
          </div>
        </div>
      </section>
    </main>
  );
}

function App() {
  return (
    <CRMProvider>
      <AppShell />
    </CRMProvider>
  );
}

createRoot(document.getElementById("root")).render(<App />);
