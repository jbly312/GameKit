"""Shared infrastructure for GameKit services.

What belongs here: things two services provably need in the same shape —
token hashing, the error envelope, engine and session construction, the game
identity. What does not: anything a single service happens to want, and
`Base` (see `database.py` for why).
"""
