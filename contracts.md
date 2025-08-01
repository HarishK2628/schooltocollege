# School Finder API Contracts & Integration Plan

## Overview
Backend will load CSV school data and provide search functionality based on address/location parameters.

## API Contracts

### 1. School Search Endpoint
**POST /api/schools/search**
```json
Request:
{
  "query": "New York, NY" // Can be address, city, county, metro area, or state
}

Response:
{
  "success": true,
  "data": {
    "query": "New York, NY",
    "total_schools": 3,
    "metrics": {
      "college_readiness_score": 78,
      "academic_preparation": 81,
      "college_enrollment": 69,
      "academic_performance": 75
    },
    "schools": [
      {
        "id": "school-uuid",
        "school_name": "Northwood High",
        "address": {
          "street": "1234 Main St",
          "city": "New York",
          "state": "NY",
          "zipcode": "10001"
        },
        "coordinates": {
          "latitude": 40.7589,
          "longitude": -73.9851
        },
        "metrics": {
          "college_readiness_score": 85,
          "college_preparation": 88,
          "college_enrollment": 82,
          "college_performance": 86,
          "graduation_rate": 95,
          "total_students": 1200,
          "sat_average": 1350,
          "act_average": 28
        },
        "demographics": {
          "free_reduced_lunch": 0.42,
          "diversity_breakdown": {...}
        }
      }
    ]
  }
}
```

### 2. School Details Endpoint
**GET /api/schools/{school_id}**
```json
Response:
{
  "success": true,
  "data": {
    // Complete school details with all CSV fields
  }
}
```

## Data Processing Plan

### CSV Data Loading
- Load CSV file into pandas DataFrame on startup
- Process and clean data fields
- Create search indexes for performance
- Handle missing/null values appropriately

### Search Implementation
Search will match query against these fields:
- `county_name` (exact and partial match)
- `metro_area_name` (exact and partial match) 
- `state_name` (exact and partial match)
- `address_address` (partial match)
- `address_city` (exact and partial match)

### Metrics Calculation
Calculate aggregate metrics from matching schools:
- `college_readiness_score`: Average of `act_average` and `sat_average` normalized
- `academic_preparation`: Average of `grade_academics`, `math_proficiency`, `reading_proficiency`
- `college_enrollment`: Average of `four_year_matriculation_rate`
- `academic_performance`: Average of `graduation_rate` and test scores

## Frontend Integration Changes

### Mock Data Replacement
Replace these mock functions:
- `mockSchools` → API call to `/api/schools/search`
- `mockMetrics` → Included in search response
- `mockTrendsData` → Calculate from historical data (if available) or generate based on metrics

### API Integration Points
1. **SearchSection.jsx**: Replace mock search with actual API call
2. **App.js**: Update `handleSearch` function to call backend
3. **Add error handling**: Loading states, error messages
4. **Add loading indicators**: Skeleton UI while searching

### New Features to Add
- Real-time search suggestions
- Advanced filters (school type, enrollment size, etc.)
- Geolocation-based search
- Export/bookmark functionality

## Backend Implementation Steps
1. Create CSV data loader and processor
2. Implement search algorithms
3. Build FastAPI endpoints
4. Add data validation and error handling
5. Optimize for performance (caching, indexing)
6. Update frontend to use real APIs

## Database Schema (Future Enhancement)
While CSV loading works for MVP, consider MongoDB schema:
```javascript
{
  school_id: ObjectId,
  niche_school_uuid: String,
  school_name: String,
  location: {
    address: String,
    city: String,
    state: String,
    zipcode: String,
    county: String,
    metro_area: String,
    coordinates: [longitude, latitude] // GeoJSON Point
  },
  metrics: {
    college_readiness: Number,
    academic_preparation: Number,
    // ... all other metrics
  },
  demographics: Object,
  rankings: Object,
  created_at: Date,
  updated_at: Date
}
```

## Performance Considerations
- Implement search result caching
- Use pandas indexing for fast lookups
- Consider pagination for large result sets
- Add request rate limiting