from pydantic import BaseModel
from typing import List

class Step(BaseModel):
    step_number: int
    description: str
    requires_clarification: bool
    
    class Config:
        extra = "forbid"

class PlannerOutput(BaseModel):
    goal: str
    steps: List[Step]
    blocking_questions: List[str]
    
    class Config:
        extra = "forbid"
