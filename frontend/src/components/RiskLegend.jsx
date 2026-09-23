export default function RiskLegend() {
  return (
    <div className="legend">
      <div className="legend-row"><span className="dot Low" /> Low risk</div>
      <div className="legend-row"><span className="dot Medium" /> Medium risk</div>
      <div className="legend-row"><span className="dot High" /> High risk</div>
    </div>
  );
}
