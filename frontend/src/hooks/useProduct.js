import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getProduct,
  getPriceHistory,
  getStockHistory,
  getScrapeLogs,
} from "../services/api";


function useProduct(id) {
  const [product, setProduct] =
    useState(null);

  const [priceHistory, setPriceHistory] =
    useState([]);

  const [stockHistory, setStockHistory] =
    useState([]);

  const [scrapeLogs, setScrapeLogs] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  const refreshProduct =
    useCallback(async () => {

      if (!id) {
        setLoading(false);
        return;
      }

      try {

        setLoading(true);
        setError("");

        const [
          productData,
          priceData,
          stockData,
          logsData,
        ] = await Promise.all([
          getProduct(id),
          getPriceHistory(id),
          getStockHistory(id),
          getScrapeLogs(id),
        ]);

        setProduct(
          productData
        );

        setPriceHistory(
          Array.isArray(priceData)
            ? priceData
            : []
        );

        setStockHistory(
          Array.isArray(stockData)
            ? stockData
            : []
        );

        setScrapeLogs(
          Array.isArray(logsData)
            ? logsData
            : []
        );

      } catch (error) {

        console.error(
          "Loading product details failed:",
          error
        );

        setError(
          error.message ||
          "Could not load product."
        );

      } finally {

        setLoading(false);
      }

    }, [id]);


  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      refreshProduct();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [refreshProduct]);


  return {
    product,
    priceHistory,
    stockHistory,
    scrapeLogs,
    loading,
    error,
    refreshProduct,
  };
}


export default useProduct;
