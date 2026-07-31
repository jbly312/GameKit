from tests.conftest import register
async def test_leaderboard_order(client,game, auth_headers):
    headers = {**auth_headers, "Idempotency-Key": "Key-4"}
    first_player = await register(client,auth_headers,"device-1",display_name="Pik")
    second_player = await register(client,auth_headers,"device-2")
    first_match =await client.post(
        "/matches/result",
        headers=headers,
        json={"winner_id":second_player, "loser_id":first_player},
    )
    r = await client.get('/leaderboard',headers=auth_headers)
    items = r.json()["items"]
    assert r.status_code == 200
    assert items[0]["player_id"] == second_player
    assert items[0]["rank"] == 1
    assert items[0]["rating"] == 1030
    assert items[1]["rating"] == 970
    assert items[1]["display_name"] == "Pik"

async def test_leaderboard_limit(client,auth_headers,game):
    r = await client.get('/leaderboard?limit=101',headers=auth_headers)
    assert r.status_code == 422
