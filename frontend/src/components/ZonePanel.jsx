export default function ZonePanel({ zone, zones, onChangeZone, distanceKm }) {
  const level = zone.risk?.level || "Low";
  const conditions = zone.conditions || {};

  return (
    <div>
      <div className="field">
        <label htmlFor="zone-select">Viewing zone</label>
        <select id="zone-select" value={zone.zone_id} onChange={(e) => onChangeZone(e.target.value)}>
          {zones.map((z) => (
            <option key={z.zone_id} value={z.zone_id}>
              {z.name} — {z.city}
            </option>
          ))}
        </select>
      </div>
      <p className="zone-title">{zone.name}</p>
      <p className="zone-sub">
        {zone.city}
        {typeof distanceKm === "number" ? ` · ${distanceKm} km away` : ""}
      </p>
      <span className={`risk-badge ${level}`}>{level} risk</span>
      <div style={{ marginTop: 14, fontSize: 13, color: "var(--text-muted)", lineHeight: 1.8 }}>
        <div>Rainfall: {conditions.rainfall_mm_hr?.toFixed?.(1) ?? "-"} mm/hr</div>
        <div>River level: {conditions.river_level_m?.toFixed?.(1) ?? "-"} m</div>
        <div>River rise rate: {conditions.river_rise_rate_m_hr?.toFixed?.(2) ?? "-"} m/hr</div>
        <div>Active drain issues: {conditions.active_drain_count ?? "-"}</div>
        <div>Citizen reports: {conditions.citizen_report_count ?? "-"}</div>
      </div>
    </div>
  );
}
