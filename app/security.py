import hashlib
import secrets


def generate_api_key() -> str:
    """Случайный ключ, который увидит только владелец сенсора."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """SHA-256 хеш: 64 символа, именно столько у нас в столбце api_key_hash."""
    return hashlib.sha256(api_key.encode()).hexdigest()