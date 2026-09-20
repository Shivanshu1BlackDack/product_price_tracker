import {
  useCallback,
  useState,
} from "react";

import {
  searchProducts as searchCatalogProducts,
} from "../services/api";


function useSearchProducts() {
  const [results, setResults] =
    useState([]);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const searchProducts =
    useCallback(async (query) => {
      const searchText =
        query?.trim();

      if (!searchText) {
        setResults([]);
        setError("");
        return;
      }

      try {
        setLoading(true);
        setError("");

        const data =
          await searchCatalogProducts(searchText);

        setResults(
          Array.isArray(data)
            ? data
            : [],
        );
      } catch (error) {
        console.error(
          "Catalog search failed:",
          error,
        );

        setResults([]);

        setError(
          error.message ||
          "Could not search the INE catalog.",
        );
      } finally {
        setLoading(false);
      }
    }, []);

  const clearResults =
    useCallback(() => {
      setResults([]);
      setError("");
    }, []);

  return {
    results,
    loading,
    error,
    searchProducts,
    clearResults,
  };
}

export default useSearchProducts;
