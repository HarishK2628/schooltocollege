from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging
from models import SearchRequest, SearchResponse, School
from data_processor import SchoolDataProcessor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schools", tags=["schools"])

# Global data processor instance
data_processor = None

def get_data_processor() -> SchoolDataProcessor:
    global data_processor
    if data_processor is None:
        data_processor = SchoolDataProcessor("school_data.csv")
    return data_processor

@router.post("/search", response_model=SearchResponse)
async def search_schools(
    request: SearchRequest,
    processor: SchoolDataProcessor = Depends(get_data_processor)
):
    """Search for schools based on location query"""
    try:
        logger.info(f"Searching schools for query: {request.query}")
        
        # Search for schools
        school_results = processor.search_schools(request.query)
        
        # Format school data
        formatted_schools = []
        for school_data in school_results[:50]:  # Limit to 50 results
            formatted_school = processor.format_school_data(school_data)
            formatted_schools.append(formatted_school)
        
        # Calculate aggregate metrics
        aggregate_metrics = processor.calculate_aggregate_metrics(school_results)
        
        response_data = {
            "query": request.query,
            "total_schools": len(school_results),
            "metrics": aggregate_metrics,
            "schools": formatted_schools
        }
        
        logger.info(f"Found {len(school_results)} schools for query: {request.query}")
        
        return SearchResponse(
            success=True,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error searching schools: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/{school_id}")
async def get_school_details(
    school_id: str,
    processor: SchoolDataProcessor = Depends(get_data_processor)
):
    """Get detailed information for a specific school"""
    try:
        if processor.df is None:
            raise HTTPException(status_code=500, detail="School data not loaded")
            
        # Find school by UUID
        school_row = processor.df[processor.df['niche_school_uuid'] == school_id]
        
        if school_row.empty:
            raise HTTPException(status_code=404, detail="School not found")
        
        school_data = school_row.iloc[0].to_dict()
        formatted_school = processor.format_school_data(school_data)
        
        return {
            "success": True,
            "data": formatted_school
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting school details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get school details: {str(e)}")

@router.get("/")
async def get_schools_stats(
    processor: SchoolDataProcessor = Depends(get_data_processor)
):
    """Get general statistics about schools in the database"""
    try:
        if processor.df is None:
            raise HTTPException(status_code=500, detail="School data not loaded")
        
        stats = {
            "total_schools": len(processor.df),
            "states": processor.df['state_name'].nunique(),
            "cities": processor.df['address_city'].nunique(),
            "counties": processor.df['county_name'].nunique(),
            "metro_areas": processor.df['metro_area_name'].nunique()
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")