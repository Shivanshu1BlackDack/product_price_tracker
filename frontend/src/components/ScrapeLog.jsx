import { Link } from "react-router-dom";

import useProduct from "../hooks/useProduct";


function ScrapeLog({
  products = [],
}) {
  const recentProducts =
    products.slice(0, 5);


  if (recentProducts.length === 0) {
    return (
      <div className="empty-state">

        <h3>
          No scrape activity yet
        </h3>

        <p>
          Track a product to start
          recording scrape activity.
        </p>

      </div>
    );
  }


  return (
    <div className="recent-scrape-list">

      {recentProducts.map(
        (product) => (

          <RecentProductLog
            key={product.id}
            product={product}
          />

        )
      )}

    </div>
  );
}


function RecentProductLog({
  product,
}) {
  const {
    scrapeLogs,
    loading,
  } = useProduct(
    product.id
  );


  const latestLog =
    scrapeLogs.length > 0
      ? scrapeLogs[0]
      : null;


  return (
    <div className="recent-scrape-item">

      <div className="recent-scrape-product">

        <Link
          to={`/product/${product.id}`}
        >
          {product.name}
        </Link>

        <span>
          {latestLog?.time ||
            "No scrape yet"}
        </span>

      </div>


      <div className="recent-scrape-status">

        {loading
          ? "Loading..."
          : latestLog?.status ||
            "No attempts"}

      </div>


      <div className="recent-scrape-price">

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

      </div>

    </div>
  );
}


export default ScrapeLog;