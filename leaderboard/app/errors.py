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


class NotFoundError(ToolkitError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(ToolkitError):
    status_code = 409
    code = "CONFLICT"


class ValidationError(ToolkitError):
    status_code = 400
    code = "VALIDATION_ERROR"


class MatchNotFoundError(ToolkitError):
    status_code = 404
    code = "MATCH_NOT_FOUND"


class NotAParticipantError(ToolkitError):
    status_code = 403
    code = "NOT_A_PARTICIPANT"


class MatchAlreadyFinalizedError(ToolkitError):
    status_code = 409
    code = "MATCH_ALREADY_FINALIZED"


class MatchExpiredError(ToolkitError):
    status_code = 409
    code = "MATCH_EXPIRED"


class BoardNotFoundError(ToolkitError):
    status_code = 404
    code = "BOARD_NOT_FOUND"


class BoardAlreadyExistsError(ToolkitError):
    status_code = 409
    code = "BOARD_ALREADY_EXISTS"


class BoardTypeMismatchError(ToolkitError):
    status_code = 400
    code = "BOARD_TYPE_MISMATCH"
