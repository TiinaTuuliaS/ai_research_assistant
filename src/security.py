"""Password hashing and revocable, opaque browser sessions."""
import hashlib
import hmac
import re
import secrets

PASSWORD_ITERATIONS = 600_000
HASH_PATTERN = re.compile(r"pbkdf2_sha256\$600000\$[0-9a-f]{32}\$[0-9a-f]{64}\Z")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PASSWORD_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def is_password_hash(value: str | None) -> bool:
    return bool(value and HASH_PATTERN.fullmatch(value))


def verify_password(password: str, encoded: str) -> bool:
    if not is_password_hash(encoded):
        return False
    _, iterations, salt, expected = encoded.split("$")
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
    ).hex()
    return hmac.compare_digest(actual, expected)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
