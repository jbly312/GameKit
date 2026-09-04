"""The error envelope every service answers with.

Domain-specific codes stay in the service that owns the domain: MATCH_* and
BOARD_* in leaderboard, SAVE_* and VERSION_* in cloudsave. Only the base class
and the situations every service can hit live here.
"""


class ToolkitError(Exception):
    """Base for every error the API reports in the shared `error` envelope.

    `code` is what a client branches on, so it describes the situation, not the
    class. A generic class may therefore be raised with a specific code:

        raise ConflictError("...", code="DEVICE_ALREADY_REGISTERED")
    """

    status_code: int = 500
    code: str = "INTERNAL_SERVER_ERROR"

    def __init__(self, message: str, code: str | None = None):
        self.message = message
        if code is not None:
            self.code = code
        super().__init__(message)


class UnauthorizedGameError(ToolkitError):
    status_code = 401
    code = "UNAUTHORIZED_GAME"


class UnauthorizedPlayerError(ToolkitError):
    status_code = 401
    code = "UNAUTHORIZED_PLAYER"


class NotFoundError(ToolkitError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(ToolkitError):
    status_code = 409
    code = "CONFLICT"


class ValidationError(ToolkitError):
    status_code = 400
    code = "VALIDATION_ERROR"
