import { useState } from "react";


function SearchBar({
  onSearch,
  loading = false,
}) {
  const [query, setQuery] = useState("");


  const handleSubmit = (event) => {
    event.preventDefault();

    const searchText = query.trim();

    if (!searchText || loading) {
      return;
    }

    onSearch(searchText);
  };


  return (
    <form
      className="search-bar"
      onSubmit={handleSubmit}
    >
      <input
        type="text"
        className="search-input"
        value={query}
        onChange={(event) =>
          setQuery(event.target.value)
        }
        placeholder="Search product by name..."
        disabled={loading}
      />

      <button
        type="submit"
        className="search-button"
        disabled={
          loading ||
          !query.trim()
        }
      >
        {loading ? "Searching..." : "Search"}
      </button>
    </form>
  );
}


export default SearchBar;