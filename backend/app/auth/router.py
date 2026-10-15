import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.db.models import User, CandidateProfile
from app.models import (
    UserRegisterRequest,
    UserLoginRequest,
    UserProfileResponse,
    CandidateProfileResponse,
    TokenResponse,
)
from .security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_token_expire_minutes,
)
from .dependencies import get_current_user

logger = logging.getLogger("herturn.auth.router")

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def serialize_user_profile(user: User) -> UserProfileResponse:
    """Helper to convert SQLAlchemy User and CandidateProfile to Pydantic UserProfileResponse."""
    profile_response = None
    if user.candidate_profile:
        cp = user.candidate_profile
        profile_response = CandidateProfileResponse(
            id=cp.id,
            targetRole=cp.target_role,
            previousRole=cp.previous_role,
            totalExperience=cp.total_experience,
            breakDuration=cp.break_duration,
            workMode=cp.work_mode,
            preferredLocation=cp.preferred_location,
            areasOfInterest=cp.areas_of_interest if isinstance(cp.areas_of_interest, list) else []
        )

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        fullName=user.full_name,
        isActive=user.is_active,
        createdAt=user.created_at.isoformat() if user.created_at else None,
        candidateProfile=profile_response
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new candidate user",
    description="Registers a new candidate, hashes their password with bcrypt, initializes their profile, and issues a JWT token."
)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    # 1. Enforce unique email check
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in instead."
        )

    # 2. Hash password securely
    hashed_password = get_password_hash(request.password)

    # 3. Create User record
    new_user = User(
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.fullName.strip() if request.fullName else None,
        is_active=True
    )

    # 4. Automatically create CandidateProfile
    new_profile = CandidateProfile(
        target_role=request.targetRole.strip() if request.targetRole else "Product Operations & Strategy Lead",
        work_mode="Hybrid",
        areas_of_interest=[]
    )
    new_user.candidate_profile = new_profile

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"IntegrityError during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected database error during user creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete user registration. Please try again."
        )

    # 5. Issue signed JWT access token
    access_token = create_access_token(
        subject=str(new_user.id),
        extra_claims={"email": new_user.email}
    )
    expire_minutes = get_token_expire_minutes()

    return TokenResponse(
        accessToken=access_token,
        tokenType="Bearer",
        expiresInMinutes=expire_minutes,
        user=serialize_user_profile(new_user),
        message="Account created successfully."
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate existing user",
    description="Validates candidate credentials and returns a signed JWT access token and profile info."
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    # 1. Lookup user by normalized email
    user = db.query(User).filter(User.email == request.email).first()

    # 2. Verify password (timing-safe check via bcrypt)
    if user is None or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 3. Check active account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated. Please contact support."
        )

    # 4. Generate signed JWT token
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"email": user.email}
    )
    expire_minutes = get_token_expire_minutes()

    return TokenResponse(
        accessToken=access_token,
        tokenType="Bearer",
        expiresInMinutes=expire_minutes,
        user=serialize_user_profile(user),
        message="Signed in successfully."
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current authenticated user profile",
    description="Validates Bearer token and returns the current user profile and candidate settings."
)
def get_me(current_user: User = Depends(get_current_user)):
    return serialize_user_profile(current_user)
