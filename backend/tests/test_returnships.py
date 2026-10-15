"""
Test suite for HerTurn Returnship Catalog, Matching Engine, and Persistent Bookmarking.
Verifies explainable match scores, skills overlap, unknown eligibility handling,
filtering, duplicate prevention, authentication, and cross-user isolation.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.models import User, CandidateProfile, ResumeAnalysisRecord, SavedReturnship
from app.db.session import init_db, get_db
from app.auth.security import get_password_hash, create_access_token


@pytest.fixture
def test_engine():
    """Isolated in-memory SQLite database for test suite."""
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

    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine):
    """Session fixture for isolated test database."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        expire_on_commit=False,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers_user1(db_session):
    """Generates an authenticated user and valid Bearer auth headers."""
    user = User(
        email="candidate1@herturn.test",
        hashed_password=get_password_hash("SecretPass123!"),
        full_name="Pooja Sharma",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    profile = CandidateProfile(
        user_id=user.id,
        target_role="Cloud Operations & Technical Program Manager",
        total_experience="5 years",
        break_duration="3 years",
        work_mode="Hybrid",
    )
    db_session.add(profile)
    db_session.commit()

    token = create_access_token(subject=str(user.id), extra_claims={"email": user.email})
    return {"Authorization": f"Bearer {token}"}, user


@pytest.fixture
def auth_headers_user2(db_session):
    """Generates a second distinct authenticated user for isolation testing."""
    user = User(
        email="candidate2@herturn.test",
        hashed_password=get_password_hash("SecretPass456!"),
        full_name="Anita Deshmukh",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(subject=str(user.id), extra_claims={"email": user.email})
    return {"Authorization": f"Bearer {token}"}, user


# ============================================================================
# 1. CATALOG LISTING & FILTERING TESTS
# ============================================================================

def test_list_returnships_all(client):
    """Verifies that the catalog endpoint returns all opportunities with breakdown counts and categories."""
    res = client.get("/api/returnships")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total"] == len(data["items"])
    assert data["total"] >= 7
    assert data["verifiedCount"] >= 5
    assert data["sampleCount"] >= 2
    assert len(data["allSkills"]) > 0
    assert len(data.get("categories", [])) >= 4


def test_list_returnships_filtering_work_arrangement(client):
    """Tests filtering by work arrangement (Remote vs Hybrid vs On-site)."""
    # Remote
    res_remote = client.get("/api/returnships?workArrangement=Remote")
    assert res_remote.status_code == 200
    items_remote = res_remote.json()["items"]
    assert len(items_remote) >= 2
    for item in items_remote:
        assert item["workArrangement"] == "Remote"

    # Hybrid
    res_hybrid = client.get("/api/returnships?workArrangement=Hybrid")
    assert res_hybrid.status_code == 200
    items_hybrid = res_hybrid.json()["items"]
    assert len(items_hybrid) >= 4
    for item in items_hybrid:
        assert item["workArrangement"] == "Hybrid"

    # On-site
    res_onsite = client.get("/api/returnships?workArrangement=On-site")
    assert res_onsite.status_code == 200
    items_onsite = res_onsite.json()["items"]
    assert len(items_onsite) >= 1
    assert any("Aether" in it["company"] for it in items_onsite)


def test_list_returnships_filtering_type(client):
    """Tests filtering verified cohort programs vs sample listings."""
    res_ver = client.get("/api/returnships?type=verified")
    assert res_ver.status_code == 200
    assert res_ver.json()["total"] >= 5
    for item in res_ver.json()["items"]:
        assert item["type"] == "verified"
        assert item["sourceUrl"] is not None

    res_sam = client.get("/api/returnships?type=sample")
    assert res_sam.status_code == 200
    assert res_sam.json()["total"] >= 2
    for item in res_sam.json()["items"]:
        assert item["type"] == "sample"
        assert item["isLive"] is False


def test_list_returnships_filtering_category(client):
    """Tests filtering returnships by role category (e.g. Design & UX)."""
    res = client.get("/api/returnships?category=Design%20%26%20UX")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 3
    for it in items:
        assert it["roleCategory"] == "Design & UX"


def test_list_returnships_filtering_skill(client):
    """Tests filtering opportunities by specific skill."""
    res = client.get("/api/returnships?skill=Agile")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 2
    for item in items:
        assert any("agile" in s.lower() for s in item["skills"])


def test_list_returnships_search_query(client):
    """Tests free text search across role, company, location, and skills."""
    # Search by company
    res_comp = client.get("/api/returnships?search=Amazon")
    assert res_comp.status_code == 200
    assert any("Amazon" in item["company"] for item in res_comp.json()["items"])

    # Search by location
    res_loc = client.get("/api/returnships?search=Pune")
    assert res_loc.status_code == 200
    assert any("Dell" in item["company"] for item in res_loc.json()["items"])

    # Search by non-matching query
    res_none = client.get("/api/returnships?search=NonExistentCompanyXyz")
    assert res_none.status_code == 200
    assert res_none.json()["total"] == 0


# ============================================================================
# 2. MATCHING ENGINE & EXPLAINABILITY TESTS
# ============================================================================

def test_matching_high_skills_overlap(client):
    """Verifies that high skill overlap and role match produce high score and matched skills."""
    payload = {
        "targetRole": "Cloud Operations & Technical Program Manager",
        "verifiedSkills": ["Agile", "Cloud Fundamentals", "Technical Program Management"],
        "experienceYears": 5,
        "breakDuration": "2.5 years",
        "preferredWorkMode": "Hybrid",
        "location": "Bengaluru",
    }
    res = client.post("/api/returnships/match", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["total"] == len(data["items"])

    top_match = data["items"][0]
    # Amazon AWS Returnship should rank high
    assert top_match["id"] == "ret-1"
    assert top_match["matchScore"] >= 75
    assert "Agile" in top_match["matchedSkills"]
    assert "Cloud Fundamentals" in top_match["matchedSkills"]
    assert "Technical Program Management" in top_match["matchedSkills"]
    assert "Cross-Functional Ops" in top_match["skillsToBridge"]
    assert top_match["eligibilityStatus"] == "Eligible"
    assert "Matched 3 of 4 core skills" in top_match["matchRationale"]
    assert "recommendationNotice" in data


def test_matching_ui_ux_role_relevance(client):
    """Verifies that a UI/UX candidate sees relevant design returnships ranked at the top."""
    payload = {
        "targetRole": "UI/UX Designer",
        "verifiedSkills": ["Figma", "User Research", "Wireframing", "Design Systems"],
        "experienceYears": 4,
        "breakDuration": "2 years",
        "preferredWorkMode": "Hybrid",
    }
    res = client.post("/api/returnships/match", json=payload)
    assert res.status_code == 200
    data = res.json()
    items = data["items"]
    top_item = items[0]
    assert top_item["roleCategory"] == "Design & UX"
    assert top_item["matchScore"] >= 80
    assert any(s in top_item["matchedSkills"] for s in ["Figma", "Design Systems", "User Research"])
    # Check that top items are Design & UX roles
    top_categories = [it["roleCategory"] for it in items[:3]]
    assert "Design & UX" in top_categories


def test_matching_career_break_not_penalized(client):
    """Verifies that career breaks are never penalized in match score calculation."""
    payload_short_break = {
        "targetRole": "Business Architecture Associate",
        "verifiedSkills": ["Business Architecture", "SQL / Data Modeling"],
        "experienceYears": 6,
        "breakDuration": "2 years",
        "preferredWorkMode": "Hybrid",
    }
    payload_long_break = {
        "targetRole": "Business Architecture Associate",
        "verifiedSkills": ["Business Architecture", "SQL / Data Modeling"],
        "experienceYears": 6,
        "breakDuration": "6 years",  # Long career break
        "preferredWorkMode": "Hybrid",
    }

    res1 = client.post("/api/returnships/match", json=payload_short_break)
    res2 = client.post("/api/returnships/match", json=payload_long_break)

    score1 = res1.json()["items"][0]["matchScore"]
    score2 = res2.json()["items"][0]["matchScore"]

    # Long career break should have equal or greater match score (never penalized)
    assert score2 >= score1


def test_matching_unknown_eligibility_when_break_duration_missing(client):
    """Factual eligibility: missing break duration must be treated as unknown, not satisfied."""
    payload = {
        "targetRole": "Cloud Operations",
        "verifiedSkills": ["Cloud Fundamentals", "Agile"],
        "experienceYears": 5,
        "breakDuration": None,  # Unknown break duration
    }
    res = client.post("/api/returnships/match", json=payload)
    assert res.status_code == 200
    top_match = res.json()["items"][0]
    # Must flag that break duration is unknown rather than claiming eligibility
    assert "Review Requirements" in top_match["eligibilityStatus"]
    assert "break duration unknown" in top_match["eligibilityStatus"]


def test_matching_unknown_eligibility_when_experience_unverified(client):
    """Factual eligibility: missing prior experience must be treated as unverified."""
    payload = {
        "targetRole": "Cloud Operations",
        "verifiedSkills": ["Cloud Fundamentals", "Agile"],
        "experienceYears": None,  # Experience unverified
        "breakDuration": "3 years",
    }
    res = client.post("/api/returnships/match", json=payload)
    assert res.status_code == 200
    top_match = res.json()["items"][0]
    assert "Review Requirements" in top_match["eligibilityStatus"]
    assert "experience unverified" in top_match["eligibilityStatus"]


def test_matching_sample_opportunity_status(client):
    """Sample demonstration listings must explicitly indicate sample status."""
    payload = {
        "targetRole": "Product Manager",
        "verifiedSkills": ["Product Discovery", "Mixpanel"],
        "experienceYears": 3,
        "breakDuration": "2 years",
    }
    res = client.post("/api/returnships/match", json=payload)
    assert res.status_code == 200
    sample_item = next(it for it in res.json()["items"] if it["type"] == "sample")
    assert sample_item["eligibilityStatus"] == "Sample Demonstration Listing"


def test_matching_authenticated_auto_fallback_from_db(client, auth_headers_user1, db_session):
    """When authenticated, matching automatically pulls profile attributes if payload is empty."""
    headers, user = auth_headers_user1

    # Add a resume analysis with verified skills for this user
    analysis = ResumeAnalysisRecord(
        user_id=user.id,
        target_role="Cloud Operations & Technical Program Manager",
        structured_analysis={
            "verifiedSkills": [
                {"name": "Agile", "category": "Methodology"},
                {"name": "Cloud Fundamentals", "category": "Tech"},
            ]
        },
    )
    db_session.add(analysis)
    db_session.commit()

    # Call /match without specifying skills or targetRole
    res = client.post("/api/returnships/match", json={}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    summary = data["candidateProfileSummary"]
    assert summary["isAuthenticated"] is True
    assert summary["targetRole"] == "Cloud Operations & Technical Program Manager"
    assert summary["skillsCount"] == 2


# ============================================================================
# 3. BOOKMARKING & PERSISTENCE TESTS
# ============================================================================

def test_saved_returnships_unauthenticated_rejected(client):
    """Unauthenticated access to saved returnships must return 401."""
    res_get = client.get("/api/returnships/saved")
    assert res_get.status_code == 401

    res_post = client.post("/api/returnships/save/ret-1")
    assert res_post.status_code == 401

    res_del = client.delete("/api/returnships/save/ret-1")
    assert res_del.status_code == 401


def test_save_returnship_unknown_id_returns_404(client, auth_headers_user1):
    """Attempting to bookmark an opportunity that does not exist returns 404."""
    headers, _ = auth_headers_user1
    res = client.post("/api/returnships/save/non-existent-opportunity-id", headers=headers)
    assert res.status_code == 404
    assert "does not exist in catalog" in res.json()["detail"]


def test_save_list_and_remove_bookmarks(client, auth_headers_user1):
    """Full lifecycle: save opportunity, list bookmarks, delete bookmark."""
    headers, _ = auth_headers_user1

    # Initially 0 saved
    res_init = client.get("/api/returnships/saved", headers=headers)
    assert res_init.status_code == 200
    assert res_init.json()["count"] == 0

    # Save ret-1 (AWS)
    res_save1 = client.post("/api/returnships/save/ret-1", headers=headers)
    assert res_save1.status_code == 200
    assert res_save1.json()["saved"] is True

    # Save ret-3 (Intuit)
    res_save2 = client.post("/api/returnships/save/ret-3", headers=headers)
    assert res_save2.status_code == 200
    assert res_save2.json()["saved"] is True

    # List saved returnships
    res_list = client.get("/api/returnships/saved", headers=headers)
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["count"] == 2
    assert "ret-1" in data["savedIds"]
    assert "ret-3" in data["savedIds"]
    # Check attached opportunity details
    assert data["items"][0]["opportunity"]["company"] is not None

    # Idempotent re-save: saving ret-1 again does not duplicate
    res_resave = client.post("/api/returnships/save/ret-1", headers=headers)
    assert res_resave.status_code == 200
    assert res_resave.json()["saved"] is True

    # Check count is still 2
    res_check = client.get("/api/returnships/saved", headers=headers)
    assert res_check.json()["count"] == 2

    # Remove ret-1
    res_del = client.delete("/api/returnships/save/ret-1", headers=headers)
    assert res_del.status_code == 200
    assert res_del.json()["saved"] is False

    # Check remaining count is 1 (only ret-3)
    res_final = client.get("/api/returnships/saved", headers=headers)
    assert res_final.json()["count"] == 1
    assert res_final.json()["savedIds"] == ["ret-3"]


def test_cross_user_bookmark_isolation(client, auth_headers_user1, auth_headers_user2):
    """Verifies strict cross-user isolation: User A cannot see or delete User B's bookmarks."""
    headers1, user1 = auth_headers_user1
    headers2, user2 = auth_headers_user2

    # User 1 saves ret-1
    client.post("/api/returnships/save/ret-1", headers=headers1)

    # User 2 saves ret-2
    client.post("/api/returnships/save/ret-2", headers=headers2)

    # User 1 lists bookmarks -> sees only ret-1
    res1 = client.get("/api/returnships/saved", headers=headers1)
    assert res1.json()["count"] == 1
    assert res1.json()["savedIds"] == ["ret-1"]

    # User 2 lists bookmarks -> sees only ret-2
    res2 = client.get("/api/returnships/saved", headers=headers2)
    assert res2.json()["count"] == 1
    assert res2.json()["savedIds"] == ["ret-2"]

    # User 2 attempts to delete ret-1 (which belongs to User 1)
    res_del_cross = client.delete("/api/returnships/save/ret-1", headers=headers2)
    assert res_del_cross.status_code == 200
    assert res_del_cross.json()["saved"] is False
    assert "Bookmark not found" in res_del_cross.json()["message"]

    # User 1's bookmark for ret-1 remains completely intact
    res1_after = client.get("/api/returnships/saved", headers=headers1)
    assert res1_after.json()["count"] == 1
    assert res1_after.json()["savedIds"] == ["ret-1"]
