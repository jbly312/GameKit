import secrets
import hashlib

def generate_raw_token() -> str:
    return secrets.token_urlsafe(32)

def hash_value(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()