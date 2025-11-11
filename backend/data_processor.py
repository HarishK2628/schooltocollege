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
        self.df: Optional[pd.DataFrame] = None
        self.load_data()

    def _compute_college_readiness_score(self, school_row: Dict) -> Optional[float]:
        """
        Compute an ACT-like College Readiness score per school.
        Preference order:
        1) act_average
        2) SAT-based proxy using (SAT_total - 400) / 52 on 400–1600 SAT
        3) grade_academics letter mapped to ACT-like scale
        Returns a rounded score (1–36) or None if not computable.
        """
        try:
            # 1) ACT direct
            act = school_row.get('act_average')
            if act is not None and pd.notna(act):
                try:
                    val = float(act)
                    if np.isfinite(val) and val > 0:
                        return float(round(val))
                except (TypeError, ValueError):
                    pass

            # 2) SAT proxy
            sat = school_row.get('sat_average')
            sat_total = None
            try:
                if sat is not None and pd.notna(sat):
                    sat_total = float(sat)
                else:
                    sm = school_row.get('sat_math_average')
                    sv = school_row.get('sat_verbal_average')
                    if sm is not None and sv is not None and pd.notna(sm) and pd.notna(sv):
                        sat_total = float(sm) + float(sv)
            except (TypeError, ValueError):
                sat_total = None

            if sat_total is not None and np.isfinite(sat_total):
                # Clamp SAT into 400–1600 and convert
                sat_total = max(400.0, min(1600.0, sat_total))
                act_proxy = (sat_total - 400.0) / 52.0
                act_proxy = max(1.0, min(36.0, act_proxy))
                return float(round(act_proxy))

            # 3) Letter grade mapping
            letter = school_row.get('grade_academics')
            if isinstance(letter, str) and letter.strip():
                grade_map = {
                    'A+': 36, 'A': 34, 'A-': 32,
                    'B+': 29, 'B': 27, 'B-': 25,
                    'C+': 22, 'C': 20, 'C-': 18,
                    'D+': 16, 'D': 15, 'D-': 14
                }
                val = grade_map.get(letter.strip().upper())
                if val is not None:
                    return float(val)
        except Exception:
            pass
        return None

    def load_data(self):
        """Load and preprocess the CSV data"""
        try:
            logger.info(f"Loading school data from {self.csv_path}")
            self.df = pd.read_csv(self.csv_path)
            logger.info(f"Loaded {len(self.df)} schools")

            self._preprocess_data()

        except Exception as e:
            logger.error(f"Error loading CSV data: {e}")
            raise

    def _preprocess_data(self):
        """Clean and preprocess the data"""

        # Fix accidental space in column name
        try:
            if 'college_ enrollment' in self.df.columns:
                self.df.rename(columns={'college_ enrollment': 'college_enrollment'}, inplace=True)
                logger.info("Renamed 'college_ enrollment' to 'college_enrollment'")
        except Exception as e:
            logger.warning(f"Could not rename college enrollment column: {e}")

        # Normalize alternate CSV schemas
        try:
            cols = set(self.df.columns)
            if {'NAME', 'ADDRESS', 'CITY', 'STATE', 'ZIP'}.issubset(cols) and 'school_name' not in cols:
                rename_map = {
                    'NAME': 'school_name',
                    'ADDRESS': 'address_address',
                    'CITY': 'address_city',
                    'STATE': 'address_state',
                    'ZIP': 'address_zipcode',
                    'COUNTY': 'county_name',
                }
                self.df.rename(columns={k: v for k, v in rename_map.items() if k in self.df.columns}, inplace=True)

                if 'state_name' not in self.df.columns:
                    self.df['state_name'] = self.df.get('address_state')
                if 'metro_area_name' not in self.df.columns:
                    self.df['metro_area_name'] = ''
                for col in [
                    'act_average', 'graduation_rate', 'total_students',
                    'math_proficiency', 'reading_proficiency',
                    'college_enrollment', 'free_reduced_lunch',
                    'latitude', 'longitude', 'sat_average',
                    'sat_math_average', 'sat_verbal_average'
                ]:
                    if col not in self.df.columns:
                        self.df[col] = pd.NA
        except Exception as e:
            logger.warning(f"Schema normalization skipped due to error: {e}")

        # Numeric columns (clean "70%" -> 70.0, etc.)
        numeric_columns = [
            'latitude', 'longitude', 'act_average', 'sat_average',
            'graduation_rate', 'total_students', 'math_proficiency',
            'reading_proficiency', 'college_enrollment', 'free_reduced_lunch',
            'student_teacher_ratio', 'sat_math_average', 'sat_verbal_average',
            'diversity_breakdown_african_american',
            'diversity_breakdown_asian',
            'diversity_breakdown_hispanic',
            'diversity_breakdown_international',
            'diversity_breakdown_multiracial',
            'diversity_breakdown_native_american',
            'diversity_breakdown_pacific_islander',
            'diversity_breakdown_unknown',
            'diversity_breakdown_white'
        ]

        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(
                    self.df[col].astype(str).str.replace(r'[^0-9.\-]', '', regex=True),
                    errors='coerce'
                )

        # Replace non-finite numeric values with NaN
        self.df.replace([np.inf, -np.inf], np.nan, inplace=True)

        # Clean text columns
        text_columns = [
            'school_name', 'address_address', 'address_city',
            'address_state', 'county_name', 'metro_area_name', 'state_name'
        ]
        for col in text_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).replace({'nan': ''}).fillna('')

        # Search index columns (lowercase)
        self.df['search_school_name'] = self.df.get('school_name', '').astype(str).str.lower()
        self.df['search_address'] = self.df.get('address_address', '').astype(str).str.lower()
        self.df['search_city'] = self.df.get('address_city', '').astype(str).str.lower()
        self.df['search_county'] = self.df.get('county_name', '').astype(str).str.lower()
        self.df['search_metro'] = self.df.get('metro_area_name', '').astype(str).str.lower()
        self.df['search_state'] = self.df.get('state_name', '').astype(str).str.lower()

        # Normalized fields for exact address matching
        def _normalize_series(s: pd.Series) -> pd.Series:
            return (
                s.astype(str)
                 .str.lower()
                 .str.replace(r"[^a-z0-9]", "", regex=True)
                 .fillna("")
            )

        try:
            self.df['normalized_address'] = _normalize_series(self.df.get('address_address', pd.Series(index=self.df.index, dtype=object)))
            self.df['normalized_city'] = _normalize_series(self.df.get('address_city', pd.Series(index=self.df.index, dtype=object)))
            self.df['normalized_state'] = _normalize_series(self.df.get('address_state', pd.Series(index=self.df.index, dtype=object)))
            self.df['normalized_zip'] = _normalize_series(self.df.get('address_zipcode', pd.Series(index=self.df.index, dtype=object)))
            self.df['normalized_full_address'] = (
                self.df['normalized_address'] +
                self.df['normalized_city'] +
                self.df['normalized_state'] +
                self.df['normalized_zip']
            )
        except Exception as e:
            logger.warning(f"Failed to build normalized address fields: {e}")

        # Create stable school IDs
        try:
            logger.info("Creating stable school IDs...")

            def create_id(row):
                name = str(row.get('school_name', '')).strip().upper()
                name_slug = re.sub(r'[^A-Z0-9]+', '-', name)

                city = str(row.get('address_city', '')).strip().upper()
                city_slug = re.sub(r'[^A-Z0-9]+', '-', city)

                state = str(row.get('address_state', '')).strip().upper()

                id_parts = [part for part in [name_slug, city_slug, state] if part]

                if not name_slug:
                    # Fallback: deterministic hash-like string
                    raw = (str(row.get('address_address', '')) + '|' +
                           str(row.get('address_city', '')) + '|' +
                           str(row.get('address_state', '')) + '|' +
                           str(row.get('address_zipcode', '')))
                    return f"NO-NAME-{abs(hash(raw))}"

                return "-".join(id_parts)

            self.df['stable_school_id'] = self.df.apply(create_id, axis=1)
            self.df.dropna(subset=['stable_school_id'], inplace=True)
            logger.info(f"Created {self.df['stable_school_id'].nunique()} unique stable IDs.")
        except Exception as e:
            logger.error(f"Error creating stable school IDs: {e}")
            raise

    def search_schools(self, query: str) -> List[Dict]:
        """Search for schools based on query"""
        if self.df is None:
            return []

        query_lower = (query or '').strip().lower()
        if not query_lower:
            return []

        normalized_query = re.sub(r'[^a-z0-9\s]', ' ', query_lower)
        stopwords = {'area', 'county', 'state', 'city', 'school', 'schools', 'district'}
        tokens = [t for t in normalized_query.split() if t and t not in stopwords]

        if not tokens and query_lower:
            tokens = [query_lower]

        match_tokens = [t for t in tokens if len(t) > 2] or tokens.copy()

        def _norm(s: str) -> str:
            return re.sub(r'[^a-z0-9]', '', (s or '').lower())

        # Address-first heuristic
        is_address_query = any(ch.isdigit() for ch in query_lower)
        if is_address_query:
            try:
                norm_query = _norm(query_lower)
                if norm_query:
                    addr_col = 'address_address' if 'address_address' in self.df.columns else ('ADDRESS' if 'ADDRESS' in self.df.columns else None)
                    city_col = 'address_city' if 'address_city' in self.df.columns else ('CITY' if 'CITY' in self.df.columns else None)
                    state_col = 'address_state' if 'address_state' in self.df.columns else ('STATE' if 'STATE' in self.df.columns else None)
                    zip_col = 'address_zipcode' if 'address_zipcode' in self.df.columns else ('ZIP' if 'ZIP' in self.df.columns else None)

                    if addr_col and city_col and state_col:
                        addr_series = self.df[addr_col].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
                        parts = [addr_series,
                                 self.df[city_col].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True),
                                 self.df[state_col].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True)]
                        if zip_col:
                            parts.append(self.df[zip_col].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True))
                        full_series = parts[0]
                        for p in parts[1:]:
                            full_series = full_series + p

                        exact_addr = addr_series == norm_query
                        exact_full = full_series == norm_query

                        if exact_addr.any() or exact_full.any():
                            addr_matches = self.df[exact_addr | exact_full].copy()
                            return [self.format_school_data(row) for _, row in addr_matches.iterrows()]
            except Exception:
                pass

        # Phrase or token matches across location fields
        location_columns = [
            'search_school_name', 'search_city', 'search_county',
            'search_metro', 'search_state', 'search_address'
        ]
        base_condition = pd.Series(False, index=self.df.index, dtype=bool)
        for column in location_columns:
            if column in self.df.columns:
                base_condition |= self.df[column].str.contains(query_lower, na=False, regex=False)

        if match_tokens:
            token_any = pd.Series(False, index=self.df.index, dtype=bool)
            for token in match_tokens:
                for column in location_columns:
                    if column in self.df.columns:
                        token_any |= self.df[column].str.contains(token, na=False, regex=False)
            base_condition |= token_any

        base_matches = bool(base_condition.any())
        candidate_df = self.df[base_condition].copy() if base_matches else self.df.iloc[0:0].copy()

        if match_tokens:
            token_condition = pd.Series(True, index=self.df.index, dtype=bool)
            for token in match_tokens:
                token_matches = (
                    self.df['search_school_name'].str.contains(token, na=False, regex=False) |
                    self.df['search_city'].str.contains(token, na=False, regex=False) |
                    self.df['search_county'].str.contains(token, na=False, regex=False) |
                    self.df['search_state'].str.contains(token, na=False, regex=False)
                )
                token_condition &= token_matches
            filtered_df = candidate_df[token_condition.loc[candidate_df.index]].copy()
            if filtered_df.empty:
                if base_matches and not candidate_df.empty:
                    filtered_df = candidate_df.copy()
                else:
                    return []
        else:
            filtered_df = candidate_df.copy()

        if filtered_df.empty:
            return []

        # Relevance score
        filtered_df['relevance_score'] = 0.0
        token_phrase = ' '.join(match_tokens)

        if tokens:
            for token in tokens:
                filtered_df.loc[filtered_df['search_school_name'].str.contains(token, na=False), 'relevance_score'] += 70
                filtered_df.loc[filtered_df['search_city'].str.contains(token, na=False), 'relevance_score'] += 120
                filtered_df.loc[filtered_df['search_county'].str.contains(token, na=False), 'relevance_score'] += 100
                filtered_df.loc[filtered_df['search_state'].str.contains(token, na=False), 'relevance_score'] += 60

        if token_phrase:
            filtered_df.loc[filtered_df['search_city'] == token_phrase, 'relevance_score'] += 200
            filtered_df.loc[filtered_df['search_county'] == token_phrase, 'relevance_score'] += 150
            filtered_df.loc[filtered_df['search_school_name'] == token_phrase, 'relevance_score'] += 150

        filtered_df.loc[filtered_df['search_metro'].str.contains(query_lower, na=False), 'relevance_score'] += 30
        filtered_df.loc[filtered_df['search_metro'] == query_lower, 'relevance_score'] += 50

        filtered_df['relevance_score'] += filtered_df['act_average'].fillna(0) * 0.1
        filtered_df['relevance_score'] += filtered_df['sat_average'].fillna(0) * 0.01

        filtered_df = filtered_df.sort_values('relevance_score', ascending=False)

        return [self.format_school_data(row) for _, row in filtered_df.iterrows()]

    def calculate_aggregate_metrics(self, schools_data: List[Dict]) -> Dict[str, float]:
        """Calculate aggregate metrics from school list"""
        if not schools_data:
            return {
                'college_readiness_score': 0,
                'academic_preparation': 0,
                'college_enrollment': 0,
                'academic_performance': 0
            }

        # If formatted via format_school_data(...)
        if 'metrics' in schools_data[0]:
            df = pd.DataFrame([s['metrics'] for s in schools_data if 'metrics' in s])
            df.rename(columns={
                'college_readiness_score': 'act_average',
                'college_enrollment': 'college_enrollment',
                'college_performance': 'graduation_rate',
                'graduation_rate': 'graduation_rate'
            }, inplace=True)

            for col in ['college_enrollment', 'graduation_rate', 'math_proficiency', 'reading_proficiency']:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: (x / 100.0) if (x is not None and pd.notna(x)) else x)
        else:
            df = pd.DataFrame(schools_data)
            for col in ['college_enrollment', 'graduation_rate', 'math_proficiency', 'reading_proficiency']:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: (x / 100.0) if (x is not None and pd.notna(x) and float(x) > 1) else x)

        # College Readiness
        act_avg = df.get('act_average', pd.Series(dtype=float)).dropna()
        sat_avg = df.get('sat_average', pd.Series(dtype=float)).dropna()

        college_readiness = 0.0
        if not act_avg.empty:
            college_readiness = max(0.0, float(act_avg.mean()))
        elif not sat_avg.empty:
            college_readiness = max(0.0, (float(sat_avg.mean()) - 400.0) / 52.0)

        # Academic Preparation
        math_prof = df.get('math_proficiency', pd.Series(dtype=float)).dropna()
        reading_prof = df.get('reading_proficiency', pd.Series(dtype=float)).dropna()
        academic_prep = ((math_prof.mean() if not math_prof.empty else 0.5) +
                         (reading_prof.mean() if not reading_prof.empty else 0.5)) * 50

        # College Enrollment
        matriculation = df.get('college_enrollment', pd.Series(dtype=float)).dropna()
        college_enrollment = (matriculation.mean() if not matriculation.empty else 0.6) * 100

        # Academic Performance
        grad_rate = df.get('graduation_rate', pd.Series(dtype=float)).dropna()
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

        matches = self.df[self.df['stable_school_id'] == school_id]
        if matches.empty:
            return None

        if len(matches) == 1:
            return self.format_complete_school_profile(matches.iloc[0].to_dict())

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

        return self.format_complete_school_profile(matches.loc[best_idx].to_dict())

    def format_school_data(self, school_row: Dict) -> Dict:
        """Format raw school data into API response format"""

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

        def safe_get_numeric(value, multiplier=1.0):
            numeric = safe_get(value)
            if numeric is None:
                return None
            try:
                result = float(numeric) * float(multiplier)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(result):
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

        def safe_get_string(value):
            v = safe_get(value)
            if v is None:
                return None
            s = str(v).strip()
            return s if s else None

        # Fallback ID if stable ID missing
        fallback_id = "-".join(filter(None, [
            safe_get_string(school_row.get('school_name')) or '',
            safe_get_string(school_row.get('address_state')) or '',
            safe_get_zipcode(school_row.get('address_zipcode')) or ''
        ])).replace(' ', '_') or None

        lat = safe_get(school_row.get('latitude'))
        lon = safe_get(school_row.get('longitude'))
        coords = None
        if lat is not None and lon is not None:
            try:
                if np.isfinite(float(lat)) and np.isfinite(float(lon)):
                    coords = {'latitude': float(lat), 'longitude': float(lon)}
            except Exception:
                coords = None

        total_students_val = school_row.get('total_students')
        total_students = None
        if total_students_val is not None and pd.notna(total_students_val):
            try:
                total_students = int(float(total_students_val))
                if total_students <= 0:
                    total_students = None
            except (TypeError, ValueError):
                total_students = None

        return {
            'id': safe_get_string(school_row.get('stable_school_id')) or fallback_id,
            'school_name': school_row.get('school_name', ''),
            'address': {
                'street': school_row.get('address_address', ''),
                'city': school_row.get('address_city', ''),
                'state': school_row.get('address_state', ''),
                'zipcode': safe_get_zipcode(school_row.get('address_zipcode'))
            },
            'coordinates': coords,
            'metrics': {
                'college_readiness_score': self._compute_college_readiness_score(school_row),
                'college_preparation': self._calculate_college_prep_score(school_row),
                'college_enrollment': safe_get_numeric(school_row.get('college_enrollment'), 1.0),
                'college_performance': safe_get_numeric(school_row.get('graduation_rate'), 1.0),
                'graduation_rate': safe_get_numeric(school_row.get('graduation_rate'), 1.0),
                'total_students': total_students,
                'sat_average': safe_get(school_row.get('sat_average')),
                'act_average': safe_get(school_row.get('act_average')),
                'math_proficiency': safe_get_numeric(school_row.get('math_proficiency'), 1.0),
                'reading_proficiency': safe_get_numeric(school_row.get('reading_proficiency'), 1.0)
            },
            'demographics': {
                'free_reduced_lunch': safe_get(school_row.get('free_reduced_lunch')),
                'diversity_breakdown': self._extract_diversity_data(school_row)
            },
            'school_type': self._determine_school_type(school_row),
            'grades_offered': safe_get_string(school_row.get('grades_offered'))
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

        def safe_get_numeric(value, multiplier=1.0):
            numeric = safe_get(value)
            if numeric is None:
                return None
            try:
                result = float(numeric) * float(multiplier)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(result):
                return None
            return result

        def safe_get_bool(value):
            numeric = safe_get(value)
            if numeric is None:
                return None
            # accept 0/1 and True/False
            if isinstance(numeric, (int, float, np.number)):
                return bool(int(numeric))
            if isinstance(numeric, str) and numeric.strip().isdigit():
                return bool(int(numeric.strip()))
            return None

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

        # Top colleges
        top_colleges = []
        seen_colleges = set()
        for i in range(1, 11):
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

        # Top majors
        top_majors = []
        seen_majors = set()
        for i in range(1, 11):
            major_name = safe_get_string(school_row.get(f'top_major_{i:02d}'))
            if not major_name:
                continue
            major_uuid = normalize_identifier(school_row.get(f'top_major_uuid_{i:02d}'))
            major_cip = normalize_identifier(school_row.get(f'top_major_cip_code_{i:02d}'))
            dedupe_key = (major_name, major_uuid)
            if dedupe_key in seen_majors:
                continue
            seen_majors.add(dedupe_key)
            top_majors.append({
                'rank': i,
                'uuid': major_uuid,
                'cip_code': major_cip,
                'name': major_name
            })

        # Fallback ID
        fallback_id = "-".join(filter(None, [
            safe_get_string(school_row.get('school_name')) or '',
            safe_get_string(school_row.get('address_state')) or '',
            safe_get_zipcode(school_row.get('address_zipcode')) or ''
        ])).replace(' ', '_') or None

        return {
            # Basic Information
            'id': safe_get_string(school_row.get('stable_school_id')) or fallback_id,
            'school_name': safe_get_string(school_row.get('school_name')),
            'nces_id': safe_get_string(school_row.get('nces_id')),
            'niche_sd_uuid': safe_get_string(school_row.get('niche_sd_uuid')),
            'lea_id': safe_get(school_row.get('lea_id')),
            'sd_name': safe_get_string(school_row.get('sd_name')),
            'level': safe_get_string(school_row.get('level')),
            'school_type': self._determine_school_type(school_row),

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

            # Academic Performance (kept as raw percentage points, e.g., 70)
            'college_enrollment': safe_get_numeric(school_row.get('college_enrollment'), 1.0),
            'graduation_rate': safe_get_numeric(school_row.get('graduation_rate'), 1.0),
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
        scores: List[float] = []

        math_prof = school_row.get('math_proficiency')
        if math_prof is not None and pd.notna(math_prof):
            try:
                scores.append(float(math_prof))
            except (TypeError, ValueError):
                pass

        reading_prof = school_row.get('reading_proficiency')
        if reading_prof is not None and pd.notna(reading_prof):
            try:
                scores.append(float(reading_prof))
            except (TypeError, ValueError):
                pass

        grade_academics = school_row.get('grade_academics')
        if grade_academics is not None and pd.notna(grade_academics):
            grade_map = {'A+': 100, 'A': 95, 'A-': 90, 'B+': 85, 'B': 80, 'B-': 75, 'C+': 70, 'C': 65}
            if isinstance(grade_academics, str):
                mapped = grade_map.get(grade_academics.strip().upper())
                if mapped is not None:
                    scores.append(float(mapped))

        return (sum(scores) / len(scores)) if scores else None

    def _extract_diversity_data(self, school_row: Dict) -> Dict[str, float]:
        """Extract diversity breakdown from school data"""
        diversity: Dict[str, float] = {}
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
            if value is not None and pd.notna(value) and isinstance(value, (int, float, np.number)) and value > 0:
                try:
                    diversity[label] = float(value)
                except (ValueError, TypeError):
                    pass

        return diversity

    def _determine_school_type(self, school_row: Dict) -> str:
        """Determine school type from boolean flags"""
        val_public = school_row.get('is_public', 0)
        val_charter = school_row.get('is_charter', 0)

        def as_bool(v):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return False
            if isinstance(v, bool):
                return v
            if isinstance(v, (int, float, np.number)):
                return int(v) == 1
            if isinstance(v, str) and v.strip().isdigit():
                return int(v.strip()) == 1
            return False

        if as_bool(val_public):
            return 'Public'
        elif as_bool(val_charter):
            return 'Charter'
        else:
            return 'Private'
