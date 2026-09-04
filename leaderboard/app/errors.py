"""Leaderboard's error codes, on top of the shared envelope.

The generic classes come from toolkit_core; what is defined here is what only
this service can hit.
"""

from toolkit_core.errors import (
    ConflictError,
    NotFoundError,
    ToolkitError,
    UnauthorizedGameError,
    UnauthorizedPlayerError,
    ValidationError,
)

__all__ = [
    "BoardAlreadyExistsError",
    "BoardNotFoundError",
    "BoardTypeMismatchError",
    "ConflictError",
    "MatchAlreadyFinalizedError",
    "MatchExpiredError",
    "MatchNotFoundError",
    "NotAParticipantError",
    "NotFoundError",
    "ToolkitError",
    "UnauthorizedGameError",
    "UnauthorizedPlayerError",
    "ValidationError",
]


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
