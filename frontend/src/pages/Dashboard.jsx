import { useState } from "react";

import {
  Link,
} from "react-router-dom";

import SearchBar from "../components/Searchbar";
import ProductTable from "../components/ProductTable";
import StatusBadge from "../components/StatusBadge";
import SummaryCard from "../components/SummaryCard";
import ScrapeLog from "../components/ScrapeLog";

import useProducts from "../hooks/useProducts";
import useSearchProducts from "../hooks/useSearchProducts";

import {
  scrapeProduct,
  trackProduct,
} from "../services/api";


function Dashboard() {

  const {
    products,
    loading: productsLoading,
    error: productsError,
    refreshProducts,
  } = useProducts();


  const {
    results,
    loading: searchLoading,
    error: searchError,
    searchProducts,
    clearResults,
  } = useSearchProducts();


  const [
    trackingProductId,
    setTrackingProductId,
  ] = useState(null);


  const [
    trackError,
    setTrackError,
  ] = useState("");


  const [
    trackSuccess,
    setTrackSuccess,
  ] = useState("");

  const [
    checkingProductId,
    setCheckingProductId,
  ] = useState(null);

  const [
    priceCheckError,
    setPriceCheckError,
  ] = useState("");

  const [
    priceCheckSuccess,
    setPriceCheckSuccess,
  ] = useState("");


  // ==========================================================
  // SEARCH
  // ==========================================================

  const handleSearch =
    async (query) => {

      setTrackError("");
      setTrackSuccess("");

      await searchProducts(
        query
      );
    };


  // ==========================================================
  // TRACK
  // ==========================================================

  const handleTrack =
    async (product) => {

      try {

        setTrackingProductId(
          product.store_product_id ||
          product.id
        );

        setTrackError("");
        setTrackSuccess("");


        console.log(
          "Tracking catalog product:",
          product
        );


        const response = await trackProduct({
          product_id: product.id,
        });


        console.log(
          "Track response:",
          response
        );


        if (!response?.success) {

          throw new Error(
            response?.message ||
            "Could not track product."
          );
        }


        setTrackSuccess(
          response?.scrape_success === false
            ? `${product.name} is tracked. Its first price check failed, so review the audit log.`
            : `${product.name} is now tracked and its price has been checked.`
        );


        clearResults();


        await refreshProducts();

      } catch (error) {

        console.error(
          "Track product failed:",
          error
        );

        setTrackError(
          error.message ||
          "Could not track product."
        );

      } finally {

        setTrackingProductId(
          null
        );
      }
    };


  // ==========================================================
  // CHECK ONE TRACKED PRODUCT
  // ==========================================================

  const handlePriceCheck =
    async (product) => {

      if (
        !product ||
        checkingProductId === product.id
      ) {
        return;
      }

      try {

        setCheckingProductId(product.id);
        setPriceCheckError("");
        setPriceCheckSuccess("");

        const response = await scrapeProduct(product.id);

        if (!response?.success) {
          throw new Error(
            response?.message ||
            "Price check failed."
          );
        }

        setPriceCheckSuccess(
          `${product.name} has been checked and updated.`
        );

        await refreshProducts();

      } catch (error) {

        console.error(
          "Product price check failed:",
          error
        );

        setPriceCheckError(
          error.message ||
          "Could not check this product's price."
        );

      } finally {

        setCheckingProductId(null);
      }
    };


  // ==========================================================
  // SUMMARY
  // ==========================================================

  const trackedCount =
    products.length;


  const scrapedCount =
    products.filter(
      (product) =>
        Boolean(
          product.last_scraped_at
        )
    ).length;


  const inStockCount =
    products.filter(
      (product) => {

        const stock =
          (
            product.stock ||
            ""
          ).toLowerCase();

        return (
          stock.includes(
            "in stock"
          ) &&
          !stock.includes(
            "out of stock"
          )
        );
      }
    ).length;


  const latestProduct =
    products.length
      ? products[0]
      : null;


  return (
    <div className="dashboard-page">

      {/* ================================================== */}
      {/* HERO */}
      {/* ================================================== */}

      <section className="dashboard-hero">

        <div className="dashboard-hero-content">

          <p className="eyebrow">
            PRICE TRACKER
          </p>

          <h1>
            Track prices.
            <br />
            Catch changes.
          </h1>

          <p className="page-description">
            Search the INE catalog,
            select a product, and track
            its live price and stock.
          </p>


          <SearchBar
            onSearch={
              handleSearch
            }
            loading={
              searchLoading
            }
          />

        </div>

      </section>


      {/* ================================================== */}
      {/* SEARCH ERROR */}
      {/* ================================================== */}

      {searchError && (
        <div className="search-empty">

          <h3>
            Search failed
          </h3>

          <p>
            {searchError}
          </p>

        </div>
      )}


      {/* ================================================== */}
      {/* TRACK ERROR */}
      {/* ================================================== */}

      {trackError && (
        <div className="search-empty">

          <h3>
            Could not track product
          </h3>

          <p>
            {trackError}
          </p>

        </div>
      )}


      {/* ================================================== */}
      {/* TRACK SUCCESS */}
      {/* ================================================== */}

      {trackSuccess && (
        <div className="search-success">

          <p>
            {trackSuccess}
          </p>

        </div>
      )}


      {priceCheckError && (
        <div className="search-empty">

          <h3>
            Price check failed
          </h3>

          <p>
            {priceCheckError}
          </p>

        </div>
      )}


      {priceCheckSuccess && (
        <div className="search-success">

          <p>
            {priceCheckSuccess}
          </p>

        </div>
      )}


      {/* ================================================== */}
      {/* CATALOG SEARCH RESULTS */}
      {/* ================================================== */}

      {results.length > 0 && (

        <section className="search-results">

          <div className="section-header">

            <div>

              <p className="eyebrow">
                PRODUCT CATALOG
              </p>

              <h2>
                Search results
              </h2>

              <p className="section-description">
                Select a product to start
                tracking it.
              </p>

            </div>

          </div>


          <div className="search-result-list">

            {results.map(
              (product) => {

                const productKey =
                  product.store_product_id ||
                  product.id;


                const isTracked =
                  product.is_tracked;


                const isTracking =
                  trackingProductId ===
                  productKey;


                return (
                  <div
                    className="search-result-item"
                    key={productKey}
                  >

                    <div className="search-result-info">

                      <p className="search-result-category">
                        {product.category ||
                          "PRODUCT"}
                      </p>

                      <h3>
                        <Link
                          to={`/product/${product.id}`}
                          className="search-result-name"
                        >
                          {product.name}
                        </Link>
                      </h3>

                      <p className="search-result-meta">

                        {product.brand ||
                          "Unknown brand"}

                        {product.sku
                          ? ` · ${product.sku}`
                          : ""}

                      </p>

                      <p className="search-result-meta">

                        INE Product ID:{" "}

                        {product.store_product_id ||
                          product.id}

                      </p>

                    </div>


                    <div className="search-result-status">

                      {isTracked ? (

                        <StatusBadge
                          type="scrape"
                          value="Tracked"
                        />

                      ) : (

                        <span>
                          Catalog product
                        </span>

                      )}

                    </div>


                    <button
                      type="button"
                      className="search-result-action"
                      disabled={
                        isTracked ||
                        isTracking
                      }
                      onClick={() =>
                        handleTrack(
                          product
                        )
                      }
                    >

                      {isTracked
                        ? "Tracked"
                        : isTracking
                          ? "Checking..."
                          : "Track & Check Price"}

                    </button>

                  </div>
                );
              }
            )}

          </div>

        </section>
      )}


      {/* ================================================== */}
      {/* SUMMARY */}
      {/* ================================================== */}

      <section className="summary-grid">

        <SummaryCard
          label="TRACKED PRODUCTS"
          value={trackedCount}
          change=""
          note="Products currently monitored"
        />

        <SummaryCard
          label="SCRAPED"
          value={scrapedCount}
          change=""
          note="Products with scrape history"
        />

        <SummaryCard
          label="IN STOCK"
          value={inStockCount}
          change=""
          note="Currently available"
        />

        <SummaryCard
          label="LATEST"
          value={
            latestProduct
              ? `₹${Number(
                  latestProduct.price ||
                  0
                ).toLocaleString(
                  "en-IN"
                )}`
              : "—"
          }
          change=""
          note={
            latestProduct
              ? latestProduct.name
              : "No tracked products"
          }
        />

      </section>


      {/* ================================================== */}
      {/* TRACKED PRODUCTS */}
      {/* ================================================== */}

      <section className="panel">

        <div className="panel-header">

          <div>

            <p className="eyebrow">
              TRACKED INVENTORY
            </p>

            <h2>
              Your products
            </h2>

          </div>

          <span className="panel-count">
            {trackedCount} products
          </span>

        </div>


        {productsLoading ? (

          <div className="empty-state">
            <h3>
              Loading products...
            </h3>
          </div>

        ) : productsError ? (

          <div className="empty-state">

            <h3>
              Could not load products
            </h3>

            <p>
              {productsError}
            </p>

          </div>

        ) : (

          <ProductTable
            products={products}
            checkingProductId={checkingProductId}
            onPriceCheck={handlePriceCheck}
          />

        )}

      </section>


      {/* ================================================== */}
      {/* RECENT ACTIVITY */}
      {/* ================================================== */}

      <section className="panel">

        <div className="panel-header">

          <div>

            <p className="eyebrow">
              SCRAPE ACTIVITY
            </p>

            <h2>
              Recent activity
            </h2>

          </div>

          <Link
            to="/logs"
            className="panel-count"
          >
            View all
          </Link>

        </div>


        <ScrapeLog
          products={products}
        />

      </section>

    </div>
  );
}


export default Dashboard;
