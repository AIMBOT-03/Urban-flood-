import { useState, useMemo } from "react";
import { api } from "../api.js";
import SendAlertModal from "./SendAlertModal.jsx";

const RISK_ORDER = { High: 0, Medium: 1, Low: 2 };

export default function AdminOverview({ overview, onRefresh }) {
  const [sortKey, setSortKey] = useState("risk");
  const [alertZone, setAlertZone] = useState(null);
  const [simulating, setSimulating] = useState(null);
  const [toast, setToast] = useState(null);

  const sortedZones = useMemo(() => {
    const zones = [...(overview?.zones || [])];
    zones.sort((a, b) => {
      if (sortKey === "risk") return RISK_ORDER[a.risk.level] - RISK_ORDER[b.risk.level];
      if (sortKey === "name") return a.name.localeCompare(b.name);
      if (sortKey === "city") return a.city.localeCompare(b.city);
      if (sortKey === "subscribers") return b.subscribers - a.subscribers;
      return 0;
    });
    return zones;
  }, [overview, sortKey]);

  async function handleSimulate(zoneId) {
    setSimulating(zoneId);
    try {
      const result = await api.simulate(zoneId, {
        rainfall_mm_hr: 90,
        river_level_m: 9.5,
        river_rise_rate_m_hr: 1.4,
      });
      setToast(
        `Simulated heavy rain on ${zoneId} → risk now ${result.risk.level}` +
          (result.escalated_to_high ? " (alert triggered)" : "")
      );
      onRefresh();
    } catch (err) {
      setToast(`Simulation failed: ${err.message}`);
    } finally {
      setSimulating(null);
      setTimeout(() => setToast(null), 5000);
    }
  }

  if (!overview) return <p>Loading overview...</p>;

  return (
    <div>
      <div className="stat-row">
        <div className="stat-card">
          <div className="value" style={{ color: "var(--high)" }}>{overview.risk_counts.High}</div>
          <div className="label">High risk zones</div>
        </div>
        <div className="stat-card">
          <div className="value" style={{ color: "var(--medium)" }}>{overview.risk_counts.Medium}</div>
          <div className="label">Medium risk zones</div>
        </div>
        <div className="stat-card">
          <div className="value" style={{ color: "var(--low)" }}>{overview.risk_counts.Low}</div>
          <div className="label">Low risk zones</div>
        </div>
        <div className="stat-card">
          <div className="value">{overview.total_subscribers}</div>
          <div className="label">SMS subscribers</div>
        </div>
        <div className="stat-card">
          <div className="value">{overview.pending_reports}</div>
          <div className="label">Pending reports</div>
        </div>
      </div>

      {toast && <p className="msg success" style={{ marginTop: 12 }}>{toast}</p>}

      <div className="card" style={{ marginTop: 16 }}>
        <h3>Zones</h3>
        <table>
          <thead>
            <tr>
              <th onClick={() => setSortKey("name")}>Zone</th>
              <th onClick={() => setSortKey("city")}>City</th>
              <th onClick={() => setSortKey("risk")}>Risk</th>
              <th onClick={() => setSortKey("subscribers")}>Subscribers</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedZones.map((z) => (
              <tr key={z.zone_id}>
                <td>{z.name}</td>
                <td>{z.city}</td>
                <td><span className={`risk-badge ${z.risk.level}`}>{z.risk.level}</span></td>
                <td>{z.subscribers}</td>
                <td style={{ display: "flex", gap: 8 }}>
                  <button className="secondary" onClick={() => setAlertZone(z)}>Send Alert</button>
                  <button
                    className="secondary"
                    onClick={() => handleSimulate(z.zone_id)}
                    disabled={simulating === z.zone_id}
                    title="Demo: simulate heavy rain to test the alert pipeline"
                  >
                    {simulating === z.zone_id ? "Simulating..." : "Simulate Heavy Rain"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {alertZone && (
        <SendAlertModal
          zone={alertZone}
          onClose={() => setAlertZone(null)}
          onSent={(result) => {
            setToast(
              result.mock
                ? `(Mock) SMS logged for ${result.recipients} recipient(s).`
                : `SMS sent to ${result.recipients} recipient(s).`
            );
            setAlertZone(null);
            onRefresh();
            setTimeout(() => setToast(null), 5000);
          }}
        />
      )}
    </div>
  );
}
