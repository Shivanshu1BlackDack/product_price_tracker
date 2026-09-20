import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getCatalog,
} from "../services/api";


function useCatalog() {
  const [catalog, setCatalog] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  const refreshCatalog =
    useCallback(
      async () => {

        try {

          setLoading(true);
          setError("");

          const data =
            await getCatalog();

          setCatalog(
            Array.isArray(data)
              ? data
              : []
          );

        } catch (error) {

          console.error(
            "Catalog loading failed:",
            error
          );

          setError(
            error.message ||
            "Could not load catalog."
          );

        } finally {

          setLoading(false);
        }
      },
      []
    );


  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      refreshCatalog();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [refreshCatalog]);


  return {
    catalog,
    loading,
    error,
    refreshCatalog,
  };
}


export default useCatalog;
