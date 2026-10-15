import json
from unittest.mock import patch, MagicMock
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.models import User, ResumeAnalysisRecord, RoadmapRecord
from app.db.session import init_db, get_db
from app.auth.security import get_password_hash, create_access_token


@pytest.fixture
def test_engine():
    """
    Creates an isolated in-memory SQLite database with StaticPool and foreign keys.
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
    """Provides a database session for test verification."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_engine):
    """
    FastAPI TestClient with overridden get_db pointing to isolated test DB.
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


@pytest.fixture
def user_tokens(client):
    """
    Creates two distinct users (User A and User B) and returns their emails and auth tokens.
    """
    # User A
    res_a = client.post("/api/auth/register", json={
        "email": "user_a@example.com",
        "password": "PasswordA123!",
        "fullName": "Alice Candidate",
        "targetRole": "Frontend Architect"
    })
    token_a = res_a.json()["accessToken"]

    # User B
    res_b = client.post("/api/auth/register", json={
        "email": "user_b@example.com",
        "password": "PasswordB123!",
        "fullName": "Bob Returnee",
        "targetRole": "DevOps Lead"
    })
    token_b = res_b.json()["accessToken"]

    return {
        "user_a": {"token": token_a, "email": "user_a@example.com"},
        "user_b": {"token": token_b, "email": "user_b@example.com"},
    }


SAMPLE_ROADMAP = {
    "targetRole": "Product Operations & Strategy Lead",
    "durationWeeks": 4,
    "personalizedSummary": "Focused 4-week returnship preparation plan.",
    "weeks": [
        {
            "weekNumber": 1,
            "title": "Foundation & Core Alignment",
            "theme": "Skill Alignment",
            "weeklyGoal": "Master product operations workflows",
            "commitment": "6 hours",
            "topics": ["Agile", "PRD Writing"],
            "tasks": [
                {"id": "w1-t1", "text": "Draft initial one-page PRD spec", "completed": False},
                {"id": "w1-t2", "text": "Complete Agile lifecycle review", "completed": False}
            ],
            "expectedDeliverable": "One-page PRD draft",
            "skillGapAddressed": "Modern agile cadence",
            "resources": []
        },
        {
            "weekNumber": 2,
            "title": "Stakeholder & Data Operations",
            "theme": "Data Metrics",
            "weeklyGoal": "Analyze metric dashboards",
            "commitment": "6 hours",
            "topics": ["SQL", "Metrics"],
            "tasks": [
                {"id": "w2-t1", "text": "Build KPI metrics dashboard", "completed": False}
            ],
            "expectedDeliverable": "KPI Dashboard artifact",
            "skillGapAddressed": "Data analysis",
            "resources": []
        }
    ]
}


# ============================================================================
# Candidate Analysis History Tests
# ============================================================================

def test_get_analyses_unauthenticated_rejected(client):
    """GET /api/candidate/analyses without token returns 401."""
    res = client.get("/api/candidate/analyses")
    assert res.status_code == 401


def test_get_analyses_empty_for_new_candidate(client, user_tokens):
    """New candidate with no saved analyses receives clean empty list."""
    token = user_tokens["user_a"]["token"]
    res = client.get("/api/candidate/analyses", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["totalCount"] == 0
    assert data["analyses"] == []


def test_analysis_persistence_and_retrieval(client, user_tokens, test_db):
    """
    When authenticated, creating a ResumeAnalysisRecord persists it in the database
    and GET /api/candidate/analyses retrieves it with structured data.
    """
    token_a = user_tokens["user_a"]["token"]

    # Directly insert an analysis record for User A
    user_a = test_db.query(User).filter(User.email == "user_a@example.com").first()
    analysis_record = ResumeAnalysisRecord(
        user_id=user_a.id,
        file_name="Alice_Resume_2026.pdf",
        file_size_bytes=102400,
        word_count=350,
        target_role="Frontend Architect",
        model_used="gemini-3.1-flash-lite-preview",
        structured_analysis={
            "resumeSummary": "Experienced frontend engineer returning after career break.",
            "verifiedSkills": [{"skill": "React", "evidenceCitation": "Built SPA dashboards"}],
            "skillGaps": [{"missingCompetency": "Next.js App Router", "severity": "Medium"}],
            "evidenceNotes": "Documented in PDF"
        }
    )
    test_db.add(analysis_record)
    test_db.commit()

    # Query analyses via API
    res = client.get("/api/candidate/analyses", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    data = res.json()
    assert data["totalCount"] == 1
    assert data["analyses"][0]["fileName"] == "Alice_Resume_2026.pdf"
    assert data["analyses"][0]["targetRole"] == "Frontend Architect"
    assert "structuredAnalysis" in data["analyses"][0]
    assert data["analyses"][0]["structuredAnalysis"]["resumeSummary"].startswith("Experienced frontend")


def test_cross_user_analysis_isolation(client, user_tokens, test_db):
    """User B cannot see User A's saved analyses."""
    user_a = test_db.query(User).filter(User.email == "user_a@example.com").first()
    analysis_a = ResumeAnalysisRecord(
        user_id=user_a.id,
        file_name="Alice_Secret_Resume.pdf",
        file_size_bytes=50000,
        word_count=200,
        target_role="Confidential Role",
        model_used="gemini-model",
        structured_analysis={"resumeSummary": "Alice private data"}
    )
    test_db.add(analysis_a)
    test_db.commit()

    # User B queries their own analyses
    token_b = user_tokens["user_b"]["token"]
    res_b = client.get("/api/candidate/analyses", headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 200
    assert res_b.json()["totalCount"] == 0
    assert res_b.json()["analyses"] == []


# ============================================================================
# Candidate Roadmap History & Progress Tests
# ============================================================================

def test_get_roadmap_unauthenticated_rejected(client):
    """GET /api/candidate/roadmap without token returns 401."""
    res = client.get("/api/candidate/roadmap")
    assert res.status_code == 401


def test_get_roadmap_empty_state_returns_clean_response(client, user_tokens):
    """Candidate without generated roadmap receives hasRoadmap=False and 200 OK."""
    token = user_tokens["user_a"]["token"]
    res = client.get("/api/candidate/roadmap", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["hasRoadmap"] is False
    assert data["roadmap"] is None
    assert data["tasksProgress"] == {}
    assert "No saved roadmap" in data["message"]


def test_roadmap_persistence_and_retrieval(client, user_tokens, test_db):
    """
    Candidate can retrieve their latest saved roadmap and initial 0% progress.
    """
    user_a = test_db.query(User).filter(User.email == "user_a@example.com").first()
    roadmap_rec = RoadmapRecord(
        user_id=user_a.id,
        target_role="Product Operations & Strategy Lead",
        duration_weeks=4,
        model_used="gemini-3.1-flash-lite-preview",
        is_rag_used=True,
        rag_source_count=3,
        structured_roadmap=SAMPLE_ROADMAP,
        tasks_progress={"w1-t1": False, "w1-t2": False, "w2-t1": False}
    )
    test_db.add(roadmap_rec)
    test_db.commit()

    token_a = user_tokens["user_a"]["token"]
    res = client.get("/api/candidate/roadmap", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    data = res.json()
    assert data["hasRoadmap"] is True
    assert data["targetRole"] == "Product Operations & Strategy Lead"
    assert data["durationWeeks"] == 4
    assert data["isRagUsed"] is True
    assert data["ragSourceCount"] == 3
    assert data["totalTasksCount"] == 3
    assert data["completedCount"] == 0
    assert data["completionPercentage"] == 0.0


def test_patch_progress_valid_task_updates(client, user_tokens, test_db):
    """
    PATCH /api/candidate/roadmap/progress updates task completion and recalculates metrics.
    """
    user_a = test_db.query(User).filter(User.email == "user_a@example.com").first()
    roadmap_rec = RoadmapRecord(
        user_id=user_a.id,
        target_role="Product Operations & Strategy Lead",
        duration_weeks=4,
        structured_roadmap=SAMPLE_ROADMAP,
        tasks_progress={"w1-t1": False, "w1-t2": False, "w2-t1": False}
    )
    test_db.add(roadmap_rec)
    test_db.commit()

    token_a = user_tokens["user_a"]["token"]

    # 1. Check w1-t1 as True
    patch_res = client.patch(
        "/api/candidate/roadmap/progress",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"taskId": "w1-t1", "completed": True}
    )
    assert patch_res.status_code == 200
    pdata = patch_res.json()
    assert pdata["success"] is True
    assert pdata["tasksProgress"]["w1-t1"] is True
    assert pdata["completedCount"] == 1
    assert pdata["totalTasksCount"] == 3
    assert pdata["completionPercentage"] == 33.3

    # 2. Check w2-t1 as True (now 2 out of 3 = 66.7%)
    patch_res2 = client.patch(
        "/api/candidate/roadmap/progress",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"taskId": "w2-t1", "completed": True}
    )
    assert patch_res2.status_code == 200
    pdata2 = patch_res2.json()
    assert pdata2["completedCount"] == 2
    assert pdata2["completionPercentage"] == 66.7

    # 3. Uncheck w1-t1 (now 1 out of 3 = 33.3%)
    patch_res3 = client.patch(
        "/api/candidate/roadmap/progress",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"taskId": "w1-t1", "completed": False}
    )
    assert patch_res3.status_code == 200
    assert patch_res3.json()["tasksProgress"]["w1-t1"] is False
    assert patch_res3.json()["completedCount"] == 1


