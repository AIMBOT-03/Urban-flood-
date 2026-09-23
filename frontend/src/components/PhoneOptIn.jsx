import { useState } from "react";
import { api } from "../api.js";

export default function PhoneOptIn({ zone }) {
  const [phone, setPhone] = useState("");
  const [status, setStatus] = useState(null); // { type: "success"|"error", text }
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus(null);
    setLoading(true);
    try {
      await api.subscribe(phone, zone.zone_id);
      setStatus({ type: "success", text: `You'll get SMS alerts for ${zone.name}.` });
      setPhone("");
    } catch (err) {
      setStatus({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <p className="zone-sub">
        No account needed. Just your number — we'll text you if <strong>{zone.name}</strong> turns High risk.
      </p>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="phone">Mobile number</label>
          <input
            id="phone"
            type="tel"
            placeholder="98XXXXXXXX"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            required
            maxLength={10}
            pattern="[6-9][0-9]{9}"
          />
        </div>
        <button className="primary" type="submit" disabled={loading}>
          {loading ? "Subscribing..." : "Subscribe for this zone"}
        </button>
      </form>
      {status && <p className={`msg ${status.type}`} style={{ marginTop: 10 }}>{status.text}</p>}
    </div>
  );
}
