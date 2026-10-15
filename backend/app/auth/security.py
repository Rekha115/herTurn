import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt

logger = logging.getLogger("herturn.auth.security")

DEFAULT_DEV_SECRET = "herturn-dev-secret-key-change-in-production-38f72a91b"
ALGORITHM = "HS256"
DEFAULT_EXPIRE_MINUTES = 1440  # 24 hours


def get_jwt_secret() -> str:
    """
    Retrieves the JWT signing secret key from the environment.
    Strictly forbids default development secrets in production mode.
    """
    secret = os.getenv("JWT_SECRET_KEY")
    environment = (os.getenv("ENVIRONMENT") or "development").strip().lower()

    if environment == "production":
        if not secret or secret == DEFAULT_DEV_SECRET or len(secret) < 32:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: A strong JWT_SECRET_KEY (at least 32 characters) "
                "must be configured in production environment."
            )
        return secret

    # Development or testing fallback
    if not secret:
        logger.warning(
            "JWT_SECRET_KEY is not set in environment. Using development secret. "
            "Set JWT_SECRET_KEY in backend/.env for production."
        )
        return DEFAULT_DEV_SECRET

    return secret


def get_token_expire_minutes() -> int:
    """Retrieves access token expiration time in minutes from environment."""
    try:
        return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(DEFAULT_EXPIRE_MINUTES)))
    except (ValueError, TypeError):
        return DEFAULT_EXPIRE_MINUTES


def get_password_hash(password: str) -> str:
    """
    Hashes a plaintext password using bcrypt with standard salt rounds.
    Never returns plaintext or weak hashes.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.
    Safely returns False on malformed hashes or mismatch.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a signed JWT access token.
    'subject' (sub) represents the user's unique identifier.
    """
    secret = get_jwt_secret()
    expire_minutes = get_token_expire_minutes()
    now_utc = datetime.now(timezone.utc)
    expire_utc = now_utc + (expires_delta or timedelta(minutes=expire_minutes))

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now_utc,
        "exp": expire_utc,
    }

    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token's signature, format, and expiration.
    Raises jwt.ExpiredSignatureError, jwt.InvalidTokenError on failure.
    """
    secret = get_jwt_secret()
    return jwt.decode(
        token,
        secret,
        algorithms=[ALGORITHM],
        options={"require": ["exp", "iat", "sub"]}
    )
