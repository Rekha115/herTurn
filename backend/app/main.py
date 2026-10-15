import os
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
from sqlalchemy.orm import Session

import sys
from pathlib import Path

# Ensure backend directory is in sys.path when executed from any directory or IDE
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from app.resume_parser import (
        parse_resume_bytes,
        ResumeParseError,
        MAX_FILE_SIZE_BYTES
    )
    from app.models import (
        ResumeAnalysisRequest,
        ResumeAnalysisResponse,
        RoadmapGenerateRequest,
        RoadmapGenerateResponse,
        StructuredRoadmap,
        ResourceRetrievalRequest,
        ResourceRetrievalResponse,
        RetrievedResourceItem,
    )
    from app.analyzer import (
        analyze_resume_with_gemini,
        generate_roadmap_with_gemini,
        GeminiAnalysisError,
    )
    from app.rag.retriever import retrieve_verified_resources
    from app.db import init_db
    from app.db.session import get_db
    from app.db.models import User, ResumeAnalysisRecord, RoadmapRecord
    from app.auth.dependencies import get_optional_current_user
    from app.auth.router import router as auth_router
    from app.candidate.router import router as candidate_router
    from app.returnships.router import router as returnships_router
except ImportError:
    from .resume_parser import (
        parse_resume_bytes,
        ResumeParseError,
        MAX_FILE_SIZE_BYTES
    )
    from .models import (
        ResumeAnalysisRequest,
        ResumeAnalysisResponse,
        RoadmapGenerateRequest,
        RoadmapGenerateResponse,
        StructuredRoadmap,
        ResourceRetrievalRequest,
        ResourceRetrievalResponse,
        RetrievedResourceItem,
    )
    from .analyzer import (
        analyze_resume_with_gemini,
        generate_roadmap_with_gemini,
        GeminiAnalysisError,
    )
    from .rag.retriever import retrieve_verified_resources
    from .db import init_db
    from .db.session import get_db
    from .db.models import User, ResumeAnalysisRecord, RoadmapRecord
    from .auth.dependencies import get_optional_current_user
    from .auth.router import router as auth_router
    from .candidate.router import router as candidate_router
    from .returnships.router import router as returnships_router



from contextlib import asynccontextmanager

logger = logging.getLogger("herturn.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager: ensures database tables exist on startup
    and knowledge base is ingested if needed.
    """
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database initialization warning on startup: {e}")

    try:
        from app.rag.ingestion import ingest_resources
        ingest_resources()
    except Exception as e:
        logger.warning(f"Knowledge base auto-ingestion warning on startup: {e}")
    yield


# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title="HerTurn Career Relaunch API",
    description="Backend services for HerTurn: resume text extraction, skills gap analysis, and returnship matching.",
    version="1.0.0",
    lifespan=lifespan
)

def get_allowed_cors_origins() -> list[str]:
    """
    Computes allowed CORS origins based on ENVIRONMENT and ALLOWED_ORIGINS.
    - In production: strictly uses origins explicitly configured in ALLOWED_ORIGINS.
    - In development/testing: includes localhost defaults plus any configured in ALLOWED_ORIGINS.
    """
    environment = (os.getenv("ENVIRONMENT") or "development").strip().lower()
    raw_allowed = os.getenv("ALLOWED_ORIGINS", "")
    explicit_origins = [o.strip() for o in raw_allowed.split(",") if o.strip()]

    if environment == "production":
        if not explicit_origins:
            logger.warning(
                "CRITICAL: ENVIRONMENT=production but ALLOWED_ORIGINS is empty. "
                "CORS will block external cross-origin browser requests."
            )
            return []
        return explicit_origins

    # Development & test defaults
    dev_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    for o in explicit_origins:
        if o not in dev_origins:
            dev_origins.append(o)
    return dev_origins


ALLOWED_CORS_ORIGINS = get_allowed_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register Sub-routers
app.include_router(auth_router)
app.include_router(candidate_router)
app.include_router(returnships_router, prefix="/api/returnships", tags=["returnships"])



# Response Models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    message: str


class ResumeParseResponse(BaseModel):
    success: bool
    status: str
    filename: str
    file_type: str
    file_size_bytes: int
    word_count: int
    extracted_text: str
    message: str
    phase_notice: str


@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint confirming that the backend API service is running.
    """
    return HealthResponse(
        status="healthy",
        service="HerTurn Backend API",
        version="1.0.0",
        message="HerTurn backend is operational and ready to process requests."
    )


@app.post("/api/resume/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)):
    """
    Accepts multipart PDF or DOCX file upload.
    Validates file format and 5MB size limit.
    Extracts text content via PyMuPDF (PDF) or python-docx (DOCX).
    Returns extracted text, word count, metadata, and transparent next-step guidance.
    """
    filename = file.filename or "uploaded_resume.pdf"

    # Read uploaded bytes into memory
    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file stream: {str(e)}"
        )

    file_size = len(file_bytes)

    # Validate size upfront
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of 5 MB ({file_size / (1024 * 1024):.2f} MB received)."
        )

    # Perform parsing and extraction
    try:
        extracted_text, file_type, word_count = parse_resume_bytes(filename, file_bytes)
    except ResumeParseError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while processing the document: {str(e)}"
        )

    return ResumeParseResponse(
        success=True,
        status="extracted",
        filename=filename,
        file_type=file_type,
        file_size_bytes=file_size,
        word_count=word_count,
        extracted_text=extracted_text,
        message="Resume text extracted successfully.",
        phase_notice=(
            "Phase 1 text extraction complete. Deep LLM resume skill gap analysis "
            "and RAG-based roadmap generation can be triggered via POST /api/resume/analyze."
        )
    )


