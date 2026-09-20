const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000/api";


async function request(
  endpoint,
  options = {}
) {
  const method = (
    options.method ||
    "GET"
  ).toUpperCase();

  const response =
    await fetch(
      `${API_URL}${endpoint}`,
      {
        headers: {
          "Content-Type":
            "application/json",

          ...(options.headers || {}),
        },

        ...options,
      }
    );


  let data = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }


  if (!response.ok) {
    throw new Error(
      data?.error ||
      data?.message ||
      `Request failed with status ${response.status}`
    );
  }

  if (method !== "GET") {
    window.dispatchEvent(
      new CustomEvent(
        "product-tracking-changed"
      )
    );
  }


  return data;
}


// ============================================================
// CATALOG
// ============================================================

export async function getCatalog() {
  return request(
    "/catalog/"
  );
}


export async function syncCatalog() {
  return request(
    "/catalog/sync/",
    {
      method: "POST",
    }
  );
}


// ============================================================
// SEARCH LOCAL CATALOG
// ============================================================

export async function searchProducts(
  query
) {
  return request(
    `/products/search/?q=${encodeURIComponent(
      query
    )}`
  );
}


// ============================================================
// TRACKED PRODUCTS
// ============================================================

export async function getTrackedProducts() {
  return request(
    "/products/tracked/"
  );
}


// ============================================================
// PRODUCT
// ============================================================

export async function getProduct(
  id
) {
  return request(
    `/products/${id}/`
  );
}


// ============================================================
// PRICE HISTORY
// ============================================================

export async function getPriceHistory(
  id
) {
  return request(
    `/products/${id}/history/`
  );
}


// ============================================================
// STOCK HISTORY
// ============================================================

export async function getStockHistory(
  id
) {
  return request(
    `/products/${id}/stock-history/`
  );
}


// ============================================================
// PRODUCT LOGS
// ============================================================

export async function getScrapeLogs(
  id
) {
  return request(
    `/products/${id}/logs/`
  );
}


// ============================================================
// ALL LOGS
// ============================================================

export async function getAllScrapeLogs() {
  return request(
    "/scrape-logs/"
  );
}


// ============================================================
// TRACK PRODUCT
// ============================================================

export async function trackProduct(
  product
) {
  return request(
    "/products/track/",
    {
      method: "POST",

      body: JSON.stringify(
        product
      ),
    }
  );
}


// ============================================================
// UNTRACK
// ============================================================

export async function untrackProduct(
  id
) {
  return request(
    `/products/${id}/`,
    {
      method: "DELETE",
    }
  );
}


// ============================================================
// MANUAL SCRAPE
// ============================================================

export async function scrapeProduct(
  id,
  options = {}
) {
  return request(
    `/products/${id}/scrape/${
      options.headed
        ? "?headed=true"
        : ""
    }`,
    {
      method: "POST",

      body: JSON.stringify({
        headed: Boolean(options.headed),
      }),
    }
  );
}


// ============================================================
// SCRAPE ALL
// ============================================================

export async function scrapeAllTrackedProducts() {
  return request(
    "/products/scrape-all/",
    {
      method: "POST",
    }
  );
}
