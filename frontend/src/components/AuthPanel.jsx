import React, { useState } from "react";
import { FileUp, LogIn, LogOut, Send } from "lucide-react";
import { useCRM } from "../context/CRMContext";

export function AuthPanel() {
  const { user, login, logout, importLeads, sendReport, setError } = useCRM();
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [message, setMessage] = useState("");

  async function submitLogin(event) {
    event.preventDefault();
    try {
      await login(credentials);
      setMessage("Signed in.");
    } catch (error) {
      setError(error.message);
    }
  }

  async function uploadCsv(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const result = await importLeads(file);
      setMessage(`Import queued: ${result.job_id}`);
    } catch (error) {
      setError(error.message);
    } finally {
      event.target.value = "";
    }
  }

  async function triggerReport() {
    try {
      const result = await sendReport();
      setMessage(result.result?.reason || "Report request completed.");
    } catch (error) {
      setError(error.message);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Access and operations</h2>
          <p>{user ? `${user.full_name} · ${user.role}` : "JWT-secured analytics and imports"}</p>
        </div>
        {user && (
          <button type="button" className="icon-button" title="Sign out" onClick={logout}>
            <LogOut size={16} />
          </button>
        )}
      </div>

      {!user ? (
        <form className="auth-form" onSubmit={submitLogin}>
          <label>
            Email
            <input value={credentials.email} onChange={(event) => setCredentials((current) => ({ ...current, email: event.target.value }))} type="email" />
          </label>
          <label>
            Password
            <input value={credentials.password} onChange={(event) => setCredentials((current) => ({ ...current, password: event.target.value }))} type="password" />
          </label>
          <button type="submit">
            <LogIn size={16} />
            Sign in
          </button>
        </form>
      ) : (
        <div className="ops-list">
          <label className="file-upload">
            <FileUp size={16} />
            Import CSV
            <input type="file" accept=".csv,text/csv" onChange={uploadCsv} />
          </label>
          <button type="button" className="secondary-button" onClick={triggerReport}>
            <Send size={16} />
            Send summary
          </button>
        </div>
      )}

      {message && <p className="operation-message">{message}</p>}
    </section>
  );
}
