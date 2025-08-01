from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Address(BaseModel):
    street: str
    city: str
    state: str
    zipcode: Optional[str] = None

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class SchoolMetrics(BaseModel):
    college_readiness_score: Optional[float] = None
    college_preparation: Optional[float] = None
    college_enrollment: Optional[float] = None
    college_performance: Optional[float] = None
    graduation_rate: Optional[float] = None
    total_students: Optional[int] = None
    sat_average: Optional[float] = None
    act_average: Optional[float] = None
    math_proficiency: Optional[float] = None
    reading_proficiency: Optional[float] = None

class Demographics(BaseModel):
    free_reduced_lunch: Optional[float] = None
    diversity_breakdown: Optional[Dict[str, float]] = None

class School(BaseModel):
    id: str
    school_name: str
    address: Address
    coordinates: Optional[Coordinates] = None
    metrics: SchoolMetrics
    demographics: Optional[Demographics] = None
    school_type: Optional[str] = None
    grades_offered: Optional[str] = None

class AggregateMetrics(BaseModel):
    college_readiness_score: float
    academic_preparation: float
    college_enrollment: float
    academic_performance: float

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]
    
class SchoolSearchData(BaseModel):
    query: str
    total_schools: int
    metrics: AggregateMetrics
    schools: List[School]