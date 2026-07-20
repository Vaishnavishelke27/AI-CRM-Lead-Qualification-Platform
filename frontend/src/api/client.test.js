import { beforeEach, describe, expect, it, vi } from "vitest";

const storage = new Map();
globalThis.localStorage = {
  getItem: (key) => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, value),
  removeItem: (key) => storage.delete(key),
};

const { api, getLeadWebSocketAuthMessage, getLeadWebSocketUrl, setAuthToken } = await import("./client.js");

describe("API client", () => {
  beforeEach(() => {
    storage.clear();
    setAuthToken("");
    globalThis.fetch = vi.fn();
  });

  it("adds the bearer token to protected requests", async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });
    setAuthToken("signed-token");

    await api.listLeads();

    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^https?:\/\/[^/]+\/leads$/),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer signed-token" }),
      }),
    );
  });

  it("clears persisted authentication", () => {
    setAuthToken("signed-token");
    setAuthToken("");
    expect(storage.has("ai_crm_token")).toBe(false);
  });

  it("keeps WebSocket credentials out of the URL", () => {
    setAuthToken("signed-token");
    expect(getLeadWebSocketUrl()).not.toContain("signed-token");
    expect(getLeadWebSocketUrl()).not.toContain("?");
    expect(JSON.parse(getLeadWebSocketAuthMessage())).toEqual({
      type: "authenticate",
      token: "signed-token",
    });
  });

  it("targets the task, email, analytics, and CSV import endpoints", async () => {
    globalThis.fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    });

    await api.listTasks();
    await api.updateTask(7, { status: "completed" });
    await api.generateEmail({ lead_id: 3, purpose: "follow_up" });
    await api.analytics();
    await api.importLeads(new Blob(["name,email\nLead,lead@example.com"], { type: "text/csv" }));

    const calls = globalThis.fetch.mock.calls;
    expect(calls[0][0]).toMatch(/\/tasks$/);
    expect(calls[1][0]).toMatch(/\/tasks\/7$/);
    expect(calls[1][1].method).toBe("PUT");
    expect(calls[2][0]).toMatch(/\/emails\/generate$/);
    expect(calls[3][0]).toMatch(/\/analytics\/overview$/);
    expect(calls[4][0]).toMatch(/\/leads\/import$/);
    expect(calls[4][1].body).toBeInstanceOf(FormData);
    expect(calls[4][1].headers).not.toHaveProperty("Content-Type");
  });
});
