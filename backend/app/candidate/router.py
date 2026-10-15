import logging
from typing import Set, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.session import get_db
from app.db.models import User, ResumeAnalysisRecord, RoadmapRecord
from app.auth.dependencies import get_current_user
from app.models import (
    CandidateAnalysesResponse,
    CandidateAnalysisItem,
    CandidateRoadmapResponse,
    RoadmapProgressUpdateRequest,
    CandidateRoadmapProgressResponse,
)

logger = logging.getLogger("herturn.candidate.router")

router = APIRouter(prefix="/api/candidate", tags=["Candidate Management"])


def extract_valid_task_ids(structured_roadmap: Any) -> Set[str]:
    """
    Extracts all legitimate task identifiers from a structured roadmap JSON dictionary.
    Guarantees validation against arbitrary or forged task IDs.
    """
    valid_ids: Set[str] = set()
    if not isinstance(structured_roadmap, dict):
        return valid_ids

    weeks = structured_roadmap.get("weeks", [])
    if isinstance(weeks, list):
        for week in weeks:
            if isinstance(week, dict):
                tasks = week.get("tasks", [])
                if isinstance(tasks, list):
                    for task in tasks:
                        if isinstance(task, dict) and "id" in task and task["id"]:
                            valid_ids.add(str(task["id"]).strip())
    return valid_ids


@router.get(
    "/analyses",
    response_model=CandidateAnalysesResponse,
    summary="List candidate saved resume analyses",
    description="Retrieves all historical resume analyses generated for the currently authenticated candidate, scoped strictly to their user ID."
)
def get_candidate_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = (
        db.query(ResumeAnalysisRecord)
        .filter(ResumeAnalysisRecord.user_id == current_user.id)
        .order_by(ResumeAnalysisRecord.created_at.desc())
        .all()
    )

    items = [
        CandidateAnalysisItem(
            id=rec.id,
            fileName=rec.file_name,
            fileSizeBytes=rec.file_size_bytes,
            wordCount=rec.word_count,
            targetRole=rec.target_role,
            modelUsed=rec.model_used,
            structuredAnalysis=rec.structured_analysis,
            createdAt=rec.created_at.isoformat() if rec.created_at else ""
        )
        for rec in records
    ]

    return CandidateAnalysesResponse(
        success=True,
        totalCount=len(items),
        analyses=items,
        message="Candidate analyses retrieved successfully."
    )


