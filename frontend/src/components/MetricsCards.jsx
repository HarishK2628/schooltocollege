import React from 'react';
import { Card, CardContent } from './ui/card';

const MetricsCards = ({ metrics, isSearched }) => {
  const formatMetricValue = (value) => {
    if (value === null || value === undefined) return '--';
    const numeric = Number(value);
    if (Number.isNaN(numeric)) return '--';
    return Math.round(numeric);
  };

  const metricsData = [
    {
      title: 'College Readiness Score',
      value: isSearched ? metrics.college_readiness_score : null,
      description: 'Overall readiness assessment'
    },
    {
      title: 'Academic Preparation', 
      value: isSearched ? metrics.academic_preparation : null,
      description: 'Curriculum rigor and quality'
    },
    {
      title: 'College Enrollment',
      value: isSearched ? metrics.college_enrollment : null,
      description: 'Post-graduation enrollment rates'
    },
    {
      title: 'Academic Performance',
      value: isSearched ? metrics.academic_performance : null,
      description: 'Test scores and achievement'
    }
  ];

  return (
    <div className="px-6 py-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {metricsData.map((metric, index) => (
            <Card key={index} className="bg-gray-50 border-gray-200">
              <CardContent className="p-6">
                <div className="text-sm font-medium text-gray-600 mb-2">
                  {metric.title}
                </div>
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {formatMetricValue(metric.value)}
                </div>
                <div className="text-xs text-gray-500">
                  {metric.description}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MetricsCards;
