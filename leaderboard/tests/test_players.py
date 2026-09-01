
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