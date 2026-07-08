import React, { useState } from "react";
import { Plus } from "lucide-react";
import { useCRM } from "../context/CRMContext";

const initialForm = {
  name: "",
  email: "",
  company: "",
  source: "",
  status: "new",
  lead_score: "",
  category: "",
};

export function LeadForm() {
  const { createLead, setError } = useCRM();
  const [form, setForm] = useState(initialForm);
  const [saving, setSaving] = useState(false);
  const [validation, setValidation] = useState("");

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setValidation("");

    if (!form.name.trim()) {
      setValidation("Name is required.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      setValidation("Enter a valid email address.");
      return;
    }
    if (form.lead_score !== "" && (Number(form.lead_score) < 0 || Number(form.lead_score) > 100)) {
      setValidation("Score must be between 0 and 100.");
      return;
    }

    const payload = {
      name: form.name.trim(),
      email: form.email.trim(),
      company: form.company.trim() || null,
      source: form.source.trim() || null,
      status: form.status,
      category: form.category.trim() || null,
    };
    if (form.lead_score !== "") {
      payload.lead_score = Number(form.lead_score);
    }

    setSaving(true);
    try {
      await createLead(payload);
      setForm(initialForm);
    } catch (error) {
      setError(error.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Manual entry</h2>
          <p>AI scoring runs when score is blank</p>
        </div>
      </div>
      <form className="lead-form" onSubmit={submit}>
        <label>
          Name
          <input value={form.name} onChange={(event) => updateField("name", event.target.value)} required />
        </label>
        <label>
          Email
          <input value={form.email} onChange={(event) => updateField("email", event.target.value)} type="email" required />
        </label>
        <label>
          Company
          <input value={form.company} onChange={(event) => updateField("company", event.target.value)} />
        </label>
        <label>
          Source
          <input value={form.source} onChange={(event) => updateField("source", event.target.value)} placeholder="referral, webinar" />
        </label>
        <label>
          Status
          <select value={form.status} onChange={(event) => updateField("status", event.target.value)}>
            <option value="new">new</option>
            <option value="contacted">contacted</option>
            <option value="qualified">qualified</option>
            <option value="converted">converted</option>
          </select>
        </label>
        <label>
          Score
          <input value={form.lead_score} onChange={(event) => updateField("lead_score", event.target.value)} type="number" min="0" max="100" />
        </label>
        <label>
          Category
          <select value={form.category} onChange={(event) => updateField("category", event.target.value)}>
            <option value="">Auto</option>
            <option value="Hot">Hot</option>
            <option value="Warm">Warm</option>
            <option value="Cold">Cold</option>
          </select>
        </label>
        {validation && <div className="form-error">{validation}</div>}
        <button type="submit" disabled={saving}>
          <Plus size={16} />
          {saving ? "Saving" : "Add lead"}
        </button>
      </form>
    </section>
  );
}
