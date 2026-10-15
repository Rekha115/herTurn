import os
import pytest
from datetime import timedelta
import jwt
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.models import User, CandidateProfile
from app.db.session import init_db, get_db
from app.auth.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    get_jwt_secret,
    DEFAULT_DEV_SECRET,
    ALGORITHM,
)


from sqlalchemy.pool import StaticPool

@pytest.fixture
def test_engine():
    """
    Creates an isolated in-memory SQLite database with StaticPool and foreign keys.
    StaticPool ensures worker threads in FastAPI share the exact same in-memory DB.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    init_db(target_engine=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_db(test_engine):
    """Provides a database session for test setup and verification."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine):
    """
    FastAPI TestClient with overridden get_db dependency pointing to the isolated test database.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ============================================================================
# Unit Tests: Password Hashing & Security Utilities
# ============================================================================

def test_password_hashing_and_verification():
    """Verify that bcrypt hashes passwords securely and verifies them timing-safely."""
    plain = "SuperSecretPassword123!"
    hashed = get_password_hash(plain)

    # Must be bcrypt hash format ($2b$...)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert hashed != plain

    # Successful verification
    assert verify_password(plain, hashed) is True

    # Incorrect password fails
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(plain, "") is False
    assert verify_password(plain, "corrupted_hash") is False


def test_password_hash_empty_raises_error():
    """Empty passwords must not be hashed."""
    with pytest.raises(ValueError):
        get_password_hash("")


def test_jwt_creation_and_decoding():
    """Verify JWT token issuance and successful payload decoding."""
    token = create_access_token(subject="42", extra_claims={"email": "priya@example.com"})
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["email"] == "priya@example.com"
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expired_token_raises_error():
    """Expired tokens must raise jwt.ExpiredSignatureError."""
    expired_token = create_access_token(
        subject="42",
        expires_delta=timedelta(seconds=-10)
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_jwt_invalid_and_malformed_tokens():
    """Malformed or invalidly signed tokens must raise jwt.InvalidTokenError."""
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("this.is.a.completely.malformed.token")

    # Tampered token with wrong secret
    tampered_token = jwt.encode(
        {"sub": "42", "exp": 9999999999},
        "completely_different_signing_secret_key_12345",
        algorithm=ALGORITHM
    )
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered_token)


def test_production_secret_enforcement(monkeypatch):
    """Production mode must reject default dev secret or short secrets."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc_info:
        get_jwt_secret()
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(exc_info.value)

    # Rejects short secret in production
    monkeypatch.setenv("JWT_SECRET_KEY", "too_short")
    with pytest.raises(RuntimeError):
        get_jwt_secret()

    # Accepts strong secret (>= 32 chars) in production
    strong_secret = "a_very_strong_production_secret_key_with_sufficient_entropy_12345"
    monkeypatch.setenv("JWT_SECRET_KEY", strong_secret)
    assert get_jwt_secret() == strong_secret


# ============================================================================
# API Tests: Registration Endpoint (POST /api/auth/register)
# ============================================================================

