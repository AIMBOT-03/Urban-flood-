import { useState } from "react";
import { api } from "../api.js";

export default function ActionLog({ log, onRefresh }) {
  const [note, setNote] = useState("");

  async function addNote(e) {
    e.preventDefault();
    if (!note.trim()) return;
    await api.addAction(note.trim());
    setNote("");
    onRefresh();
  }

  return (
    <div>
      <form onSubmit={addNote} style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <input
          style={{ flex: 1, background: "var(--bg)", border: "1px solid var(--border)", color: "var(--text)", padding: "8px 10px", borderRadius: 6, fontSize: 14 }}
          placeholder="e.g. Pumps dispatched to Naraj"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        <button className="secondary" type="submit">Log</button>
      </form>
      <div>
        {log.length === 0 && <p style={{ color: "var(--text-muted)" }}>No actions logged yet.</p>}
        {log.map((entry) => (
          <div className="action-log-item" key={entry.action_id}>
            <div>{entry.message}</div>
            <div className="time">{new Date(entry.created_at).toLocaleString()} · {entry.actor}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
