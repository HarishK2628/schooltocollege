import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { TrendingUp } from 'lucide-react';

const TrendsSection = ({ trendsData, isSearched }) => {
  if (!isSearched) {
    return (
      <div className="px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <Card className="bg-gray-50 border-gray-200">
            <CardHeader>
              <CardTitle className="text-xl font-bold text-gray-900">Trends</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="text-center py-12">
                <TrendingUp className="mx-auto w-12 h-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-medium text-gray-600 mb-2">No trends available</h3>
                <p className="text-gray-500">Trend data will appear here once you find schools.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="px-6 py-6">
      <div className="max-w-7xl mx-auto">
        <Card className="bg-white border-gray-200">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-gray-900">Trends</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="mb-4">
              <div className="text-sm font-medium text-gray-600 mb-1">College Readiness Score</div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-green-600">+2%</span>
                <span className="text-sm text-gray-500">Last 12 Months +2%</span>
              </div>
            </div>
            
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center relative overflow-hidden">
              <svg width="100%" height="200" className="absolute inset-0">
                <defs>
                  <linearGradient id="trendGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.1" />
                  </linearGradient>
                </defs>
                
                {/* Trend line */}
                <polyline
                  fill="none"
                  stroke="#3B82F6"
                  strokeWidth="3"
                  points="50,150 120,130 190,140 260,125 330,145 400,115 470,120"
                />
                
                {/* Area under line */}
                <polygon
                  fill="url(#trendGradient)"
                  points="50,150 120,130 190,140 260,125 330,145 400,115 470,120 470,180 50,180"
                />
              </svg>
              
              {/* Month labels */}
              <div className="absolute bottom-4 left-0 right-0 flex justify-between px-4 text-xs text-gray-500">
                {trendsData.map((item, index) => (
                  <span key={index}>{item.month}</span>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TrendsSection;