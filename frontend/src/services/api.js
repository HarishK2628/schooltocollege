import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// API functions
export const schoolAPI = {
  // Search for schools based on location query
  searchSchools: async (query) => {
    try {
      const response = await apiClient.post('/schools/search', { query });
      return response.data;
    } catch (error) {
      console.error('Error searching schools:', error);
      throw new Error(error.response?.data?.detail || 'Failed to search schools');
    }
  },

  // Get details for a specific school
  getSchoolDetails: async (schoolId, params = {}) => {
    try {
      const filteredParams = Object.fromEntries(
        Object.entries(params).filter(([_, value]) => value !== undefined && value !== null && value !== '')
      );
      const response = await apiClient.get(`/schools/${schoolId}`, { params: filteredParams });
      return response.data;
    } catch (error) {
      console.error('Error getting school details:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get school details');
    }
  },

  // Get general statistics
  getStats: async () => {
    try {
      const response = await apiClient.get('/schools/');
      return response.data;
    } catch (error) {
      console.error('Error getting stats:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get statistics');
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await apiClient.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw new Error('API health check failed');
    }
  }
};

export default apiClient;
