from app.routers import boards as boards_router
from tests.conftest import board_me, board_top, create_board, register, submit_score


def error_code(response):
    return response.json()["error"]["code"]


# --- creating boards -----------------------------------------------------


async def test_create_and_list_boards(client, auth_headers, game):
    created = await create_board(client, auth_headers, "highscore", name="High Score")

    assert created.status_code == 201
    assert created.json()["key"] == "highscore"
    assert created.json()["type"] == "SCORE"

    listed = await client.get("/boards", headers=auth_headers)
    keys = [b["key"] for b in listed.json()["items"]]

    # the rating board comes with the game, the score board was just added
    assert keys == ["rating", "highscore"]


async def test_duplicate_board_key_is_rejected(client, auth_headers, game):
    await create_board(client, auth_headers, "highscore")
    again = await create_board(client, auth_headers, "highscore")

    assert again.status_code == 409
    assert error_code(again) == "BOARD_ALREADY_EXISTS"


async def test_board_key_must_be_url_safe(client, auth_headers, game):
    bad = await create_board(client, auth_headers, "High Score!")

    assert bad.status_code == 422
    assert error_code(bad) == "VALIDATION_ERROR"


async def test_same_key_may_exist_in_another_game(
    client, auth_headers, other_auth_headers, game, other_game
):
    ours = await create_board(client, auth_headers, "highscore")
    theirs = await create_board(client, other_auth_headers, "highscore")

    assert ours.status_code == 201
    assert theirs.status_code == 201


# --- submitting scores ---------------------------------------------------


async def test_submitted_score_appears_in_top(client, auth_headers, game):
    player_id, token = await register(client, auth_headers, "device-1", display_name="Ann")
    await create_board(client, auth_headers, "highscore")

    submitted = await submit_score(client, auth_headers, token, "highscore", 4820, "k-1")

    assert submitted.status_code == 201
    assert submitted.json()["value"] == 4820
    assert submitted.json()["best_value"] == 4820
    assert submitted.json()["rank"] == 1

    items = (await board_top(client, auth_headers, "highscore")).json()["items"]
    assert items == [
        {"rank": 1, "player_id": player_id, "display_name": "Ann", "value": 4820}
    ]


async def test_repeated_idempotency_key_stores_one_score(client, auth_headers, game):
    _, token = await register(client, auth_headers, "device-2")
    await create_board(client, auth_headers, "highscore")

    first = await submit_score(client, auth_headers, token, "highscore", 100, "k-2")
    second = await submit_score(client, auth_headers, token, "highscore", 100, "k-2")

    assert first.json()["score_id"] == second.json()["score_id"]
    items = (await board_top(client, auth_headers, "highscore")).json()["items"]
    assert len(items) == 1


async def test_race_on_idempotency_key_returns_the_existing_score(
    client, auth_headers, game, monkeypatch
):
    """Two retries of one submission race; the loser must not surface a 500.

    The lookup is forced to miss once, which is what a concurrent request sees
    before the winner commits: the INSERT then hits the unique constraint.
    """
    _, token = await register(client, auth_headers, "device-3")
    await create_board(client, auth_headers, "highscore")
    first = await submit_score(client, auth_headers, token, "highscore", 700, "k-3")

    real_lookup = boards_router._score_for_key
    calls = {"n": 0}

    async def missing_on_first_call(db, board_id, idempotency_key):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return await real_lookup(db, board_id, idempotency_key)

    monkeypatch.setattr(boards_router, "_score_for_key", missing_on_first_call)

    second = await submit_score(client, auth_headers, token, "highscore", 700, "k-3")

    assert second.status_code == 201
    assert second.json()["score_id"] == first.json()["score_id"]


async def test_idempotency_key_of_another_player_is_rejected(client, auth_headers, game):
    _, first_token = await register(client, auth_headers, "device-4")
    _, second_token = await register(client, auth_headers, "device-5")
    await create_board(client, auth_headers, "highscore")

    await submit_score(client, auth_headers, first_token, "highscore", 100, "shared")
    stolen = await submit_score(client, auth_headers, second_token, "highscore", 999, "shared")

    assert stolen.status_code == 409
    assert error_code(stolen) == "IDEMPOTENCY_KEY_CONFLICT"


async def test_score_cannot_be_submitted_to_a_rating_board(client, auth_headers, game):
    _, token = await register(client, auth_headers, "device-6")

    rejected = await submit_score(client, auth_headers, token, "rating", 5000, "k-4")

    assert rejected.status_code == 400
    assert error_code(rejected) == "BOARD_TYPE_MISMATCH"


async def test_unknown_board_is_not_found(client, auth_headers, game):
    _, token = await register(client, auth_headers, "device-7")

    submitted = await submit_score(client, auth_headers, token, "nope", 1, "k-5")
    listed = await board_top(client, auth_headers, "nope")

    assert submitted.status_code == 404
    assert error_code(submitted) == "BOARD_NOT_FOUND"
    assert listed.status_code == 404


# --- aggregation and ordering --------------------------------------------


async def test_best_aggregation_keeps_the_highest(client, auth_headers, game):
    _, token = await register(client, auth_headers, "device-8")
    await create_board(client, auth_headers, "highscore")

    await submit_score(client, auth_headers, token, "highscore", 500, "k-6")
    worse = await submit_score(client, auth_headers, token, "highscore", 120, "k-7")

    assert worse.json()["value"] == 120
    assert worse.json()["best_value"] == 500
    items = (await board_top(client, auth_headers, "highscore")).json()["items"]
    assert items[0]["value"] == 500


