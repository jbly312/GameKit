from tests.conftest import register
async def test_match_idempotency(client, auth_headers, game):
    headers = {**auth_headers, "Idempotency-Key": "Key-1"}
    first_player = await register(client,auth_headers,"device-1")
    second_player = await register(client,auth_headers,"device-2")

    first_match =await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id":first_player, "loser_id":second_player}
    )
    second_match = await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id": first_player, "loser_id": second_player}
    )
    assert first_match.status_code == 201
    assert first_match.json() == second_match.json()
    assert second_match.json()["winner_rating"] == 1030

async def test_match_self(client, auth_headers, game):
    first_player = await register(client,auth_headers,"device-3")
    headers = {**auth_headers, "Idempotency-Key": "Key-2"}
    match = await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id": first_player, "loser_id": first_player}
    )
    assert match.status_code == 400

async def test_match_unknown_player(client, auth_headers, game):
    first_player = await register(client,auth_headers,"device-4")
    headers = {**auth_headers, "Idempotency-Key": "Key-3"}
    match = await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id": first_player,"loser_id": 99999},
    )
    assert match.status_code == 404