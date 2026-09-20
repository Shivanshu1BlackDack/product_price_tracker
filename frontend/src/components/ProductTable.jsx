import { Link } from "react-router-dom";

import {
  ArrowRight,
  RefreshCw,
} from "lucide-react";

import StatusBadge from "./StatusBadge";


function ProductTable({
  products = [],
  checkingProductId = null,
  onPriceCheck,
}) {

  if (products.length === 0) {

    return (
      <div className="empty-state">

        <h3>
          No tracked products
        </h3>

        <p>
          Search the catalog and track
          a product to see it here.
        </p>

      </div>
    );
  }


  return (
    <div className="product-table-wrapper">

      <table className="product-table">

        <thead>

          <tr>
            <th>Product</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Last Scraped</th>
            <th>Status</th>
            <th>Action</th>
          </tr>

        </thead>


        <tbody>

          {products.map(
            (product) => {
              const checking =
                checkingProductId === product.id;

              return (

              <tr
                key={product.id}
              >

                <td>

                  <Link
                    to={`/product/${product.id}`}
                    className="product-table-name"
                  >
                    {product.name}
                  </Link>

                  <div className="product-table-meta">
                    {product.brand ||
                      "Unknown brand"}

                    {product.sku
                      ? ` · ${product.sku}`
                      : ""}
                  </div>

                </td>


                <td>

                  {product.price !==
                    null &&
                  product.price !==
                    undefined

                    ? `₹${Number(
                        product.price
                      ).toLocaleString(
                        "en-IN"
                      )}`

                    : "—"}

                </td>


                <td>

                  <StatusBadge
                    type="stock"
                    value={
                      product.stock ||
                      "Unknown"
                    }
                  />

                </td>


                <td>

                  {product.last_scraped_at
                    ? new Date(
                        product.last_scraped_at
                      ).toLocaleString(
                        "en-IN"
                      )
                    : "Never"}

                </td>


                <td>

                  <StatusBadge
                    type="scrape"
                    value={
                      product.last_scraped_at
                        ? "Success"
                        : "Pending"
                    }
                  />

                </td>


                <td>

                  <div className="product-table-actions">

                    {onPriceCheck && (
                      <button
                        type="button"
                        className="product-table-check"
                        disabled={checking}
                        onClick={() => onPriceCheck(product)}
                      >
                        <RefreshCw
                          aria-hidden="true"
                          className={
                            checking
                              ? "price-check-icon is-spinning"
                              : "price-check-icon"
                          }
                          size={13}
                          strokeWidth={2}
                        />
                        {checking
                          ? "Checking..."
                          : "Check Price"}
                      </button>
                    )}

                    <Link
                      to={`/product/${product.id}`}
                      className="product-table-action"
                      aria-label={`Open ${product.name}`}
                      title="Open product details"
                    >
                      <ArrowRight
                        aria-hidden="true"
                        size={15}
                        strokeWidth={2}
                      />
                    </Link>

                  </div>

                </td>

              </tr>
              );
            }
          )}

        </tbody>

      </table>

    </div>
  );
}


export default ProductTable;
