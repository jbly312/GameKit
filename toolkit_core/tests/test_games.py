"""Ordering contract of create_game, checked without a database.

The DB-backed behaviour is covered through leaderboard's suite; what is worth
pinning here is the sequence, because that is what makes registration atomic
and it is invisible in any single service's tests.
"""

import pytest
from toolkit_core.games import create_game
from toolkit_core.security import hash_value


class FakeSession:
    def __init__(self):
        self.calls = []

    def add(self, obj):
        self.calls.append("add")

    async def flush(self):
        self.calls.append("flush")

    async def commit(self):
        self.calls.append("commit")


class FakeGame:
    def __init__(self, **fields):
        self.__dict__.update(fields)
        self.id = "generated-id"


async def test_hook_runs_between_flush_and_commit():
    """flush gives the hook an id; commit comes once, after the hook."""
    db = FakeSession()

    async def after_create(session, game):
        db.calls.append("after_create")

    await create_game(db, FakeGame, "My Game", after_create=after_create)

    assert db.calls == ["add", "flush", "after_create", "commit"]


async def test_nothing_is_committed_when_the_hook_fails():
    db = FakeSession()

    async def exploding(session, game):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await create_game(db, FakeGame, "My Game", after_create=exploding)

    assert "commit" not in db.calls


async def test_works_without_a_hook():
    db = FakeSession()

    await create_game(db, FakeGame, "My Game")

    assert db.calls == ["add", "flush", "commit"]


async def test_supplied_key_is_kept_and_generated_keys_differ():
    game, api_key, _ = await create_game(
        FakeSession(), FakeGame, "My Game", api_key="shared-key"
    )
    assert api_key == "shared-key"
    assert game.api_key == "shared-key"

    _, first, _ = await create_game(FakeSession(), FakeGame, "A")
    _, second, _ = await create_game(FakeSession(), FakeGame, "B")
    assert first != second


async def test_secret_is_returned_raw_and_stored_hashed():
    """The returned secret is the only copy in existence."""
    game, _, secret = await create_game(FakeSession(), FakeGame, "My Game")

    assert game.api_secret_hash == hash_value(secret)
    assert game.api_secret_hash != secret
