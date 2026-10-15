"""
HerTurn Returnship Opportunity & Bookmark Router.
Provides search, filtering, explainable candidate matching, and persistent bookmarking.
All user bookmark queries are strictly scoped to the authenticated user ID.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, SavedReturnship, CandidateProfile, ResumeAnalysisRecord
from app.auth.dependencies import get_current_user, get_optional_current_user
from app.models import (
    ReturnshipItem,
    ReturnshipsListResponse,
    ReturnshipMatchRequest,
    ReturnshipMatchResponse,
    SavedReturnshipsResponse,
    SavedReturnshipItem,
    BookmarkToggleResponse,
)
from app.returnships.catalog import (
    get_all_returnships,
    get_returnship_by_id,
    get_distinct_skills,
    get_distinct_categories,
    filter_returnships,
)
from app.returnships.matcher import match_all_returnships

router = APIRouter()


@router.get("", response_model=ReturnshipsListResponse, summary="List and filter returnships")
def list_returnships(
    search: Optional[str] = Query(None, description="Search query across company, role, skills, or city"),
    work_arrangement: Optional[str] = Query(None, alias="workArrangement", description="Filter by Hybrid, Remote, or On-site"),
    type: Optional[str] = Query(None, description="Filter by verified vs sample"),
    skill: Optional[str] = Query(None, description="Filter by required skill"),
    category: Optional[str] = Query(None, description="Filter by role category (e.g. Design & UX, Software Engineering)"),
):
    """
    Retrieve returnship opportunities with optional filters for work arrangement,
    verification type, skill requirements, role category, and search query.
    """
    filtered = filter_returnships(
        search=search,
        work_arrangement=work_arrangement,
        type_=type,
        skill=skill,
        category=category,
    )

    verified_count = sum(1 for item in filtered if item.type == "verified")
    sample_count = sum(1 for item in filtered if item.type == "sample")

    return ReturnshipsListResponse(
        total=len(filtered),
        verifiedCount=verified_count,
        sampleCount=sample_count,
        allSkills=get_distinct_skills(),
        categories=get_distinct_categories(),
        items=filtered,
        message=f"Retrieved {len(filtered)} opportunities.",
    )


@router.post("/match", response_model=ReturnshipMatchResponse, summary="Generate candidate returnship recommendations")
def match_returnships(
    payload: ReturnshipMatchRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute explainable match scores between candidate qualifications and returnship opportunities.
    Uses verified skills, target role, experience, career break duration, and work mode preferences.
    If authenticated and payload fields are missing, automatically leverages the user's stored profile.
    """
    target_role = payload.targetRole
    skills = list(payload.verifiedSkills)
    exp_years = payload.experienceYears
    break_dur = payload.breakDuration
    work_mode = payload.preferredWorkMode
    loc = payload.location
    transferable = list(payload.transferableSkills)

    # Fallback to stored user profile / latest analysis if authenticated and fields missing
    if current_user:
        profile: Optional[CandidateProfile] = current_user.candidate_profile
        if profile:
            if not target_role:
                target_role = profile.target_role
            if not exp_years and profile.total_experience:
                exp_years = profile.total_experience
            if not break_dur and profile.break_duration:
                break_dur = profile.break_duration
            if not work_mode and profile.work_mode:
                work_mode = profile.work_mode

        # Check latest resume analysis for skills and transferable strengths if not provided
        if not skills or not transferable:
            latest_analysis = (
                db.query(ResumeAnalysisRecord)
                .filter(ResumeAnalysisRecord.user_id == current_user.id)
                .order_by(ResumeAnalysisRecord.created_at.desc())
                .first()
            )
            if latest_analysis and latest_analysis.structured_analysis:
                raw = latest_analysis.structured_analysis
                if not skills:
                    raw_skills = raw.get("verifiedSkills") or raw.get("verified_skills") or []
                    for s in raw_skills:
                        if isinstance(s, dict) and "name" in s:
                            skills.append(s["name"])
                        elif isinstance(s, str):
                            skills.append(s)
                if not transferable:
                    raw_trans = raw.get("transferableStrengths") or raw.get("transferable_strengths") or []
                    for t in raw_trans:
                        if isinstance(t, dict) and "title" in t:
                            transferable.append(t["title"])
                        elif isinstance(t, str):
                            transferable.append(t)

    matched_items = match_all_returnships(
        candidate_skills=skills,
        target_role=target_role,
        experience_years=exp_years,
        break_duration=break_dur,
        preferred_work_mode=work_mode,
        location=loc,
        role_category=payload.roleCategory,
        search=payload.search,
        transferable_skills=transferable,
    )

    return ReturnshipMatchResponse(
        total=len(matched_items),
        candidateProfileSummary={
            "targetRole": target_role,
            "skillsCount": len(skills),
            "experienceYears": exp_years,
            "breakDuration": break_dur,
            "preferredWorkMode": work_mode,
            "location": loc,
            "roleCategory": payload.roleCategory,
            "isAuthenticated": bool(current_user),
        },
        items=matched_items,
        message=f"Computed match scores for {len(matched_items)} returnships.",
    )


