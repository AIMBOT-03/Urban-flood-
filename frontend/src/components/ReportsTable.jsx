import { useState, useMemo } from "react";
import { api } from "../api.js";

const SEVERITY_ORDER = { blocked_drain: 0, waterlogging: 1, other: 2 };
const TYPE_LABEL = { blocked_drain: "Blocked drain", waterlogging: "Waterlogging", other: "Other" };

export default function ReportsTable({ reports, onRefresh }) {
  const [filter, setFilter] = useState("all");

  const filtered = useMemo(() => {
    const list = filter === "all" ? reports : reports.filter((r) => r.status === filter);
    return [...list].sort((a, b) => SEVERITY_ORDER[a.report_type] - SEVERITY_ORDER[b.report_type]);
  }, [reports, filter]);

  async function markResolved(reportId) {
    await api.updateReportStatus(reportId, "resolved");
    onRefresh();
  }

  return (
    <div>
      <div className="field" style={{ maxWidth: 220 }}>
        <label>Filter</label>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All</option>
          <option value="pending">Pending</option>
          <option value="resolved">Resolved</option>
        </select>
      </div>
      <table>
        <thead>
          <tr>
            <th>Photo</th>
            <th>Type</th>
            <th>Zone</th>
            <th>Description</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((r) => (
            <tr key={r.report_id}>
              <td>
                {r.photo_url ? (
                  <img src={api.uploadsUrl(r.photo_url)} alt="report" className="report-photo" />
                ) : (
                  "—"
                )}
              </td>
              <td>{TYPE_LABEL[r.report_type] || r.report_type}</td>
              <td>{r.zone_id}</td>
              <td>{r.description}</td>
              <td><span className="pill">{r.status}</span></td>
              <td>
                {r.status !== "resolved" && (
                  <button className="secondary" onClick={() => markResolved(r.report_id)}>
                    Mark resolved
                  </button>
                )}
              </td>
            </tr>
          ))}
          {filtered.length === 0 && (
            <tr><td colSpan={6} style={{ color: "var(--text-muted)" }}>No reports yet.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
