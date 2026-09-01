"""The 1v1 rating exposed as a board.

Its values come from players.rating rather than from submitted scores, but it is
read through the same /boards/{key}/top endpoint as any other board.
"""

from tests.conftest import board_me, board_top, play_match, register


async def test_rating_board_order(client, game, auth_headers):
    first_player = await register(client, auth_headers, "device-1", display_name="Pik")
    second_player = await register(client, auth_headers, "device-2")

    played = await play_match(
        client, auth_headers, winner=second_player, loser=first_player, idempotency_key="key-4"
    )
    assert played.status_code == 200

    r = await board_top(client, auth_headers, "rating")
    items = r.json()["items"]

    assert r.status_code == 200
    assert r.json()["board_key"] == "rating"
    assert items[0]["player_id"] == second_player[0]
    assert items[0]["rank"] == 1
    assert items[0]["value"] == 1030
    assert items[1]["player_id"] == first_player[0]
    assert items[1]["rank"] == 2
    assert items[1]["value"] == 970
    assert items[1]["display_name"] == "Pik"


async def test_rating_board_pagination_keeps_absolute_ranks(client, game, auth_headers):
    first_player = await register(client, auth_headers, "device-3")
    second_player = await register(client, auth_headers, "device-4")
    third_player = await register(client, auth_headers, "device-5")

    # first beats third twice, second beats third once -> first > second > third
    await play_match(client, auth_headers, winner=first_player, loser=third_player, idempotency_key="key-5")
    await play_match(client, auth_headers, winner=first_player, loser=third_player, idempotency_key="key-6")
    await play_match(client, auth_headers, winner=second_player, loser=third_player, idempotency_key="key-7")

    r = await board_top(client, auth_headers, "rating", limit=1, offset=1)
    body = r.json()

    assert r.status_code == 200
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["player_id"] == second_player[0]
    assert body["items"][0]["rank"] == 2


async def test_rating_board_is_scoped_to_the_game(
    client, auth_headers, other_auth_headers, game, other_game
):
    await register(client, auth_headers, "device-6", display_name="Ours")
    await register(client, other_auth_headers, "device-7", display_name="Theirs")

    r = await board_top(client, auth_headers, "rating")
    names = [item["display_name"] for item in r.json()["items"]]

    assert names == ["Ours"]


async def test_rating_board_limit(client, auth_headers, game):
    r = await board_top(client, auth_headers, "rating", limit=101)

    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_rating_board_reports_own_standing(client, auth_headers, game):
    winner = await register(client, auth_headers, "device-8")
    loser = await register(client, auth_headers, "device-9")
    await play_match(client, auth_headers, winner=winner, loser=loser, idempotency_key="key-8")

    r = await board_me(client, auth_headers, loser[1], "rating")

    assert r.status_code == 200
    assert r.json()["rank"] == 2
    assert r.json()["value"] == 970


async def test_fresh_player_is_ranked_by_starting_rating(client, auth_headers, game):
    """A rating board has a value for every player from the moment they register."""
    _, token = await register(client, auth_headers, "device-10")

    r = await board_me(client, auth_headers, token, "rating")

    assert r.status_code == 200
    assert r.json()["value"] == 1000
    assert r.json()["rank"] == 1
