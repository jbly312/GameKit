from tests.conftest import register
async def test_match_idempotency(client, auth_headers, game):
    first_id, first_token = await register(client, auth_headers, "device-1")
    second_id, second_token = await register(client, auth_headers, "device-2")
    headers = {**auth_headers, "X-Player-Token": first_token, "Idempotency-Key": "key-1"}

    first_match =await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id":first_id, "loser_id":second_id}
    )
    second_match = await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id": first_id, "loser_id": second_id}
    )
    assert first_match.status_code == 201
    assert first_match.json() == second_match.json()
    assert second_match.json()["status"] == "PENDING"
    assert second_match.json()["winner_rating"] is None

async def test_match_self(client, auth_headers, game):
    first_id, first_token = await register(client, auth_headers, "device-3")
    headers = {**auth_headers, "X-Player-Token": first_token, "Idempotency-Key": "key-2"}
    match = await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id": first_id, "loser_id": first_id}
    )
    assert match.status_code == 400

async def test_match_unknown_player(client, auth_headers, game):
    first_id, first_token = await register(client, auth_headers, "device-4")
    headers = {**auth_headers, "X-Player-Token": first_token, "Idempotency-Key": "key-3"}
    match = await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id": first_id,"loser_id": 99999},
    )
    assert match.status_code == 404