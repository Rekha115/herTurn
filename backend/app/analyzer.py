import os
import json
import asyncio
import logging
from typing import Optional

from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types
from pydantic import ValidationError

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from app.models import (
        ResumeAnalysisRequest,
        StructuredLLMAnalysis,
        ResumeAnalysisResponse,
        RoadmapGenerateRequest,
        StructuredRoadmap,
        RoadmapGenerateResponse,
        RetrievedResourceItem,
    )
    from app.rag.retriever import retrieve_verified_resources
except ImportError:
    from .models import (
        ResumeAnalysisRequest,
        StructuredLLMAnalysis,
        ResumeAnalysisResponse,
        RoadmapGenerateRequest,
        StructuredRoadmap,
        RoadmapGenerateResponse,
        RetrievedResourceItem,
    )
    from .rag.retriever import retrieve_verified_resources


# Load environment variables from backend/.env explicitly, as well as current working directory
load_dotenv(backend_dir / ".env")
load_dotenv()

logger = logging.getLogger("herturn.analyzer")

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite-preview"



class GeminiAnalysisError(Exception):
    """Custom exception for Gemini analysis issues."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_gemini_client() -> genai.Client:
    """
    Retrieves and initializes the official google-genai Client.
    Validates that GEMINI_API_KEY is configured in the environment.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip() or api_key == "your_gemini_api_key_here":
        raise GeminiAnalysisError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env "
            "or as an environment variable to enable live AI resume analysis.",
            status_code=503
        )
    
    timeout_sec = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "60.0"))
    timeout_ms = int(timeout_sec * 1000)
    return genai.Client(api_key=api_key.strip(), http_options=types.HttpOptions(timeout=timeout_ms))




def build_analysis_prompt(request: ResumeAnalysisRequest) -> str:
    """
    Constructs an objective, factual, anti-bias prompt for Gemini.
    Strictly instructs the model never to invent qualifications,
    never to treat career breaks as deficiencies, and to distinguish
    facts from inferences.
    """
    pref = request.preferences
    
    prompt = f"""You are the senior career intelligence engine for HerTurn, an empowering career relaunch platform for women restarting their professional journeys after career pauses.

YOUR MANDATORY OBJECTIVITY & ANTI-BIAS RULES:
1. FACTUAL GROUNDING: Extract ONLY facts, skills, employment dates, and credentials explicitly documented in the candidate's resume text below.
2. NEVER INVENT: Never hallucinate or assume unstated company names, universities, job titles, or certifications. If an item is missing or unstated, record it as "Not specified" or "Unknown in resume".
3. NO HIATUS PENALTY: Never treat a career break alone as a skills deficiency or lack of capability. Lived experience, caregiving, and community leadership build high-leverage transferable adaptability, stakeholder empathy, crisis management, and prioritization instincts.
4. ROLE-TARGETED GAP ANALYSIS: Objectively compare the candidate's documented skills against contemporary industry expectations for the target role: "{pref.targetRole}". Identify actionable gaps in contemporary tools (e.g. cloud tools, modern analytics, agile tooling, generative AI workflows) that can be refreshed in a 4-6 week sprint.
5. EXPLICIT EVIDENCE: For each verified skill, cite direct context or phrasing from the resume. In 'evidenceNotes', explicitly list what facts were found vs. what is inferred or recommended.

CANDIDATE ONBOARDING CONTEXT:
- Target Role: {pref.targetRole}
- Self-Reported Previous Role: {pref.previousRole or 'Not provided'}
- Total Prior Experience: {pref.totalExperience or 'Not provided'}
- Career Pause Duration & Context: {pref.breakDuration or 'Not specified'}
- Work Preference: {pref.workMode or 'Flexible'} ({pref.preferredLocation or 'Flexible'})
- Expressed Areas of Interest: {', '.join(pref.areasOfInterest) if pref.areasOfInterest else 'General career relaunch'}

RESUME TEXT CONTENT:
\"\"\"
{request.resumeText}
\"\"\"

Produce your complete analysis conforming precisely to the requested JSON schema.
"""
    return prompt


