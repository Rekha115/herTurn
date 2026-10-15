import os
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import StructuredLLMAnalysis

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Health check test
# ---------------------------------------------------------------------------
def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "HerTurn" in data["service"]


# ---------------------------------------------------------------------------
# 2. Request validation & input bounds tests
# ---------------------------------------------------------------------------
def test_analyze_empty_resume_text_rejected():
    payload = {
        "resumeText": "",
        "preferences": {
            "targetRole": "Product Manager"
        }
    }
    response = client.post("/api/resume/analyze", json=payload)
    assert response.status_code == 422  # Pydantic min_length validation failure


def test_analyze_too_short_resume_text_rejected():
    payload = {
        "resumeText": "Too short",
        "preferences": {
            "targetRole": "Product Manager"
        }
    }
    response = client.post("/api/resume/analyze", json=payload)
    assert response.status_code == 422 or response.status_code == 400


def test_analyze_missing_target_role_rejected():
    payload = {
        "resumeText": "This is a valid resume text with sufficient length for testing.",
        "preferences": {}
    }
    response = client.post("/api/resume/analyze", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 3. Missing API key handling test
# ---------------------------------------------------------------------------
def test_analyze_missing_api_key_returns_503(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    payload = {
        "resumeText": "Senior Analyst with 5 years experience in SQL, Python, stakeholder presentation.",
        "preferences": {
            "targetRole": "Product Operations Lead",
            "previousRole": "Senior Business Analyst",
            "breakDuration": "3 years"
        }
    }
    response = client.post("/api/resume/analyze", json=payload)
    assert response.status_code == 503
    assert "Gemini API key is not configured" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 4. Mocked LLM response validation test (No API key required)
# ---------------------------------------------------------------------------
def test_analyze_with_mocked_gemini_success(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")

    mock_analysis_data = {
        "resumeSummary": "5 years experienced analyst with strong data modeling and agile background.",
        "extractedExperience": [
            {
                "title": "Senior Business Analyst",
                "organization": "FinTech Corp",
                "duration": "2018 - 2022",
                "highlights": ["Led SQL data reporting", "Managed agile cross-functional sprints"]
            }
        ],
        "extractedEducation": [
            {
                "degree": "B.Tech in Computer Science",
                "institution": "State University",
                "year": "2018"
            }
        ],
        "verifiedSkills": [
            {
                "name": "SQL & Data Modeling",
                "category": "Technical",
                "evidence": "Led SQL data reporting across transactional cohorts"
            },
            {
                "name": "Agile Sprint Leadership",
                "category": "Methodology",
                "evidence": "Managed agile cross-functional sprints"
            }
        ],
        "transferableStrengths": [
            {
                "title": "Cross-Functional Negotiation",
                "description": "Proven ability to align executive stakeholders across technical and product domains.",
                "sourceOfEvidence": "FinTech Corp sprint governance"
            }
        ],
        "targetRoleRequirements": [
            {
                "requirement": "Modern Product Analytics (Mixpanel / Amplitude)",
                "currentStatus": "Needs Strengthening",
                "importance": "Critical",
                "reasoning": "Candidate has strong SQL fundamentals but lacks event-based instrumentation evidence."
            }
        ],
        "skillGaps": [
            {
                "name": "Mixpanel & Event Tracking",
                "category": "Modern Analytics",
                "importance": "Critical",
                "explanation": "Modern product operations relies on real-time event analytics over static SQL dumps.",
                "recommendedAction": "Complete Week 2 analytics sandbox in the HerTurn roadmap."
            }
        ],
        "suggestedNextSteps": [
            {
                "action": "Complete Product Discovery Module",
                "detail": "Focus on PRD authoring and metrics in your 4-week sprint.",
                "priority": "High"
            }
        ],
        "evidenceNotes": "All listed technical skills were found explicitly in resume text. Career break was not penalized."
    }

    # Create mock response object
    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_analysis_data)
    mock_response.parsed = None

    # Patch genai.Client
    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.return_value = mock_response

        payload = {
            "resumeText": "Senior Business Analyst at FinTech Corp. Led SQL data reporting and managed agile sprints.",
            "preferences": {
                "targetRole": "Product Operations Lead",
                "previousRole": "Senior Business Analyst",
                "breakDuration": "3 years (Caregiving)",
                "workMode": "Hybrid"
            }
        }

        response = client.post("/api/resume/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "analyzed"
        assert data["targetRole"] == "Product Operations Lead"
        assert len(data["analysis"]["verifiedSkills"]) == 2
        assert data["analysis"]["verifiedSkills"][0]["name"] == "SQL & Data Modeling"
        assert len(data["analysis"]["skillGaps"]) == 1
        assert "evidenceNotes" in data["analysis"]


# ---------------------------------------------------------------------------
# 5. Upstream Gemini timeout & model 404 error handling tests
# ---------------------------------------------------------------------------
def test_analyze_gemini_timeout_returns_504(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")
    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.side_effect = TimeoutError("The read operation timed out")

        payload = {
            "resumeText": "Senior Business Analyst with experience in SQL, Python, stakeholder presentation.",
            "preferences": {"targetRole": "Product Operations Lead"}
        }
        response = client.post("/api/resume/analyze", json=payload)
        assert response.status_code == 504
        assert "timed out" in response.json()["detail"].lower()


def test_analyze_gemini_model_not_found_returns_404(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")
    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.side_effect = Exception("models/gemini-invalid is not found 404")

        payload = {
            "resumeText": "Senior Business Analyst with experience in SQL, Python, stakeholder presentation.",
            "preferences": {"targetRole": "Product Operations Lead"}
        }
        response = client.post("/api/resume/analyze", json=payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6. CORS origin configuration tests
# ---------------------------------------------------------------------------
def test_cors_origins_resolution_dev_vs_production(monkeypatch):
    from app.main import get_allowed_cors_origins

    # Development: localhost included even if ALLOWED_ORIGINS is empty
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    dev_origins = get_allowed_cors_origins()
    assert "http://localhost:5173" in dev_origins
    assert "http://127.0.0.1:5173" in dev_origins

    # Development with custom origins
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://preview.herturn.app")
    dev_with_custom = get_allowed_cors_origins()
    assert "https://preview.herturn.app" in dev_with_custom
    assert "http://localhost:5173" in dev_with_custom

    # Production: strictly explicit origins only
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://app.herturn.com,https://staging.herturn.com")
    prod_origins = get_allowed_cors_origins()
    assert prod_origins == ["https://app.herturn.com", "https://staging.herturn.com"]
    assert "http://localhost:5173" not in prod_origins

    # Production without ALLOWED_ORIGINS: empty list with warning
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    empty_prod = get_allowed_cors_origins()
    assert empty_prod == []

