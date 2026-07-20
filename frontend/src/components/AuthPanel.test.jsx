import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

let crmState;

vi.mock("../context/CRMContext", () => ({
  useCRM: () => crmState,
}));

const { AuthPanel } = await import("./AuthPanel.jsx");

describe("AuthPanel", () => {
  beforeEach(() => {
    crmState = {
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
      importLeads: vi.fn(),
      sendReport: vi.fn(),
      setError: vi.fn(),
    };
  });

  it("shows login controls to signed-out users", () => {
    const html = renderToStaticMarkup(<AuthPanel />);
    expect(html).toContain("Sign in");
    expect(html).not.toContain("Import CSV");
  });

  it("shows privileged operations to an authenticated manager", () => {
    crmState.user = { full_name: "CRM Manager", role: "manager" };
    const html = renderToStaticMarkup(<AuthPanel />);
    expect(html).toContain("CRM Manager");
    expect(html).toContain("Import CSV");
    expect(html).toContain("Send summary");
  });
});
