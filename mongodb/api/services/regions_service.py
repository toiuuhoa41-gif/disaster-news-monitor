from typing import List, Optional
from fastapi import HTTPException
from mongodb.api.models.region import Region
from mongodb.api.config.database import Database


class RegionsService:
    def __init__(self):
        pass  # Use lazy loading
    
    @property
    def db(self):
        return Database.get_db()
    
    @property
    def collection(self):
        return self.db['regions']

    async def get_all_regions(self) -> List[Region]:
        """Get all regions"""
        cursor = self.collection.find()
        regions = await cursor.to_list(length=None)
        return regions

    async def get_region_by_id(self, region_id: str) -> Optional[Region]:
        """Get a region by ID"""
        region = await self.collection.find_one({"_id": region_id})
        return region

    async def create_region(self, region_data: dict) -> Region:
        """Create a new region"""
        result = await self.collection.insert_one(region_data)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def update_region(self, region_id: str, region_data: dict) -> Region:
        """Update a region"""
        result = await self.collection.update_one(
            {"_id": region_id},
            {"$set": region_data}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Region not found")
        return await self.collection.find_one({"_id": region_id})

    async def delete_region(self, region_id: str) -> dict:
        """Delete a region"""
        result = await self.collection.delete_one({"_id": region_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Region not found")
        return {"detail": "Region deleted successfully"}
