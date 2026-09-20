import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getTrackedProducts,
} from "../services/api";


function useProducts() {
  const [products, setProducts] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const refreshProducts =
    useCallback(async () => {
      try {
        setLoading(true);
        setError("");

        const data =
          await getTrackedProducts();

        setProducts(
          Array.isArray(data)
            ? data
            : [],
        );
      } catch (error) {
        console.error(
          "Loading tracked products failed:",
          error,
        );

        setError(
          error.message ||
          "Could not load tracked products.",
        );
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      refreshProducts();
    }, 0);

    window.addEventListener(
      "product-tracking-changed",
      refreshProducts,
    );

    return () => {
      window.clearTimeout(timeoutId);
      window.removeEventListener(
        "product-tracking-changed",
        refreshProducts,
      );
    };
  }, [refreshProducts]);

  return {
    products,
    loading,
    error,
    refreshProducts,
  };
}

export default useProducts;
