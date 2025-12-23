from pydantic import BaseModel
from typing import List, Optional

class Keyword(BaseModel):
    id: str
    name: str
    disaster_type: str
    severity: Optional[str] = None

class KeywordGroup(BaseModel):
    weather: List[str]
    flood: List[str]
    drought: List[str]
    earthquake: List[str]
    general: List[str]