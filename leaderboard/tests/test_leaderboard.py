from tests.conftest import play_match, register


async def test_leaderboard_order(client, game, auth_headers):
    first_player = await register(client, auth_headers, "device-1", display_name="Pik")
    second_player = await register(client, auth_headers, "device-2")

    played = await play_match(
        client, auth_headers, winner=second_player, loser=first_player, idempotency_key="key-4"
    )
    assert played.status_code == 200

    r = await client.get("/leaderboard", headers=auth_headers)
    items = r.json()["items"]

    assert r.status_code == 200
    assert items[0]["player_id"] == second_player[0]
    assert items[0]["rank"] == 1
    assert items[0]["rating"] == 1030
    assert items[1]["player_id"] == first_player[0]
    assert items[1]["rank"] == 2
    assert items[1]["rating"] == 970
    assert items[1]["display_name"] == "Pik"


async def test_leaderboard_pagination_keeps_absolute_ranks(client, game, auth_headers):
    first_player = await register(client, auth_headers, "device-3")
    second_player = await register(client, auth_headers, "device-4")
    third_player = await register(client, auth_headers, "device-5")

    # first beats third twice, second beats third once -> first > second > third
    await play_match(client, auth_headers, winner=first_player, loser=third_player, idempotency_key="key-5")
    await play_match(client, auth_headers, winner=first_player, loser=third_player, idempotency_key="key-6")
    await play_match(client, auth_headers, winner=second_player, loser=third_player, idempotency_key="key-7")

    r = await client.get("/leaderboard?limit=1&offset=1", headers=auth_headers)
    body = r.json()

    assert r.status_code == 200
    assert body["limit"] == 1
    assert body["offset"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["player_id"] == second_player[0]
    assert body["items"][0]["rank"] == 2


async def test_leaderboard_is_scoped_to_the_game(
    client, auth_headers, other_auth_headers, game, other_game
):
    await register(client, auth_headers, "device-6", display_name="Ours")
    await register(client, other_auth_headers, "device-7", display_name="Theirs")

    r = await client.get("/leaderboard", headers=auth_headers)
    names = [item["display_name"] for item in r.json()["items"]]

    assert names == ["Ours"]


async def test_leaderboard_limit(client, auth_headers, game):
    r = await client.get('/leaderboard?limit=101', headers=auth_headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
