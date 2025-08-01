#!/usr/bin/env python3
"""
Comprehensive Backend Test Suite for School Finder API
Tests all endpoints with various scenarios and validates responses
"""

import requests
import json
import time
import os
from typing import Dict, List, Any

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

class SchoolFinderAPITester:
    def __init__(self):
        self.base_url = API_URL
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name: str, success: bool, message: str, response_data: Any = None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'response_data': response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        if not success:
            self.failed_tests.append(result)
            
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        print("\n=== Testing Health Endpoint ===")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("Health Check", True, f"API is healthy - {data.get('message')}")
                else:
                    self.log_test("Health Check", False, f"Unexpected health response: {data}")
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Health Check", False, f"Request failed: {str(e)}")
            
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        print("\n=== Testing Root Endpoint ===")
        
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'message' in data:
                    self.log_test("Root Endpoint", True, f"Root endpoint working: {data['message']}")
                else:
                    self.log_test("Root Endpoint", False, f"Unexpected root response: {data}")
            else:
                self.log_test("Root Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Root Endpoint", False, f"Request failed: {str(e)}")
            
    def test_schools_stats_endpoint(self):
        """Test the schools stats endpoint"""
        print("\n=== Testing Schools Stats Endpoint ===")
        
        try:
            response = requests.get(f"{self.base_url}/schools/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'data' in data:
                    stats = data['data']
                    required_fields = ['total_schools', 'states', 'cities', 'counties', 'metro_areas']
                    
                    if all(field in stats for field in required_fields):
                        self.log_test("Schools Stats", True, 
                                    f"Stats retrieved: {stats['total_schools']} schools, "
                                    f"{stats['states']} states, {stats['cities']} cities")
                    else:
                        self.log_test("Schools Stats", False, f"Missing required fields in stats: {stats}")
                else:
                    self.log_test("Schools Stats", False, f"Invalid stats response: {data}")
            else:
                self.log_test("Schools Stats", False, f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Schools Stats", False, f"Request failed: {str(e)}")
            
    def test_search_endpoint(self, query: str, expected_min_results: int = 0):
        """Test school search with a specific query"""
        try:
            payload = {"query": query}
            response = requests.post(f"{self.base_url}/schools/search", 
                                   json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if not data.get('success'):
                    self.log_test(f"Search '{query}'", False, "Response success=false")
                    return None
                    
                if 'data' not in data:
                    self.log_test(f"Search '{query}'", False, "Missing 'data' field")
                    return None
                    
                search_data = data['data']
                required_fields = ['query', 'total_schools', 'metrics', 'schools']
                
                missing_fields = [field for field in required_fields if field not in search_data]
                if missing_fields:
                    self.log_test(f"Search '{query}'", False, f"Missing fields: {missing_fields}")
                    return None
                
                # Validate metrics structure
                metrics = search_data['metrics']
                required_metrics = ['college_readiness_score', 'academic_preparation', 
                                  'college_enrollment', 'academic_performance']
                
                missing_metrics = [metric for metric in required_metrics if metric not in metrics]
                if missing_metrics:
                    self.log_test(f"Search '{query}'", False, f"Missing metrics: {missing_metrics}")
                    return None
                
                # Validate schools array
                schools = search_data['schools']
                total_schools = search_data['total_schools']
                
                if total_schools >= expected_min_results:
                    # Validate first school structure if any schools returned
                    if schools and len(schools) > 0:
                        school = schools[0]
                        required_school_fields = ['id', 'school_name', 'address', 'metrics']
                        
                        missing_school_fields = [field for field in required_school_fields 
                                               if field not in school]
                        if missing_school_fields:
                            self.log_test(f"Search '{query}'", False, 
                                        f"Missing school fields: {missing_school_fields}")
                            return None
                        
                        # Validate address structure
                        address = school['address']
                        if not isinstance(address, dict) or 'city' not in address:
                            self.log_test(f"Search '{query}'", False, "Invalid address structure")
                            return None
                    
                    self.log_test(f"Search '{query}'", True, 
                                f"Found {total_schools} schools, returned {len(schools)} results")
                    return data
                else:
                    self.log_test(f"Search '{query}'", False, 
                                f"Expected at least {expected_min_results} results, got {total_schools}")
                    return None
                    
            else:
                self.log_test(f"Search '{query}'", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_test(f"Search '{query}'", False, f"Request failed: {str(e)}")
            return None
            
    def test_school_detail_endpoint(self, school_id: str):
        """Test getting details for a specific school"""
        try:
            response = requests.get(f"{self.base_url}/schools/{school_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    school = data['data']
                    required_fields = ['id', 'school_name', 'address', 'metrics']
                    
                    missing_fields = [field for field in required_fields if field not in school]
                    if missing_fields:
                        self.log_test(f"School Detail {school_id}", False, 
                                    f"Missing fields: {missing_fields}")
                        return None
                    
                    self.log_test(f"School Detail {school_id}", True, 
                                f"Retrieved details for: {school['school_name']}")
                    return data
                else:
                    self.log_test(f"School Detail {school_id}", False, f"Invalid response: {data}")
                    return None
                    
            elif response.status_code == 404:
                self.log_test(f"School Detail {school_id}", True, "School not found (404) - expected")
                return None
            else:
                self.log_test(f"School Detail {school_id}", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_test(f"School Detail {school_id}", False, f"Request failed: {str(e)}")
            return None
            
    def test_search_scenarios(self):
        """Test various search scenarios"""
        print("\n=== Testing Search Scenarios ===")
        
        # Test state searches
        state_queries = [
            ("New York", 50),
            ("California", 100),
            ("Massachusetts", 20),
            ("Texas", 50),
            ("Florida", 30)
        ]
        
        for query, min_results in state_queries:
            self.test_search_endpoint(query, min_results)
            time.sleep(0.5)  # Rate limiting
            
        # Test city searches
        city_queries = [
            ("Boston", 5),
            ("Los Angeles", 10),
            ("Chicago", 5),
            ("New York", 10),
            ("Miami", 3)
        ]
        
        for query, min_results in city_queries:
            self.test_search_endpoint(query, min_results)
            time.sleep(0.5)
            
        # Test county searches
        county_queries = [
            ("Middlesex County", 1),
            ("Los Angeles County", 5),
            ("Cook County", 3)
        ]
        
        for query, min_results in county_queries:
            self.test_search_endpoint(query, min_results)
            time.sleep(0.5)
            
        # Test metro area searches
        metro_queries = [
            ("Boston Area", 1),
            ("New York Area", 5),
            ("Los Angeles Area", 5)
        ]
        
        for query, min_results in metro_queries:
            self.test_search_endpoint(query, min_results)
            time.sleep(0.5)
            
        # Test address searches
        address_queries = [
            ("Main Street", 0),
            ("123", 0),
            ("Avenue", 0)
        ]
        
        for query, min_results in address_queries:
            self.test_search_endpoint(query, min_results)
            time.sleep(0.5)
            
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n=== Testing Edge Cases ===")
        
        # Test empty query
        try:
            payload = {"query": ""}
            response = requests.post(f"{self.base_url}/schools/search", json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Empty Query", True, f"Empty query handled: {data['data']['total_schools']} results")
            else:
                self.log_test("Empty Query", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Empty Query", False, f"Error: {str(e)}")
            
        # Test very long query
        try:
            payload = {"query": "x" * 1000}
            response = requests.post(f"{self.base_url}/schools/search", json=payload, timeout=10)
            if response.status_code in [200, 400]:
                self.log_test("Long Query", True, "Long query handled appropriately")
            else:
                self.log_test("Long Query", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Long Query", False, f"Error: {str(e)}")
            
        # Test non-existent location
        self.test_search_endpoint("Nonexistentville", 0)
        
        # Test malformed request
        try:
            response = requests.post(f"{self.base_url}/schools/search", 
                                   json={"invalid": "field"}, timeout=10)
            if response.status_code in [400, 422]:
                self.log_test("Malformed Request", True, "Malformed request rejected appropriately")
            else:
                self.log_test("Malformed Request", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Malformed Request", False, f"Error: {str(e)}")
            
    def test_data_quality(self):
        """Test data quality in responses"""
        print("\n=== Testing Data Quality ===")
        
        # Get some search results to validate
        search_result = self.test_search_endpoint("California", 10)
        
        if search_result and search_result['data']['schools']:
            schools = search_result['data']['schools']
            
            # Test coordinate validity
            schools_with_coords = [s for s in schools if s.get('coordinates')]
            if schools_with_coords:
                coord_issues = []
                for school in schools_with_coords[:5]:  # Check first 5
                    coords = school['coordinates']
                    lat, lng = coords.get('latitude'), coords.get('longitude')
                    
                    if lat is None or lng is None:
                        coord_issues.append(f"{school['school_name']}: Missing coordinates")
                    elif not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                        coord_issues.append(f"{school['school_name']}: Invalid coordinates")
                        
                if coord_issues:
                    self.log_test("Coordinate Validation", False, f"Issues: {coord_issues}")
                else:
                    self.log_test("Coordinate Validation", True, "Coordinates are valid")
            else:
                self.log_test("Coordinate Validation", True, "No coordinates to validate")
                
            # Test metric ranges
            metric_issues = []
            for school in schools[:5]:  # Check first 5
                metrics = school.get('metrics', {})
                
                for metric_name, value in metrics.items():
                    if value is not None:
                        if metric_name in ['college_enrollment', 'college_performance', 'graduation_rate', 
                                         'math_proficiency', 'reading_proficiency']:
                            if not (0 <= value <= 100):
                                metric_issues.append(f"{school['school_name']}: {metric_name}={value} out of range")
                        elif metric_name in ['sat_average']:
                            if not (400 <= value <= 1600):
                                metric_issues.append(f"{school['school_name']}: {metric_name}={value} out of range")
                        elif metric_name in ['act_average']:
                            if not (1 <= value <= 36):
                                metric_issues.append(f"{school['school_name']}: {metric_name}={value} out of range")
                                
            if metric_issues:
                self.log_test("Metric Range Validation", False, f"Issues: {metric_issues[:3]}")  # Show first 3
            else:
                self.log_test("Metric Range Validation", True, "Metric values are in reasonable ranges")
                
            # Test school type classification
            school_types = [s.get('school_type') for s in schools[:10]]
            valid_types = ['Public', 'Charter', 'Private']
            invalid_types = [t for t in school_types if t and t not in valid_types]
            
            if invalid_types:
                self.log_test("School Type Validation", False, f"Invalid types: {set(invalid_types)}")
            else:
                self.log_test("School Type Validation", True, "School types are valid")
                
    def test_performance(self):
        """Test API performance"""
        print("\n=== Testing Performance ===")
        
        # Test search response time
        start_time = time.time()
        result = self.test_search_endpoint("California", 0)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if response_time < 2.0:
            self.log_test("Search Performance", True, f"Response time: {response_time:.2f}s")
        else:
            self.log_test("Search Performance", False, f"Slow response: {response_time:.2f}s")
            
    def test_school_detail_with_real_id(self):
        """Test school detail endpoint with a real school ID"""
        print("\n=== Testing School Detail with Real ID ===")
        
        # First get a school ID from search
        search_result = self.test_search_endpoint("Boston", 1)
        
        if search_result and search_result['data']['schools']:
            school_id = search_result['data']['schools'][0]['id']
            if school_id:
                self.test_school_detail_endpoint(school_id)
            else:
                self.log_test("School Detail Real ID", False, "No school ID found in search results")
        else:
            self.log_test("School Detail Real ID", False, "Could not get school ID from search")
            
        # Test with invalid ID
        self.test_school_detail_endpoint("invalid-uuid-12345")
        
    def run_all_tests(self):
        """Run all test suites"""
        print(f"🚀 Starting School Finder API Tests")
        print(f"📍 Testing API at: {self.base_url}")
        print("=" * 60)
        
        # Basic endpoint tests
        self.test_health_endpoint()
        self.test_root_endpoint()
        self.test_schools_stats_endpoint()
        
        # Search functionality tests
        self.test_search_scenarios()
        
        # School detail tests
        self.test_school_detail_with_real_id()
        
        # Edge case tests
        self.test_edge_cases()
        
        # Data quality tests
        self.test_data_quality()
        
        # Performance tests
        self.test_performance()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n🚨 FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  • {test['test']}: {test['message']}")
                
        print("\n" + "=" * 60)

if __name__ == "__main__":
    print("School Finder API Backend Test Suite")
    print(f"Backend URL: {BASE_URL}")
    print(f"API URL: {API_URL}")
    
    tester = SchoolFinderAPITester()
    tester.run_all_tests()