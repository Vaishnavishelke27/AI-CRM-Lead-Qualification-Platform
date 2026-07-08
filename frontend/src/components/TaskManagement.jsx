import React, { useMemo } from "react";
import { CheckCircle2, Clock3, Plus } from "lucide-react";
import { useCRM } from "../context/CRMContext";

function priorityForTask(task, leads) {
  const lead = leads.find((item) => item.id === task.lead_id);
  const score = lead?.lead_score ?? 0;
  if (score >= 75) return "high";
  if (score >= 45) return "medium";
  return "low";
}

function priorityRank(priority) {
  return { high: 0, medium: 1, low: 2 }[priority] ?? 3;
}

export function TaskManagement() {
  const { tasks, leads, selectedLead, createTask, updateTask, setError } = useCRM();

  const sortedTasks = useMemo(() => {
    return [...tasks].sort((a, b) => {
      const priorityDelta = priorityRank(priorityForTask(a, leads)) - priorityRank(priorityForTask(b, leads));
      if (priorityDelta !== 0) return priorityDelta;
      return new Date(a.due_date || "2999-01-01") - new Date(b.due_date || "2999-01-01");
    });
  }, [tasks, leads]);

  async function createFollowUp() {
    if (!selectedLead) return;
    try {
      await createTask({
        lead_id: selectedLead.id,
        context: { next_action: "manual follow-up" },
      });
    } catch (error) {
      setError(error.message);
    }
  }

  async function changeStatus(task, status) {
    try {
      await updateTask(task.id, { status });
    } catch (error) {
      setError(error.message);
    }
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <div>
          <h2>Task management</h2>
          <p>Sorted by lead score priority</p>
        </div>
        <button type="button" className="secondary-button" onClick={createFollowUp} disabled={!selectedLead}>
          <Plus size={16} />
          Follow-up
        </button>
      </div>

      <div className="task-list">
        {sortedTasks.length === 0 ? (
          <div className="empty-state">No tasks yet.</div>
        ) : (
          sortedTasks.map((task) => {
            const lead = leads.find((item) => item.id === task.lead_id);
            const priority = priorityForTask(task, leads);
            return (
              <article className="task-item" key={task.id}>
                <div>
                  <span className={`priority ${priority}`}>{priority}</span>
                  <strong>{task.description}</strong>
                  <small>{lead?.name || "Unknown lead"} · {task.due_date ? new Date(task.due_date).toLocaleString() : "No due date"}</small>
                </div>
                <div className="status-actions">
                  <button type="button" className="icon-button" title="Mark open" onClick={() => changeStatus(task, "open")}>
                    <Clock3 size={16} />
                  </button>
                  <button type="button" className="icon-button" title="Mark done" onClick={() => changeStatus(task, "done")}>
                    <CheckCircle2 size={16} />
                  </button>
                </div>
              </article>
            );
          })
        )}
      </div>
    </section>
  );
}
