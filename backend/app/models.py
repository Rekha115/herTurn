from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CandidatePreferences(BaseModel):
    fullName: Optional[str] = Field(default=None, max_length=120)
    email: Optional[str] = Field(default=None, max_length=150)
    targetRole: str = Field(..., min_length=2, max_length=200, description="Target career role")
    previousRole: Optional[str] = Field(default=None, max_length=200)
    totalExperience: Optional[str] = Field(default=None, max_length=100)
    breakDuration: Optional[str] = Field(default=None, max_length=150)
    workMode: Optional[str] = Field(default=None, max_length=50)
    preferredLocation: Optional[str] = Field(default=None, max_length=150)
    areasOfInterest: Optional[List[str]] = Field(default_factory=list)


class ResumeAnalysisRequest(BaseModel):
    resumeText: str = Field(..., min_length=20, max_length=100_000, description="Extracted resume text")
    preferences: CandidatePreferences
    fileName: Optional[str] = Field(default=None, max_length=255)


# ---------------------------------------------------------------------------
# LLM Structured Output Sub-Models
# ---------------------------------------------------------------------------

class VerifiedSkill(BaseModel):
    name: str = Field(..., description="Skill name explicitly mentioned in the resume")
    category: str = Field(..., description="Category: e.g. Technical, Professional, Leadership, Methodology")
    evidence: str = Field(..., description="Direct quote or specific context from resume supporting this skill")


class ExperienceItem(BaseModel):
    title: str = Field(..., description="Job title, or 'Not Specified'")
    organization: str = Field(..., description="Company, organization, or 'Not Specified'")
    duration: Optional[str] = Field(default=None, description="Dates or timeframe if mentioned")
    highlights: List[str] = Field(default_factory=list, description="Key duties or achievements documented")


class EducationItem(BaseModel):
    degree: str = Field(..., description="Degree or certificate name")
    institution: str = Field(..., description="Institution name, or 'Not Specified'")
    year: Optional[str] = Field(default=None, description="Graduation year if stated")


class TransferableStrength(BaseModel):
    title: str = Field(..., description="Strength title (e.g., Cross-Functional Orchestration)")
    description: str = Field(..., description="How this strength provides value in professional work")
    sourceOfEvidence: str = Field(..., description="Whether evidence stems from career history, projects, or caregiver/hiatus resilience")


class TargetRoleRequirement(BaseModel):
    requirement: str = Field(..., description="Competency typically required for target role")
    currentStatus: str = Field(..., description="'Supported', 'Partially Supported', or 'Needs Strengthening'")
    importance: str = Field(..., description="'High', 'Medium', or 'Critical'")
    reasoning: str = Field(..., description="Assessment based purely on resume evidence")


class SkillGap(BaseModel):
    name: str = Field(..., description="Specific tool, technology, or domain knowledge gap")
    category: str = Field(..., description="e.g. Modern Analytics, Framework, Tooling")
    importance: str = Field(..., description="'Critical', 'High', or 'Medium'")
    explanation: str = Field(..., description="Why this gap matters for the target role and how to bridge it")
    recommendedAction: str = Field(..., description="Concrete learning recommendation for the roadmap")


class ActionRecommendation(BaseModel):
    action: str = Field(..., description="Action title")
    detail: str = Field(..., description="Specific context or guidance")
    priority: str = Field(default="Medium", description="'High', 'Medium', or 'Low'")


# ---------------------------------------------------------------------------
# Complete Structured LLM Output Schema
# ---------------------------------------------------------------------------

class StructuredLLMAnalysis(BaseModel):
    resumeSummary: str = Field(..., description="Fact-based summary of candidate's documented career history")
    extractedExperience: List[ExperienceItem] = Field(default_factory=list, description="Documented work experiences")
    extractedEducation: List[EducationItem] = Field(default_factory=list, description="Documented education/credentials")
    verifiedSkills: List[VerifiedSkill] = Field(default_factory=list, description="Skills explicitly found in the resume")
    transferableStrengths: List[TransferableStrength] = Field(default_factory=list, description="Transferable competencies with supporting evidence")
    targetRoleRequirements: List[TargetRoleRequirement] = Field(default_factory=list, description="Target role competencies evaluation")
    skillGaps: List[SkillGap] = Field(default_factory=list, description="Actionable gaps to bridge for target role")
    suggestedNextSteps: List[ActionRecommendation] = Field(default_factory=list, description="Immediate next steps")
    evidenceNotes: str = Field(..., description="Explicit notes on facts found vs inferences, and missing fields")


