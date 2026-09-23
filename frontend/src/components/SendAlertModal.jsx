import { useState } from "react";
import { api } from "../api.js";

export default function SendAlertModal({ zone, onClose, onSent }) {
  const [message, setMessage] = useState(
    `Flood risk alert for ${zone.name}. Please stay alert and avoid low-lying areas.`
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSend() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.sendAlert(zone.zone_id, message);
      onSent(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Send alert — {zone.name}</h3>
        <div className="field">
          <label>Message</label>
          <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={4} />
        </div>
        {error && <p className="msg error">{error}</p>}
        <div className="modal-actions">
          <button className="secondary" onClick={onClose}>Cancel</button>
          <button className="primary" onClick={handleSend} disabled={loading}>
            {loading ? "Sending..." : "Send SMS"}
          </button>
        </div>
      </div>
    </div>
  );
}
