from pydantic import BaseModel
from typing import Optional, Literal
from .router import RouterOutput
from .planner import PlannerOutput
from .executor import ExecutorOutput
from .validator import ValidatorOutput

class PipelineRequest(BaseModel):
    input: str

class ErrorResponse(BaseModel):
    stage: Literal["router", "planner", "executor", "validator", "request"]
    error_type: str
    message: str

class PipelineResponse(BaseModel):
    request_id: str
    router: Optional[RouterOutput] = None
    planner: Optional[PlannerOutput] = None
    executor: Optional[ExecutorOutput] = None
    validator: Optional[ValidatorOutput] = None
    error: Optional[ErrorResponse] = None