def test_patch_progress_batch_map_update(client, user_tokens, test_db):
    """PATCH /api/candidate/roadmap/progress supports batch tasksProgress map."""
    user_a = test_db.query(User).filter(User.email == "user_a@example.com").first()
    roadmap_rec = RoadmapRecord(
        user_id=user_a.id,
        target_role="Product Operations & Strategy Lead",
        duration_weeks=4,
        structured_roadmap=SAMPLE_ROADMAP,
        tasks_progress={}
    )
    test_db.add(roadmap_rec)
    test_db.commit()

    token_a = user_tokens["user_a"]["token"]
    patch_res = client.patch(
        "/api/candidate/roadmap/progress",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"tasksProgress": {"w1-t1": True, "w1-t2": True, "w2-t1": True}}
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["completedCount"] == 3
    assert data["completionPercentage"] == 100.0


def test_patch_progress_invalid_task_id_rejected(client, user_tokens, test_db):
    """
    Submitting an arbitrary, hallucinated or forged task ID must be rejected with 400 Bad Request.
    """
    user_a = test_db.query(User).filter(User.email == "user_a@example.com").first()
    roadmap_rec = RoadmapRecord(
        user_id=user_a.id,
        target_role="Product Operations & Strategy Lead",
        duration_weeks=4,
        structured_roadmap=SAMPLE_ROADMAP,
        tasks_progress={}
    )
    test_db.add(roadmap_rec)
    test_db.commit()

    token_a = user_tokens["user_a"]["token"]

    # Unknown task ID
    res = client.patch(
        "/api/candidate/roadmap/progress",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"taskId": "malicious_fake_task_999", "completed": True}
    )
    assert res.status_code == 400
    assert "Invalid task ID" in res.json()["detail"]


