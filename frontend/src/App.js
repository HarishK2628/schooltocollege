import React, { useState } from "react";
import "./App.css";
import Header from "./components/Header";
import SearchSection from "./components/SearchSection";
import MetricsCards from "./components/MetricsCards";
import TrendsSection from "./components/TrendsSection";
import MapSection from "./components/MapSection";
import SchoolsSection from "./components/SchoolsSection";
import LoadingSpinner from "./components/LoadingSpinner";
import ErrorMessage from "./components/ErrorMessage";
import { schoolAPI } from "./services/api";
import { mockTrendsData } from "./mock";

function App() {
  const [searchResults, setSearchResults] = useState(null);
  const [isSearched, setIsSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentQuery, setCurrentQuery] = useState('');

  const handleSearch = async (address) => {
    setIsLoading(true);
    setError(null);
    setCurrentQuery(address);
    
    try {
      console.log('Searching for:', address);
      
      const response = await schoolAPI.searchSchools(address);
      
      if (response.success && response.data) {
        const hasSchools = (response.data.total_schools || 0) > 0;
        const fallbackMetrics = {
          college_readiness_score: null,
          academic_preparation: null,
          college_enrollment: null,
          academic_performance: null
        };

        // Transform API response to match frontend expectations
        const transformedData = {
          address: address,
          coordinates: response.data.schools.length > 0 && response.data.schools[0].coordinates 
            ? [response.data.schools[0].coordinates.latitude, response.data.schools[0].coordinates.longitude]
            : [40.7589, -73.9851], // Default to NYC
          schools: response.data.schools.map(school => ({
            id: school.id,
            school_name: school.school_name,
            address_address: school.address.street,
            address_city: school.address.city,
            address_state: school.address.state,
            address_zipcode: school.address.zipcode,
            latitude: school.coordinates?.latitude || 40.7589,
            longitude: school.coordinates?.longitude || -73.9851,
            college_readiness_score: school.metrics?.college_readiness_score || school.metrics?.act_average || 0,
            college_preparation: school.metrics?.college_preparation || 0,
            college_enrollment: school.metrics?.college_enrollment || 0,
            total_students: school.metrics?.total_students,
            grade_academics: school.grade_academics || 'N/A',
            graduation_rate: school.metrics?.graduation_rate ? school.metrics.graduation_rate / 100 : null,
            graduation_rate_percent: school.metrics?.graduation_rate ?? null,
            sat_average: school.metrics?.sat_average,
            act_average: school.metrics?.act_average,
            math_proficiency: school.metrics?.math_proficiency ? school.metrics.math_proficiency / 100 : null,
            reading_proficiency: school.metrics?.reading_proficiency ? school.metrics.reading_proficiency / 100 : null,
            is_public: school.school_type === 'Public',
            is_charter: school.school_type === 'Charter',
            is_high: true // Assuming high school for now
          })),
          metrics: hasSchools ? response.data.metrics : fallbackMetrics,
          trends: mockTrendsData // Still using mock trends data
        };
        
        setSearchResults(transformedData);
        setIsSearched(true);
        console.log('Search completed successfully:', transformedData);
      } else {
        throw new Error('Invalid response format');
      }
      
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message || 'Failed to search schools. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    if (currentQuery) {
      handleSearch(currentQuery);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      
      <SearchSection 
        onSearch={handleSearch}
        isSearched={isSearched}
        isLoading={isLoading}
      />
      
      {error && (
        <div className="px-6 py-4">
          <div className="max-w-7xl mx-auto">
            <ErrorMessage message={error} onRetry={handleRetry} />
          </div>
        </div>
      )}
      
      {isLoading ? (
        <div className="px-6 py-8">
          <div className="max-w-7xl mx-auto">
            <LoadingSpinner message="Searching for schools..." />
          </div>
        </div>
      ) : (
        <>
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
        </>
      )}
    </div>
  );
}

export default App;
