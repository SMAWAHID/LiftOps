from pydantic import BaseModel
from typing import Literal, List

class ValidatorOutput(BaseModel):
    valid: bool
    issues: List[str]
    recommended_action: Literal["accept", "revise", "ask_user"]
    
    class Config:
        extra = "forbid"
