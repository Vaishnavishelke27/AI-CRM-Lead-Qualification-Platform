import React from "react";
import { Brain, Building2, Mail, RefreshCw, UserRound } from "lucide-react";
import { useCRM } from "../context/CRMContext";

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function MetadataBlock({ value }) {
  if (!value || Object.keys(value).length === 0) {
    return <p className="muted">No AI insights stored yet.</p>;
  }
  return <pre className="metadata">{JSON.stringify(value, null, 2)}</pre>;
}

export function LeadDetail() {
  const { selectedLead, tasks, emails, enrichLead, scoreLead, setError } = useCRM();

  if (!selectedLead) {
    return (
      <section className="panel detail-panel">
        <div className="empty-state">Select or create a lead to view details.</div>
      </section>
    );
  }

  const leadTasks = tasks.filter((task) => task.lead_id === selectedLead.id);
  const leadEmails = emails.filter((email) => email.lead_id === selectedLead.id);

  async function runAi() {
    try {
      await enrichLead(selectedLead.id);
      await scoreLead(selectedLead.id);
    } catch (error) {
      setError(error.message);
    }
  }

  return (
    <section className="panel detail-panel">
      <div className="detail-header">
        <div>
          <p className="eyebrow">Lead detail</p>
          <h2>{selectedLead.name}</h2>
          <div className="detail-meta">
            <span><Mail size={14} /> {selectedLead.email}</span>
            <span><Building2 size={14} /> {selectedLead.company || "No company"}</span>
            <span><UserRound size={14} /> {selectedLead.status}</span>
            <span>Owner: {selectedLead.assigned_to || "Unassigned"}</span>
          </div>
        </div>
        <button type="button" className="secondary-button" onClick={runAi}>
          <RefreshCw size={16} />
          Refresh AI
        </button>
      </div>

      <div className="score-band">
        <div>
          <span>Lead score</span>
          <strong>{selectedLead.lead_score}</strong>
        </div>
        <div>
          <span>Category</span>
          <strong>{selectedLead.category || "-"}</strong>
        </div>
        <div>
          <span>Created</span>
          <strong>{formatDate(selectedLead.created_at)}</strong>
        </div>
      </div>

      <div className="detail-section">
        <h3><Brain size={18} /> AI insights</h3>
        <MetadataBlock value={selectedLead.ai_metadata} />
      </div>

      <div className="detail-grid">
        <div className="detail-section">
          <h3>Tasks timeline</h3>
          {leadTasks.length === 0 ? (
            <p className="muted">No tasks yet.</p>
          ) : (
            <ol className="timeline">
              {leadTasks.map((task) => (
                <li key={task.id}>
                  <strong>{task.description}</strong>
                  <span>{task.status} · due {formatDate(task.due_date)}</span>
                </li>
              ))}
            </ol>
          )}
        </div>
        <div className="detail-section">
          <h3>Email history</h3>
          {leadEmails.length === 0 ? (
            <p className="muted">No generated emails yet.</p>
          ) : (
            <div className="email-history">
              {leadEmails.map((email) => (
                <article key={email.id}>
                  <strong>{email.subject}</strong>
                  <p>{email.body}</p>
                  <small>{formatDate(email.sent_at)} · opens {email.open_count} · clicks {email.click_count}</small>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
