from pydantic import BaseModel
from typing import List, Optional

class RegionBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool

class RegionCreate(RegionBase):
    pass

class RegionUpdate(RegionBase):
    pass

class Region(RegionBase):
    id: str

    class Config:
        from_attributes = True

class RegionList(BaseModel):
    total: int
    regions: List[Region]