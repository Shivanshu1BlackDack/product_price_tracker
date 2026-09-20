function SummaryCard({ label, value, change, note }) {
  return (
    <div className="summary-card">
      <p className="summary-label">{label}</p>

      <div className="summary-main">
        <span className="summary-value">{value}</span>
        <span className="summary-change">{change}</span>
      </div>

      <p className="summary-note">{note}</p>
    </div>
  );
}

export default SummaryCard;