def test_patch_progress_unauthorized_cross_user_rejected(client, user_tokens, test_db):
    """
    User B cannot update User A's roadmap progress by passing User A's roadmapId.
    """
    user_a = test_db.query(User).filter(User.email == "user_a@example.com").first()
    roadmap_a = RoadmapRecord(
        user_id=user_a.id,
        target_role="Product Operations & Strategy Lead",
        duration_weeks=4,
        structured_roadmap=SAMPLE_ROADMAP,
        tasks_progress={}
    )
    test_db.add(roadmap_a)
    test_db.commit()

    token_b = user_tokens["user_b"]["token"]
    # User B attempts to patch User A's roadmap ID
    res = client.patch(
        "/api/candidate/roadmap/progress",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"roadmapId": roadmap_a.id, "taskId": "w1-t1", "completed": True}
    )
    # Must return 404 because query is scoped to user_b.id
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# ============================================================================
# Endpoint Integration Tests: /api/resume/analyze & /api/roadmap/generate
# ============================================================================

def test_analyze_resume_endpoint_persists_when_authenticated(client, user_tokens, monkeypatch, test_db):
    """POST /api/resume/analyze with Bearer token persists record to database."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")
    token_a = user_tokens["user_a"]["token"]

    mock_analysis_data = {
        "resumeSummary": "5 years experienced analyst.",
        "extractedExperience": [],
        "extractedEducation": [],
        "verifiedSkills": [{"name": "SQL", "category": "Tech", "evidence": "Used SQL"}],
        "transferableStrengths": [{"title": "Agility", "description": "Quick learner", "sourceOfEvidence": "Projects"}],
        "targetRoleRequirements": [],
        "skillGaps": [],
        "suggestedNextSteps": [],
        "evidenceNotes": "Documented in resume"
    }
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(mock_analysis_data)
    mock_resp.parsed = None

    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.return_value = mock_resp

        payload = {
            "resumeText": "Experienced professional with background in SQL and data analytics.",
            "preferences": {
                "targetRole": "Frontend Architect",
                "previousRole": "Analyst",
            },
            "fileName": "MyResume.pdf"
        }

        res = client.post("/api/resume/analyze", headers={"Authorization": f"Bearer {token_a}"}, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["isPersisted"] is True
        assert data["recordId"] is not None

        # Verify database record
        user_a = test_db.query(User).filter(User.email == "user_a@example.com").first()
        rec = test_db.query(ResumeAnalysisRecord).filter(ResumeAnalysisRecord.id == data["recordId"]).first()
        assert rec is not None
        assert rec.user_id == user_a.id
        assert rec.file_name == "MyResume.pdf"


def test_analyze_resume_endpoint_unauthenticated_does_not_persist(client, monkeypatch, test_db):
    """POST /api/resume/analyze without Bearer token does not persist to database."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")

    mock_analysis_data = {
        "resumeSummary": "Guest candidate summary.",
        "extractedExperience": [],
        "extractedEducation": [],
        "verifiedSkills": [],
        "transferableStrengths": [],
        "targetRoleRequirements": [],
        "skillGaps": [],
        "suggestedNextSteps": [],
        "evidenceNotes": "Guest mode"
    }
    mock_resp = MagicMock()
    mock_resp.text = json.dumps(mock_analysis_data)
    mock_resp.parsed = None

    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.return_value = mock_resp

        payload = {
            "resumeText": "Guest user resume text with sufficient length for validation testing.",
            "preferences": {"targetRole": "Guest Role"},
        }

        count_before = test_db.query(ResumeAnalysisRecord).count()
        res = client.post("/api/resume/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["isPersisted"] is False
        assert data["recordId"] is None

        count_after = test_db.query(ResumeAnalysisRecord).count()
        assert count_after == count_before


def test_generate_roadmap_endpoint_persists_when_authenticated(client, user_tokens, monkeypatch, test_db):
    """POST /api/roadmap/generate with Bearer token persists record and initializes tasks."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-key")
    token_a = user_tokens["user_a"]["token"]

    mock_resp = MagicMock()
    mock_resp.text = json.dumps(SAMPLE_ROADMAP)
    mock_resp.parsed = None

    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.return_value = mock_resp

        payload = {
            "targetRole": "Product Operations & Strategy Lead",
            "durationWeeks": 4,
            "verifiedSkills": ["Agile"],
            "skillGaps": ["Metrics"]
        }

        res = client.post("/api/roadmap/generate", headers={"Authorization": f"Bearer {token_a}"}, json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["isPersisted"] is True
        assert data["recordId"] is not None

        # Verify DB record and tasks_progress initialization
        rec = test_db.query(RoadmapRecord).filter(RoadmapRecord.id == data["recordId"]).first()
        assert rec is not None
        assert "w1-t1" in rec.tasks_progress
        assert rec.tasks_progress["w1-t1"] is False

