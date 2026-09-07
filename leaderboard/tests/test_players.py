from tests.conftest import (
    board_me,
    create_board,
    login,
    register,
    submit_score,
)


def error_code(response):
    return response.json()["error"]["code"]


async def test_register(client,game, auth_headers):
    r = await client.post('/players/register', headers=auth_headers, json={"device_id":"device-1", "display_name":"Lancy"})
    assert r.status_code == 201
    body = r.json()
    assert body["player_id"] > 0
    assert len(body["player_token"]) > 20

async def test_register_duplicate(client,game, auth_headers):
    r_first = await client.post('/players/register', headers=auth_headers, json={"device_id":"d1"})
    r_second = await client.post('/players/register', headers=auth_headers, json={"device_id": "d1"})
    assert r_first.status_code == 201
    assert r_second.status_code == 409

async def test_unauthorized(client,game):
    headers = {"x-api-key": "wrong"}
    r = await client.get('/boards/rating/top', headers=headers)
    assert r.status_code == 401


# --- login ---------------------------------------------------------------


async def test_login_returns_the_same_player_with_a_new_token(
    client, auth_headers, game
):
    player_id, old_token = await register(client, auth_headers, "device-2")

    logged_in = await login(client, auth_headers, "device-2")

    assert logged_in.status_code == 200
    assert logged_in.json()["player_id"] == player_id
    assert logged_in.json()["player_token"] != old_token


async def test_login_invalidates_the_previous_token(client, auth_headers, game):
    """Rotation has to revoke, not just issue.

    Only the hash is stored, so a login cannot hand back the old token — it
    mints a new one. If the old one kept working, every login would leave
    another live credential behind.
    """
    _, old_token = await register(client, auth_headers, "device-3")
    await login(client, auth_headers, "device-3")

    stale = await board_me(client, auth_headers, old_token, "rating")

    assert stale.status_code == 401
    assert error_code(stale) == "UNAUTHORIZED_PLAYER"


async def test_token_from_login_works(client, auth_headers, game):
    player_id, _ = await register(client, auth_headers, "device-4")

    fresh_token = (await login(client, auth_headers, "device-4")).json()["player_token"]
    mine = await board_me(client, auth_headers, fresh_token, "rating")

    assert mine.status_code == 200
    assert mine.json()["player_id"] == player_id


async def test_progress_survives_losing_the_token(client, auth_headers, game):
    """What the endpoint is actually for: reinstalling must not cost the account."""
    player_id, token = await register(client, auth_headers, "device-5", display_name="Ann")
    await create_board(client, auth_headers, "highscore")
    await submit_score(client, auth_headers, token, "highscore", 4820, "k-login")

    # the device "reinstalls the game" and comes back with only its device_id
    recovered = (await login(client, auth_headers, "device-5")).json()["player_token"]
    mine = await board_me(client, auth_headers, recovered, "highscore")

    assert mine.json()["player_id"] == player_id
    assert mine.json()["display_name"] == "Ann"
    assert mine.json()["value"] == 4820


async def test_login_of_an_unknown_device_is_not_found(client, auth_headers, game):
    """The client's cue to register instead."""
    missing = await login(client, auth_headers, "never-seen")

    assert missing.status_code == 404
    assert error_code(missing) == "PLAYER_NOT_FOUND"


async def test_device_id_is_scoped_to_the_game(
    client, auth_headers, other_auth_headers, game, other_game
):
    """The same device registered in two games is two players.

    Without the game_id in the lookup, logging in to one game would hand back
    the other game's player.
    """
    ours, _ = await register(client, auth_headers, "shared-device")
    theirs, _ = await register(client, other_auth_headers, "shared-device")

    assert ours != theirs
    assert (await login(client, auth_headers, "shared-device")).json()["player_id"] == ours
    assert (
        await login(client, other_auth_headers, "shared-device")
    ).json()["player_id"] == theirs


async def test_login_rejects_an_unknown_api_key(client, auth_headers, game):
    await register(client, auth_headers, "device-6")

    r = await login(client, {"x-api-key": "wrong"}, "device-6")

    assert r.status_code == 401
    assert error_code(r) == "UNAUTHORIZED_GAME"
