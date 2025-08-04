import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const DiversityChart = ({ diversityData }) => {
  // Define colors for each demographic group
  const COLORS = {
    'African American': '#8884d8',
    'Asian': '#82ca9d', 
    'Hispanic/Latino': '#ffc658',
    'White': '#ff7c7c',
    'Multiracial': '#8dd1e1',
    'Native American': '#d084d0',
    'Pacific Islander': '#ffb347',
    'International': '#87ceeb',
    'Unknown': '#ddd'
  };

  // Convert diversity data to chart format and calculate percentages
  const chartData = Object.entries(diversityData || {})
    .filter(([key, value]) => value && value > 0)
    .map(([name, value]) => ({
      name,
      value: parseFloat(value),
      percentage: (parseFloat(value) * 100).toFixed(1)
    }))
    .sort((a, b) => b.value - a.value); // Sort by value descending

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{data.payload.name}</p>
          <p className="text-sm text-gray-600">
            {data.payload.percentage}% of students
          </p>
        </div>
      );
    }
    return null;
  };

  // Custom legend
  const CustomLegend = ({ payload }) => {
    return (
      <div className="flex flex-wrap justify-center gap-2 mt-4">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center text-sm">
            <div 
              className="w-3 h-3 rounded-full mr-2"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-gray-700">
              {entry.value} ({chartData.find(d => d.name === entry.value)?.percentage}%)
            </span>
          </div>
        ))}
      </div>
    );
  };

  if (!chartData || chartData.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-600 mb-2">No Diversity Data Available</h3>
        <p className="text-gray-500">Student demographic information is not available for this school.</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              outerRadius={100}
              innerRadius={40}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[entry.name] || '#cccccc'} 
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      
      {/* Summary statistics */}
      <div className="mt-6 bg-gray-50 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-3">Diversity Summary</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Total Groups:</span>
            <span className="ml-2 font-medium">{chartData.length}</span>
          </div>
          <div>
            <span className="text-gray-600">Largest Group:</span>
            <span className="ml-2 font-medium">
              {chartData[0]?.name} ({chartData[0]?.percentage}%)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiversityChart;