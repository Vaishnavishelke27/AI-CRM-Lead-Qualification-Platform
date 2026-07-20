import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

let crmState;

vi.mock("../context/CRMContext", () => ({
  useCRM: () => crmState,
}));

const { AnalyticsDashboard } = await import("./AnalyticsDashboard.jsx");
const { EmailComposer } = await import("./EmailComposer.jsx");
const { LeadForm } = await import("./LeadForm.jsx");
const { TaskManagement } = await import("./TaskManagement.jsx");

describe("CRM components", () => {
  beforeEach(() => {
    crmState = {
      analytics: null,
      createLead: vi.fn(),
      createTask: vi.fn(),
      generateEmail: vi.fn(),
      leads: [],
      selectedLead: null,
      setError: vi.fn(),
      tasks: [],
      updateTask: vi.fn(),
    };
  });

  it("renders lead entry fields and automatic scoring guidance", () => {
    const html = renderToStaticMarkup(<LeadForm />);
    expect(html).toContain("Manual entry");
    expect(html).toContain("AI scoring runs when score is blank");
    expect(html).toContain('type="email"');
  });

  it("sorts high-priority tasks before low-priority tasks", () => {
    crmState.leads = [
      { id: 1, name: "Cold Lead", lead_score: 10 },
      { id: 2, name: "Hot Lead", lead_score: 90 },
    ];
    crmState.tasks = [
      { id: 1, lead_id: 1, description: "Cold task", status: "open" },
      { id: 2, lead_id: 2, description: "Hot task", status: "open" },
    ];
    crmState.selectedLead = crmState.leads[1];

    const html = renderToStaticMarkup(<TaskManagement />);
    expect(html.indexOf("Hot task")).toBeLessThan(html.indexOf("Cold task"));
  });

  it("prioritizes the book-demo template for hot leads", () => {
    crmState.selectedLead = {
      id: 2,
      name: "Hot Lead",
      email: "hot@example.com",
      lead_score: 90,
      category: "Hot",
      ai_metadata: {},
    };

    const html = renderToStaticMarkup(<EmailComposer />);
    expect(html.indexOf("Book demo")).toBeLessThan(html.indexOf("Initial outreach"));
  });

  it("shows the signed-out analytics state when data is unavailable", () => {
    const html = renderToStaticMarkup(<AnalyticsDashboard />);
    expect(html).toContain("Log in to view CRM analytics");
  });
});
