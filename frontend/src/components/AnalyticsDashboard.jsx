import React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useCRM } from "../context/CRMContext";

const colors = ["#164b5f", "#5b8e7d", "#d79a32", "#9f2f28", "#7b61a3"];

export function AnalyticsDashboard() {
  const { analytics } = useCRM();

  if (!analytics) {
    return (
      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Analytics</h2>
            <p>Log in to view CRM analytics</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="panel analytics-panel">
      <div className="panel-heading">
        <div>
          <h2>Analytics</h2>
          <p>Conversion, source effectiveness, and AI performance</p>
        </div>
      </div>
      <div className="chart-grid">
        <article>
          <h3>Lead conversion funnel</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={analytics.funnel}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="stage" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count">
                {analytics.funnel.map((_, index) => (
                  <Cell fill={colors[index % colors.length]} key={index} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </article>

        <article>
          <h3>Source effectiveness</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={analytics.source_effectiveness}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="source" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="avg_score" stroke="#164b5f" strokeWidth={3} />
              <Line type="monotone" dataKey="leads" stroke="#d79a32" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </article>

        <article>
          <h3>AI accuracy metrics</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={analytics.ai_accuracy}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="metric" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#5b8e7d" />
            </BarChart>
          </ResponsiveContainer>
        </article>

        <article>
          <h3>Sales routing</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={analytics.routing}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="assignee" hide />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#7b61a3" />
            </BarChart>
          </ResponsiveContainer>
        </article>
      </div>
    </section>
  );
}
