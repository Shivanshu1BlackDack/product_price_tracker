function StatusBadge({ type, value }) {
  const getClassName = () => {
    if (type === "stock") {
      if (value === "In Stock") {
        return "stock-in";
      }

      if (value === "Out of Stock") {
        return "stock-out";
      }

      if (value === "Low Stock") {
        return "stock-low";
      }

      return "stock-unknown";
    }

    if (value === "Success") {
      return "scrape-success";
    }

    if (value === "Retried") {
      return "scrape-retried";
    }

    if (value === "Failed") {
      return "scrape-failed";
    }

    return "scrape-unknown";
  };

  return (
    <span className={`status-badge ${getClassName()}`}>
      <span className="status-indicator"></span>
      {value}
    </span>
  );
}

export default StatusBadge;