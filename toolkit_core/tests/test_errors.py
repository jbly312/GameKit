from toolkit_core.errors import ConflictError, ToolkitError, UnauthorizedPlayerError
from toolkit_core.security import generate_raw_token, hash_value


def test_class_supplies_a_default_code():
    error = ConflictError("nope")

    assert error.status_code == 409
    assert error.code == "CONFLICT"


def test_code_can_be_set_where_it_is_raised():
    """A generic class must be able to report a specific situation."""
    error = ConflictError("nope", code="DEVICE_ALREADY_REGISTERED")

    assert error.code == "DEVICE_ALREADY_REGISTERED"
    assert ConflictError("other").code == "CONFLICT"  # not leaked onto the class


def test_player_and_game_failures_are_distinguishable():
    """A bad player token must not report a problem with the game's key."""
    assert UnauthorizedPlayerError("x").code == "UNAUTHORIZED_PLAYER"
    assert issubclass(UnauthorizedPlayerError, ToolkitError)


def test_hashing_is_stable_and_not_reversible():
    raw = generate_raw_token()

    assert hash_value(raw) == hash_value(raw)
    assert raw not in hash_value(raw)
    assert generate_raw_token() != generate_raw_token()
