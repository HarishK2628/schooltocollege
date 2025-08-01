import React from 'react';
import { Search, User } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';

const Header = () => {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
              <span className="text-white font-bold text-sm">CR</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900">College Readiness</h1>
          </div>
        </div>
        
        <nav className="hidden md:flex items-center space-x-8">
          <a href="#" className="text-blue-600 font-medium border-b-2 border-blue-600 pb-2">Overview</a>
          <a href="#" className="text-gray-600 hover:text-gray-900">Schools</a>
          <a href="#" className="text-gray-600 hover:text-gray-900">Districts</a>
          <a href="#" className="text-gray-600 hover:text-gray-900">State</a>
        </nav>

        <div className="flex items-center space-x-4">
          <Search className="w-5 h-5 text-gray-500" />
          <Avatar className="w-8 h-8">
            <AvatarImage src="/api/placeholder/32/32" />
            <AvatarFallback>
              <User className="w-4 h-4" />
            </AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  );
};

export default Header;