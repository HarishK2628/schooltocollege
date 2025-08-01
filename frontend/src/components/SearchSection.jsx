import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';

const SearchSection = ({ onSearch, isSearched }) => {
  const [address, setAddress] = useState('');

  const handleSearch = () => {
    if (address.trim()) {
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
              placeholder="Enter an address..."
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full pl-4 pr-10 py-3 text-lg border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          </div>
          <Button 
            onClick={handleSearch}
            className="px-8 py-3 text-lg bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
          >
            Find Schools
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SearchSection;