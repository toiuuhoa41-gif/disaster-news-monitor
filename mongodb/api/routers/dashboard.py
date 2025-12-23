from fastapi import APIRouter, HTTPException
from typing import List
from mongodb.api.services.stats_service import StatsUpdateService
from mongodb.api.services.cache_service import cached, get_cache_service
from mongodb.api.schemas.dashboard import DashboardOverview, SeverityBreakdown, DisasterTypeDistribution, CrawlActivityTimeline

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview():
    """Get dashboard overview stats - cached for 5 minutes"""
    cache = get_cache_service()
    cache_key = "dashboard:overview"
    
    # Try cache first
    cached_data = await cache.get(cache_key)
    if cached_data:
        return DashboardOverview(**cached_data)
    
    # Get from service
    stats_service = StatsUpdateService()
    overview = await stats_service.get_dashboard_overview()
    
    # Cache the result
    if hasattr(overview, 'model_dump'):
        await cache.set(cache_key, overview.model_dump(), ttl=300)
    elif hasattr(overview, 'dict'):
        await cache.set(cache_key, overview.dict(), ttl=300)
    
    return overview


@router.get("/severity", response_model=SeverityBreakdown)
async def get_severity_breakdown():
    """Get severity breakdown - cached for 5 minutes"""
    cache = get_cache_service()
    cache_key = "dashboard:severity"
    
    cached_data = await cache.get(cache_key)
    if cached_data:
        return SeverityBreakdown(**cached_data)
    
    stats_service = StatsUpdateService()
    severity_data = await stats_service.get_severity_breakdown()
    
    if hasattr(severity_data, 'model_dump'):
        await cache.set(cache_key, severity_data.model_dump(), ttl=300)
    elif hasattr(severity_data, 'dict'):
        await cache.set(cache_key, severity_data.dict(), ttl=300)
    
    return severity_data


@router.get("/disaster-types", response_model=DisasterTypeDistribution)
async def get_disaster_type_distribution():
    """Get disaster type distribution - cached for 5 minutes"""
    cache = get_cache_service()
    cache_key = "dashboard:disaster_types"
    
    cached_data = await cache.get(cache_key)
    if cached_data:
        return DisasterTypeDistribution(**cached_data)
    
    stats_service = StatsUpdateService()
    distribution = await stats_service.get_disaster_type_distribution()
    
    if hasattr(distribution, 'model_dump'):
        await cache.set(cache_key, distribution.model_dump(), ttl=300)
    elif hasattr(distribution, 'dict'):
        await cache.set(cache_key, distribution.dict(), ttl=300)
    
    return distribution


@router.get("/crawl-timeline", response_model=List[CrawlActivityTimeline])
async def get_crawl_activity_timeline():
    """Get crawl timeline - cached for 2 minutes"""
    cache = get_cache_service()
    cache_key = "dashboard:crawl_timeline"
    
    cached_data = await cache.get(cache_key)
    if cached_data:
        return [CrawlActivityTimeline(**item) for item in cached_data]
    
    stats_service = StatsUpdateService()
    timeline = await stats_service.get_crawl_activity_timeline()
    
    # Cache list of models
    timeline_data = []
    for item in timeline:
        if hasattr(item, 'model_dump'):
            timeline_data.append(item.model_dump())
        elif hasattr(item, 'dict'):
            timeline_data.append(item.dict())
        else:
            timeline_data.append(item)
    
    await cache.set(cache_key, timeline_data, ttl=120)
    
    return timeline


@router.delete("/cache")
async def clear_dashboard_cache():
    """Clear all dashboard cache"""
    cache = get_cache_service()
    count = await cache.delete_pattern("dashboard:*")
    return {"cleared": count, "message": "Dashboard cache cleared"}