@router.get(
    "/roadmap",
    response_model=CandidateRoadmapResponse,
    summary="Get candidate latest roadmap and task progress",
    description="Retrieves the current candidate's active career relaunch roadmap and live task completion progress."
)
def get_candidate_roadmap(
    resume_analysis_id: Optional[int] = Query(None, alias="resumeAnalysisId", description="Optional filter by specific resume analysis ID"),
    duration_weeks: Optional[int] = Query(None, alias="durationWeeks", description="Optional duration in weeks (4 or 6)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(RoadmapRecord).filter(RoadmapRecord.user_id == current_user.id)
    if resume_analysis_id is not None:
        query = query.filter(RoadmapRecord.resume_analysis_id == resume_analysis_id)
    if duration_weeks is not None:
        query = query.filter(RoadmapRecord.duration_weeks == duration_weeks)

    rec = query.order_by(RoadmapRecord.created_at.desc()).first()

    if rec is None:
        return CandidateRoadmapResponse(
            success=True,
            hasRoadmap=False,
            roadmapId=None,
            resumeAnalysisId=resume_analysis_id,
            targetRole=None,
            durationWeeks=duration_weeks,
            modelUsed=None,
            isRagUsed=None,
            ragSourceCount=None,
            roadmap=None,
            tasksProgress={},
            completedCount=0,
            totalTasksCount=0,
            completionPercentage=0.0,
            createdAt=None,
            updatedAt=None,
            message="No saved roadmap found for this candidate criteria."
        )

    # Calculate completion metrics
    tasks_progress: Dict[str, bool] = dict(rec.tasks_progress or {})
    valid_task_ids = extract_valid_task_ids(rec.structured_roadmap)
    total_count = len(valid_task_ids)
    completed_count = sum(1 for tid in valid_task_ids if tasks_progress.get(tid) is True)
    completion_percentage = (
        round((completed_count / total_count) * 100.0, 1) if total_count > 0 else 0.0
    )

    return CandidateRoadmapResponse(
        success=True,
        hasRoadmap=True,
        roadmapId=rec.id,
        resumeAnalysisId=rec.resume_analysis_id,
        targetRole=rec.target_role,
        durationWeeks=rec.duration_weeks,
        modelUsed=rec.model_used,
        isRagUsed=rec.is_rag_used,
        ragSourceCount=rec.rag_source_count,
        roadmap=rec.structured_roadmap,
        tasksProgress=tasks_progress,
        completedCount=completed_count,
        totalTasksCount=total_count,
        completionPercentage=completion_percentage,
        createdAt=rec.created_at.isoformat() if rec.created_at else None,
        updatedAt=rec.updated_at.isoformat() if rec.updated_at else None,
        message="Candidate roadmap retrieved successfully."
    )


@router.patch(
    "/roadmap/progress",
    response_model=CandidateRoadmapProgressResponse,
    summary="Update task checklist completion state",
    description="Updates task completion checkboxes for the candidate's roadmap, validating task identifiers against the stored curriculum."
)
def update_roadmap_progress(
    request: RoadmapProgressUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Scope query strictly to current_user.id
    query = db.query(RoadmapRecord).filter(RoadmapRecord.user_id == current_user.id)
    if request.roadmapId is not None:
        query = query.filter(RoadmapRecord.id == request.roadmapId)

    rec = query.order_by(RoadmapRecord.created_at.desc()).first()
    if rec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap record not found for this candidate."
        )

    # Validate against actual task IDs present in the roadmap
    valid_task_ids = extract_valid_task_ids(rec.structured_roadmap)

    if request.taskId is None and not request.tasksProgress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'taskId' with 'completed' or 'tasksProgress' map must be provided."
        )

    # Validate single task update
    if request.taskId is not None:
        clean_task_id = request.taskId.strip()
        if clean_task_id not in valid_task_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid task ID '{request.taskId}'. Task does not exist in the candidate's roadmap."
            )
        if request.completed is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Field 'completed' (boolean) is required when updating a specific taskId."
            )

    # Validate batch task map
    if request.tasksProgress:
        for tid in request.tasksProgress:
            clean_tid = str(tid).strip()
            if clean_tid not in valid_task_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid task ID '{tid}'. Task does not exist in the candidate's roadmap."
                )

    # Apply progress updates
    current_progress: Dict[str, bool] = dict(rec.tasks_progress or {})

    if request.taskId is not None and request.completed is not None:
        current_progress[request.taskId.strip()] = bool(request.completed)

    if request.tasksProgress:
        for tid, val in request.tasksProgress.items():
            current_progress[str(tid).strip()] = bool(val)

    rec.tasks_progress = current_progress
    flag_modified(rec, "tasks_progress")

    try:
        db.commit()
        db.refresh(rec)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit roadmap progress update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist roadmap task progress."
        )

    total_count = len(valid_task_ids)
    completed_count = sum(1 for tid in valid_task_ids if current_progress.get(tid) is True)
    completion_percentage = (
        round((completed_count / total_count) * 100.0, 1) if total_count > 0 else 0.0
    )

    return CandidateRoadmapProgressResponse(
        success=True,
        roadmapId=rec.id,
        tasksProgress=current_progress,
        completedCount=completed_count,
        totalTasksCount=total_count,
        completionPercentage=completion_percentage,
        message="Roadmap task progress updated successfully."
    )
