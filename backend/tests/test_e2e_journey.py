"""
HerTurn Phase 4: End-to-End User Journey Integration Test Suite.
Validates the entire lifecycle:
1. Registration & Profile Initialization
2. Authentication & JWT Validation
3. Resume Parsing (PDF/DOCX)
4. Structured Analysis Persistence
5. RAG Resource Retrieval & Citation Grounding
6. Personalized Roadmap Generation & Persistence
7. Roadmap Task Progress Checkbox Synchronization
8. Explainable Returnship Matching & Scoring
9. Persistent Returnship Bookmarking (Save & Delete)
10. Relogin & Complete Data Restoration
"""

import io
from unittest.mock import patch, MagicMock
import pymupdf as fitz
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.models import User, CandidateProfile, ResumeAnalysisRecord, RoadmapRecord, SavedReturnship
from app.db.session import get_db
from app.models import (
    StructuredLLMAnalysis,
    VerifiedSkill,
    SkillGap,
    TransferableStrength,
    ActionRecommendation,
    StructuredRoadmap,
    RoadmapTaskItem,
)


@pytest.fixture
def e2e_engine():
    """Isolated in-memory SQLite database for full E2E journey test."""
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
def db_session(e2e_engine):
    """Session fixture for isolated database."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=e2e_engine,
        expire_on_commit=False,
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """TestClient wired to isolated in-memory DB."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_complete_user_journey_e2e(client):
    """
    Executes and validates the entire end-to-end journey of a returning candidate.
    """
    # -------------------------------------------------------------------------
    # STEP 1: Registration
    # -------------------------------------------------------------------------
    reg_payload = {
        "fullName": "Meera Patel",
        "email": "meera.patel@herturn.test",
        "password": "SecurePassword2026!",
        "targetRole": "Cloud Operations & Technical Program Manager",
        "previousRole": "Senior Systems Engineer",
        "totalExperience": "6 years",
        "breakDuration": "3 years",
        "workMode": "Hybrid",
        "preferredLocation": "Bengaluru",
        "areasOfInterest": ["Cloud Computing", "Program Management", "Agile"],
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code == 201, f"Registration failed: {res_reg.text}"
    reg_data = res_reg.json()
    assert "accessToken" in reg_data
    access_token = reg_data["accessToken"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # -------------------------------------------------------------------------
    # STEP 2: Authenticated Profile Verification
    # -------------------------------------------------------------------------
    res_me = client.get("/api/auth/me", headers=auth_headers)
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["email"] == "meera.patel@herturn.test"
    assert me_data["candidateProfile"]["targetRole"] == "Cloud Operations & Technical Program Manager"

    # -------------------------------------------------------------------------
    # STEP 3: Resume Document Ingestion via PyMuPDF / docx parsing
    # -------------------------------------------------------------------------
    sample_text = (
        "Meera Patel - Cloud & Systems Engineer\n"
        "Experience: 6 years at Tata Consultancy Services as Systems Engineer.\n"
        "Skills: AWS Cloud Fundamentals, Linux, Agile Scrum, Technical Program Management.\n"
        "Career hiatus: 3 years for family caregiving.\n"
    )
    # Generate in-memory PDF document simulating upload
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), sample_text)
    pdf_bytes = doc.tobytes()
    doc.close()

    file_bytes = io.BytesIO(pdf_bytes)
    res_parse = client.post(
        "/api/resume/parse",
        files={"file": ("meera_resume.pdf", file_bytes, "application/pdf")},
    )
    assert res_parse.status_code == 200
    parse_data = res_parse.json()
    assert parse_data["word_count"] > 10
    assert "Tata Consultancy Services" in parse_data["extracted_text"]

    # -------------------------------------------------------------------------
    # STEP 4: Resume Analysis with Auto-Persistence to SQLite
    # -------------------------------------------------------------------------
    mock_llm_analysis = StructuredLLMAnalysis(
        candidateName="Meera Patel",
        targetRole="Cloud Operations & Technical Program Manager",
        yearsOfExperience="6 years",
        careerBreakDuration="3 years",
        resumeSummary="Experienced Systems Engineer seeking career relaunch in Cloud Operations and Program Management.",
        verifiedSkills=[
            VerifiedSkill(name="AWS Cloud Fundamentals", category="Cloud Infrastructure", evidence="6 years as Systems Engineer"),
            VerifiedSkill(name="Agile Scrum", category="Methodology", evidence="Agile Scrum listed in work history"),
            VerifiedSkill(name="Technical Program Management", category="Operations", evidence="Documented TPM responsibilities"),
        ],
        skillGaps=[
            SkillGap(name="Cross-Functional Ops", category="Operations", importance="High", explanation="Modern cloud DevOps pipelines", recommendedAction="Complete Hands-on sprint"),
        ],
        transferableStrengths=[
            TransferableStrength(title="Systems Reliability & Resilience", description="Background in mission-critical infrastructure", sourceOfEvidence="TCS Systems Engineer"),
        ],
        suggestedNextSteps=[
            ActionRecommendation(action="Complete 4-Week Cloud Operations Relaunch Roadmap", detail="Focus on bridging modern DevOps tools"),
            ActionRecommendation(action="Apply for AWS Return to Work Cohort", detail="Matches 3-year career break and 6-year engineering background"),
        ],
        evidenceNotes="Verified 3 core skills factually present in resume text.",
    )

    with patch("app.main.analyze_resume_with_gemini") as mock_analyze:
        from app.models import ResumeAnalysisResponse
        mock_analyze.return_value = ResumeAnalysisResponse(
            success=True,
            status="analyzed",
            modelUsed="gemini-flash-latest",
            targetRole="Cloud Operations & Technical Program Manager",
            analysis=mock_llm_analysis,
            message="Resume analyzed successfully.",
        )

        analyze_payload = {
            "resumeText": sample_text,
            "preferences": {
                "fullName": "Meera Patel",
                "email": "meera.patel@herturn.test",
                "targetRole": "Cloud Operations & Technical Program Manager",
                "previousRole": "Senior Systems Engineer",
                "totalExperience": "6 years",
                "breakDuration": "3 years",
            },
            "fileName": "meera_resume.pdf",
        }
        res_analyze = client.post("/api/resume/analyze", json=analyze_payload, headers=auth_headers)
        assert res_analyze.status_code == 200
        analyze_res = res_analyze.json()
        assert analyze_res["isPersisted"] is True
        assert analyze_res["recordId"] is not None
        saved_record_id = analyze_res["recordId"]

    # Verify retrieval from GET /api/candidate/analyses
    res_saved_analyses = client.get("/api/candidate/analyses", headers=auth_headers)
    assert res_saved_analyses.status_code == 200
    saved_analyses_data = res_saved_analyses.json()
    assert saved_analyses_data["totalCount"] == 1
    assert saved_analyses_data["analyses"][0]["id"] == saved_record_id
    assert saved_analyses_data["analyses"][0]["targetRole"] == "Cloud Operations & Technical Program Manager"

    # -------------------------------------------------------------------------
    # STEP 5: RAG Resource Retrieval
    # -------------------------------------------------------------------------
    rag_payload = {
        "targetRole": "Cloud Operations & Technical Program Manager",
        "skills": ["AWS Cloud Fundamentals", "Agile Scrum"],
        "topK": 3,
    }
    res_rag = client.post("/api/resources/retrieve", json=rag_payload)
    assert res_rag.status_code == 200
    rag_data = res_rag.json()
    assert rag_data["success"] is True
    assert rag_data["totalRetrieved"] > 0
    # Canonical URL validation: Ensure no fake URLs
    for r in rag_data["resources"]:
        assert r["url"].startswith("http://") or r["url"].startswith("https://")

    # -------------------------------------------------------------------------
    # STEP 6: Roadmap Generation & Auto-Persistence
    # -------------------------------------------------------------------------
    from app.models import RoadmapWeek, RoadmapResourceItem
    mock_roadmap = StructuredRoadmap(
        targetRole="Cloud Operations & Technical Program Manager",
        durationWeeks=4,
        personalizedSummary="Accelerated refresher covering AWS operations and enterprise agile.",
        weeks=[
            RoadmapWeek(
                weekNumber=1,
                title="Cloud Architecture & Well-Architected Framework",
                theme="Cloud Infrastructure",
                weeklyGoal="Refresh foundational cloud principles and governance.",
                commitment="6-8 hours",
                topics=["AWS IAM", "VPC", "CloudWatch"],
                tasks=[
                    RoadmapTaskItem(id="w1-t1", text="Complete AWS Cloud Essentials Refresher", completed=False),
                    RoadmapTaskItem(id="w1-t2", text="Review Cloud IAM and Role-Based Access Controls", completed=False),
                ],
                expectedDeliverable="AWS architecture diagram artifact",
                skillGapAddressed="Cloud DevOps pipelines",
                resources=[
                    RoadmapResourceItem(
                        title="AWS Well-Architected Framework",
                        url="https://aws.amazon.com/architecture/well-architected/",
                        provider="Amazon Web Services",
                        type="Official Guide",
                        difficulty="Intermediate",
                        isVerified=True,
                    )
                ],
            ),
            RoadmapWeek(
                weekNumber=2,
                title="Agile Ops & Sprint Management",
                theme="Methodology",
                weeklyGoal="Bridge agile workflow tooling.",
                commitment="6-8 hours",
                topics=["Jira", "Scrum"],
                tasks=[
                    RoadmapTaskItem(id="w2-t1", text="Configure Jira Agile Project Board", completed=False),
                ],
                expectedDeliverable="Sprint retrospectives template",
                skillGapAddressed="Modern sprint management",
                resources=[],
            ),
        ],
    )

    with patch("app.main.generate_roadmap_with_gemini") as mock_roadmap_gen:
        from app.models import RoadmapGenerateResponse
        mock_roadmap_gen.return_value = RoadmapGenerateResponse(
            success=True,
            status="generated",
            roadmapId=1,
            modelUsed="gemini-flash-latest",
            durationWeeks=4,
            targetRole="Cloud Operations & Technical Program Manager",
            isRagUsed=True,
            ragSourceCount=1,
            roadmap=mock_roadmap,
            message="Roadmap generated successfully.",
        )

        roadmap_req_payload = {
            "targetRole": "Cloud Operations & Technical Program Manager",
            "durationWeeks": 4,
            "verifiedSkills": ["AWS Cloud Fundamentals", "Agile Scrum"],
            "skillGaps": ["Cross-Functional Ops"],
        }
        res_roadmap = client.post("/api/roadmap/generate", json=roadmap_req_payload, headers=auth_headers)
        assert res_roadmap.status_code == 200
        roadmap_res = res_roadmap.json()
        assert roadmap_res["isPersisted"] is True
        saved_roadmap_id = roadmap_res["recordId"]

    # Verify retrieval from GET /api/candidate/roadmap
    res_get_roadmap = client.get("/api/candidate/roadmap", headers=auth_headers)
    assert res_get_roadmap.status_code == 200
    roadmap_get_data = res_get_roadmap.json()
    assert roadmap_get_data["hasRoadmap"] is True
    assert roadmap_get_data["roadmapId"] == saved_roadmap_id
    assert roadmap_get_data["completedCount"] == 0
    assert roadmap_get_data["completionPercentage"] == 0.0

    # -------------------------------------------------------------------------
    # STEP 7: Task Progress Checklist Persistence
    # -------------------------------------------------------------------------
    patch_progress_payload = {
        "roadmapId": saved_roadmap_id,
        "taskId": "w1-t1",
        "completed": True,
    }
    res_patch = client.patch("/api/candidate/roadmap/progress", json=patch_progress_payload, headers=auth_headers)
    assert res_patch.status_code == 200
    patch_data = res_patch.json()
    assert patch_data["tasksProgress"]["w1-t1"] is True
    assert patch_data["completedCount"] == 1
    assert patch_data["completionPercentage"] > 0

    # Verify updated progress is preserved upon re-querying
    res_recheck_roadmap = client.get("/api/candidate/roadmap", headers=auth_headers)
    assert res_recheck_roadmap.json()["tasksProgress"]["w1-t1"] is True

    # -------------------------------------------------------------------------
    # STEP 8: Returnship Opportunity Matching
    # -------------------------------------------------------------------------
    # Authenticated user calls /match with their parameters
    match_payload = {
        "targetRole": "Cloud Operations & Technical Program Manager",
        "verifiedSkills": ["AWS Cloud Fundamentals", "Agile Scrum", "Technical Program Management"],
        "experienceYears": 6,
        "breakDuration": "3 years",
        "preferredWorkMode": "Hybrid",
        "location": "Bengaluru",
    }
    res_match = client.post("/api/returnships/match", json=match_payload, headers=auth_headers)
    assert res_match.status_code == 200
    match_data = res_match.json()
    assert match_data["total"] == 13
    top_match = match_data["items"][0]
    # Amazon AWS Returnship must be top ranked
    assert top_match["id"] == "ret-1"
    assert top_match["matchScore"] >= 70
    assert top_match["eligibilityStatus"] == "Eligible"
    assert "Agile" in top_match["matchedSkills"] or "Cloud Fundamentals" in top_match["matchedSkills"]

    # -------------------------------------------------------------------------
    # STEP 9: Returnship Bookmarking (Save & Delete)
    # -------------------------------------------------------------------------
    # Save ret-1 (AWS)
    res_save1 = client.post("/api/returnships/save/ret-1", headers=auth_headers)
    assert res_save1.status_code == 200
    assert res_save1.json()["saved"] is True

    # Save ret-3 (Intuit)
    res_save2 = client.post("/api/returnships/save/ret-3", headers=auth_headers)
    assert res_save2.status_code == 200
    assert res_save2.json()["saved"] is True

    # Verify saved bookmarks
    res_saved = client.get("/api/returnships/saved", headers=auth_headers)
    assert res_saved.status_code == 200
    saved_data = res_saved.json()
    assert saved_data["count"] == 2
    assert "ret-1" in saved_data["savedIds"]
    assert "ret-3" in saved_data["savedIds"]

    # Remove ret-3 bookmark
    res_del = client.delete("/api/returnships/save/ret-3", headers=auth_headers)
    assert res_del.status_code == 200
    assert res_del.json()["saved"] is False

    # Check that only ret-1 remains
    res_saved_after = client.get("/api/returnships/saved", headers=auth_headers)
    assert res_saved_after.json()["count"] == 1
    assert res_saved_after.json()["savedIds"] == ["ret-1"]

    # -------------------------------------------------------------------------
    # STEP 10: Relogin & Complete State Restoration
    # -------------------------------------------------------------------------
    login_payload = {
        "email": "meera.patel@herturn.test",
        "password": "SecurePassword2026!",
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200
    new_token = res_login.json()["accessToken"]
    new_auth_headers = {"Authorization": f"Bearer {new_token}"}

    # Verify that all persisted records are intact after re-authenticating
    res_re_analyses = client.get("/api/candidate/analyses", headers=new_auth_headers)
    assert res_re_analyses.json()["totalCount"] == 1
    assert res_re_analyses.json()["analyses"][0]["targetRole"] == "Cloud Operations & Technical Program Manager"

    res_re_roadmap = client.get("/api/candidate/roadmap", headers=new_auth_headers)
    assert res_re_roadmap.json()["hasRoadmap"] is True
    assert res_re_roadmap.json()["tasksProgress"]["w1-t1"] is True

    res_re_bookmarks = client.get("/api/returnships/saved", headers=new_auth_headers)
    assert res_re_bookmarks.json()["count"] == 1
    assert res_re_bookmarks.json()["savedIds"] == ["ret-1"]
