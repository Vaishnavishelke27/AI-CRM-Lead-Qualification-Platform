import React, { useMemo, useState } from "react";
import { MailPlus, Send } from "lucide-react";
import { useCRM } from "../context/CRMContext";

const templates = [
  { label: "Initial outreach", purpose: "initial_outreach", tone: "professional" },
  { label: "Book demo", purpose: "book_demo", tone: "concise" },
  { label: "Nurture follow-up", purpose: "nurture_follow_up", tone: "professional" },
];

export function EmailComposer() {
  const { selectedLead, generateEmail, setError } = useCRM();
  const [templateIndex, setTemplateIndex] = useState(0);
  const [draft, setDraft] = useState({ subject: "", body: "" });
  const [saving, setSaving] = useState(false);

  const suggestedTemplates = useMemo(() => {
    if (!selectedLead) return templates;
    if (selectedLead.lead_score >= 75) return [templates[1], templates[0], templates[2]];
    if (selectedLead.lead_score >= 45) return [templates[0], templates[2], templates[1]];
    return [templates[2], templates[0], templates[1]];
  }, [selectedLead]);
  const selectedTemplate = suggestedTemplates[templateIndex] ?? suggestedTemplates[0];

  async function generateDraft() {
    if (!selectedLead) return;
    setSaving(true);
    try {
      const email = await generateEmail({
        lead_id: selectedLead.id,
        purpose: selectedTemplate.purpose,
        tone: selectedTemplate.tone,
        context: {
          score: selectedLead.lead_score,
          category: selectedLead.category,
          ai_metadata: selectedLead.ai_metadata,
        },
      });
      setDraft({ subject: email.subject, body: email.body });
    } catch (error) {
      setError(error.message);
    } finally {
      setSaving(false);
    }
  }

  function sendEmail() {
    if (!selectedLead) return;
    if (!draft.subject.trim() || !draft.body.trim()) {
      setError("Generate or enter an email subject and body first.");
      return;
    }
    const subject = encodeURIComponent(draft.subject);
    const body = encodeURIComponent(draft.body);
    window.location.href = `mailto:${selectedLead.email}?subject=${subject}&body=${body}`;
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Email composer</h2>
          <p>{selectedLead ? `For ${selectedLead.name}` : "Select a lead"}</p>
        </div>
      </div>

      <div className="composer">
        <label>
          AI template
          <select value={templateIndex} onChange={(event) => setTemplateIndex(Number(event.target.value))} disabled={!selectedLead}>
            {suggestedTemplates.map((template, index) => (
              <option key={template.purpose} value={index}>
                {template.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Subject
          <input value={draft.subject} onChange={(event) => setDraft((current) => ({ ...current, subject: event.target.value }))} disabled={!selectedLead} />
        </label>
        <label>
          Body
          <textarea value={draft.body} onChange={(event) => setDraft((current) => ({ ...current, body: event.target.value }))} disabled={!selectedLead} rows={8} />
        </label>
        <div className="composer-actions">
          <button type="button" className="secondary-button" disabled={!selectedLead || saving} onClick={generateDraft}>
            <MailPlus size={16} />
            {saving ? "Working" : "Generate"}
          </button>
          <button type="button" disabled={!selectedLead || saving} onClick={sendEmail}>
            <Send size={16} />
            Send
          </button>
        </div>
      </div>
    </section>
  );
}
