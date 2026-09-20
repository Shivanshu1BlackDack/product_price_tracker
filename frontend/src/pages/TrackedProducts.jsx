import { useState } from "react";
import { Link } from "react-router-dom";

import {
  RefreshCw,
} from "lucide-react";

import StatusBadge from "../components/StatusBadge";
import useProducts from "../hooks/useProducts";

import {
  scrapeProduct,
  untrackProduct,
} from "../services/api";


function formatPrice(value) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  return `₹${Number(value).toLocaleString("en-IN")}`;
}


function formatDate(value) {
  if (!value) {
    return "Never";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}


function productInitial(product) {
  return (
    product.brand ||
    product.name ||
    "P"
  )
    .slice(0, 3)
    .toUpperCase();
}


function TrackedProducts() {
  const {
    products,
    loading,
    error,
    refreshProducts,
  } = useProducts();

  const [
    activeAction,
    setActiveAction,
  ] = useState(null);

  const [
    actionError,
    setActionError,
  ] = useState("");

  const runScrape = async (id) => {
    try {
      setActiveAction({
        id,
        type: "price-check",
      });
      setActionError("");

      const response = await scrapeProduct(id);

      if (!response?.success) {
        throw new Error(
          response?.message ||
          "Price check failed.",
        );
      }

      await refreshProducts();
    } catch (error) {
      setActionError(
        error.message ||
        "Could not check this product's price.",
      );
    } finally {
      setActiveAction(null);
    }
  };

  const removeTracking = async (id) => {
    try {
      setActiveAction({
        id,
        type: "untrack",
      });
      setActionError("");

      await untrackProduct(id);
      await refreshProducts();
    } catch (error) {
      setActionError(
        error.message ||
        "Could not untrack product.",
      );
    } finally {
      setActiveAction(null);
    }
  };

  return (
    <div className="tracked-products-page">
      <section className="inventory-header">
        <div>
          <p className="eyebrow">PRODUCT MONITORING</p>

          <h1>Tracked Products Inventory</h1>

          <p className="page-description">
            Manage products currently under automated price and
            stock monitoring.
          </p>
        </div>

        <div className="inventory-count">
          Total Tracked: {products.length}
        </div>
      </section>

      {actionError && (
        <div className="search-empty">
          <h3>Action failed</h3>
          <p>{actionError}</p>
        </div>
      )}

      {loading ? (
        <div className="empty-state">
          <h3>Loading tracked products...</h3>
        </div>
      ) : error ? (
        <div className="empty-state">
          <h3>Could not load products</h3>
          <p>{error}</p>
        </div>
      ) : products.length === 0 ? (
        <div className="empty-state">
          <h3>No tracked products yet</h3>
          <p>Search the catalog from the dashboard to begin.</p>
        </div>
      ) : (
        <section className="product-card-grid">
          {products.map((product) => {
            const busy =
              activeAction?.id === product.id;

            const checkingPrice =
              busy &&
              activeAction?.type === "price-check";

            return (
              <article
                className="tracked-product-card"
                key={product.id}
              >
                <div className="card-top">
                  <div className="card-product-image">
                    {productInitial(product)}
                  </div>

                  <StatusBadge
                    type="stock"
                    value={
                      product.stock ||
                      "Unknown"
                    }
                  />
                </div>

                <div className="tracked-product-content">
                  <p className="tracked-product-category">
                    {product.category || "PRODUCT"}
                  </p>

                  <h2>
                    <Link
                      to={`/product/${product.id}`}
                      className="tracked-product-name"
                    >
                      {product.name}
                    </Link>
                  </h2>

                  <p className="tracked-product-brand">
                    {product.brand || "Unknown brand"}
                    {product.sku ? ` · ${product.sku}` : ""}
                  </p>

                  <div className="tracked-product-price-row">
                    <span className="tracked-product-price">
                      {formatPrice(product.price)}
                    </span>

                    <span className="tracked-product-time">
                      Last scraped {formatDate(product.last_scraped_at)}
                    </span>
                  </div>
                </div>

                <div className="card-divider"></div>

                <div className="product-card-footer">
                  <Link
                    to={`/product/${product.id}`}
                    className="analytics-link"
                  >
                    View Details
                    <span>→</span>
                  </Link>

                  <div className="action-buttons">
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={busy}
                      onClick={() => runScrape(product.id)}
                    >
                      <RefreshCw
                        aria-hidden="true"
                        className={
                          checkingPrice
                            ? "price-check-icon is-spinning"
                            : "price-check-icon"
                        }
                        size={13}
                        strokeWidth={2}
                      />
                      {checkingPrice
                        ? "Checking..."
                        : "Check Price"}
                    </button>

                    <button
                      type="button"
                      className="dark-button"
                      disabled={busy}
                      onClick={() => removeTracking(product.id)}
                    >
                      Untrack
                    </button>
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </div>
  );
}

export default TrackedProducts;
