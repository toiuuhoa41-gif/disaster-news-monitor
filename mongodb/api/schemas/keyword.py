from pydantic import BaseModel
from typing import List

class KeywordBase(BaseModel):
    name: str
    type: str

class KeywordCreate(KeywordBase):
    pass

class Keyword(KeywordBase):
    id: str

    class Config:
        from_attributes = True

class KeywordGroup(BaseModel):
    weather: List[str]
    flood: List[str]
    drought: List[str]
    earthquake: List[str]
    general: List[str]