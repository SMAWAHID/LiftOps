from pydantic import BaseModel
from typing import Literal, List

class RouterOutput(BaseModel):
    intent: str
    classification: Literal["task", "plan", "summary", "question", "no-op"]
    confidence: Literal["high", "medium", "low"]
    
    class Config:
        extra = "forbid"
