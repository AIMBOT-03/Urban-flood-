import { useState } from "react";
import { api } from "../api.js";

export default function ReportForm({ zone, userPosition }) {
  const [description, setDescription] = useState("");
  const [reportType, setReportType] = useState("blocked_drain");
  const [photo, setPhoto] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus(null);
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("zone_id", zone.zone_id);
      formData.append("description", description);
      formData.append("report_type", reportType);
      if (userPosition) {
        formData.append("lat", userPosition[0]);
        formData.append("lon", userPosition[1]);
      }
      if (photo) formData.append("photo", photo);

      await api.submitReport(formData);
      setStatus({ type: "success", text: "Thanks — your report helps improve predictions for this zone." });
      setDescription("");
      setPhoto(null);
      e.target.reset();
    } catch (err) {
      setStatus({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <p className="zone-sub">Choked drain or waterlogging near you? Report it for <strong>{zone.name}</strong>.</p>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="type">Type</label>
          <select id="type" value={reportType} onChange={(e) => setReportType(e.target.value)}>
            <option value="blocked_drain">Blocked / choked drain</option>
            <option value="waterlogging">Waterlogging</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="desc">Description</label>
          <textarea
            id="desc"
            placeholder="e.g. Drain near market fully blocked, water rising"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label htmlFor="photo">Photo (optional)</label>
          <input id="photo" type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files[0])} />
        </div>
        <button className="primary" type="submit" disabled={loading}>
          {loading ? "Submitting..." : "Submit report"}
        </button>
      </form>
      {status && <p className={`msg ${status.type}`} style={{ marginTop: 10 }}>{status.text}</p>}
    </div>
  );
}
