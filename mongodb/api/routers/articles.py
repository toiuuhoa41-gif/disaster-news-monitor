from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from mongodb.api.services.articles_service import ArticlesService
from mongodb.api.schemas.article import ArticleResponse, ArticleFilter

router = APIRouter()


def get_articles_service():
    """Dependency injection for ArticlesService"""
    return ArticlesService()


@router.get("/latest", response_model=List[ArticleResponse])
async def get_latest_articles(
    limit: int = Query(20, le=100), 
    severity: Optional[str] = None, 
    type: Optional[str] = None,
    service: ArticlesService = Depends(get_articles_service)
):
    """
    Get latest disaster articles for the real-time panel.
    """
    try:
        articles = await service.get_latest_articles(limit=limit, severity=severity, type=type)
        return articles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=Dict[str, Any])
async def get_articles(
    limit: int = Query(20, ge=1, le=500),
    skip: int = Query(0, ge=0),
    page: int = Query(1, ge=1),
    sort_by: str = Query("collected_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="asc or desc"),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    region: Optional[str] = None,
    disaster_type: Optional[str] = None,
    severity: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    service: ArticlesService = Depends(get_articles_service)
):
    """
    Get articles with various filters for the dashboard and analytics.
    Returns paginated response with articles array and metadata.
    """
    try:
        filters = ArticleFilter(
            from_date=from_date,
            to_date=to_date,
            region=region,
            disaster_type=disaster_type,
            severity=severity,
            source=source
        )
        
        # Calculate skip from page if not provided
        actual_skip = skip if skip > 0 else (page - 1) * limit
        
        articles = await service.get_articles(
            filters=filters, 
            limit=limit, 
            skip=actual_skip,
            sort_by=sort_by,
            sort_order=sort_order,
            search=search
        )
        
        # Get total count for pagination
        total = await service.get_total_count(filters=filters, search=search)
        
        return {
            "articles": articles,
            "total": total,
            "page": page,
            "limit": limit,
            "has_more": actual_skip + len(articles) < total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))