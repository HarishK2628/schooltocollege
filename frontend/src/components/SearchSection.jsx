import React, { useState } from 'react';
import { Search, MapPin } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';

const SearchSection = ({ onSearch, isSearched, isLoading }) => {
  const [address, setAddress] = useState('');

  const handleSearch = () => {
    if (address.trim() && !isLoading) {
      onSearch(address);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="bg-white px-6 py-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {isSearched ? 'College Readiness' : 'Overview'}
        </h1>
        <p className="text-gray-600 mb-8">
          Find college readiness data for schools near you.
        </p>
        
        <div className="flex max-w-2xl space-x-4">
          <div className="flex-1 relative">
            <Input
              type="text"
              placeholder="Enter address, city, county, or state..."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="w-full pl-4 pr-10 py-3 text-lg border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              ) : (
                <Search className="w-5 h-5 text-gray-400" />
              )}
            </div>
          </div>
          <Button 
            onClick={handleSearch}
            disabled={isLoading || !address.trim()}
            className="px-8 py-3 text-lg bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Searching...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <MapPin className="w-4 h-4" />
                <span>Find Schools</span>
              </div>
            )}
          </Button>
        </div>
        
        {isSearched && (
          <div className="mt-4 text-sm text-gray-500">
            <MapPin className="inline w-4 h-4 mr-1" />
            Showing schools for: <span className="font-medium">{address}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchSection;