import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import chromadb

from app.main import app
from app.rag.ingestion import (
    load_knowledge_base,
    normalize_resource_chunk,
    ingest_resources,
    COLLECTION_NAME
)
from app.rag.retriever import retrieve_verified_resources
from app.models import StructuredRoadmap

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def ensure_rag_collection_initialized():
    """Ensure the default ChromaDB collection is ingested before running RAG tests."""
    ingest_resources()


# ---------------------------------------------------------------------------
# Sample Curated Test Resources
# ---------------------------------------------------------------------------
SAMPLE_TEST_RESOURCES = [
    {
        "id": "test-res-react",
        "title": "React Official Documentation: Quick Start & Hooks",
        "url": "https://react.dev/learn",
        "provider": "React Team / Meta",
        "skills": ["React", "Component Architecture", "Hooks", "Frontend Development"],
        "targetRoles": ["Frontend Engineer", "Full Stack Engineer"],
        "difficulty": "Beginner",
        "type": "Official Documentation",
        "description": "The authoritative guide to thinking in React, functional components, and hooks.",
        "isVerified": True
    },
    {
        "id": "test-res-fastapi",
        "title": "FastAPI Official Tutorial & Modern Python APIs",
        "url": "https://fastapi.tiangolo.com/tutorial/",
        "provider": "FastAPI / Sebastián Ramírez",
        "skills": ["FastAPI", "Python", "REST APIs", "Pydantic", "Async Programming"],
        "targetRoles": ["Backend Developer", "Software Engineer"],
        "difficulty": "Intermediate",
        "type": "Interactive Documentation",
        "description": "Comprehensive hands-on guide to building production-ready RESTful APIs in Python.",
        "isVerified": True
    },
    {
        "id": "test-res-lenny-prd",
        "title": "Lenny's Newsletter: How to Write an Impactful 1-Page PRD",
        "url": "https://www.lennysnewsletter.com/p/how-to-write-a-prd",
        "provider": "Lenny's Newsletter",
        "skills": ["PRD Authoring", "Product Requirements", "User Stories"],
        "targetRoles": ["Product Manager", "Product Operations Lead"],
        "difficulty": "Intermediate",
        "type": "Guide & Template",
        "description": "Practical framework for authoring concise, outcome-oriented Product Requirement Documents.",
        "isVerified": True
    }
]


# ---------------------------------------------------------------------------
# 1. Ingestion, Normalization & Idempotency / Deduplication Tests
# ---------------------------------------------------------------------------

def test_load_curated_knowledge_base():
    """Verify default knowledge base loads and contains verified resources."""
    kb = load_knowledge_base()
    assert isinstance(kb, list)
    assert len(kb) >= 20
    for item in kb:
        assert item["id"].startswith("res-")
        assert item["url"].startswith("http")
        assert item["isVerified"] is True
        assert len(item["skills"]) > 0
        assert len(item["targetRoles"]) > 0
        assert item["provider"]
        assert item["type"]


def test_normalize_resource_chunk_structure():
    """Verify document normalization creates structured embeddings text and metadata."""
    item = SAMPLE_TEST_RESOURCES[0]
    res_id, chunk_text, meta = normalize_resource_chunk(item)

    assert res_id == "test-res-react"
    assert "Title: React Official Documentation" in chunk_text
    assert "Provider: React Team / Meta" in chunk_text
    assert "Applicable Skills: React, Component Architecture" in chunk_text

    assert meta["id"] == "test-res-react"
    assert meta["url"] == "https://react.dev/learn"
    assert meta["provider"] == "React Team / Meta"
    assert meta["isVerified"] is True
    assert "React" in meta["skills_csv"]
    assert "Frontend Engineer" in meta["roles_csv"]
    assert meta["description"]


