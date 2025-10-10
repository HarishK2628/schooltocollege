import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
import re
from pathlib import Path
from decimal import Decimal, InvalidOperation

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
            'free_reduced_lunch', 'student_teacher_ratio'
        ]
        
        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # Replace non-finite numeric values with NaN for downstream safety
        self.df.replace([np.inf, -np.inf], np.nan, inplace=True)
        
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
            
        query_lower = (query or '').strip().lower()
        if not query_lower:
            return []

        # Break the query into tokens to improve matching precision
        normalized_query = re.sub(r'[^a-z0-9\\s]', ' ', query_lower)
        stopwords = {'area', 'county', 'state', 'city', 'school', 'schools', 'district'}
        tokens = [
            token for token in normalized_query.split()
            if token and token not in stopwords
        ]

        if not tokens and query_lower:
            tokens = [query_lower]

        match_tokens = [token for token in tokens if len(token) > 2]
        if not match_tokens and tokens:
            match_tokens = tokens.copy()

        # Base condition: any part of the query matches key location fields
        location_columns = [
            'search_school_name',
            'search_city',
            'search_county',
            'search_metro',
            'search_state',
            'search_address'
        ]
        base_condition = pd.Series(False, index=self.df.index, dtype=bool)
        for column in location_columns:
            if column in self.df.columns:
                base_condition |= self.df[column].str.contains(query_lower, na=False)

        base_matches = base_condition.any()
        candidate_df = self.df[base_condition].copy() if base_matches else self.df.iloc[0:0].copy()

        # Token condition: ensure every meaningful token appears in precise fields
        if match_tokens:
            token_condition = pd.Series(True, index=self.df.index, dtype=bool)
            for token in match_tokens:
                token_matches = (
                    self.df['search_school_name'].str.contains(token, na=False) |
                    self.df['search_city'].str.contains(token, na=False) |
                    self.df['search_county'].str.contains(token, na=False) |
                    self.df['search_state'].str.contains(token, na=False)
                )
                token_condition &= token_matches
            filtered_df = candidate_df[token_condition.loc[candidate_df.index]].copy()

            # If no results after strict filtering, fall back to base condition
            if filtered_df.empty:
                if base_matches and not candidate_df.empty:
                    filtered_df = candidate_df.copy()
                else:
                    return []
        else:
            filtered_df = candidate_df.copy()

        if filtered_df.empty:
            return []

        # Compute relevance score with higher weight for precise matches
        filtered_df['relevance_score'] = 0.0

        token_phrase = ' '.join(match_tokens)

        if tokens:
            for token in tokens:
                filtered_df.loc[
                    filtered_df['search_school_name'].str.contains(token, na=False),
                    'relevance_score'
                ] += 70
                filtered_df.loc[
                    filtered_df['search_city'].str.contains(token, na=False),
                    'relevance_score'
                ] += 120
                filtered_df.loc[
                    filtered_df['search_county'].str.contains(token, na=False),
                    'relevance_score'
                ] += 100
                filtered_df.loc[
                    filtered_df['search_state'].str.contains(token, na=False),
                    'relevance_score'
                ] += 60

        if token_phrase:
            filtered_df.loc[
                filtered_df['search_city'] == token_phrase,
                'relevance_score'
            ] += 200
            filtered_df.loc[
                filtered_df['search_county'] == token_phrase,
                'relevance_score'
            ] += 150
            filtered_df.loc[
                filtered_df['search_school_name'] == token_phrase,
                'relevance_score'
            ] += 150

        # Metro matches still provide a small boost
        filtered_df.loc[
            filtered_df['search_metro'].str.contains(query_lower, na=False),
            'relevance_score'
        ] += 30
        filtered_df.loc[
            filtered_df['search_metro'] == query_lower,
            'relevance_score'
        ] += 50

        # Add test score contribution
        filtered_df['relevance_score'] += filtered_df['act_average'].fillna(0) * 0.1
        filtered_df['relevance_score'] += filtered_df['sat_average'].fillna(0) * 0.01

        # Sort by relevance score
        filtered_df = filtered_df.sort_values('relevance_score', ascending=False)

        # Convert to list of dictionaries
        return filtered_df.to_dict('records')
    
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

    def get_school_record(
        self,
        school_id: str,
        *,
        name: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zipcode: Optional[str] = None
    ) -> Optional[Dict]:
        """Return the best matching school record for a given ID and optional location hints."""
        if self.df is None:
            return None

        matches = self.df[self.df['niche_school_uuid'] == school_id]
        if matches.empty:
            return None

        if len(matches) == 1:
            return matches.iloc[0].to_dict()

        def normalize_text(value: Optional[str]) -> str:
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return ''
            return str(value).strip().lower()

        def normalize_zip(value: Optional[str]) -> str:
            cleaned = normalize_text(value)
            if not cleaned:
                return ''
            try:
                decimal_value = Decimal(cleaned)
                return str(int(decimal_value))
            except (InvalidOperation, ValueError):
                digits = re.sub(r'[^0-9]', '', cleaned)
                return digits[:9]

        target_name = normalize_text(name)
        target_city = normalize_text(city)
        target_state = normalize_text(state)
        target_zip = normalize_zip(zipcode)

        best_idx = matches.index[0]
        best_score = -1
        best_quality = -1

        for idx, row in matches.iterrows():
            score = 0

            row_name = normalize_text(row.get('school_name'))
            if target_name:
                if row_name == target_name:
                    score += 6
                elif target_name in row_name:
                    score += 3

            row_city = normalize_text(row.get('address_city'))
            if target_city:
                if row_city == target_city:
                    score += 4
                elif target_city in row_city:
                    score += 2

            row_state = normalize_text(row.get('address_state'))
            if target_state:
                if row_state == target_state:
                    score += 3
                elif target_state in row_state:
                    score += 1

            row_zip = normalize_zip(row.get('address_zipcode'))
            if target_zip and row_zip == target_zip:
                score += 2

            completeness = row.count()

            if score > best_score or (score == best_score and completeness > best_quality):
                best_score = score
                best_quality = completeness
                best_idx = idx

        return matches.loc[best_idx].to_dict()
    
    def format_school_data(self, school_row: Dict) -> Dict:
        """Format raw school data into API response format"""
        def safe_get(value):
            """Safely get a value, ensuring non-finite numbers are filtered out."""
            if value is None:
                return None
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned == '' or cleaned.lower() in {'nan', 'inf', '-inf'}:
                    return None
            if isinstance(value, (int, float, np.number)):
                if not np.isfinite(value):
                    return None
            if pd.isna(value):
                return None
            return value
            
        def safe_get_numeric(value, multiplier=1):
            """Safely get a numeric value, converting NaN/Inf/0 to None."""
            numeric = safe_get(value)
            if numeric is None:
                return None
            try:
                result = float(numeric) * multiplier
            except (TypeError, ValueError):
                return None
            if not np.isfinite(result) or result == 0:
                return None
            return result

        def safe_get_zipcode(value):
            cleaned = safe_get(value)
            if cleaned is None:
                return None
            if isinstance(cleaned, (int, np.integer)):
                return f"{int(cleaned):05d}"
            if isinstance(cleaned, (float, np.floating)):
                if np.isnan(cleaned):
                    return None
                return f"{int(cleaned):05d}"
            try:
                decimal_value = Decimal(str(cleaned))
                return f"{int(decimal_value):05d}"
            except (InvalidOperation, ValueError, TypeError):
                digits = re.sub(r'[^0-9]', '', str(cleaned))
                if not digits:
                    return None
                if len(digits) >= 9:
                    return f"{digits[:5]}-{digits[5:9]}"
                if len(digits) >= 5:
                    return digits[:5]
                return digits
            
        return {
            'id': school_row.get('niche_school_uuid', ''),
            'school_name': school_row.get('school_name', ''),
            'address': {
                'street': school_row.get('address_address', ''),
                'city': school_row.get('address_city', ''),
                'state': school_row.get('address_state', ''),
                'zipcode': safe_get_zipcode(school_row.get('address_zipcode'))
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
            if value is None:
                return None
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned == '' or cleaned.lower() in {'nan', 'inf', '-inf'}:
                    return None
            if isinstance(value, (int, float, np.number)):
                if not np.isfinite(value):
                    return None
            if pd.isna(value):
                return None
            return value
            
        def safe_get_string(value):
            cleaned_value = safe_get(value)
            if cleaned_value is None:
                return None
            if isinstance(cleaned_value, str):
                stripped = cleaned_value.strip()
                return stripped if stripped else None
            return str(cleaned_value)
            
        def safe_get_numeric(value, multiplier=1):
            numeric = safe_get(value)
            if numeric is None:
                return None
            try:
                result = float(numeric) * multiplier
            except (TypeError, ValueError):
                return None
            if not np.isfinite(result) or result == 0:
                return None
            return result
            
        def safe_get_bool(value):
            numeric = safe_get(value)
            if numeric is None:
                return None
            return bool(numeric) if numeric in [0, 1, 0.0, 1.0] else None

        def safe_get_zipcode(value):
            cleaned = safe_get(value)
            if cleaned is None:
                return None
            if isinstance(cleaned, (int, np.integer)):
                return f"{int(cleaned):05d}"
            if isinstance(cleaned, (float, np.floating)):
                if np.isnan(cleaned):
                    return None
                return f"{int(cleaned):05d}"
            try:
                decimal_value = Decimal(str(cleaned))
                return f"{int(decimal_value):05d}"
            except (InvalidOperation, ValueError, TypeError):
                digits = re.sub(r'[^0-9]', '', str(cleaned))
                if not digits:
                    return None
                if len(digits) >= 9:
                    return f"{digits[:5]}-{digits[5:9]}"
                if len(digits) >= 5:
                    return digits[:5]
                return digits

        def normalize_identifier(value):
            """Normalize identifier-like fields to readable strings"""
            cleaned = safe_get_string(value)
            if cleaned is None:
                return None
            try:
                decimal_value = Decimal(cleaned)
                normalized = format(decimal_value.normalize(), 'f')
                if '.' in normalized:
                    normalized = normalized.rstrip('0').rstrip('.')
                return normalized
            except (InvalidOperation, ValueError):
                return cleaned.strip()
        
        # Extract top colleges
        top_colleges = []
        seen_colleges = set()
        for i in range(1, 11):  # top_college_01 to top_college_10
            college_name = safe_get_string(school_row.get(f'top_college_{i:02d}'))
            if not college_name:
                continue
            college_uuid = normalize_identifier(school_row.get(f'top_college_uuid_{i:02d}'))
            college_ipeds = normalize_identifier(school_row.get(f'top_college_ipeds_{i:02d}'))
            dedupe_key = (college_name, college_uuid)
            if dedupe_key in seen_colleges:
                continue
            seen_colleges.add(dedupe_key)
            top_colleges.append({
                'rank': i,
                'uuid': college_uuid,
                'ipeds': college_ipeds,
                'name': college_name
            })
        
        # Extract top majors
        top_majors = []
        seen_majors = set()
        for i in range(1, 11):  # top_major_01 to top_major_10
            major_name = safe_get_string(school_row.get(f'top_major_{i:02d}'))
            if not major_name:
                continue
            major_uuid = normalize_identifier(school_row.get(f'top_major_uuid_{i:02d}'))
            major_cip = normalize_identifier(school_row.get(f'top_major_cip_code_{i:02d}'))
            dedupe_key = (major_name, major_uuid)
            if dedupe_key in seen_majors:
                continue
            top_majors.append({
                'rank': i,
                'uuid': major_uuid,
                'cip_code': major_cip,
                'name': major_name
            })
            seen_majors.add(dedupe_key)
        
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
            'address_zipcode': safe_get_zipcode(school_row.get('address_zipcode')),
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
            
            # Diversity Information
            'diversity_breakdown': self._extract_diversity_data(school_row),
            
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

