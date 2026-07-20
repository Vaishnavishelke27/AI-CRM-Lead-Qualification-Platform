import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, getLeadWebSocketAuthMessage, getLeadWebSocketUrl, setAuthToken } from "../api/client";

const CRMContext = createContext(null);

export function CRMProvider({ children }) {
  const [health, setHealth] = useState("checking");
  const [leads, setLeads] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [emails, setEmails] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [user, setUser] = useState(null);
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async (authenticatedUser = user) => {
    setLoading(true);
    setError("");
    try {
      const healthResult = await api.health().catch(() => ({ status: "offline" }));
      setHealth(healthResult.status ?? "offline");
      if (!authenticatedUser) {
        setLeads([]);
        setTasks([]);
        setEmails([]);
        setAnalytics(null);
        setSelectedLeadId(null);
        return;
      }
      const [leadsResult, tasksResult, emailsResult, analyticsResult] = await Promise.all([
        api.listLeads(),
        api.listTasks(),
        api.listEmails(),
        api.analytics().catch(() => null),
      ]);
      setLeads(Array.isArray(leadsResult) ? leadsResult : []);
      setTasks(Array.isArray(tasksResult) ? tasksResult : []);
      setEmails(Array.isArray(emailsResult) ? emailsResult : []);
      setAnalytics(analyticsResult);
      setSelectedLeadId((current) => current ?? leadsResult?.[0]?.id ?? null);
    } catch (requestError) {
      setHealth("offline");
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    api.me()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  useEffect(() => {
    if (!user) return undefined;
    const socket = new WebSocket(getLeadWebSocketUrl());
    socket.onopen = () => socket.send(getLeadWebSocketAuthMessage());
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type !== "authenticated") refresh();
    };
    return () => socket.close();
  }, [refresh, user]);

  const selectedLead = useMemo(
    () => leads.find((lead) => lead.id === selectedLeadId) ?? leads[0] ?? null,
    [leads, selectedLeadId],
  );

  const createLead = useCallback(
    async (payload) => {
      const lead = await api.createLead(payload);
      await refresh();
      setSelectedLeadId(lead.id);
      return lead;
    },
    [refresh],
  );

  const updateLead = useCallback(
    async (id, payload) => {
      const lead = await api.updateLead(id, payload);
      await refresh();
      setSelectedLeadId(lead.id);
      return lead;
    },
    [refresh],
  );

  const deleteLead = useCallback(
    async (id) => {
      await api.deleteLead(id);
      await refresh();
      setSelectedLeadId(null);
    },
    [refresh],
  );

  const createTask = useCallback(
    async (payload) => {
      const response = await api.createTask(payload);
      await refresh();
      return response;
    },
    [refresh],
  );

  const updateTask = useCallback(
    async (id, payload) => {
      const task = await api.updateTask(id, payload);
      await refresh();
      return task;
    },
    [refresh],
  );

  const generateEmail = useCallback(
    async (payload) => {
      const email = await api.generateEmail(payload);
      await refresh();
      return email;
    },
    [refresh],
  );

  const login = useCallback(async (payload) => {
    const result = await api.login(payload);
    setAuthToken(result.access_token);
    setUser(result.user);
    await refresh(result.user);
    return result.user;
  }, [refresh]);

  const logout = useCallback(() => {
    setAuthToken("");
    setUser(null);
    setAnalytics(null);
    setLeads([]);
    setTasks([]);
    setEmails([]);
    setSelectedLeadId(null);
  }, []);

  const importLeads = useCallback(
    async (file) => {
      const result = await api.importLeads(file);
      await refresh();
      return result;
    },
    [refresh],
  );

  const sendReport = useCallback(() => api.sendReport(), []);

  const enrichLead = useCallback(
    async (leadId) => {
      const result = await api.enrichLead(leadId);
      await refresh();
      return result;
    },
    [refresh],
  );

  const scoreLead = useCallback(
    async (leadId) => {
      const result = await api.scoreLead(leadId);
      await refresh();
      return result;
    },
    [refresh],
  );

  const value = useMemo(
    () => ({
      health,
      leads,
      tasks,
      emails,
      analytics,
      user,
      selectedLead,
      selectedLeadId,
      loading,
      error,
      setSelectedLeadId,
      refresh,
      createLead,
      updateLead,
      deleteLead,
      createTask,
      updateTask,
      generateEmail,
      enrichLead,
      scoreLead,
      login,
      logout,
      importLeads,
      sendReport,
      setError,
    }),
    [
      health,
      leads,
      tasks,
      emails,
      analytics,
      user,
      selectedLead,
      selectedLeadId,
      loading,
      error,
      refresh,
      createLead,
      updateLead,
      deleteLead,
      createTask,
      updateTask,
      generateEmail,
      enrichLead,
      scoreLead,
      login,
      logout,
      importLeads,
      sendReport,
    ],
  );

  return <CRMContext.Provider value={value}>{children}</CRMContext.Provider>;
}

export function useCRM() {
  const context = useContext(CRMContext);
  if (!context) {
    throw new Error("useCRM must be used inside CRMProvider");
  }
  return context;
}
