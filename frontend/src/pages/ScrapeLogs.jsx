import {
  useEffect,
  useState,
} from "react";

import {
  getAllScrapeLogs,
} from "../services/api";

import StatusBadge from "../components/StatusBadge";


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleString(
    "en-IN"
  );
}


function ScrapeLogs() {
  const [
    logs,
    setLogs,
  ] = useState([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  useEffect(() => {

    const loadLogs =
      async () => {

        try {

          setLoading(true);
          setError("");

          const data =
            await getAllScrapeLogs();

          setLogs(
            Array.isArray(data)
              ? data
              : []
          );

        } catch (error) {

          console.error(
            "Loading scrape logs failed:",
            error
          );

          setError(
            error.message ||
            "Could not load scrape logs."
          );

        } finally {

          setLoading(false);
        }
      };


    loadLogs();

  }, []);


  if (loading) {

    return (
      <div className="empty-state">

        <h3>
          Loading scrape logs...
        </h3>

      </div>
    );
  }


  if (error) {

    return (
      <div className="empty-state">

        <h3>
          Could not load scrape logs
        </h3>

        <p>
          {error}
        </p>

      </div>
    );
  }


  return (
    <div className="scrape-logs-page">

      <div className="inventory-header">

        <div>

          <p className="eyebrow">
            SCRAPE ACTIVITY
          </p>

          <h1>
            Scrape logs
          </h1>

          <p className="section-description">
            Every recorded scrape attempt
            for tracked products.
          </p>

        </div>

        <div className="inventory-count">
          {logs.length} attempts
        </div>

      </div>


      {logs.length === 0 ? (

        <div className="empty-state">

          <h3>
            No scrape attempts
          </h3>

          <p>
            Scrape activity will appear
            here after products are tracked.
          </p>

        </div>

      ) : (

        <div className="panel">

          <div className="scrape-log-wrapper">

            <table className="scrape-log-table">

              <thead>

                <tr>
                  <th>Product</th>
                  <th>Time</th>
                  <th>Attempt</th>
                  <th>Status</th>
                  <th>Details</th>
                  <th>Duration</th>
                </tr>

              </thead>


              <tbody>

                {logs.map(
                  (log) => (

                    <tr
                      key={log.id}
                    >

                      <td>
                        {log.product ||
                          "Unknown product"}
                      </td>

                      <td>
                        {formatDate(
                          log.time
                        )}
                      </td>

                      <td>
                        #{log.attempt}
                      </td>

                      <td>

                        <StatusBadge
                          type="scrape"
                          value={
                            log.status
                          }
                        />

                      </td>

                      <td>
                        {log.details ||
                          "—"}
                      </td>

                      <td>
                        {log.duration ||
                          "—"}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        </div>

      )}

    </div>
  );
}


export default ScrapeLogs;