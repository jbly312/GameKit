from datetime import datetime, timedelta, timezone

from app.models.match import Match, MatchStatus
from tests.conftest import confirm_match, register, submit_match

STARTING_RATING = 1000
RATING_DELTA = 30


def error_code(response):
    return response.json()["error"]["code"]


async def ratings(client, headers):
    """player_id -> rating, straight from the leaderboard."""
    r = await client.get("/leaderboard", headers=headers)
    return {item["player_id"]: item["rating"] for item in r.json()["items"]}


# --- submitting a result -------------------------------------------------


async def test_match_idempotency(client, auth_headers, game):
    first_id, first_token = await register(client, auth_headers, "device-1")
    second_id, second_token = await register(client, auth_headers, "device-2")

    first_match = await submit_match(
        client, auth_headers, first_token, first_id, second_id, "key-1"
    )
    second_match = await submit_match(
        client, auth_headers, first_token, first_id, second_id, "key-1"
    )

    assert first_match.status_code == 201
    assert first_match.json() == second_match.json()
    assert second_match.json()["status"] == "PENDING"
    assert second_match.json()["winner_rating"] is None


async def test_match_self(client, auth_headers, game):
    first_id, first_token = await register(client, auth_headers, "device-3")

    match = await submit_match(
        client, auth_headers, first_token, first_id, first_id, "key-2"
    )

    assert match.status_code == 400
    assert error_code(match) == "VALIDATION_ERROR"


async def test_match_unknown_player(client, auth_headers, game):
    first_id, first_token = await register(client, auth_headers, "device-4")

    match = await submit_match(
        client, auth_headers, first_token, first_id, 99999, "key-3"
    )

    assert match.status_code == 404
    assert error_code(match) == "PLAYER_NOT_FOUND"


async def test_submitter_must_be_a_participant(client, auth_headers, game):
    first_id, _ = await register(client, auth_headers, "device-5")
    second_id, _ = await register(client, auth_headers, "device-6")
    _, outsider_token = await register(client, auth_headers, "device-7")

    match = await submit_match(
        client, auth_headers, outsider_token, first_id, second_id, "key-4"
    )

    assert match.status_code == 403
    assert error_code(match) == "NOT_A_PARTICIPANT"


async def test_submitted_match_does_not_move_ratings(client, auth_headers, game):
    first_id, first_token = await register(client, auth_headers, "device-8")
    second_id, _ = await register(client, auth_headers, "device-9")

    await submit_match(client, auth_headers, first_token, first_id, second_id, "key-5")

    assert await ratings(client, auth_headers) == {
        first_id: STARTING_RATING,
        second_id: STARTING_RATING,
    }


# --- confirming ----------------------------------------------------------


async def test_confirm_applies_rating(client, auth_headers, game):
    winner_id, winner_token = await register(client, auth_headers, "device-10")
    loser_id, loser_token = await register(client, auth_headers, "device-11")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-6"
    )
    confirmed = await confirm_match(
        client, auth_headers, loser_token, submitted.json()["match_id"], accept=True
    )

    assert confirmed.status_code == 200
    body = confirmed.json()
    assert body["match_id"] == submitted.json()["match_id"]
    assert body["status"] == "CONFIRMED"
    assert body["winner_rating"] == STARTING_RATING + RATING_DELTA
    assert body["loser_rating"] == STARTING_RATING - RATING_DELTA
    assert await ratings(client, auth_headers) == {
        winner_id: STARTING_RATING + RATING_DELTA,
        loser_id: STARTING_RATING - RATING_DELTA,
    }


async def test_loser_may_submit_and_winner_confirms(client, auth_headers, game):
    """Either participant can be the submitter — the roles come from the body, not the caller."""
    winner_id, winner_token = await register(client, auth_headers, "device-12")
    loser_id, loser_token = await register(client, auth_headers, "device-13")

    submitted = await submit_match(
        client, auth_headers, loser_token, winner_id, loser_id, "key-7"
    )
    confirmed = await confirm_match(
        client, auth_headers, winner_token, submitted.json()["match_id"], accept=True
    )

    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"
    assert confirmed.json()["winner_rating"] == STARTING_RATING + RATING_DELTA


async def test_dispute_leaves_ratings_untouched(client, auth_headers, game):
    winner_id, winner_token = await register(client, auth_headers, "device-14")
    loser_id, loser_token = await register(client, auth_headers, "device-15")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-8"
    )
    disputed = await confirm_match(
        client, auth_headers, loser_token, submitted.json()["match_id"], accept=False
    )

    assert disputed.status_code == 200
    assert disputed.json()["status"] == "DISPUTED"
    assert disputed.json()["winner_rating"] is None
    assert disputed.json()["loser_rating"] is None
    assert await ratings(client, auth_headers) == {
        winner_id: STARTING_RATING,
        loser_id: STARTING_RATING,
    }