async def analyze_resume_with_gemini(
    request: ResumeAnalysisRequest,
    model_override: Optional[str] = None
) -> ResumeAnalysisResponse:
    """
    Analyzes resume text using Google Gemini with structured Pydantic output.
    Safely validates response schema and handles provider exceptions.
    """
    # 1. Initialize client
    client = get_gemini_client()

    # 2. Determine model
    model_name = model_override or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL

    # 3. Build prompt
    prompt = build_analysis_prompt(request)

    # Active non-deprecated candidate models supported on Gemini API
    supported_models = [
        "gemini-flash-latest",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
    ]
    candidate_models = [model_name]
    for fallback in supported_models:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    response = None
    last_error = None
    successful_model = model_name

    for candidate in candidate_models:
        for attempt in range(2):
            try:
                logger.info(f"Calling Gemini model '{candidate}' (attempt {attempt + 1}) for target role '{request.preferences.targetRole}'")
                response = client.models.generate_content(
                    model=candidate,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=StructuredLLMAnalysis,
                        temperature=0.2,
                    ),
                )
                successful_model = candidate
                logger.info(f"Successfully generated analysis with model '{candidate}'")
                break
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"Model '{candidate}' attempt {attempt + 1} failed: {err_msg}")
                last_error = e
                
                # If invalid auth, do not retry other models
                if "API_KEY_INVALID" in err_msg or "401" in err_msg or "403" in err_msg:
                    raise GeminiAnalysisError(
                        "Gemini API authentication failed. Please verify that your GEMINI_API_KEY is valid.",
                        status_code=401
                    )
                # If transient high demand, wait briefly before retrying this candidate
                if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg.lower():
                    if attempt < 1:
                        await asyncio.sleep(1.5)
                        continue
                break
        if response is not None:
            break

    if response is None:
        err_str = str(last_error) if last_error else "All models failed"
        if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
            raise GeminiAnalysisError(
                "Google Gemini servers are currently experiencing high demand. Please try again in a few moments.",
                status_code=503
            )
        elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            raise GeminiAnalysisError(
                "Gemini API rate limit or quota exceeded. Please try again shortly.",
                status_code=429
            )
        elif "timed out" in err_str.lower() or "timeout" in err_str.lower():
            raise GeminiAnalysisError(
                "Communication with Google Gemini API timed out. Upstream services may be experiencing high latency or network degradation. Please try again.",
                status_code=504
            )
        elif "404" in err_str or "not found" in err_str.lower():
            raise GeminiAnalysisError(
                f"Configured Gemini model was not found: {err_str}",
                status_code=404
            )
        else:
            raise GeminiAnalysisError(
                f"Error communicating with Google Gemini API: {err_str}",
                status_code=502
            )

    # 5. Extract and parse response text
    raw_text = response.text
    if not raw_text or not raw_text.strip():
        raise GeminiAnalysisError(
            "Gemini API returned an empty response. Please re-run analysis.",
            status_code=502
        )

    # 6. Validate with Pydantic model
    try:
        # If response.parsed is available directly from the SDK, use it; otherwise parse JSON
        if hasattr(response, "parsed") and response.parsed is not None and isinstance(response.parsed, StructuredLLMAnalysis):
            structured_data = response.parsed
        else:
            data_dict = json.loads(raw_text)
            structured_data = StructuredLLMAnalysis.model_validate(data_dict)

    except (json.JSONDecodeError, ValidationError) as val_err:
        logger.error(f"Failed to validate LLM output against schema: {val_err}")
        raise GeminiAnalysisError(
            f"The AI model output could not be validated against the required schema: {str(val_err)}",
            status_code=502
        )

    return ResumeAnalysisResponse(
        success=True,
        status="analyzed",
        modelUsed=successful_model,
        targetRole=request.preferences.targetRole,
        analysis=structured_data,
        message="Resume analyzed successfully via Google Gemini."
    )


