from backend.app.schemas.validator import ValidatorOutput
from backend.app.schemas.executor import ExecutorOutput

class ValidatorAgent:
    def run(self, executor_output: ExecutorOutput) -> ValidatorOutput:
        # Safety Check Logic
        dangerous_keywords = ["drop", "delete", "rm ", "shutdown", "truncate"]
        
        # Check Execution Output details
        content_to_check = str(executor_output.output).lower()
        
        issues = []
        is_valid = True
        recommended_action = "accept"

        for kw in dangerous_keywords:
            if kw in content_to_check:
                is_valid = False
                issues.append(f"Safety Violation: Detected dangerous keyword '{kw}'")
                recommended_action = "revise"
        
        if not is_valid:
            issues.append("Action blocked by Safety Protocol Level 1.")

        return ValidatorOutput(
            valid=is_valid,
            issues=issues,
            recommended_action=recommended_action
        )
