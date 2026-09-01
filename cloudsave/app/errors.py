class ToolkitError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

class UnauthorizedGameError(ToolkitError):
    status_code = 401
    code = "UNAUTHORIZED_GAME"

class NotFoundError(ToolkitError):
    status_code = 404
    code = "SAVE_NOT_FOUND"

class ConflictError(ToolkitError):
    status_code = 409
    code = "VERSION_CONFLICT"

class ValidationError(ToolkitError):
    status_code = 400
    code = "VALIDATION_ERROR"

class UnauthorizedPlayerError(ToolkitError):
    status_code = 401
    code = "UNAUTHORIZED_PLAYER"