@app.post("/api/resume/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    request: ResumeAnalysisRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyzes resume text and onboarding preferences with Google Gemini.
    Returns structured, factual skill mapping, role gap identification,
    and anti-bias transferable strengths.
    If authenticated, securely associates and persists structured analysis with the user.
    """
    # Validate resume text length
    if not request.resumeText or len(request.resumeText.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text is too brief or empty. Please provide extractable resume content with at least 20 characters."
        )

    try:
        result = await analyze_resume_with_gemini(request)

        # Persist structured analysis if authenticated
        if current_user is not None:
            try:
                analysis_dict = (
                    result.analysis.model_dump()
                    if hasattr(result.analysis, "model_dump")
                    else result.analysis
                )
                record = ResumeAnalysisRecord(
                    user_id=current_user.id,
                    file_name=request.fileName or "uploaded_resume.pdf",
                    file_size_bytes=len(request.resumeText.encode("utf-8")),
                    word_count=len(request.resumeText.split()),
                    target_role=request.preferences.targetRole or result.targetRole,
                    model_used=result.modelUsed,
                    structured_analysis=analysis_dict,
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                result.recordId = record.id
                result.isPersisted = True
            except Exception as db_err:
                db.rollback()
                logger.error(f"Failed to persist resume analysis for user {current_user.id}: {db_err}")

        return result
    except GeminiAnalysisError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while analyzing resume: {str(e)}"
        )


@app.post("/api/roadmap/generate", response_model=RoadmapGenerateResponse)
async def generate_roadmap(
    request: RoadmapGenerateRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a personalized 4-week or 6-week career relaunch roadmap
    using Google Gemini, tailored to the candidate's verified skills,
    identified skill gaps, and target role.
    If authenticated, securely persists the generated curriculum and initializes task progress.
    """
    if request.durationWeeks not in (4, 6):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Duration must be either 4 or 6 weeks (received {request.durationWeeks})."
        )

    if not request.targetRole or len(request.targetRole.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid targetRole is required to generate a personalized roadmap."
        )

    # Performance Optimization: If an authenticated candidate already has a valid completed roadmap
    # for this exact resumeAnalysisId and duration, return it immediately without redundant AI calls.
    if current_user is not None and request.resumeAnalysisId is not None:
        try:
            existing = (
                db.query(RoadmapRecord)
                .filter(
                    RoadmapRecord.user_id == current_user.id,
                    RoadmapRecord.resume_analysis_id == request.resumeAnalysisId,
                    RoadmapRecord.duration_weeks == request.durationWeeks
                )
                .order_by(RoadmapRecord.created_at.desc())
                .first()
            )
            if existing is not None and existing.structured_roadmap:
                logger.info(
                    f"Reusing existing completed roadmap (ID: {existing.id}) for user {current_user.id}, "
                    f"resumeAnalysisId {request.resumeAnalysisId}, duration {request.durationWeeks}w"
                )
                return RoadmapGenerateResponse(
                    success=True,
                    status="generated",
                    targetRole=existing.target_role,
                    durationWeeks=existing.duration_weeks,
                    modelUsed=existing.model_used or "persisted-cache",
                    roadmap=StructuredRoadmap.model_validate(existing.structured_roadmap),
                    message="Roadmap retrieved from existing verified curriculum.",
                    isRagUsed=existing.is_rag_used,
                    ragStatus="verified_rag_used" if existing.is_rag_used else "cached",
                    ragSourceCount=existing.rag_source_count,
                    recordId=existing.id,
                    resumeAnalysisId=existing.resume_analysis_id,
                    generationId=request.generationId,
                    isPersisted=True,
                    isCached=True
                )
        except Exception as cache_err:
            logger.warning(f"Note on roadmap cache lookup: {cache_err}")

    try:
        result = await generate_roadmap_with_gemini(request)
        result.resumeAnalysisId = request.resumeAnalysisId
        result.generationId = request.generationId

        # Persist structured roadmap and initialize task progress if authenticated
        if current_user is not None:
            try:
                initial_progress: Dict[str, bool] = {}
                if result.roadmap and hasattr(result.roadmap, "weeks"):
                    for week in result.roadmap.weeks:
                        for task in getattr(week, "tasks", []):
                            task_id = getattr(task, "id", None)
                            if task_id:
                                initial_progress[str(task_id).strip()] = False

                roadmap_dict = (
                    result.roadmap.model_dump()
                    if hasattr(result.roadmap, "model_dump")
                    else result.roadmap
                )

                valid_resume_analysis_id = None
                if request.resumeAnalysisId:
                    exists = db.query(ResumeAnalysisRecord.id).filter(
                        ResumeAnalysisRecord.id == request.resumeAnalysisId,
                        ResumeAnalysisRecord.user_id == current_user.id
                    ).first()
                    if exists:
                        valid_resume_analysis_id = request.resumeAnalysisId

                record = RoadmapRecord(
                    user_id=current_user.id,
                    resume_analysis_id=valid_resume_analysis_id,
                    target_role=request.targetRole,
                    duration_weeks=request.durationWeeks,
                    model_used=result.modelUsed,
                    is_rag_used=result.isRagUsed,
                    rag_source_count=result.ragSourceCount,
                    structured_roadmap=roadmap_dict,
                    tasks_progress=initial_progress,
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                result.recordId = record.id
                result.isPersisted = True
            except Exception as db_err:
                db.rollback()
                logger.error(f"Failed to persist roadmap record for user {current_user.id}: {db_err}")

        return result
    except GeminiAnalysisError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error while generating roadmap: {str(e)}"
        )



@app.post("/api/resources/retrieve", response_model=ResourceRetrievalResponse)
async def retrieve_resources(request: ResourceRetrievalRequest):
    """
    Retrieves verified educational and career learning resources from the local
    ChromaDB vector store matching the candidate's target role and skill gaps.
    Preserves verified URLs, provider, difficulty, and relevance scoring.
    """
    if not request.targetRole or len(request.targetRole.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid targetRole is required for resource retrieval."
        )

    try:
        result = retrieve_verified_resources(
            target_role=request.targetRole,
            skill_gaps=request.skillGaps,
            top_k=request.topK or 6,
        )

        resources_list = [
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
            for r in result.get("resources", [])
        ]

        return ResourceRetrievalResponse(
            success=True,
            status=result.get("rag_status", "retrieved"),
            targetRole=request.targetRole,
            totalRetrieved=len(resources_list),
            isRagUsed=result.get("is_rag_used", False),
            ragStatus=result.get("rag_status", "unavailable"),
            resources=resources_list,
            message=result.get("message", "Resources retrieved successfully.")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resource retrieval failed: {str(e)}"
        )