async def test_ascending_board_treats_lower_as_better(client, auth_headers, game):
    """Speedruns: the smaller number wins."""
    fast_id, fast_token = await register(client, auth_headers, "device-9")
    slow_id, slow_token = await register(client, auth_headers, "device-10")
    await create_board(client, auth_headers, "speedrun", sort_direction="ASC")

    await submit_score(client, auth_headers, slow_token, "speedrun", 94.5, "k-8")
    await submit_score(client, auth_headers, fast_token, "speedrun", 31.2, "k-9")
    await submit_score(client, auth_headers, fast_token, "speedrun", 88.0, "k-10")

    items = (await board_top(client, auth_headers, "speedrun")).json()["items"]

    assert [i["player_id"] for i in items] == [fast_id, slow_id]
    assert items[0]["value"] == 31.2  # the worse 88.0 did not replace it


async def test_last_aggregation_keeps_the_most_recent(client, auth_headers, game):
    _, token = await register(client, auth_headers, "device-11")
    await create_board(client, auth_headers, "current", aggregation="LAST")

    await submit_score(client, auth_headers, token, "current", 900, "k-11")
    await submit_score(client, auth_headers, token, "current", 40, "k-12")

    items = (await board_top(client, auth_headers, "current")).json()["items"]

    assert items[0]["value"] == 40


async def test_equal_scores_rank_the_earlier_submission_first(client, auth_headers, game):
    early_id, early_token = await register(client, auth_headers, "device-12")
    late_id, late_token = await register(client, auth_headers, "device-13")
    await create_board(client, auth_headers, "highscore")

    await submit_score(client, auth_headers, early_token, "highscore", 1000, "k-13")
    await submit_score(client, auth_headers, late_token, "highscore", 1000, "k-14")

    items = (await board_top(client, auth_headers, "highscore")).json()["items"]

    assert [i["player_id"] for i in items] == [early_id, late_id]
    assert [i["rank"] for i in items] == [1, 2]


async def test_ranks_stay_absolute_across_pages(client, auth_headers, game):
    await create_board(client, auth_headers, "highscore")
    for n, value in enumerate([400, 300, 200, 100], start=14):
        _, token = await register(client, auth_headers, f"device-{n}")
        await submit_score(client, auth_headers, token, "highscore", value, f"k-p{n}")

    first_page = (await board_top(client, auth_headers, "highscore", limit=2)).json()
    second_page = (
        await board_top(client, auth_headers, "highscore", limit=2, offset=2)
    ).json()

    assert [i["rank"] for i in first_page["items"]] == [1, 2]
    assert [i["rank"] for i in second_page["items"]] == [3, 4]
    assert [i["value"] for i in second_page["items"]] == [200, 100]


# --- own standing --------------------------------------------------------


async def test_me_reports_rank_beyond_the_first_page(client, auth_headers, game):
    await create_board(client, auth_headers, "highscore")
    for n, value in enumerate([900, 800, 700], start=20):
        _, token = await register(client, auth_headers, f"device-{n}")
        await submit_score(client, auth_headers, token, "highscore", value, f"k-m{n}")
    _, last_token = await register(client, auth_headers, "device-23")
    await submit_score(client, auth_headers, last_token, "highscore", 10, "k-m23")

    mine = await board_me(client, auth_headers, last_token, "highscore")

    assert mine.status_code == 200
    assert mine.json()["value"] == 10
    assert mine.json()["rank"] == 4


async def test_me_is_empty_for_a_player_without_scores(client, auth_headers, game):
    _, token = await register(client, auth_headers, "device-24")
    await create_board(client, auth_headers, "highscore")

    mine = await board_me(client, auth_headers, token, "highscore")

    assert mine.status_code == 200
    assert mine.json()["value"] is None
    assert mine.json()["rank"] is None


# --- isolation -----------------------------------------------------------


async def test_board_of_another_game_is_invisible(
    client, auth_headers, other_auth_headers, game, other_game
):
    await create_board(client, auth_headers, "highscore")

    seen = await board_top(client, other_auth_headers, "highscore")

    assert seen.status_code == 404
    assert error_code(seen) == "BOARD_NOT_FOUND"


async def test_scores_are_scoped_to_the_game(
    client, auth_headers, other_auth_headers, game, other_game
):
    _, ours = await register(client, auth_headers, "device-25", display_name="Ours")
    _, theirs = await register(client, other_auth_headers, "device-26", display_name="Theirs")
    await create_board(client, auth_headers, "highscore")
    await create_board(client, other_auth_headers, "highscore")

    await submit_score(client, auth_headers, ours, "highscore", 10, "k-s1")
    await submit_score(client, other_auth_headers, theirs, "highscore", 99, "k-s2")

    items = (await board_top(client, auth_headers, "highscore")).json()["items"]

    assert [i["display_name"] for i in items] == ["Ours"]


async def test_submitting_requires_a_player_token(client, auth_headers, game):
    await create_board(client, auth_headers, "highscore")

    anonymous = await client.post(
        "/boards/highscore/scores",
        headers={**auth_headers, "Idempotency-Key": "k-anon"},
        json={"value": 1},
    )

    assert anonymous.status_code == 422
    assert error_code(anonymous) == "VALIDATION_ERROR"
