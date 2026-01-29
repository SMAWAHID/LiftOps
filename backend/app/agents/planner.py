from backend.app.schemas.planner import PlannerOutput, Step
from backend.app.schemas.router import RouterOutput

class PlannerAgent:
    def run(self, router_output: RouterOutput) -> PlannerOutput:
        classification = router_output.classification
        original_intent = router_output.intent
        
        steps = []
        blocking_questions = []
        
        if classification == "plan":
            steps = [
                Step(step_number=1, description="Analyze requirements", requires_clarification=False),
                Step(step_number=2, description="Draft implementation plan", requires_clarification=False),
                Step(step_number=3, description="Execute first phase", requires_clarification=False),
                Step(step_number=4, description="Verify results", requires_clarification=False)
            ]
        elif classification == "question":
            blocking_questions = ["Could you provide more context?"]
            steps = [Step(step_number=1, description="Answer user question", requires_clarification=True)]
        else:
            steps = [Step(step_number=1, description=f"Execute: {original_intent}", requires_clarification=False)]
            
        return PlannerOutput(
            goal=f"Fulfil intent: {original_intent}",
            steps=steps,
            blocking_questions=blocking_questions
        )
