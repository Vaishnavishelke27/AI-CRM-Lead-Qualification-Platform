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
});
