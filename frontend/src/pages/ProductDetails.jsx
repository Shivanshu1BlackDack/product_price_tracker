import { useState } from "react";
import {
  Link,
  useParams,
} from "react-router-dom";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import {
  RefreshCw,
} from "lucide-react";

import StatusBadge from "../components/StatusBadge";

import useProduct from "../hooks/useProduct";

import {
  scrapeProduct,
  trackProduct,
} from "../services/api";


function formatPrice(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  return `₹${Number(
    value
  ).toLocaleString(
    "en-IN"
  )}`;
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(
    date.getTime()
  )) {
    return value;
  }

  return date.toLocaleString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }
  );
}


function chartDate(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
    }
  );
}


function ProductDetails() {
  const { id } =
    useParams();


  const {
    product,
    priceHistory,
    stockHistory,
    scrapeLogs,
    loading,
    error,
    refreshProduct,
  } = useProduct(id);


  const [
    scraping,
    setScraping,
  ] = useState(false);


  const [
    scrapeError,
    setScrapeError,
  ] = useState("");


  const [
    scrapeSuccess,
    setScrapeSuccess,
  ] = useState("");


  // ==========================================================
  // PRICE CHECK
  // ==========================================================

  const handlePriceCheck =
    async () => {

      if (
        !product ||
        scraping
      ) {
        return;
      }

      try {

        setScraping(true);
        setScrapeError("");
        setScrapeSuccess("");


        const response = product.is_tracked
          ? await scrapeProduct(product.id)
          : await trackProduct({
            product_id: product.id,
          });


        console.log(
          "Price check response:",
          response
        );


        if (!response?.success) {

          throw new Error(
            response?.message ||
            "Scrape failed."
          );
        }


        if (
          !product.is_tracked &&
          response?.scrape_success === false
        ) {
          setScrapeError(
            "Product is now tracked, but its first price check failed. Review the scrape activity below."
          );
        } else {
          setScrapeSuccess(
            product.is_tracked
              ? "Latest product price and stock have been updated."
              : "Product is now tracked and its current price has been checked."
          );
        }


        await refreshProduct();

      } catch (error) {

        console.error(
            "Price check failed:",
          error
        );

        setScrapeError(
          error.message ||
            "Could not check this product's price."
        );

      } finally {

        setScraping(false);
      }
    };


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (
      <div className="empty-state">

        <h3>
          Loading product...
        </h3>

        <p>
          Fetching product details.
        </p>

      </div>
    );
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (error) {

    return (
      <div className="empty-state">

        <h3>
          Could not load product
        </h3>

        <p>
          {error}
        </p>

        <Link
          to="/"
          className="back-home-button"
        >
          Back to dashboard
        </Link>

      </div>
    );
  }


  if (!product) {

    return (
      <div className="empty-state">

        <h3>
          Product not found
        </h3>

        <p>
          No product exists with this ID.
        </p>

        <Link
          to="/"
          className="back-home-button"
        >
          Back to dashboard
        </Link>

      </div>
    );
  }


  const priceChartData =
    priceHistory.map(
      (item) => ({
        date: item.date,
        label: chartDate(
          item.date
        ),
        price: Number(
          item.price
        ),
      })
    );


  const latestLog =
    scrapeLogs.length > 0
      ? scrapeLogs[0]
      : null;

  const specifications =
    product.specifications &&
    typeof product.specifications === "object"
      ? Object.entries(product.specifications)
          .filter(([, value]) =>
            value !== null &&
            value !== undefined &&
            String(value).trim() !== ""
          )
      : [];


  return (
    <div className="product-details-page">

      {/* ================================================== */}
      {/* BACK */}
      {/* ================================================== */}

      <Link
        to="/"
        className="back-link"
      >
        ← Back to dashboard
      </Link>


      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <section className="product-header">

        <div className="product-heading">

          <div className="large-product-image">
            {product.brand
              ? product.brand
                  .charAt(0)
                  .toUpperCase()
              : "P"}
          </div>


          <div>

            <p className="eyebrow">
              {product.category ||
                "PRODUCT"}
            </p>

            <h1>
              {product.name}
            </h1>

            <p className="product-subtitle">

              {product.brand ||
                "Unknown brand"}

              {product.sku
                ? ` · SKU ${product.sku}`
                : ""}

            </p>

          </div>

        </div>


        <div className="product-header-price">

          <strong>
            {formatPrice(
              product.price
            )}
          </strong>

          <StatusBadge
            type="stock"
            value={
              product.stock ||
              "Unknown"
            }
          />


          <button
            type="button"
            className="scrape-button"
            disabled={scraping}
            onClick={
              handlePriceCheck
            }
          >
            <RefreshCw
              aria-hidden="true"
              className={
                scraping
                  ? "price-check-icon is-spinning"
                  : "price-check-icon"
              }
              size={14}
              strokeWidth={2}
            />
            {scraping
              ? "Checking price..."
              : product.is_tracked
                ? "Check Price"
                : "Track & Check Price"}
          </button>

        </div>

      </section>


      {/* ================================================== */}
      {/* FEEDBACK */}
      {/* ================================================== */}

      {scrapeSuccess && (
        <div className="search-success">

          <p>
            {scrapeSuccess}
          </p>

        </div>
      )}


      {scrapeError && (
        <div className="search-empty">

          <h3>
            Price check failed
          </h3>

          <p>
            {scrapeError}
          </p>

        </div>
      )}


      {/* ================================================== */}
      {/* META */}
      {/* ================================================== */}

      <section className="product-meta">

        <div>
          <span>
            INE PRODUCT ID
          </span>

          <strong>
            {product.store_product_id ||
              "—"}
          </strong>
        </div>


        <div>
          <span>
            SKU
          </span>

          <strong>
            {product.sku ||
              "—"}
          </strong>
        </div>


        <div>
          <span>
            SELLER
          </span>

          <strong>
            {product.seller ||
              "—"}
          </strong>
        </div>


        <div>
          <span>
            DELIVERY
          </span>

          <strong>
            {product.delivery ||
              "—"}
          </strong>
        </div>


        <div>
          <span>
            LAST SCRAPED
          </span>

          <strong>
            {formatDate(
              product.last_scraped_at
            )}
          </strong>
        </div>

      </section>


      {/* ================================================== */}
      {/* STATS */}
      {/* ================================================== */}

      <section className="product-stats">

        <div className="product-stat">

          <span>
            CURRENT PRICE
          </span>

          <strong>
            {formatPrice(
              product.price
            )}
          </strong>

        </div>


        <div className="product-stat">

          <span>
            STOCK
          </span>

          <strong>
            {product.stock ||
              "Unknown"}
          </strong>

        </div>


        <div className="product-stat">

          <span>
            DISCOUNT
          </span>

          <strong>
            {product.discount !==
              null &&
            product.discount !==
              undefined
              ? `${product.discount}%`
              : "—"}
          </strong>

        </div>


        <div className="product-stat">

          <span>
            SCRAPE STATUS
          </span>

          <strong>
            {latestLog?.status ||
              "No attempts"}
          </strong>

        </div>

      </section>


      {/* ================================================== */}
      {/* PRICE HISTORY CHART */}
      {/* ================================================== */}

      <section className="section-card">

        <div className="section-header">

          <div>

            <p className="eyebrow">
              PRICE HISTORY
            </p>

            <h2>
              Price over time
            </h2>

          </div>

          <span className="panel-count">
            {priceHistory.length} records
          </span>

        </div>


        {priceChartData.length === 0 ? (

          <div className="empty-state">

            <h3>
              No price history yet
            </h3>

            <p>
              A successful scrape will
              create a price record.
            </p>

          </div>

        ) : (

          <div className="chart-card">

            <div className="price-chart">

              <ResponsiveContainer
                width="100%"
                height="100%"
              >

                <LineChart
                  data={
                    priceChartData
                  }
                  margin={{
                    top: 15,
                    right: 20,
                    left: 10,
                    bottom: 5,
                  }}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                  />

                  <XAxis
                    dataKey="label"
                  />

                  <YAxis
                    tickFormatter={(
                      value
                    ) =>
                      `₹${Number(
                        value
                      ).toLocaleString(
                        "en-IN"
                      )}`
                    }
                  />

                  <Tooltip
                    formatter={(
                      value
                    ) => [
                      formatPrice(
                        value
                      ),
                      "Price",
                    ]}
                  />

                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="var(--dark)"
                    strokeWidth={2}
                    dot={{
                      r: 3,
                    }}
                  />

                </LineChart>

              </ResponsiveContainer>

            </div>

          </div>
        )}

      </section>


      {/* ================================================== */}
      {/* PRICE HISTORY TABLE */}
      {/* ================================================== */}

      {priceHistory.length > 0 && (

        <section className="section-card">

          <div className="section-header">

            <div>

              <p className="eyebrow">
                RECORDED PRICES
              </p>

              <h2>
                Price history
              </h2>

            </div>

          </div>


          <div className="history-table-wrapper">

            <table className="history-table">

              <thead>

                <tr>
                  <th>Date</th>
                  <th>Price</th>
                </tr>

              </thead>


              <tbody>

                {[...priceHistory]
                  .reverse()
                  .map(
                    (
                      item,
                      index
                    ) => (

                      <tr
                        key={`${item.date}-${index}`}
                      >

                        <td>
                          {formatDate(
                            item.date
                          )}
                        </td>

                        <td>
                          {formatPrice(
                            item.price
                          )}
                        </td>

                      </tr>

                    )
                  )}

              </tbody>

            </table>

          </div>

        </section>
      )}


      {/* ================================================== */}
      {/* STOCK HISTORY */}
      {/* ================================================== */}

      <section className="section-card">

        <div className="section-header">

          <div>

            <p className="eyebrow">
              STOCK HISTORY
            </p>

            <h2>
              Availability over time
            </h2>

          </div>

          <span className="panel-count">
            {stockHistory.length} records
          </span>

        </div>


        {stockHistory.length === 0 ? (

          <div className="empty-state">

            <h3>
              No stock history yet
            </h3>

          </div>

        ) : (

          <div className="stock-history-list">

            {[...stockHistory]
              .reverse()
              .map(
                (
                  item,
                  index
                ) => (

                  <div
                    className="stock-history-row"
                    key={`${item.time}-${index}`}
                  >

                    <div className="stock-history-info">

                      <div className="stock-history-main">

                        <span className="timeline-dot" />

                        <strong>
                          {item.status}
                        </strong>

                      </div>

                      <p>
                        {formatDate(
                          item.time
                        )}
                      </p>

                    </div>


                    {item.note && (
                      <span className="stock-history-note">
                        {item.note}
                      </span>
                    )}

                  </div>

                )
              )}

          </div>

        )}

      </section>


      {/* ================================================== */}
      {/* SCRAPE LOG */}
      {/* ================================================== */}

      <section className="section-card">

        <div className="section-header">

          <div>

            <p className="eyebrow">
              SCRAPE LOG
            </p>

            <h2>
              Scraping activity
            </h2>

            <p className="section-description">
              Every scrape attempt for
              this product.
            </p>

          </div>

          <span className="panel-count">
            {scrapeLogs.length} attempts
          </span>

        </div>


        {scrapeLogs.length === 0 ? (

          <div className="empty-state">

            <h3>
              No scrape attempts yet
            </h3>

          </div>

        ) : (

          <div className="scrape-log-wrapper">

            <table className="scrape-log-table">

              <thead>

                <tr>
                  <th>Time</th>
                  <th>Attempt</th>
                  <th>Status</th>
                  <th>Details</th>
                  <th>Duration</th>
                </tr>

              </thead>


              <tbody>

                {scrapeLogs.map(
                  (log) => (

                    <tr
                      key={log.id}
                    >

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

        )}

      </section>


      {/* ================================================== */}
      {/* SPECIFICATIONS */}
      {/* ================================================== */}

      {specifications.length > 0 && (

        <section className="section-card">

          <div className="section-header">

            <div>

              <p className="eyebrow">
                SPECIFICATIONS
              </p>

              <h2>
                Product details
              </h2>

            </div>

          </div>


          <div className="history-table-wrapper">

            <table className="history-table">

              <tbody>

                {specifications.map(
                  ([key, value]) => (

                    <tr key={key}>

                      <th>
                        {key}
                      </th>

                      <td>
                        {String(value)}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        </section>

      )}


      {/* ================================================== */}
      {/* DESCRIPTION */}
      {/* ================================================== */}

      {(product.description ||
        product.about) && (

        <section className="section-card">

          <div className="section-header">

            <div>

              <p className="eyebrow">
                PRODUCT INFORMATION
              </p>

              <h2>
                About this product
              </h2>

            </div>

          </div>


          <div className="about-section">

            {product.description && (
              <p>
                {product.description}
              </p>
            )}

            {product.about && (
              <p>
                {product.about}
              </p>
            )}

          </div>

        </section>

      )}

    </div>
  );
}


export default ProductDetails;