# ---------------------------------------------------------------------------
# API Response Model
# ---------------------------------------------------------------------------

class ResumeAnalysisResponse(BaseModel):
    success: bool
    status: str
    modelUsed: str
    targetRole: str
    analysis: StructuredLLMAnalysis
    message: str
    recordId: Optional[int] = Field(default=None, description="Persisted record ID when user is authenticated")
    isPersisted: bool = Field(default=False, description="Whether analysis was persisted to the database")


# ---------------------------------------------------------------------------
# Roadmap Pydantic Models (POST /api/roadmap/generate)
# ---------------------------------------------------------------------------

class RoadmapTaskItem(BaseModel):
    id: str = Field(..., description="Unique task identifier, e.g. 'w1-t1'")
    text: str = Field(..., description="Actionable task description")
    completed: bool = Field(default=False, description="Initial completion status")


class RoadmapResourceItem(BaseModel):
    title: str = Field(..., description="Resource or guide title")
    type: str = Field(default="Guide / Reference", description="Resource type: e.g. 'Official Docs', 'Interactive Lab', 'Framework Guide'")
    url: str = Field(default="#", description="Safe external reference URL")
    isExternal: bool = Field(default=True)
    label: str = Field(default="Generic suggested reference (unverified by RAG)", description="Clear label noting resource status")
    provider: Optional[str] = Field(default=None, description="Resource provider or platform")
    difficulty: Optional[str] = Field(default=None, description="Difficulty level, e.g. Beginner, Intermediate")
    isVerified: bool = Field(default=False, description="Whether resource was retrieved from verified knowledge base")


class RoadmapWeek(BaseModel):
    weekNumber: int = Field(..., ge=1, le=12, description="Week number")
    title: str = Field(..., description="Week title")
    theme: str = Field(..., description="Weekly focus theme")
    weeklyGoal: str = Field(..., description="Primary weekly goal or learning objective")
    commitment: str = Field(default="6–8 hours", description="Estimated weekly time commitment")
    topics: List[str] = Field(default_factory=list, description="Core concepts and learning topics")
    tasks: List[RoadmapTaskItem] = Field(..., min_length=1, description="Actionable tasks and milestone checkpoints")
    expectedDeliverable: str = Field(..., description="Tangible artifact or outcome to showcase, e.g. PRD, portfolio project, case study")
    skillGapAddressed: str = Field(..., description="Specific candidate skill gap this week bridges")
    resources: List[RoadmapResourceItem] = Field(default_factory=list, description="General learning resources")


class StructuredRoadmap(BaseModel):
    targetRole: str = Field(..., description="Target role for which roadmap is built")
    durationWeeks: int = Field(..., description="Duration in weeks (4 or 6)")
    personalizedSummary: str = Field(..., description="Tailored roadmap summary directly referencing candidate background")
    weeks: List[RoadmapWeek] = Field(..., description="Week-by-week curriculum modules")


class RoadmapGenerateRequest(BaseModel):
    targetRole: str = Field(..., min_length=2, max_length=200, description="Target career role")
    durationWeeks: int = Field(default=4, description="Duration in weeks: must be 4 or 6")
    analysis: Optional[StructuredLLMAnalysis] = Field(default=None, description="Output from resume analysis if available")
    verifiedSkills: Optional[List[str]] = Field(default_factory=list, description="List of verified skills from resume")
    skillGaps: Optional[List[str]] = Field(default_factory=list, description="List of identified skill gaps to bridge")
    preferences: Optional[CandidatePreferences] = Field(default=None, description="Candidate preferences and background context")
    resumeAnalysisId: Optional[int] = Field(default=None, description="Linked resume analysis record ID")
    generationId: Optional[str] = Field(default=None, description="Client generation tracking identifier")


# ---------------------------------------------------------------------------
# RAG Retrieval Pydantic Models (POST /api/resources/retrieve)
# ---------------------------------------------------------------------------