def test_register_success_and_candidate_profile_creation(client, test_db):
    """Verify successful user registration, candidate profile auto-creation, and token response."""
    payload = {
        "email": "priya.sharma@example.com",
        "password": "SecurePassword123!",
        "fullName": "Priya Sharma",
        "targetRole": "AI & Engineering Lead"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert "accessToken" in data
    assert data["tokenType"] == "Bearer"
    assert data["expiresInMinutes"] > 0
    assert data["user"]["email"] == "priya.sharma@example.com"
    assert data["user"]["fullName"] == "Priya Sharma"
    assert data["user"]["candidateProfile"]["targetRole"] == "AI & Engineering Lead"

    # Verify persistence in database
    db_user = test_db.query(User).filter(User.email == "priya.sharma@example.com").first()
    assert db_user is not None
    assert db_user.full_name == "Priya Sharma"
    assert db_user.hashed_password != payload["password"]
    assert verify_password(payload["password"], db_user.hashed_password) is True

    # Verify candidate profile relationship
    assert db_user.candidate_profile is not None
    assert db_user.candidate_profile.target_role == "AI & Engineering Lead"


def test_register_duplicate_email_conflict(client):
    """Duplicate email registration must return 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
        "fullName": "Test User",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt to register identical email
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]

    # Attempt uppercase email (should be normalized)
    payload_upper = {
        "email": "DUPLICATE@EXAMPLE.COM",
        "password": "DifferentPassword123!",
    }
    res3 = client.post("/api/auth/register", json=payload_upper)
    assert res3.status_code == 409


def test_register_validation_errors(client):
    """Pydantic validation must reject invalid emails and short passwords."""
    # Invalid email
    res_bad_email = client.post("/api/auth/register", json={
        "email": "not-a-valid-email",
        "password": "ValidPassword123!"
    })
    assert res_bad_email.status_code == 422

    # Password too short (< 8 chars)
    res_short_pw = client.post("/api/auth/register", json={
        "email": "short@example.com",
        "password": "short"
    })
    assert res_short_pw.status_code == 422


# ============================================================================
# API Tests: Login Endpoint (POST /api/auth/login)
# ============================================================================

def test_login_success(client):
    """Verify that an existing user can log in with valid credentials."""
    # Register first
    client.post("/api/auth/register", json={
        "email": "ananya@example.com",
        "password": "MySecretPassword123!",
        "fullName": "Ananya Roy"
    })

    # Log in
    login_res = client.post("/api/auth/login", json={
        "email": "ananya@example.com",
        "password": "MySecretPassword123!"
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "accessToken" in data
    assert data["tokenType"] == "Bearer"
    assert data["user"]["email"] == "ananya@example.com"
    assert data["user"]["fullName"] == "Ananya Roy"


def test_login_invalid_password(client):
    """Login with wrong password must return 401 Unauthorized."""
    client.post("/api/auth/register", json={
        "email": "user@example.com",
        "password": "CorrectPassword123!"
    })

    res = client.post("/api/auth/login", json={
        "email": "user@example.com",
        "password": "IncorrectPassword999!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_login_nonexistent_user(client):
    """Login with unknown email must return 401 Unauthorized."""
    res = client.post("/api/auth/login", json={
        "email": "unknown@example.com",
        "password": "SomePassword123!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]


def test_login_deactivated_user(client, test_db):
    """Deactivated user cannot log in and receives 403 Forbidden."""
    client.post("/api/auth/register", json={
        "email": "deactivated@example.com",
        "password": "ValidPassword123!"
    })

    # Deactivate user
    user = test_db.query(User).filter(User.email == "deactivated@example.com").first()
    user.is_active = False
    test_db.commit()

    res = client.post("/api/auth/login", json={
        "email": "deactivated@example.com",
        "password": "ValidPassword123!"
    })
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"].lower()


# ============================================================================
# API Tests: Current User Endpoint (GET /api/auth/me)
# ============================================================================

def test_get_me_with_valid_token(client):
    """GET /api/auth/me returns the authenticated user's profile."""
    reg_res = client.post("/api/auth/register", json={
        "email": "me_test@example.com",
        "password": "MyPassword123!",
        "fullName": "Me Test",
        "targetRole": "Senior Frontend Engineer"
    })
    token = reg_res.json()["accessToken"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_info = res.json()
    assert user_info["email"] == "me_test@example.com"
    assert user_info["fullName"] == "Me Test"
    assert user_info["candidateProfile"]["targetRole"] == "Senior Frontend Engineer"


def test_get_me_without_token(client):
    """GET /api/auth/me without Authorization header returns 401."""
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert "Authentication credentials were not provided" in res.json()["detail"]


def test_get_me_with_expired_token(client):
    """GET /api/auth/me with an expired token returns 401."""
    expired_token = create_access_token(
        subject="1",
        expires_delta=timedelta(seconds=-10)
    )
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_get_me_with_malformed_token(client):
    """GET /api/auth/me with malformed token returns 401."""
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401
    assert "Invalid or malformed" in res.json()["detail"]


def test_get_me_inactive_user(client, test_db):
    """GET /api/auth/me with active token but deactivated user returns 403."""
    reg_res = client.post("/api/auth/register", json={
        "email": "inactive_token@example.com",
        "password": "MyPassword123!"
    })
    token = reg_res.json()["accessToken"]

    # Deactivate user
    user = test_db.query(User).filter(User.email == "inactive_token@example.com").first()
    user.is_active = False
    test_db.commit()

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"].lower()
