from pydantic import BaseModel
from typing import Literal, Dict, Any

class ExecutorOutput(BaseModel):
    execution_type: Literal["task", "plan"]
    status: Literal["simulated"]
    output: Dict[str, Any]
    
    class Config:
        extra = "forbid"
