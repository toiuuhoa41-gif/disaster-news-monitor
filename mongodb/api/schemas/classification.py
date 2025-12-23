from pydantic import BaseModel
from typing import Optional

class ClassificationResult(BaseModel):
    is_disaster: bool
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    confidence: float

class ClassificationRequest(BaseModel):
    title: str
    content: str