class RetrievedResourceItem(BaseModel):
    id: str = Field(..., description="Unique resource ID")
    title: str = Field(..., description="Resource title")
    url: str = Field(..., description="Canonical verified URL")
    provider: str = Field(..., description="Resource author or platform")
    type: str = Field(default="Guide", description="Resource type")
    difficulty: str = Field(default="All Levels", description="Difficulty level")
    description: Optional[str] = Field(default="", description="Resource description")
    isVerified: bool = Field(default=True, description="Whether resource URL and content have been verified")
    skills: List[str] = Field(default_factory=list, description="Relevant skills covered")
    targetRoles: List[str] = Field(default_factory=list, description="Target career roles")
    relevanceScore: Optional[float] = Field(default=None, description="Normalized retrieval relevance score (0-1)")


class ResourceRetrievalRequest(BaseModel):
    targetRole: str = Field(..., min_length=2, max_length=200, description="Target career role")
    skillGaps: Optional[List[str]] = Field(default_factory=list, description="Specific candidate skill gaps")
    topK: Optional[int] = Field(default=6, ge=1, le=20, description="Max number of resources to retrieve")


class ResourceRetrievalResponse(BaseModel):
    success: bool
    status: str
    targetRole: str
    totalRetrieved: int
    isRagUsed: bool
    ragStatus: str
    resources: List[RetrievedResourceItem]
    message: str


class RoadmapGenerateResponse(BaseModel):
    success: bool
    status: str
    targetRole: str
    durationWeeks: int
    modelUsed: str
    roadmap: StructuredRoadmap
    message: str
    ragStatus: str = Field(default="unavailable", description="'verified_rag_used', 'empty_results', 'rag_disabled', 'unavailable'")
    isRagUsed: bool = Field(default=False, description="Whether verified RAG context was retrieved and injected")
    ragSourceCount: int = Field(default=0, description="Number of verified resources retrieved")
    retrievedResources: List[RetrievedResourceItem] = Field(default_factory=list, description="List of verified resources retrieved for roadmap")
    recordId: Optional[int] = Field(default=None, description="Persisted record ID when user is authenticated")
    resumeAnalysisId: Optional[int] = Field(default=None, description="Linked resume analysis ID")
    generationId: Optional[str] = Field(default=None, description="Echoed client generation tracking identifier")
    isPersisted: bool = Field(default=False, description="Whether roadmap was persisted to the database")
    isCached: bool = Field(default=False, description="Whether roadmap was served from existing valid persisted record")


# ---------------------------------------------------------------------------
# Authentication Pydantic Models (POST /api/auth/register, /api/auth/login, /api/auth/me)
# ---------------------------------------------------------------------------