def build_roadmap_prompt(
    request: RoadmapGenerateRequest,
    rag_context: Optional[str] = None
) -> str:
    """
    Constructs an objective, personalized, anti-bias curriculum prompt for Gemini.
    Strictly instructs the model to build a 4 or 6 week progression tailored to
    the candidate's verified skills, identified skill gaps, and target role.
    If rag_context is provided, enforces strict citation from verified resources only.
    """
    target_role = request.targetRole
    duration_weeks = request.durationWeeks

    # Extract candidate preferences & background if provided
    pref_summary = "Not provided"
    if request.preferences:
        pref = request.preferences
        pref_summary = (
            f"Previous Role: {pref.previousRole or 'Not specified'}, "
            f"Total Prior Experience: {pref.totalExperience or 'Not specified'}, "
            f"Career Break Context: {pref.breakDuration or 'Not specified'}, "
            f"Work Mode: {pref.workMode or 'Flexible'}, "
            f"Areas of Interest: {', '.join(pref.areasOfInterest) if pref.areasOfInterest else 'General relaunch'}"
        )

    # Compile verified skills
    verified_skills_list = []
    if request.analysis and request.analysis.verifiedSkills:
        for s in request.analysis.verifiedSkills:
            verified_skills_list.append(f"- {s.name} ({s.category}): {s.evidence}")
    elif request.verifiedSkills:
        for s in request.verifiedSkills:
            verified_skills_list.append(f"- {s}")

    verified_skills_str = (
        "\n".join(verified_skills_list)
        if verified_skills_list
        else "- Foundational domain and operational acumen from documented career history"
    )

    # Compile skill gaps
    skill_gaps_list = []
    if request.analysis and request.analysis.skillGaps:
        for g in request.analysis.skillGaps:
            skill_gaps_list.append(f"- {g.name} ({g.category}): {g.explanation} (Action: {g.recommendedAction})")
    elif request.skillGaps:
        for g in request.skillGaps:
            skill_gaps_list.append(f"- {g}")

    skill_gaps_str = (
        "\n".join(skill_gaps_list)
        if skill_gaps_list
        else f"- Contemporary tools, modern workflows, and returnee interview storytelling for {target_role}"
    )

    resume_summary = (
        request.analysis.resumeSummary
        if request.analysis and request.analysis.resumeSummary
        else "Experienced professional restarting their career after a career hiatus."
    )

    # Resource citation rules based on whether RAG context is available
    if rag_context:
        resource_rules = f"""7. RESOURCE SOURCING VIA VERIFIED RAG KNOWLEDGE BASE:
{rag_context}
- CRITICAL ANTI-HALLUCINATION REQUIREMENT:
  * You may ONLY cite resources that are explicitly listed in the RETRIEVED VERIFIED LEARNING RESOURCES list above.
  * When assigning a resource to a week module, use the EXACT Title and canonical URL from the retrieved list.
  * Set 'label': "Verified Curriculum Resource (RAG)", 'isVerified': true, 'provider': <matching provider>, 'difficulty': <matching difficulty>.
  * NEVER invent, fabricate, or hallucinate URLs or resource names not in the retrieved list.
  * If a week does not have a direct matching resource from the list above, leave its resources array empty []."""
    else:
        resource_rules = """7. RESOURCE SAFETY & DISCLAIMER (RAG UNAVAILABLE):
- Note: Verified knowledge base was unavailable or returned no direct matches for these specific skills.
- Do NOT fabricate or invent fake, obscure, or broken URLs.
- For 'resources', provide generic well-known educational hubs or standard documentation guides (e.g., https://developer.mozilla.org, https://docs.python.org, https://mode.com/sql-tutorial/, https://www.atlassian.com/agile, https://www.figma.com/community, https://reforge.com/blog).
- Set 'label': "Generic curated reference (unverified by RAG)" and 'isVerified': false for every resource."""

    prompt = f"""You are the senior curriculum architect and returnee transition coach for HerTurn, an empowering career relaunch platform for women restarting their careers after career pauses.

YOUR MANDATORY CURRICULUM DESIGN RULES:
1. FACTUAL GROUNDING: Anchor this roadmap directly on the candidate's verified skills and actual skill gaps documented below. Do NOT assume a career break implies lost foundational competence. Build upon their established baseline.
2. NO INVENTED CAPABILITIES: Do not assume the candidate already knows modern toolchains they haven't used. Systematically sequence the identified gaps into progressive weekly milestones.
3. EXACT DURATION: You MUST generate exactly {duration_weeks} weeks (weekNumber 1 through {duration_weeks}).
   - If 4 weeks: An intensive, high-leverage sprint focusing on closing the most critical gaps, rapid hands-on mini-projects, and returnee interview narratives.
   - If 6 weeks: A balanced, sustainable sprint allowing deeper hands-on lab practice, portfolio artifact polish, and cohort networking.
4. ACTIONABLE OUTCOME / DELIVERABLE: Every week MUST define a tangible deliverable in 'expectedDeliverable' (e.g., '1-Page Product Requirement Document (PRD)', 'GitHub repository with SQL cohort analysis', 'Interactive Metrics Dashboard prototype', 'Portfolio case study deck').
5. EXPLICIT SKILL GAP ADDRESSED: Every week MUST explicitly state which candidate skill gap it addresses in 'skillGapAddressed'.
6. REALISTIC ACTION TASKS: Provide 3 to 4 specific, actionable checklist tasks per week. Assign clean unique IDs like 'w1-t1', 'w1-t2'.
{resource_rules}

CANDIDATE CONTEXT:
- Target Role: {target_role}
- Candidate Career Summary: {resume_summary}
- Background & Preferences: {pref_summary}

VERIFIED SKILLS DOCUMENTED IN RESUME:
{verified_skills_str}

IDENTIFIED SKILL GAPS TO BRIDGE:
{skill_gaps_str}

Produce your complete personalized roadmap conforming precisely to the requested StructuredRoadmap schema with exactly {duration_weeks} weeks.
"""
    return prompt


