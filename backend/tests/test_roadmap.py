import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Input Validation Tests
# ---------------------------------------------------------------------------
def test_roadmap_invalid_duration_rejected():
    payload = {
        "targetRole": "Product Operations Lead",
        "durationWeeks": 5  # Only 4 or 6 are allowed
    }
    response = client.post("/api/roadmap/generate", json=payload)
    assert response.status_code == 400
    assert "Duration must be either 4 or 6 weeks" in response.json()["detail"]


def test_roadmap_missing_target_role_rejected():
    payload = {
        "targetRole": "",
        "durationWeeks": 4
    }
    response = client.post("/api/roadmap/generate", json=payload)
    assert response.status_code == 422 or response.status_code == 400


# ---------------------------------------------------------------------------
# 2. Missing API Key Test
# ---------------------------------------------------------------------------
def test_roadmap_missing_api_key_returns_503(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    payload = {
        "targetRole": "Data Analyst",
        "durationWeeks": 4
    }
    response = client.post("/api/roadmap/generate", json=payload)
    assert response.status_code == 503
    assert "Gemini API key is not configured" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 3. 4-Week Structured Roadmap Mocked Success Test
# ---------------------------------------------------------------------------
def test_roadmap_4_week_generation_success(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")

    mock_roadmap_data = {
        "targetRole": "Product Operations Lead",
        "durationWeeks": 4,
        "personalizedSummary": "A focused 4-week relaunch sprint designed to build event analytics and AI PRD authoring onto your verified SQL background.",
        "weeks": [
            {
                "weekNumber": 1,
                "title": "Modern Product Analytics & Event Tracking",
                "theme": "Bridging SQL reporting into live event-based analytics taxonomy",
                "weeklyGoal": "Master Mixpanel/Amplitude event taxonomy and retention cohort calculation.",
                "commitment": "6–8 hours",
                "topics": ["Event vs Pageview models", "Funnel conversion optimization", "Retention cohort curves"],
                "tasks": [
                    {"id": "w1-t1", "text": "Set up a sandbox Mixpanel event taxonomy for an e-commerce flow", "completed": False},
                    {"id": "w1-t2", "text": "Draft 3 SQL cohort queries comparing Day 7 vs Day 30 retention", "completed": False},
                    {"id": "w1-t3", "text": "Document event schemas in a team wiki template", "completed": False}
                ],
                "expectedDeliverable": "Interactive Mixpanel event schema and cohort retention query suite",
                "skillGapAddressed": "Modern Product Analytics (Mixpanel / Amplitude)",
                "resources": [
                    {
                        "title": "Mixpanel Academy: Event Tracking Basics",
                        "type": "Guide",
                        "url": "https://mixpanel.com",
                        "isExternal": True,
                        "label": "Generic curated reference (unverified by RAG)"
                    }
                ]
            },
            {
                "weekNumber": 2,
                "title": "Agile Discovery & AI-Assisted PRD Authoring",
                "theme": "Translating business requirements into contemporary PRD templates",
                "weeklyGoal": "Author a high-impact PRD leveraging modern AI-assisted prompt workflows.",
                "commitment": "8–10 hours",
                "topics": ["1-Page PRD templates", "User story mapping", "AI copilot prompt patterns for user research"],
                "tasks": [
                    {"id": "w2-t1", "text": "Author a 1-page PRD for an automated returnship matching feature", "completed": False},
                    {"id": "w2-t2", "text": "Map out acceptance criteria using Given-When-Then syntax", "completed": False}
                ],
                "expectedDeliverable": "Complete 1-Page PRD with validated user stories and edge cases",
                "skillGapAddressed": "AI-Assisted Workflow Tools (Jira Product Discovery, Linear)",
                "resources": []
            },
            {
                "weekNumber": 3,
                "title": "Cross-Functional Execution & Stakeholder Storytelling",
                "theme": "Refining trade-off communication and sprint governance",
                "weeklyGoal": "Synthesize backlog trade-offs and practice sprint prioritization matrices.",
                "commitment": "6–8 hours",
                "topics": ["RICE prioritization", "Executive stakeholder communication", "Sprint trade-off defense"],
                "tasks": [
                    {"id": "w3-t1", "text": "Evaluate a 10-feature backlog using the RICE scoring matrix", "completed": False},
                    {"id": "w3-t2", "text": "Simulate an executive stakeholder review addressing delivery constraints", "completed": False}
                ],
                "expectedDeliverable": "RICE prioritization matrix artifact and stakeholder briefing deck",
                "skillGapAddressed": "Stakeholder Management & Agile Governance",
                "resources": []
            },
            {
                "weekNumber": 4,
                "title": "Career Relaunch Narrative & Interview Showcase",
                "theme": "Articulating career gap strengths with evidence-based portfolio artifacts",
                "weeklyGoal": "Polish behavioral interview storytelling highlighting caregiver resilience and domain mastery.",
                "commitment": "6–8 hours",
                "topics": ["STAR framework with career break articulation", "Portfolio walkthrough prep", "Salary and fellowship negotiation"],
                "tasks": [
                    {"id": "w4-t1", "text": "Package your 4-week deliverables into a public Notion or GitHub portfolio link", "completed": False},
                    {"id": "w4-t2", "text": "Conduct 2 recorded mock behavioral interview answers explaining hiatus leadership", "completed": False}
                ],
                "expectedDeliverable": "Published Career Returnee Portfolio showcase ready for employer interviews",
                "skillGapAddressed": "Interview Case Practice for Returnees",
                "resources": []
            }
        ]
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_roadmap_data)
    mock_response.parsed = None

    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.return_value = mock_response

        payload = {
            "targetRole": "Product Operations Lead",
            "durationWeeks": 4,
            "verifiedSkills": ["SQL & Data Modeling", "Agile Sprint Leadership"],
            "skillGaps": ["Modern Product Analytics", "AI-Assisted PRD Authoring"],
            "preferences": {
                "targetRole": "Product Operations Lead",
                "previousRole": "Senior Business Analyst",
                "breakDuration": "3 years (Caregiving)",
                "workMode": "Hybrid"
            }
        }

        response = client.post("/api/roadmap/generate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["status"] == "generated"
        assert data["durationWeeks"] == 4
        assert len(data["roadmap"]["weeks"]) == 4
        assert data["roadmap"]["weeks"][0]["expectedDeliverable"] != ""
        assert data["roadmap"]["weeks"][0]["skillGapAddressed"] != ""
        assert len(data["roadmap"]["weeks"][0]["tasks"]) == 3


# ---------------------------------------------------------------------------
# 4. 6-Week Structured Roadmap Mocked Success Test
# ---------------------------------------------------------------------------
def test_roadmap_6_week_generation_success(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")

    mock_weeks = []
    for w in range(1, 7):
        mock_weeks.append({
            "weekNumber": w,
            "title": f"Week {w} Milestone Module",
            "theme": f"Theme for week {w}",
            "weeklyGoal": f"Master competencies for week {w}",
            "commitment": "6–8 hours",
            "topics": [f"Topic {w}.1", f"Topic {w}.2"],
            "tasks": [
                {"id": f"w{w}-t1", "text": f"Task 1 for week {w}", "completed": False},
                {"id": f"w{w}-t2", "text": f"Task 2 for week {w}", "completed": False}
            ],
            "expectedDeliverable": f"Artifact for week {w}",
            "skillGapAddressed": f"Target gap {w}",
            "resources": []
        })

    mock_roadmap_data = {
        "targetRole": "Senior Data Analyst",
        "durationWeeks": 6,
        "personalizedSummary": "A balanced 6-week roadmap tailored for returning professionals.",
        "weeks": mock_weeks
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_roadmap_data)
    mock_response.parsed = None

    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.return_value = mock_response

        payload = {
            "targetRole": "Senior Data Analyst",
            "durationWeeks": 6,
            "verifiedSkills": ["Python", "SQL"],
            "skillGaps": ["Tableau Cloud", "dbt data transformation"]
        }

        response = client.post("/api/roadmap/generate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["durationWeeks"] == 6
        assert len(data["roadmap"]["weeks"]) == 6


# ---------------------------------------------------------------------------
# 5. Gemini Server Failure Handling Test
# ---------------------------------------------------------------------------
def test_roadmap_gemini_server_error_handling(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")

    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.side_effect = Exception("503 UNAVAILABLE. High demand spike")

        payload = {
            "targetRole": "Product Manager",
            "durationWeeks": 4
        }

        response = client.post("/api/roadmap/generate", json=payload)
        assert response.status_code == 503
        assert "Google Gemini servers are currently experiencing high demand" in response.json()["detail"]


# ---------------------------------------------------------------------------
# 6. Malformed Output Schema Validation Error Handling Test
# ---------------------------------------------------------------------------
def test_roadmap_invalid_response_schema_handling(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")

    mock_response = MagicMock()
    mock_response.text = json.dumps({"invalid": "structure"})
    mock_response.parsed = None

    with patch("app.analyzer.genai.Client") as mock_client_cls:
        mock_client_instance = MagicMock()
        mock_client_cls.return_value = mock_client_instance
        mock_client_instance.models.generate_content.return_value = mock_response

        payload = {
            "targetRole": "Product Manager",
            "durationWeeks": 4
        }

        response = client.post("/api/roadmap/generate", json=payload)
        assert response.status_code == 502
        assert "could not be validated against the required schema" in response.json()["detail"]
