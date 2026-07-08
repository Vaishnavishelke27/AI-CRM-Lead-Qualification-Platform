import React, { useMemo, useState } from "react";
import { ArrowDownUp, Filter, Sparkles, Trash2 } from "lucide-react";
import { useCRM } from "../context/CRMContext";

function compareValues(a, b, direction) {
  if (typeof a === "number" && typeof b === "number") {
    return direction === "asc" ? a - b : b - a;
  }
  return direction === "asc"
    ? String(a ?? "").localeCompare(String(b ?? ""))
    : String(b ?? "").localeCompare(String(a ?? ""));
}

export function LeadTable() {
  const { leads, selectedLeadId, setSelectedLeadId, deleteLead, enrichLead, scoreLead, setError } = useCRM();
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState({ key: "lead_score", direction: "desc" });

  const visibleLeads = useMemo(() => {
    return [...leads]
      .filter((lead) => {
        const text = `${lead.name} ${lead.company ?? ""} ${lead.email}`.toLowerCase();
        const matchesQuery = text.includes(query.toLowerCase());
        const matchesCategory = category ? lead.category === category : true;
        const matchesStatus = status ? lead.status === status : true;
        return matchesQuery && matchesCategory && matchesStatus;
      })
      .sort((a, b) => compareValues(a[sort.key], b[sort.key], sort.direction));
  }, [leads, query, category, status, sort]);

  const categories = [...new Set(leads.map((lead) => lead.category).filter(Boolean))];
  const statuses = [...new Set(leads.map((lead) => lead.status).filter(Boolean))];

  function toggleSort(key) {
    setSort((current) => ({
      key,
      direction: current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  }

  async function runAiRefresh(leadId) {
    try {
      await enrichLead(leadId);
      await scoreLead(leadId);
    } catch (error) {
      setError(error.message);
    }
  }

  return (
    <section className="panel lead-panel" aria-label="Leads">
      <div className="panel-heading">
        <div>
          <h2>Leads</h2>
          <p>{visibleLeads.length} visible</p>
        </div>
        <div className="filter-row">
          <label className="input-with-icon">
            <Filter size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search" />
          </label>
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All categories</option>
            {categories.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All statuses</option>
            {statuses.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="data-table">
        <div className="lead-row lead-head">
          {[
            ["name", "Name"],
            ["company", "Company"],
            ["lead_score", "Score"],
            ["category", "Category"],
            ["status", "Status"],
            ["assigned_to", "Owner"],
          ].map(([key, label]) => (
            <button className="sort-button" type="button" key={key} onClick={() => toggleSort(key)}>
              {label}
              <ArrowDownUp size={14} />
            </button>
          ))}
          <span>Actions</span>
        </div>
        {visibleLeads.length === 0 ? (
          <div className="empty-state">No leads match the current filters.</div>
        ) : (
          visibleLeads.map((lead) => (
            <div
              className={`lead-row ${selectedLeadId === lead.id ? "selected" : ""}`}
              key={lead.id}
              onClick={() => setSelectedLeadId(lead.id)}
              role="button"
              tabIndex={0}
            >
              <span>
                <strong>{lead.name}</strong>
                <small>{lead.email}</small>
              </span>
              <span>{lead.company || "-"}</span>
              <span className="score-pill">{lead.lead_score}</span>
              <span className={`badge ${lead.category?.toLowerCase() || "cold"}`}>{lead.category || "-"}</span>
              <span>{lead.status}</span>
              <span>{lead.assigned_to || "-"}</span>
              <span className="action-row">
                <button type="button" className="icon-button" title="Run AI refresh" onClick={(event) => {
                  event.stopPropagation();
                  runAiRefresh(lead.id);
                }}>
                  <Sparkles size={16} />
                </button>
                <button type="button" className="icon-button danger" title="Delete lead" onClick={(event) => {
                  event.stopPropagation();
                  deleteLead(lead.id).catch((error) => setError(error.message));
                }}>
                  <Trash2 size={16} />
                </button>
              </span>
            </div>
          ))
        )}
      </div>
    </section>
  );
}
