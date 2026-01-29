from backend.app.schemas.executor import ExecutorOutput
from backend.app.schemas.planner import PlannerOutput

class ExecutorAgent:
    def run(self, planner_output: PlannerOutput) -> ExecutorOutput:
        return ExecutorOutput(
            execution_type="task" if len(planner_output.steps) == 1 else "plan",
            status="simulated",
            output={
                "result": "Success",
                "goal": planner_output.goal,
                "steps_processsed": len(planner_output.steps),
                "message": "Stub execution completed."
            }
        )
