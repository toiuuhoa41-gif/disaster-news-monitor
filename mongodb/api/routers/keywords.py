from fastapi import APIRouter, HTTPException
from typing import List
from mongodb.api.services.keywords_service import KeywordsService
from mongodb.api.schemas.keyword import Keyword

router = APIRouter()

@router.get("/", response_model=List[Keyword])
async def get_keywords():
    """Retrieve all disaster-related keywords."""
    try:
        service = KeywordsService()
        keywords = await service.get_all_keywords()
        return keywords
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Keyword)
async def add_keyword(keyword: Keyword):
    """Add a new disaster-related keyword."""
    try:
        service = KeywordsService()
        new_keyword = await service.add_keyword(keyword)
        return new_keyword
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{keyword_id}", response_model=dict)
async def delete_keyword(keyword_id: str):
    """Delete a disaster-related keyword by ID."""
    try:
        service = KeywordsService()
        result = await service.delete_keyword(keyword_id)
        if result:
            return {"success": True, "message": "Keyword deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Keyword not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))