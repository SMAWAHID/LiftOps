from backend.app.schemas.router import RouterOutput
from datetime import datetime

class RouterAgent:
    def run(self, input_text: str) -> RouterOutput:
        input_lower = input_text.lower()
        
        classification = "task"
        if "plan" in input_lower or "strategy" in input_lower:
            classification = "plan"
        elif "?" in input_lower or "what" in input_lower or "how" in input_lower:
            classification = "question"
        elif "summary" in input_lower or "summarize" in input_lower:
            classification = "summary"
        elif not input_text.strip():
            classification = "no-op"
            
        return RouterOutput(
            intent=f"Processed: {input_text[:50]}...",
            classification=classification,
            confidence="high"
        )