class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=150, description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Plaintext password (min 8 chars)")
    fullName: Optional[str] = Field(default=None, max_length=120, description="Candidate full name")
    targetRole: Optional[str] = Field(default="Product Operations & Strategy Lead", max_length=200, description="Target career role")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = v.strip().lower()
        if "@" not in clean or "." not in clean.split("@")[-1]:
            raise ValueError("Please provide a valid email address.")
        return clean

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLoginRequest(BaseModel):
    email: str = Field(..., description="Account email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class CandidateProfileResponse(BaseModel):
    id: int
    targetRole: str
    previousRole: Optional[str] = None
    totalExperience: Optional[str] = None
    breakDuration: Optional[str] = None
    workMode: Optional[str] = None
    preferredLocation: Optional[str] = None
    areasOfInterest: List[str] = Field(default_factory=list)


class UserProfileResponse(BaseModel):
    id: int
    email: str
    fullName: Optional[str] = None
    isActive: bool
    createdAt: Optional[str] = None
    candidateProfile: Optional[CandidateProfileResponse] = None


class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    expiresInMinutes: int
    user: UserProfileResponse
    message: str = "Authentication successful"


# ---------------------------------------------------------------------------
# Candidate Persistent History & Roadmap Progress Models
# ---------------------------------------------------------------------------

class CandidateAnalysisItem(BaseModel):
    id: int
    fileName: Optional[str] = None
    fileSizeBytes: Optional[int] = None
    wordCount: Optional[int] = None
    targetRole: Optional[str] = None
    modelUsed: Optional[str] = None
    structuredAnalysis: Any
    createdAt: str


class CandidateAnalysesResponse(BaseModel):
    success: bool = True
    totalCount: int
    analyses: List[CandidateAnalysisItem]
    message: str = "Candidate analyses retrieved successfully."


class CandidateRoadmapResponse(BaseModel):
    success: bool = True
    hasRoadmap: bool
    roadmapId: Optional[int] = None
    resumeAnalysisId: Optional[int] = None
    targetRole: Optional[str] = None
    durationWeeks: Optional[int] = None
    modelUsed: Optional[str] = None
    isRagUsed: Optional[bool] = None
    ragSourceCount: Optional[int] = None
    roadmap: Optional[Any] = None
    tasksProgress: Dict[str, bool] = Field(default_factory=dict)
    completedCount: int = 0
    totalTasksCount: int = 0
    completionPercentage: float = 0.0
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    message: str = "Candidate roadmap retrieved."


class RoadmapProgressUpdateRequest(BaseModel):
    roadmapId: Optional[int] = None
    taskId: Optional[str] = None
    completed: Optional[bool] = None
    tasksProgress: Optional[Dict[str, bool]] = None


class CandidateRoadmapProgressResponse(BaseModel):
    success: bool = True
    roadmapId: int
    tasksProgress: Dict[str, bool]
    completedCount: int
    totalTasksCount: int
    completionPercentage: float
    message: str = "Roadmap task progress updated successfully."


# ============================================================================
# Phase 3 - Step 4: Returnships Catalog, Matching & Bookmarking Schemas
# ============================================================================

class ReturnshipItem(BaseModel):
    id: str
    company: str
    logoInitial: str
    logoBg: str
    roleTitle: str
    roleCategory: Optional[str] = "Operations & Strategy"
    industry: Optional[str] = "Technology"
    location: str
    workArrangement: str  # "Hybrid" | "Remote" | "On-site"
    type: str  # "verified" | "sample"
    verificationStatus: str
    duration: str
    stipend: str
    minBreakRequired: str
    minExperience: str
    experienceLevel: Optional[str] = None
    verificationDate: Optional[str] = None
    skills: List[str]
    description: str
    sourceUrl: Optional[str] = None
    isLive: bool = True
    badgeColor: str


class ReturnshipsListResponse(BaseModel):
    success: bool = True
    total: int
    verifiedCount: int
    sampleCount: int
    allSkills: List[str]
    categories: List[str] = Field(default_factory=list)
    items: List[ReturnshipItem]
    message: str = "Returnships retrieved successfully."


class ReturnshipMatchRequest(BaseModel):
    targetRole: Optional[str] = None
    verifiedSkills: List[str] = Field(default_factory=list)
    experienceYears: Optional[Union[int, float, str]] = None
    breakDuration: Optional[str] = None
    preferredWorkMode: Optional[str] = None
    location: Optional[str] = None
    roleCategory: Optional[str] = None
    search: Optional[str] = None
    transferableSkills: List[str] = Field(default_factory=list)


class MatchedReturnshipItem(ReturnshipItem):
    matchScore: int  # 0 to 100 percentage
    matchedSkills: List[str] = Field(default_factory=list)
    skillsToBridge: List[str] = Field(default_factory=list)
    eligibilityStatus: str  # "Eligible", "Likely Eligible", "Review Requirements", "Sample Demonstration"
    matchRationale: str


class ReturnshipMatchResponse(BaseModel):
    success: bool = True
    total: int
    recommendationNotice: str = (
        "HerTurn match scores are heuristic recommendations to assist career returnees with learning prioritization and application planning. They are not hiring guarantees or formal application screenings."
    )
    candidateProfileSummary: Dict[str, Any]
    items: List[MatchedReturnshipItem]
    message: str = "Candidate returnship matches computed successfully."


class SavedReturnshipItem(BaseModel):
    id: int
    returnshipId: str
    savedAt: str
    notes: Optional[str] = None
    opportunity: Optional[ReturnshipItem] = None


class SavedReturnshipsResponse(BaseModel):
    success: bool = True
    count: int
    savedIds: List[str]
    items: List[SavedReturnshipItem]
    message: str = "Saved opportunities retrieved successfully."


class BookmarkToggleResponse(BaseModel):
    success: bool = True
    saved: bool
    returnshipId: str
    message: str


