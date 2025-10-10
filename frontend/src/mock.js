// Mock data for school search app
export const mockSchools = [
  {
    id: 1,
    school_name: "Northwood High",
    address_address: "1234 Main St",
    address_city: "New York",
    address_state: "NY",
    address_zipcode: "10001",
    latitude: 40.7589,
    longitude: -73.9851,
    college_readiness_score: 85,
    college_preparation: 88,
    college_enrollment: 82,
    graduation_rate_percent: 86,
    total_students: 1200,
    grade_academics: "A",
    graduation_rate: 0.95,
    sat_average: 1350,
    act_average: 28,
    math_proficiency: 0.78,
    reading_proficiency: 0.82,
    is_public: true,
    is_charter: false,
    is_high: true
  },
  {
    id: 2,
    school_name: "Southwood High",
    address_address: "5678 Oak Ave",
    address_city: "New York",
    address_state: "NY", 
    address_zipcode: "10002",
    latitude: 40.7505,
    longitude: -73.9934,
    college_readiness_score: 78,
    college_preparation: 80,
    college_enrollment: 75,
    graduation_rate_percent: 77,
    total_students: 980,
    grade_academics: "B+",
    graduation_rate: 0.89,
    sat_average: 1280,
    act_average: 25,
    math_proficiency: 0.72,
    reading_proficiency: 0.75,
    is_public: true,
    is_charter: false,
    is_high: true
  },
  {
    id: 3,
    school_name: "Eastwood High",
    address_address: "9101 Pine St",
    address_city: "New York", 
    address_state: "NY",
    address_zipcode: "10003",
    latitude: 40.7282,
    longitude: -73.9942,
    college_readiness_score: 72,
    college_preparation: 76,
    college_enrollment: 70,
    graduation_rate_percent: 71,
    total_students: 850,
    grade_academics: "B",
    graduation_rate: 0.85,
    sat_average: 1220,
    act_average: 23,
    math_proficiency: 0.68,
    reading_proficiency: 0.71,
    is_public: true,
    is_charter: false,
    is_high: true
  }
];

export const mockMetrics = {
  college_readiness_score: 78,
  academic_preparation: 85,
  college_enrollment: 62,
  academic_performance: 71
};

export const mockTrendsData = [
  { month: "Jan", score: 76 },
  { month: "Feb", score: 78 },
  { month: "Mar", score: 75 },
  { month: "Apr", score: 77 },
  { month: "May", score: 74 },
  { month: "Jun", score: 79 },
  { month: "Jul", score: 78 }
];

export const mockSearchResult = {
  address: "123 Main Street, New York, NY",
  coordinates: [40.7589, -73.9851],
  schools: mockSchools,
  metrics: mockMetrics,
  trends: mockTrendsData
};
