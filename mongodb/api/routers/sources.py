from fastapi import APIRouter, HTTPException, Depends
from typing import List
from mongodb.api.models.source import Source
from mongodb.api.schemas.source import SourceCreate, SourceUpdate
from mongodb.api.services.sources_service import SourcesService

router = APIRouter()


def get_sources_service():
    """Dependency injection for SourcesService"""
    return SourcesService()


@router.get("/", response_model=List[Source])
async def get_all_sources(service: SourcesService = Depends(get_sources_service)):
    """Retrieve all news sources"""
    sources = await service.get_all_sources()
    return sources

@router.get("/realtime", response_model=List[Source])
async def get_realtime_sources(service: SourcesService = Depends(get_sources_service)):
    """Retrieve only active (realtime) sources"""
    sources = await service.get_realtime_sources()
    return sources

@router.post("/", response_model=Source)
async def create_source(source: SourceCreate, service: SourcesService = Depends(get_sources_service)):
    """Create a new news source"""
    try:
        new_source = await service.create_source(source)
        return new_source
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{source_id}", response_model=Source)
async def update_source(source_id: str, source: SourceUpdate, service: SourcesService = Depends(get_sources_service)):
    """Update an existing news source"""
    try:
        updated_source = await service.update_source(source_id, source)
        return updated_source
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{source_id}", response_model=dict)
async def delete_source(source_id: str, service: SourcesService = Depends(get_sources_service)):
    """Delete a news source"""
    try:
        await service.delete_source(source_id)
        return {"message": "Source deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))