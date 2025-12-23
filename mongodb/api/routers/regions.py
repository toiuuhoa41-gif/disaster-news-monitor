from fastapi import APIRouter, HTTPException
from typing import List
from mongodb.api.models.region import Region
from mongodb.api.services.regions_service import RegionsService

router = APIRouter()

@router.get("/", response_model=List[Region])
async def get_regions():
    """Get all regions"""
    try:
        service = RegionsService()
        regions = await service.get_all_regions()
        return regions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{region_id}", response_model=Region)
async def get_region(region_id: str):
    """Get a specific region by ID"""
    try:
        service = RegionsService()
        region = await service.get_region_by_id(region_id)
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        return region
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))