async def generate_roadmap_with_gemini(
    request: RoadmapGenerateRequest,
    model_override: Optional[str] = None
) -> RoadmapGenerateResponse:
    """
    Generates a personalized 4-week or 6-week curriculum using Google Gemini
    with structured Pydantic output, augmented by verified RAG resources.
    """
    client = get_gemini_client()
    model_name = model_override or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL

    # 1. Extract candidate skill gaps to formulate RAG retrieval query
    gaps_for_query: list[str] = []
    if request.analysis and request.analysis.skillGaps:
        gaps_for_query = [g.name for g in request.analysis.skillGaps if g.name]
    elif request.skillGaps:
        gaps_for_query = [g for g in request.skillGaps if g]

    # 2. Retrieve verified resources via RAG
    try:
        rag_retrieval = retrieve_verified_resources(
            target_role=request.targetRole,
            skill_gaps=gaps_for_query,
            top_k=6,
        )
    except Exception as rag_err:
        logger.warning(f"RAG retrieval exception caught: {rag_err}")
        rag_retrieval = {
            "rag_status": "unavailable",
            "is_rag_used": False,
            "resources": [],
            "context_text": "",
            "source_count": 0,
            "message": str(rag_err),
        }

    is_rag_used = bool(rag_retrieval.get("is_rag_used", False))
    rag_status = "verified_rag_used" if is_rag_used else rag_retrieval.get("rag_status", "unavailable")
    rag_context = rag_retrieval.get("context_text") if is_rag_used else None
    raw_resources = rag_retrieval.get("resources", [])

    retrieved_models: list[RetrievedResourceItem] = []
    for r in raw_resources:
        retrieved_models.append(
            RetrievedResourceItem(
                id=str(r.get("id", "")),
                title=str(r.get("title", "")),
                url=str(r.get("url", "#")),
                provider=str(r.get("provider", "Curated Reference")),
                type=str(r.get("type", "Guide")),
                difficulty=str(r.get("difficulty", "All Levels")),
                description=str(r.get("description", "")),
                isVerified=bool(r.get("isVerified", True)),
                skills=r.get("skills", []) if isinstance(r.get("skills"), list) else [s.strip() for s in str(r.get("skills", "")).split(",") if s.strip()],
                targetRoles=r.get("targetRoles", []) if isinstance(r.get("targetRoles"), list) else [t.strip() for t in str(r.get("targetRoles", "")).split(",") if t.strip()],
                relevanceScore=r.get("relevanceScore"),
            )
        )

    # 3. Build prompt including retrieved verified resources context
    prompt = build_roadmap_prompt(request, rag_context=rag_context)

    supported_models = [
        "gemini-flash-latest",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
    ]
    candidate_models = [model_name]
    for fallback in supported_models:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    response = None
    last_error = None
    successful_model = model_name

    for candidate in candidate_models:
        for attempt in range(2):
            try:
                logger.info(f"Calling Gemini model '{candidate}' (attempt {attempt + 1}) for {request.durationWeeks}-week roadmap (RAG used: {is_rag_used})")
                response = client.models.generate_content(
                    model=candidate,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=StructuredRoadmap,
                        temperature=0.2,
                    ),
                )
                successful_model = candidate
                logger.info(f"Successfully generated roadmap with model '{candidate}'")
                break
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"Roadmap generation attempt {attempt + 1} with '{candidate}' failed: {err_msg}")
                last_error = e

                if "API_KEY_INVALID" in err_msg or "401" in err_msg or "403" in err_msg:
                    raise GeminiAnalysisError(
                        "Gemini API authentication failed. Please verify that your GEMINI_API_KEY is valid.",
                        status_code=401
                    )
                if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg.lower():
                    if attempt < 1:
                        await asyncio.sleep(1.5)
                        continue
                break
        if response is not None:
            break

    if response is None:
        err_str = str(last_error) if last_error else "All models failed"
        if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
            raise GeminiAnalysisError(
                "Google Gemini servers are currently experiencing high demand. Please try again in a few moments.",
                status_code=503
            )
        elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            raise GeminiAnalysisError(
                "Gemini API rate limit or quota exceeded. Please try again shortly.",
                status_code=429
            )
        elif "timed out" in err_str.lower() or "timeout" in err_str.lower():
            raise GeminiAnalysisError(
                "Communication with Google Gemini API timed out. Upstream services may be experiencing high latency or network degradation. Please try again.",
                status_code=504
            )
        elif "404" in err_str or "not found" in err_str.lower():
            raise GeminiAnalysisError(
                f"Configured Gemini model was not found: {err_str}",
                status_code=404
            )
        else:
            raise GeminiAnalysisError(
                f"Error communicating with Google Gemini API: {err_str}",
                status_code=502
            )

    raw_text = response.text
    if not raw_text or not raw_text.strip():
        raise GeminiAnalysisError(
            "Gemini API returned an empty response. Please re-run roadmap generation.",
            status_code=502
        )

    try:
        if hasattr(response, "parsed") and response.parsed is not None and isinstance(response.parsed, StructuredRoadmap):
            structured_roadmap = response.parsed
        else:
            data_dict = json.loads(raw_text)
            structured_roadmap = StructuredRoadmap.model_validate(data_dict)
    except (json.JSONDecodeError, ValidationError) as val_err:
        logger.error(f"Failed to validate LLM roadmap output against schema: {val_err}")
        raise GeminiAnalysisError(
            f"The AI model roadmap output could not be validated against the required schema: {str(val_err)}",
            status_code=502
        )

    # 4. Anti-hallucination verification & metadata alignment
    if is_rag_used and retrieved_models:
        verified_urls = {r.url.strip().lower(): r for r in retrieved_models if r.url}
        verified_titles = {r.title.strip().lower(): r for r in retrieved_models if r.title}

        for week in structured_roadmap.weeks:
            for res in week.resources:
                u = (res.url or "").strip().lower()
                t = (res.title or "").strip().lower()
                matched = verified_urls.get(u) or verified_titles.get(t)
                if matched:
                    res.isVerified = True
                    res.url = matched.url
                    res.title = matched.title
                    res.provider = matched.provider
                    res.difficulty = matched.difficulty
                    res.label = "Verified Curriculum Resource (RAG)"
                else:
                    res.isVerified = False
                    res.label = "Generic reference (unverified by RAG)"
    else:
        for week in structured_roadmap.weeks:
            for res in week.resources:
                res.isVerified = False
                res.label = "Generic curated reference (unverified by RAG)"

    return RoadmapGenerateResponse(
        success=True,
        status="generated",
        targetRole=request.targetRole,
        durationWeeks=request.durationWeeks,
        modelUsed=successful_model,
        roadmap=structured_roadmap,
        message=f"{request.durationWeeks}-week personalized roadmap generated successfully via Google Gemini.",
        ragStatus=rag_status,
        isRagUsed=is_rag_used,
        ragSourceCount=len(retrieved_models),
        retrievedResources=retrieved_models,
    )