def test_ingest_idempotency_no_duplicate_records():
    """Verify ingesting the same dataset multiple times does not duplicate records in ChromaDB."""
    test_chroma = chromadb.EphemeralClient()

    # First ingestion
    result_1 = ingest_resources(
        resources=SAMPLE_TEST_RESOURCES,
        chroma_client=test_chroma
    )
    assert result_1["status"] == "success"
    assert result_1["ingested_count"] == 3
    assert result_1["total_collection_count"] == 3

    # Re-run ingestion with the exact same items
    result_2 = ingest_resources(
        resources=SAMPLE_TEST_RESOURCES,
        chroma_client=test_chroma
    )
    assert result_2["status"] == "success"
    assert result_2["ingested_count"] == 3
    assert result_2["total_collection_count"] == 3  # Count remains exactly 3, 0 duplicates


# ---------------------------------------------------------------------------
# 2. Retrieval Service Relevance & Metadata Preservation Tests
# ---------------------------------------------------------------------------

def test_retrieve_verified_resources_relevance_ranking():
    """Verify retrieval returns relevant resources ranked by query matching."""
    test_chroma = chromadb.EphemeralClient()
    ingest_resources(resources=SAMPLE_TEST_RESOURCES, chroma_client=test_chroma)

    # Search for Product Management / PRD skill gaps
    retrieval = retrieve_verified_resources(
        target_role="Product Operations Lead",
        skill_gaps=["PRD Authoring", "Product Requirements"],
        top_k=2,
        chroma_client=test_chroma
    )

    assert retrieval["is_rag_used"] is True
    assert retrieval["rag_status"] == "retrieved"
    assert len(retrieval["resources"]) > 0

    top_res = retrieval["resources"][0]
    assert top_res["id"] == "test-res-lenny-prd"
    assert top_res["url"] == "https://www.lennysnewsletter.com/p/how-to-write-a-prd"
    assert top_res["provider"] == "Lenny's Newsletter"
    assert top_res["isVerified"] is True
    assert isinstance(top_res["skills"], list)
    assert isinstance(top_res["targetRoles"], list)
    assert top_res["relevanceScore"] > 0.5


def test_retrieve_verified_resources_url_and_metadata_preservation():
    """Verify canonical URLs and metadata are preserved without alteration."""
    test_chroma = chromadb.EphemeralClient()
    ingest_resources(resources=SAMPLE_TEST_RESOURCES, chroma_client=test_chroma)

    retrieval = retrieve_verified_resources(
        target_role="Backend Developer",
        skill_gaps=["FastAPI", "Python REST APIs"],
        top_k=1,
        chroma_client=test_chroma
    )

    assert retrieval["is_rag_used"] is True
    res = retrieval["resources"][0]
    assert res["id"] == "test-res-fastapi"
    assert res["url"] == "https://fastapi.tiangolo.com/tutorial/"
    assert res["difficulty"] == "Intermediate"
    assert res["type"] == "Interactive Documentation"
    assert "FastAPI" in res["skills"]


def test_retrieve_from_uninitialized_collection_graceful_handling():
    """Verify transparent fallback when vector database collection does not exist."""
    empty_chroma = chromadb.EphemeralClient()

    retrieval = retrieve_verified_resources(
        target_role="Software Engineer",
        skill_gaps=["General"],
        chroma_client=empty_chroma,
        collection_name="uninitialized_custom_collection"
    )

    assert retrieval["is_rag_used"] is False
    assert retrieval["rag_status"] == "unavailable"
    assert retrieval["resources"] == []
    assert retrieval["source_count"] == 0


# ---------------------------------------------------------------------------
# 3. Dedicated API Endpoint Tests: POST /api/resources/retrieve
# ---------------------------------------------------------------------------

