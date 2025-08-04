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
            college_readiness = max(0, act_avg.mean())
        elif not sat_avg.empty:
            # Convert SAT to ACT scale approximately
            college_readiness = max(0, (sat_avg.mean() - 400) / 52)  # Rough conversion
            
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
            'college_readiness_score': max(0, round(college_readiness, 0)),
            'academic_preparation': max(0, round(academic_prep, 0)),
            'college_enrollment': max(0, round(college_enrollment, 0)),
            'academic_performance': max(0, round(academic_performance, 0))
        }
    
    def format_school_data(self, school_row: Dict) -> Dict:
        """Format raw school data into API response format"""
        def safe_get(value):
            """Safely get a value, converting NaN to None"""
            if pd.isna(value):
                return None
            return value
            
        def safe_get_numeric(value, multiplier=1):
            """Safely get a numeric value, converting NaN to None"""
            if pd.isna(value) or value == 0:
                return None
            return value * multiplier
            
        return {
            'id': school_row.get('niche_school_uuid', ''),
            'school_name': school_row.get('school_name', ''),
            'address': {
                'street': school_row.get('address_address', ''),
                'city': school_row.get('address_city', ''),
                'state': school_row.get('address_state', ''),
                'zipcode': str(school_row.get('address_zipcode', '')) if school_row.get('address_zipcode') and not pd.isna(school_row.get('address_zipcode')) else None
            },
            'coordinates': {
                'latitude': safe_get(school_row.get('latitude')),
                'longitude': safe_get(school_row.get('longitude'))
            } if safe_get(school_row.get('latitude')) and safe_get(school_row.get('longitude')) else None,
            'metrics': {
                'college_readiness_score': safe_get(school_row.get('act_average')),
                'college_preparation': self._calculate_college_prep_score(school_row),
                'college_enrollment': safe_get_numeric(school_row.get('four_year_matriculation_rate'), 100),
                'college_performance': safe_get_numeric(school_row.get('graduation_rate'), 100),
                'graduation_rate': safe_get_numeric(school_row.get('graduation_rate'), 100),
                'total_students': int(school_row.get('total_students', 0)) if pd.notna(school_row.get('total_students')) and school_row.get('total_students') != 0 else None,
                'sat_average': safe_get(school_row.get('sat_average')),
                'act_average': safe_get(school_row.get('act_average')),
                'math_proficiency': safe_get_numeric(school_row.get('math_proficiency'), 100),
                'reading_proficiency': safe_get_numeric(school_row.get('reading_proficiency'), 100)
            },
            'demographics': {
                'free_reduced_lunch': safe_get(school_row.get('free_reduced_lunch')),
                'diversity_breakdown': self._extract_diversity_data(school_row)
            },
            'school_type': self._determine_school_type(school_row),
            'grades_offered': school_row.get('grades_offered', '')
        }
    
    def format_complete_school_profile(self, school_row: Dict) -> Dict:
        """Format complete school profile with all requested fields"""
        def safe_get(value):
            if pd.isna(value):
                return None
            return value
            
        def safe_get_string(value):
            if pd.isna(value) or value == '' or value == 'nan':
                return None
            return str(value)
            
        def safe_get_numeric(value, multiplier=1):
            if pd.isna(value) or value == 0:
                return None
            return value * multiplier
            
        def safe_get_bool(value):
            if pd.isna(value):
                return None
            return bool(value) if value in [0, 1, 0.0, 1.0] else None
        
        # Extract top colleges
        top_colleges = []
        for i in range(1, 11):  # top_college_01 to top_college_10
            college_name = safe_get_string(school_row.get(f'top_college_{i:02d}'))
            if college_name:
                top_colleges.append({
                    'uuid': safe_get_string(school_row.get(f'top_college_uuid_{i:02d}')),
                    'ipeds': safe_get_string(school_row.get(f'top_college_ipeds_{i:02d}')),
                    'name': college_name
                })
        
        # Extract top majors
        top_majors = []
        for i in range(1, 11):  # top_major_01 to top_major_10
            major_name = safe_get_string(school_row.get(f'top_major_{i:02d}'))
            if major_name:
                top_majors.append({
                    'uuid': safe_get_string(school_row.get(f'top_major_uuid_{i:02d}')),
                    'cip_code': safe_get_string(school_row.get(f'top_major_cip_code_{i:02d}')),
                    'name': major_name
                })
        
        return {
            # Basic Information
            'niche_school_uuid': safe_get_string(school_row.get('niche_school_uuid')),
            'school_name': safe_get_string(school_row.get('school_name')),
            'nces_id': safe_get_string(school_row.get('nces_id')),
            'niche_sd_uuid': safe_get_string(school_row.get('niche_sd_uuid')),
            'lea_id': safe_get(school_row.get('lea_id')),
            'sd_name': safe_get_string(school_row.get('sd_name')),
            
            # Location
            'county_name': safe_get_string(school_row.get('county_name')),
            'metro_area_name': safe_get_string(school_row.get('metro_area_name')),
            'state_name': safe_get_string(school_row.get('state_name')),
            'address_address': safe_get_string(school_row.get('address_address')),
            'address_city': safe_get_string(school_row.get('address_city')),
            'address_state': safe_get_string(school_row.get('address_state')),
            'address_zipcode': safe_get_string(school_row.get('address_zipcode')),
            'latitude': safe_get(school_row.get('latitude')),
            'longitude': safe_get(school_row.get('longitude')),
            
            # Contact Information
            'phone_number': safe_get_string(school_row.get('phone_number')),
            'website': safe_get_string(school_row.get('website')),
            
            # Academic Performance
            'four_year_matriculation_rate': safe_get_numeric(school_row.get('four_year_matriculation_rate'), 100),
            'graduation_rate': safe_get_numeric(school_row.get('graduation_rate'), 100),
            'grade_overall': safe_get_string(school_row.get('grade_overall')),
            'student_teacher_ratio': safe_get(school_row.get('student_teacher_ratio')),
            
            # Demographics
            'gender_breakdown_female': safe_get(school_row.get('gender_breakdown_female')),
            'gender_breakdown_male': safe_get(school_row.get('gender_breakdown_male')),
            'total_students': safe_get(school_row.get('total_students')),
            
            # School Characteristics
            'grades_offered': safe_get_string(school_row.get('grades_offered')),
            'is_boarding': safe_get_bool(school_row.get('is_boarding')),
            'is_charter': safe_get_bool(school_row.get('is_charter')),
            'is_pk': safe_get_bool(school_row.get('is_pk')),
            'is_elementary': safe_get_bool(school_row.get('is_elementary')),
            'is_middle': safe_get_bool(school_row.get('is_middle')),
            'is_high': safe_get_bool(school_row.get('is_high')),
            'is_public': safe_get_bool(school_row.get('is_public')),
            'religion_general': safe_get_string(school_row.get('religion_general')),
            
            # Financial Information
            'tuition': safe_get(school_row.get('tuition')),
            'pk_tuit': safe_get(school_row.get('pk_tuit')),
            
            # College and Career Readiness
            'top_colleges': top_colleges,
            'top_majors': top_majors
        }
    
    def _calculate_college_prep_score(self, school_row: Dict) -> Optional[float]:
        """Calculate college preparation score from available metrics"""
        scores = []
        
        math_prof = school_row.get('math_proficiency')
        if math_prof and not pd.isna(math_prof):
            scores.append(math_prof * 100)
            
        reading_prof = school_row.get('reading_proficiency')
        if reading_prof and not pd.isna(reading_prof):
            scores.append(reading_prof * 100)
            
        grade_academics = school_row.get('grade_academics')
        if grade_academics and not pd.isna(grade_academics):
            # Convert letter grade to numeric
            grade_map = {'A+': 100, 'A': 95, 'A-': 90, 'B+': 85, 'B': 80, 'B-': 75, 'C+': 70, 'C': 65}
            scores.append(grade_map.get(grade_academics, 70))
            
        return sum(scores) / len(scores) if scores else None
    
    def _extract_diversity_data(self, school_row: Dict) -> Dict[str, float]:
        """Extract diversity breakdown from school data"""
        diversity = {}
        diversity_fields = {
            'diversity_breakdown_african_american': 'African American',
            'diversity_breakdown_asian': 'Asian', 
            'diversity_breakdown_hispanic': 'Hispanic/Latino',
            'diversity_breakdown_white': 'White',
            'diversity_breakdown_multiracial': 'Multiracial',
            'diversity_breakdown_native_american': 'Native American',
            'diversity_breakdown_pacific_islander': 'Pacific Islander',
            'diversity_breakdown_international': 'International',
            'diversity_breakdown_unknown': 'Unknown'
        }
        
        for field, label in diversity_fields.items():
            value = school_row.get(field)
            if value and not pd.isna(value):
                diversity[label] = float(value)
                
        return diversity
    
    def _determine_school_type(self, school_row: Dict) -> str:
        """Determine school type from boolean flags"""
        if school_row.get('is_public', 0):
            return 'Public'
        elif school_row.get('is_charter', 0):
            return 'Charter'
        else:
            return 'Private'