async def test_submitter_cannot_confirm_own_match(client, auth_headers, game):
    winner_id, winner_token = await register(client, auth_headers, "device-16")
    loser_id, _ = await register(client, auth_headers, "device-17")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-9"
    )
    confirmed = await confirm_match(
        client, auth_headers, winner_token, submitted.json()["match_id"]
    )

    assert confirmed.status_code == 400
    assert error_code(confirmed) == "VALIDATION_ERROR"
    assert await ratings(client, auth_headers) == {
        winner_id: STARTING_RATING,
        loser_id: STARTING_RATING,
    }


async def test_outsider_cannot_confirm(client, auth_headers, game):
    winner_id, winner_token = await register(client, auth_headers, "device-18")
    loser_id, _ = await register(client, auth_headers, "device-19")
    _, outsider_token = await register(client, auth_headers, "device-20")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-10"
    )
    confirmed = await confirm_match(
        client, auth_headers, outsider_token, submitted.json()["match_id"]
    )

    assert confirmed.status_code == 403
    assert error_code(confirmed) == "NOT_A_PARTICIPANT"


async def test_confirm_unknown_match(client, auth_headers, game):
    _, token = await register(client, auth_headers, "device-21")

    confirmed = await confirm_match(client, auth_headers, token, 99999)

    assert confirmed.status_code == 404
    assert error_code(confirmed) == "MATCH_NOT_FOUND"


async def test_confirm_is_not_repeatable(client, auth_headers, game):
    winner_id, winner_token = await register(client, auth_headers, "device-22")
    loser_id, loser_token = await register(client, auth_headers, "device-23")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-11"
    )
    match_id = submitted.json()["match_id"]

    first = await confirm_match(client, auth_headers, loser_token, match_id)
    second = await confirm_match(client, auth_headers, loser_token, match_id)

    assert first.status_code == 200
    assert second.status_code == 409
    assert error_code(second) == "MATCH_ALREADY_FINALIZED"
    # the rating moved exactly once
    assert await ratings(client, auth_headers) == {
        winner_id: STARTING_RATING + RATING_DELTA,
        loser_id: STARTING_RATING - RATING_DELTA,
    }


async def test_disputed_match_cannot_be_confirmed(client, auth_headers, game):
    winner_id, winner_token = await register(client, auth_headers, "device-24")
    loser_id, loser_token = await register(client, auth_headers, "device-25")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-12"
    )
    match_id = submitted.json()["match_id"]

    await confirm_match(client, auth_headers, loser_token, match_id, accept=False)
    confirmed = await confirm_match(client, auth_headers, loser_token, match_id, accept=True)

    assert confirmed.status_code == 409
    assert error_code(confirmed) == "MATCH_ALREADY_FINALIZED"
    assert await ratings(client, auth_headers) == {
        winner_id: STARTING_RATING,
        loser_id: STARTING_RATING,
    }


async def test_expired_match_is_rejected_and_marked(client, auth_headers, game, db_session):
    winner_id, winner_token = await register(client, auth_headers, "device-26")
    loser_id, loser_token = await register(client, auth_headers, "device-27")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-13"
    )
    match_id = submitted.json()["match_id"]

    match = await db_session.get(Match, match_id)
    match.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()

    confirmed = await confirm_match(client, auth_headers, loser_token, match_id)

    assert confirmed.status_code == 409
    assert error_code(confirmed) == "MATCH_EXPIRED"
    await db_session.refresh(match)
    assert match.status == MatchStatus.EXPIRED
    assert await ratings(client, auth_headers) == {
        winner_id: STARTING_RATING,
        loser_id: STARTING_RATING,
    }


async def test_confirm_requires_a_player_token(client, auth_headers, game):
    winner_id, winner_token = await register(client, auth_headers, "device-28")
    loser_id, _ = await register(client, auth_headers, "device-29")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-14"
    )
    confirmed = await client.post(
        f"/matches/{submitted.json()['match_id']}/confirm",
        headers=auth_headers,
        json={"accept": True},
    )

    assert confirmed.status_code == 422
    assert error_code(confirmed) == "VALIDATION_ERROR"


async def test_confirm_rejects_an_invalid_player_token(client, auth_headers, game):
    winner_id, winner_token = await register(client, auth_headers, "device-30")
    loser_id, _ = await register(client, auth_headers, "device-31")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-15"
    )
    confirmed = await confirm_match(
        client, auth_headers, "not-a-real-token", submitted.json()["match_id"]
    )

    assert confirmed.status_code == 401
    assert error_code(confirmed) == "UNAUTHORIZED_GAME"


async def test_match_is_invisible_to_another_game(
    client, auth_headers, other_auth_headers, game, other_game
):
    winner_id, winner_token = await register(client, auth_headers, "device-32")
    loser_id, _ = await register(client, auth_headers, "device-33")
    _, outsider_token = await register(client, other_auth_headers, "device-34")

    submitted = await submit_match(
        client, auth_headers, winner_token, winner_id, loser_id, "key-16"
    )
    confirmed = await confirm_match(
        client, other_auth_headers, outsider_token, submitted.json()["match_id"]
    )

    assert confirmed.status_code == 404
    assert error_code(confirmed) == "MATCH_NOT_FOUND"
