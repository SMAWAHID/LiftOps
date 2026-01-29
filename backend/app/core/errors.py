class AppError(Exception):
    def __init__(self, message: str, stage: str = "system", error_type: str = "internal_error"):
        self.message = message
        self.stage = stage
        self.error_type = error_type
        super().__init__(self.message)

class AgentError(AppError):
    pass

class ValidationError(AppError):
    def __init__(self, message: str, stage: str):
        super().__init__(message, stage, "validation_error")
