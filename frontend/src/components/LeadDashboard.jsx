import React, { useMemo } from "react";
import { Flame, Target, TrendingUp, UsersRound } from "lucide-react";
import { useCRM } from "../context/CRMContext";

export function LeadDashboard() {
  const { leads, tasks } = useCRM();

  const metrics = useMemo(() => {
    const total = leads.length;
    const hot = leads.filter((lead) => lead.category?.toLowerCase() === "hot" || lead.lead_score >= 75).length;
    const converted = leads.filter((lead) => ["converted", "won", "customer"].includes(lead.status?.toLowerCase())).length;
    const openTasks = tasks.filter((task) => task.status?.toLowerCase() !== "done").length;
    const conversionRate = total ? Math.round((converted / total) * 100) : 0;

    return [
      { label: "Total leads", value: total, icon: UsersRound },
      { label: "Hot leads", value: hot, icon: Flame },
      { label: "Conversion rate", value: `${conversionRate}%`, icon: TrendingUp },
      { label: "Open tasks", value: openTasks, icon: Target },
    ];
  }, [leads, tasks]);

  return (
    <section className="kpi-grid" aria-label="Lead KPIs">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <article className="kpi-card" key={metric.label}>
            <div className="kpi-icon">
              <Icon size={20} />
            </div>
            <div>
              <p>{metric.label}</p>
              <strong>{metric.value}</strong>
            </div>
          </article>
        );
      })}
    </section>
  );
}