def test_api_resources_retrieve_success():
    """Verify POST /api/resources/retrieve endpoint returns structured verified resources."""
    payload = {
        "targetRole": "Frontend Engineer",
        "skillGaps": ["React", "Component Architecture"],
        "topK": 4
    }
    response = client.post("/api/resources/retrieve", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["targetRole"] == "Frontend Engineer"
    assert data["totalRetrieved"] > 0
    assert data["isRagUsed"] is True
    assert len(data["resources"]) > 0

    first_res = data["resources"][0]
    assert "title" in first_res
    assert "url" in first_res
    assert first_res["url"].startswith("http")
    assert first_res["isVerified"] is True
    assert isinstance(first_res["skills"], list)


def test_api_resources_retrieve_validation_empty_role():
    """Verify endpoint rejects empty targetRole with 400 or 422."""
    payload = {
        "targetRole": "",
        "skillGaps": ["React"]
    }
    response = client.post("/api/resources/retrieve", json=payload)
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# 4. End-to-End Roadmap Generation with RAG Integration (Mocked Gemini)
# ---------------------------------------------------------------------------

def test_roadmap_generation_with_rag_context_and_verification(monkeypatch):
    """
    Verify POST /api/roadmap/generate performs RAG retrieval, passes context to Gemini,
    and returns RAG metadata with verified badges.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")

    mock_gemini_roadmap = {
        "targetRole": "Frontend Engineer",
        "durationWeeks": 4,
        "personalizedSummary": "Personalized frontend relaunch sprint building upon documented web development acumen.",
        "weeks": [
            {
                "weekNumber": 1,
                "title": "Modern Component Architecture & State Management",
                "theme": "Rebuilding React fluency with contemporary hooks",
                "weeklyGoal": "Master functional components, hooks, and clean state decomposition.",
                "commitment": "6–8 hours",
                "topics": ["React 19", "Hooks", "Component lifecycle"],
                "tasks": [
                    {"id": "w1-t1", "text": "Build a responsive modular dashboard component in React", "completed": False},
                    {"id": "w1-t2", "text": "Refactor legacy class patterns into custom hooks", "completed": False}
                ],
                "expectedDeliverable": "Functional React interactive component deployed to GitHub",
                "skillGapAddressed": "Modern React Component Architecture",
                "resources": [
                    {
                        "title": "React Official Documentation: Quick Start & Hooks",
                        "url": "https://react.dev/learn",
                        "type": "Official Documentation",
                        "isExternal": True,
                        "label": "Verified Curriculum Resource (RAG)",
                        "provider": "React Team / Meta",
                        "difficulty": "Beginner",
                        "isVerified": True
                    }
                ]
            },
            {
                "weekNumber": 2,
                "title": "Asynchronous JavaScript & API Integration",
                "theme": "Mastering modern ES6+ async/await and data fetching",
                "weeklyGoal": "Connect React state to asynchronous REST endpoints cleanly.",
                "commitment": "6–8 hours",
                "topics": ["ES6+ Promises", "Fetch API", "Async error handling"],
                "tasks": [
                    {"id": "w2-t1", "text": "Integrate asynchronous REST data fetching with loading states", "completed": False}
                ],
                "expectedDeliverable": "Data-connected UI view with comprehensive error boundaries",
                "skillGapAddressed": "Modern JavaScript Async Patterns",
                "resources": [
                    {
                        "title": "MDN Web Docs: Modern JavaScript Essentials",
                        "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
                        "type": "Documentation & Reference",
                        "isExternal": True,
                        "label": "Verified Curriculum Resource (RAG)",
                        "provider": "Mozilla Developer Network (MDN)",
                        "difficulty": "Intermediate",
                        "isVerified": True
                    }
                ]
            },
            {
                "weekNumber": 3,
                "title": "Production Build & Version Control Collaboration",
                "theme": "Git branching workflows and CI verification",
                "weeklyGoal": "Establish clean git commit hygiene and CI build checks.",
                "commitment": "6–8 hours",
                "topics": ["Git branching", "Pull requests", "Vite build pipeline"],
                "tasks": [
                    {"id": "w3-t1", "text": "Set up GitHub branch protection and submit PR with descriptive notes", "completed": False}
                ],
                "expectedDeliverable": "Merged Pull Request with passing CI build",
                "skillGapAddressed": "Git Collaborative Workflows",
                "resources": []
            },
            {
                "weekNumber": 4,
                "title": "Portfolio Showcase & Returnee Technical Storytelling",
                "theme": "Synthesizing career break narrative into technical portfolio walkthrough",
                "weeklyGoal": "Package projects into accessible live demonstrations ready for interviewers.",
                "commitment": "6–8 hours",
                "topics": ["STAR method", "System architecture walkthrough", "Hiatus framing"],
                "tasks": [
                    {"id": "w4-t1", "text": "Record 3-minute video walkthrough explaining project design trade-offs", "completed": False}
                ],
                "expectedDeliverable": "Published GitHub portfolio with live preview link",
                "skillGapAddressed": "Technical Interview Readiness",
                "resources": []
            }
        ]
    }

    mock_gemini_response = MagicMock()
    mock_gemini_response.text = json.dumps(mock_gemini_roadmap)
    mock_gemini_response.parsed = StructuredRoadmap.model_validate(mock_gemini_roadmap)

    with patch("app.analyzer.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_gemini_response
        mock_get_client.return_value = mock_client

        payload = {
            "targetRole": "Frontend Engineer",
            "durationWeeks": 4,
            "skillGaps": ["React", "Component Architecture", "Modern JavaScript"]
        }

        response = client.post("/api/roadmap/generate", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["isRagUsed"] is True
        assert data["ragStatus"] == "verified_rag_used"
        assert data["ragSourceCount"] > 0
        assert len(data["retrievedResources"]) > 0

        # Verify resources in week 1 are marked verified
        w1_res = data["roadmap"]["weeks"][0]["resources"]
        assert len(w1_res) > 0
        assert w1_res[0]["isVerified"] is True
        assert "Verified Curriculum Resource (RAG)" in w1_res[0]["label"]
        assert w1_res[0]["url"] == "https://react.dev/learn"


def test_roadmap_generation_anti_hallucination_prevents_fake_urls(monkeypatch):
    """
    Verify that if Gemini attempts to return a hallucinated URL not in the retrieved
    knowledge base, the post-processor does NOT mark it verified.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")

    mock_gemini_roadmap = {
        "targetRole": "Frontend Engineer",
        "durationWeeks": 4,
        "personalizedSummary": "Personalized frontend sprint.",
        "weeks": [
            {
                "weekNumber": 1,
                "title": "Week 1",
                "theme": "Theme 1",
                "weeklyGoal": "Goal 1",
                "commitment": "6 hours",
                "topics": ["React"],
                "tasks": [{"id": "w1-t1", "text": "Task 1", "completed": False}],
                "expectedDeliverable": "Deliverable 1",
                "skillGapAddressed": "Gap 1",
                "resources": [
                    {
                        "title": "Invented Random Blog",
                        "url": "https://fake-invented-blog-url.xyz/secret-tricks",
                        "type": "Guide",
                        "isExternal": True,
                        "label": "Verified Curriculum Resource (RAG)", # Model attempts to claim verified
                        "isVerified": True
                    }
                ]
            },
            {
                "weekNumber": 2,
                "title": "Week 2",
                "theme": "Theme 2",
                "weeklyGoal": "Goal 2",
                "commitment": "6 hours",
                "topics": ["Testing"],
                "tasks": [{"id": "w2-t1", "text": "Task 2", "completed": False}],
                "expectedDeliverable": "Deliverable 2",
                "skillGapAddressed": "Gap 2",
                "resources": []
            },
            {
                "weekNumber": 3,
                "title": "Week 3",
                "theme": "Theme 3",
                "weeklyGoal": "Goal 3",
                "commitment": "6 hours",
                "topics": ["CI"],
                "tasks": [{"id": "w3-t1", "text": "Task 3", "completed": False}],
                "expectedDeliverable": "Deliverable 3",
                "skillGapAddressed": "Gap 3",
                "resources": []
            },
            {
                "weekNumber": 4,
                "title": "Week 4",
                "theme": "Theme 4",
                "weeklyGoal": "Goal 4",
                "commitment": "6 hours",
                "topics": ["Interview"],
                "tasks": [{"id": "w4-t1", "text": "Task 4", "completed": False}],
                "expectedDeliverable": "Deliverable 4",
                "skillGapAddressed": "Gap 4",
                "resources": []
            }
        ]
    }

    mock_gemini_response = MagicMock()
    mock_gemini_response.text = json.dumps(mock_gemini_roadmap)
    mock_gemini_response.parsed = StructuredRoadmap.model_validate(mock_gemini_roadmap)

    with patch("app.analyzer.get_gemini_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_gemini_response
        mock_get_client.return_value = mock_client

        payload = {
            "targetRole": "Frontend Engineer",
            "durationWeeks": 4,
            "skillGaps": ["React"]
        }

        response = client.post("/api/roadmap/generate", json=payload)
        assert response.status_code == 200
        data = response.json()

        # The fake URL must NOT be marked verified!
        res_item = data["roadmap"]["weeks"][0]["resources"][0]
        assert res_item["isVerified"] is False
        assert "unverified" in res_item["label"].lower()


def test_roadmap_transparent_fallback_when_chromadb_unavailable(monkeypatch):
    """
    Verify transparent fallback when ChromaDB retriever encounters an error:
    does not fail generation, but sets isRagUsed=False and never claims RAG was used.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "test-mock-gemini-key")

    mock_gemini_roadmap = {
        "targetRole": "Cloud Engineer",
        "durationWeeks": 4,
        "personalizedSummary": "Cloud relaunch sprint.",
        "weeks": [
            {
                "weekNumber": 1,
                "title": "Cloud Week 1",
                "theme": "IAM",
                "weeklyGoal": "IAM permissions",
                "commitment": "6 hours",
                "topics": ["AWS IAM"],
                "tasks": [{"id": "w1-t1", "text": "IAM task", "completed": False}],
                "expectedDeliverable": "IAM policy",
                "skillGapAddressed": "IAM",
                "resources": []
            },
            {
                "weekNumber": 2,
                "title": "Cloud Week 2",
                "theme": "S3 & EC2",
                "weeklyGoal": "Compute & Storage",
                "commitment": "6 hours",
                "topics": ["EC2"],
                "tasks": [{"id": "w2-t1", "text": "EC2 task", "completed": False}],
                "expectedDeliverable": "EC2 instance",
                "skillGapAddressed": "EC2",
                "resources": []
            },
            {
                "weekNumber": 3,
                "title": "Cloud Week 3",
                "theme": "Networking",
                "weeklyGoal": "VPC design",
                "commitment": "6 hours",
                "topics": ["VPC"],
                "tasks": [{"id": "w3-t1", "text": "VPC task", "completed": False}],
                "expectedDeliverable": "VPC architecture",
                "skillGapAddressed": "Networking",
                "resources": []
            },
            {
                "weekNumber": 4,
                "title": "Cloud Week 4",
                "theme": "Interview",
                "weeklyGoal": "Interview prep",
                "commitment": "6 hours",
                "topics": ["Interview"],
                "tasks": [{"id": "w4-t1", "text": "Mock interview", "completed": False}],
                "expectedDeliverable": "Case study deck",
                "skillGapAddressed": "Interviewing",
                "resources": []
            }
        ]
    }

    mock_gemini_response = MagicMock()
    mock_gemini_response.text = json.dumps(mock_gemini_roadmap)
    mock_gemini_response.parsed = StructuredRoadmap.model_validate(mock_gemini_roadmap)

    with patch("app.analyzer.get_gemini_client") as mock_get_client, \
         patch("app.analyzer.retrieve_verified_resources") as mock_retrieve:

        mock_retrieve.return_value = {
            "rag_status": "unavailable",
            "is_rag_used": False,
            "resources": [],
            "context_text": "",
            "source_count": 0,
            "message": "ChromaDB connection unavailable."
        }

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_gemini_response
        mock_get_client.return_value = mock_client

        payload = {
            "targetRole": "Cloud Engineer",
            "durationWeeks": 4,
            "skillGaps": ["AWS Core Services"]
        }

        response = client.post("/api/roadmap/generate", json=payload)
        assert response.status_code == 200
        data = response.json()

        # Transparent fallback verified: isRagUsed is False
        assert data["isRagUsed"] is False
        assert data["ragStatus"] == "unavailable"
        assert data["ragSourceCount"] == 0
        assert data["retrievedResources"] == []