@router.get("/saved", response_model=SavedReturnshipsResponse, summary="List saved returnship bookmarks")
def list_saved_returnships(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve all bookmarked returnship opportunities for the authenticated candidate.
    Scoped strictly to the user ID obtained from the verified JWT token.
    """
    records = (
        db.query(SavedReturnship)
        .filter(SavedReturnship.user_id == current_user.id)
        .order_by(SavedReturnship.created_at.desc())
        .all()
    )

    items: List[SavedReturnshipItem] = []
    saved_ids: List[str] = []

    for rec in records:
        saved_ids.append(rec.returnship_id)
        opp = get_returnship_by_id(rec.returnship_id)
        items.append(
            SavedReturnshipItem(
                id=rec.id,
                returnshipId=rec.returnship_id,
                savedAt=rec.created_at.isoformat() if rec.created_at else "",
                notes=rec.notes,
                opportunity=opp,
            )
        )

    return SavedReturnshipsResponse(
        count=len(items),
        savedIds=saved_ids,
        items=items,
        message="Saved returnships retrieved successfully.",
    )


@router.post("/save/{returnship_id}", response_model=BookmarkToggleResponse, summary="Save/bookmark a returnship opportunity")
def save_returnship(
    returnship_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save/bookmark a returnship opportunity for the authenticated candidate.
    Prevents duplicates and safely validates that the opportunity exists.
    """
    opp = get_returnship_by_id(returnship_id)
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Returnship opportunity '{returnship_id}' does not exist in catalog.",
        )

    existing = (
        db.query(SavedReturnship)
        .filter(
            SavedReturnship.user_id == current_user.id,
            SavedReturnship.returnship_id == returnship_id,
        )
        .first()
    )

    if existing:
        return BookmarkToggleResponse(
            saved=True,
            returnshipId=returnship_id,
            message="Opportunity is already saved in your bookmarks.",
        )

    saved_rec = SavedReturnship(
        user_id=current_user.id,
        returnship_id=returnship_id,
    )
    db.add(saved_rec)
    db.commit()
    db.refresh(saved_rec)

    return BookmarkToggleResponse(
        saved=True,
        returnshipId=returnship_id,
        message="Opportunity bookmarked successfully.",
    )


@router.delete("/save/{returnship_id}", response_model=BookmarkToggleResponse, summary="Remove a saved returnship bookmark")
def remove_saved_returnship(
    returnship_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove a saved returnship opportunity from candidate bookmarks.
    Scoped strictly to the authenticated user ID.
    """
    existing = (
        db.query(SavedReturnship)
        .filter(
            SavedReturnship.user_id == current_user.id,
            SavedReturnship.returnship_id == returnship_id,
        )
        .first()
    )

    if not existing:
        return BookmarkToggleResponse(
            saved=False,
            returnshipId=returnship_id,
            message="Bookmark not found or already removed.",
        )

    db.delete(existing)
    db.commit()

    return BookmarkToggleResponse(
        saved=False,
        returnshipId=returnship_id,
        message="Bookmark removed successfully.",
    )
