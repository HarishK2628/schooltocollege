from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging
import os
from pathlib import Path
from models import SearchRequest, SearchResponse, School
from data_processor import SchoolDataProcessor
import re

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schools", tags=["schools"])

# Global data processor instance
data_processor = None

def get_data_processor() -> SchoolDataProcessor:
    global data_processor
    if data_processor is None:
        csv_name = os.getenv("SCHOOL_CSV_PATH", "synthetic_data_filled_updated.csv")
        # Resolve CSV relative to backend directory
        backend_root = Path(__file__).resolve().parents[1]
        csv_path = backend_root / csv_name
        data_processor = SchoolDataProcessor(str(csv_path))
    return data_processor

@router.post("/search", response_model=SearchResponse)
async def search_schools(
    request: SearchRequest,
    processor: SchoolDataProcessor = Depends(get_data_processor)
):
    """Search for schools based on location query"""
    try:
        logger.info(f"Searching schools for query: {request.query}")
        
        # If query is a ZIP code, return all schools in that ZIP first
        school_results = []
        used_zip_filter = False
        q = request.query or ''
        try:
            has_letters = bool(re.search(r"[a-zA-Z]", q))
            digits_only = re.sub(r"[^0-9]", "", q)
            looks_like_zip = (not has_letters) and (len(digits_only) >= 5)
            if looks_like_zip:
                df = processor.df
                zip_col = 'address_zipcode' if 'address_zipcode' in df.columns else ('ZIP' if 'ZIP' in df.columns else None)
                if zip_col:
                    zip_series = df[zip_col].astype(str).str.replace(r"[^0-9]", "", regex=True)
                    zip5 = digits_only[:5]
                    eq_zip = zip_series.str.startswith(zip5)
                    if eq_zip.any():
                        school_results = df[eq_zip].to_dict('records')
                        used_zip_filter = True
        except Exception:
            school_results = []

        # If query looks like a street address, try exact address match next
        if not school_results and any(ch.isdigit() for ch in q):
            try:
                norm = re.sub(r'[^a-z0-9]', '', q.lower())
                df = processor.df
                # Column fallbacks for raw vs normalized schema
                addr_col = 'address_address' if 'address_address' in df.columns else 'ADDRESS'
                city_col = 'address_city' if 'address_city' in df.columns else 'CITY'
                state_col = 'address_state' if 'address_state' in df.columns else 'STATE'
                zip_col = 'address_zipcode' if 'address_zipcode' in df.columns else ('ZIP' if 'ZIP' in df.columns else None)

                addr_series = df[addr_col].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True)
                full_series = addr_series + \
                    df[city_col].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + \
                    df[state_col].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True) + \
                    (df[zip_col].astype(str).str.lower().str.replace(r"[^a-z0-9]", "", regex=True) if zip_col else '')

                eq = (addr_series == norm) | (full_series == norm)
                if eq.any():
                    school_results = df[eq].to_dict('records')
            except Exception:
                school_results = []

        # If not an address (no digits), try exact city match next
        if not school_results and q and not any(ch.isdigit() for ch in q):
            try:
                city_norm = (q or '').strip().lower()
                df = processor.df
                city_col = 'address_city' if 'address_city' in df.columns else 'CITY'
                # Exact equality on lowercased city
                eq_city = df[city_col].astype(str).str.lower() == city_norm
                if eq_city.any():
                    school_results = df[eq_city].to_dict('records')
            except Exception:
                school_results = []

        # If still nothing and not an address, try exact state match (abbrev or full name)
        if not school_results and q and not any(ch.isdigit() for ch in q):
            try:
                state_norm = (q or '').strip().lower()
                df = processor.df
                # Abbreviation column
                state_abbr_col = 'address_state' if 'address_state' in df.columns else ('STATE' if 'STATE' in df.columns else None)
                # Full name column if present
                state_full_col = 'state_name' if 'state_name' in df.columns else None

                matches = None
                if state_abbr_col:
                    eq_abbr = df[state_abbr_col].astype(str).str.lower() == state_norm
                    matches = eq_abbr
                if state_full_col:
                    eq_full = df[state_full_col].astype(str).str.lower() == state_norm
                    matches = (matches | eq_full) if matches is not None else eq_full

                if matches is not None and matches.any():
                    school_results = df[matches].to_dict('records')
            except Exception:
                school_results = []

        # Fallback to general search if nothing matched above
        if not school_results:
            school_results = processor.search_schools(request.query)
        
        # Format school data
        formatted_schools = []
        iterable = school_results if used_zip_filter else school_results[:50]
        for school_data in iterable:
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
    city: Optional[str] = None,
    state: Optional[str] = None,
    name: Optional[str] = None,
    zipcode: Optional[str] = None,
    processor: SchoolDataProcessor = Depends(get_data_processor)
):
    """Get detailed information for a specific school"""
    try:
        if processor.df is None:
            raise HTTPException(status_code=500, detail="School data not loaded")
            
        school_data = processor.get_school_record(
            school_id,
            name=name,
            city=city,
            state=state,
            zipcode=zipcode
        )

        if school_data is None:
            raise HTTPException(status_code=404, detail="School not found")

        complete_profile = processor.format_complete_school_profile(school_data)
        
        return {
            "success": True,
            "data": complete_profile
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
