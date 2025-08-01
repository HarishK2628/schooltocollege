import React, { useState } from "react";
import "./App.css";
import Header from "./components/Header";
import SearchSection from "./components/SearchSection";
import MetricsCards from "./components/MetricsCards";
import TrendsSection from "./components/TrendsSection";
import MapSection from "./components/MapSection";
import SchoolsSection from "./components/SchoolsSection";
import { mockSearchResult } from "./mock";

function App() {
  const [searchResults, setSearchResults] = useState(null);
  const [isSearched, setIsSearched] = useState(false);

  const handleSearch = (address) => {
    // Simulate API call with mock data
    console.log('Searching for:', address);
    setSearchResults(mockSearchResult);
    setIsSearched(true);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      
      <SearchSection 
        onSearch={handleSearch}
        isSearched={isSearched}
      />
      
      <MetricsCards 
        metrics={searchResults?.metrics || {}}
        isSearched={isSearched}
      />
      
      <TrendsSection 
        trendsData={searchResults?.trends || []}
        isSearched={isSearched}
      />
      
      <MapSection 
        schools={searchResults?.schools || []}
        searchCenter={searchResults?.coordinates}
        isSearched={isSearched}
      />
      
      <SchoolsSection 
        schools={searchResults?.schools || []}
        isSearched={isSearched}
      />
    </div>
  );
}

export default App;