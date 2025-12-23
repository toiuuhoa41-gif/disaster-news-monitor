from pydantic import BaseModel
from typing import Optional

class Region(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True