import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SchoolDataProcessor:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Load and preprocess the CSV data"""
        try:
            logger.info(f"Loading school data from {self.csv_path}")
            self.df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.df)} schools")
            
            # Clean and preprocess data
            self._preprocess_data()
            
        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            raise
    
    def _preprocess_data(self):
        """Clean and preprocess the data"""
        # Convert numeric columns
        numeric_columns = [
            'latitude', 'longitude', 'act_average', 'sat_average', 
            'graduation_rate', 'total_students', 'math_proficiency', 
            'reading_proficiency', 'four_year_matriculation_rate',
            'free_reduced_lunch'
        ]
        
        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Clean text columns
        text_columns = [
            'school_name', 'address_address', 'address_city', 
            'address_state', 'county_name', 'metro_area_name', 'state_name'
        ]
        
        for col in text_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).fillna('')
                
        # Create search index columns (lowercase for case-insensitive search)
        self.df['search_school_name'] = self.df['school_name'].str.lower()
        self.df['search_address'] = self.df['address_address'].str.lower()
        self.df['search_city'] = self.df['address_city'].str.lower()
        self.df['search_county'] = self.df['county_name'].str.lower()
        self.df['search_metro'] = self.df['metro_area_name'].str.lower()
        self.df['search_state'] = self.df['state_name'].str.lower()
        
    def search_schools(self, query: str) -> List[Dict]:
        """Search for schools based on query"""
        if self.df is None:
            return []
            
        query_lower = query.lower().strip()
        
        # Create search conditions
        conditions = (
            self.df['search_city'].str.contains(query_lower, na=False) |
            self.df['search_county'].str.contains(query_lower, na=False) |
            self.df['search_metro'].str.contains(query_lower, na=False) |
            self.df['search_state'].str.contains(query_lower, na=False) |
            self.df['search_address'].str.contains(query_lower, na=False)
        )
        
        # Filter results
        results = self.df[conditions].copy()
        
        # Sort by relevance (exact matches first, then by college readiness)
        results['relevance_score'] = 0
        
        # Boost exact city matches
        results.loc[results['search_city'] == query_lower, 'relevance_score'] += 100
        
        # Boost exact county matches
        results.loc[results['search_county'] == query_lower, 'relevance_score'] += 90
        
        # Boost exact state matches
        results.loc[results['search_state'] == query_lower, 'relevance_score'] += 80
        
        # Add college readiness score to relevance
        results['relevance_score'] += results['act_average'].fillna(0) * 0.1
        results['relevance_score'] += results['sat_average'].fillna(0) * 0.01
        
        # Sort by relevance score
        results = results.sort_values('relevance_score', ascending=False)
        
        # Convert to list of dictionaries
        return results.to_dict('records')
    
    def calculate_aggregate_metrics(self, schools_data: List[Dict]) -> Dict[str, float]:
        """Calculate aggregate metrics from school list"""
        if not schools_data:
            return {
                'college_readiness_score': 0,
                'academic_preparation': 0,
                'college_enrollment': 0,
                'academic_performance': 0
            }
        
        df = pd.DataFrame(schools_data)
        
        # College Readiness Score (normalized ACT/SAT averages)
        act_avg = df['act_average'].dropna()
        sat_avg = df['sat_average'].dropna()
        
        college_readiness = 0
        if not act_avg.empty:
            college_readiness = act_avg.mean()
        elif not sat_avg.empty:
            # Convert SAT to ACT scale approximately
            college_readiness = (sat_avg.mean() - 400) / 52  # Rough conversion
            
        # Academic Preparation (math + reading proficiency)
        math_prof = df['math_proficiency'].dropna()
        reading_prof = df['reading_proficiency'].dropna()
        academic_prep = ((math_prof.mean() if not math_prof.empty else 0.5) + 
                        (reading_prof.mean() if not reading_prof.empty else 0.5)) * 50
        
        # College Enrollment (matriculation rate)
        matriculation = df['four_year_matriculation_rate'].dropna()
        college_enrollment = (matriculation.mean() if not matriculation.empty else 0.6) * 100
        
        # Academic Performance (graduation rate)
        grad_rate = df['graduation_rate'].dropna()
        academic_performance = (grad_rate.mean() if not grad_rate.empty else 0.75) * 100
        
        return {
            'college_readiness_score': round(college_readiness, 0),
            'academic_preparation': round(academic_prep, 0),
            'college_enrollment': round(college_enrollment, 0),
            'academic_performance': round(academic_performance, 0)
        }
    
    def format_school_data(self, school_row: Dict) -> Dict:
        """Format raw school data into API response format"""
        return {
            'id': school_row.get('niche_school_uuid', ''),
            'school_name': school_row.get('school_name', ''),
            'address': {
                'street': school_row.get('address_address', ''),
                'city': school_row.get('address_city', ''),
                'state': school_row.get('address_state', ''),
                'zipcode': str(school_row.get('address_zipcode', '')) if school_row.get('address_zipcode') else None
            },
            'coordinates': {
                'latitude': school_row.get('latitude'),
                'longitude': school_row.get('longitude')
            } if school_row.get('latitude') and school_row.get('longitude') else None,
            'metrics': {
                'college_readiness_score': school_row.get('act_average'),
                'college_preparation': self._calculate_college_prep_score(school_row),
                'college_enrollment': school_row.get('four_year_matriculation_rate', 0) * 100 if school_row.get('four_year_matriculation_rate') else None,
                'college_performance': school_row.get('graduation_rate', 0) * 100 if school_row.get('graduation_rate') else None,
                'graduation_rate': school_row.get('graduation_rate', 0) * 100 if school_row.get('graduation_rate') else None,
                'total_students': int(school_row.get('total_students', 0)) if school_row.get('total_students') else None,
                'sat_average': school_row.get('sat_average'),
                'act_average': school_row.get('act_average'),
                'math_proficiency': school_row.get('math_proficiency', 0) * 100 if school_row.get('math_proficiency') else None,
                'reading_proficiency': school_row.get('reading_proficiency', 0) * 100 if school_row.get('reading_proficiency') else None
            },
            'demographics': {
                'free_reduced_lunch': school_row.get('free_reduced_lunch'),
                'diversity_breakdown': self._extract_diversity_data(school_row)
            },
            'school_type': self._determine_school_type(school_row),
            'grades_offered': school_row.get('grades_offered', '')
        }
    
    def _calculate_college_prep_score(self, school_row: Dict) -> Optional[float]:
        """Calculate college preparation score from available metrics"""
        scores = []
        
        if school_row.get('math_proficiency'):
            scores.append(school_row['math_proficiency'] * 100)
        if school_row.get('reading_proficiency'):
            scores.append(school_row['reading_proficiency'] * 100)
        if school_row.get('grade_academics'):
            # Convert letter grade to numeric
            grade_map = {'A+': 100, 'A': 95, 'A-': 90, 'B+': 85, 'B': 80, 'B-': 75, 'C+': 70, 'C': 65}
            scores.append(grade_map.get(school_row['grade_academics'], 70))
            
        return sum(scores) / len(scores) if scores else None
    
    def _extract_diversity_data(self, school_row: Dict) -> Dict[str, float]:
        """Extract diversity breakdown from school data"""
        diversity = {}
        diversity_fields = [
            'diversity_breakdown_african_american',
            'diversity_breakdown_asian', 
            'diversity_breakdown_hispanic',
            'diversity_breakdown_white',
            'diversity_breakdown_multiracial',
            'diversity_breakdown_native_american'
        ]
        
        for field in diversity_fields:
            if school_row.get(field):
                key = field.replace('diversity_breakdown_', '')
                diversity[key] = school_row[field]
                
        return diversity
    
    def _determine_school_type(self, school_row: Dict) -> str:
        """Determine school type from boolean flags"""
        if school_row.get('is_public', 0):
            return 'Public'
        elif school_row.get('is_charter', 0):
            return 'Charter'
        else:
            return 'Private'