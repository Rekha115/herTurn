import pytest
from sqlalchemy import create_engine, inspect, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.models import (
    User,
    CandidateProfile,
    ResumeAnalysisRecord,
    RoadmapRecord,
    SavedReturnship
)
from app.db.session import init_db


@pytest.fixture
def test_db():
    """
    Creates an isolated in-memory SQLite database with foreign key support
    for each test function, ensuring complete isolation.
    """
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Enable SQLite foreign key enforcement
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    init_db(target_engine=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_init_db_creates_all_tables():
    """Verify that init_db creates all 5 required tables with expected schema."""
    engine = create_engine("sqlite:///:memory:")
    init_db(target_engine=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    expected_tables = {
        "users",
        "candidate_profiles",
        "resume_analysis_records",
        "roadmap_records",
        "saved_returnships"
    }
    assert expected_tables.issubset(set(tables))


def test_user_creation_and_unique_email_constraint(test_db):
    """Verify User model creation and rejection of duplicate emails."""
    user1 = User(
        email="priya.sharma@example.com",
        hashed_password="hashed_secure_password_123",
        full_name="Priya Sharma",
        is_active=True
    )
    test_db.add(user1)
    test_db.commit()
    test_db.refresh(user1)

    assert user1.id is not None
    assert user1.email == "priya.sharma@example.com"
    assert user1.created_at is not None

    # Attempt to create another user with identical email
    user2 = User(
        email="priya.sharma@example.com",
        hashed_password="another_password_456",
        full_name="Duplicate Priya"
    )
    test_db.add(user2)
    with pytest.raises(IntegrityError):
        test_db.commit()

    test_db.rollback()


def test_user_and_candidate_profile_relationship(test_db):
    """Verify 1-to-1 relationship between User and CandidateProfile."""
    user = User(
        email="ananya.iyer@example.com",
        hashed_password="secure_password_hash",
        full_name="Ananya Iyer"
    )
    profile = CandidateProfile(
        target_role="Product Operations & Strategy Lead",
        previous_role="Senior Business Analyst",
        total_experience="6 years",
        break_duration="3 years (Caregiving)",
        work_mode="Hybrid",
        preferred_location="Bengaluru",
        areas_of_interest=["Product Discovery", "Metrics", "Agile Operations"]
    )
    user.candidate_profile = profile

    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    assert user.candidate_profile is not None
    assert user.candidate_profile.target_role == "Product Operations & Strategy Lead"
    assert user.candidate_profile.user_id == user.id
    assert user.candidate_profile.areas_of_interest == ["Product Discovery", "Metrics", "Agile Operations"]
    assert profile.user.email == "ananya.iyer@example.com"


def test_cascade_delete_removes_all_child_records(test_db):
    """Verify cascading delete: deleting a user purges profiles, analyses, roadmaps, and bookmarks."""
    user = User(
        email="sneha.patel@example.com",
        hashed_password="secure_hash_sneha",
        full_name="Sneha Patel"
    )
    profile = CandidateProfile(target_role="Data Analyst")
    user.candidate_profile = profile

    analysis = ResumeAnalysisRecord(
        file_name="Sneha_Resume.pdf",
        file_size_bytes=102400,
        word_count=350,
        target_role="Data Analyst",
        model_used="gemini-3.1-flash-lite-preview",
        structured_analysis={"summary": "Experienced analyst with SQL acumen."}
    )
    user.resume_analyses.append(analysis)

    roadmap = RoadmapRecord(
        target_role="Data Analyst",
        duration_weeks=4,
        model_used="gemini-3.1-flash-lite-preview",
        is_rag_used=True,
        rag_source_count=3,
        structured_roadmap={"weeks": [{"weekNumber": 1, "title": "SQL Deep Dive"}]},
        tasks_progress={"w1-t1": True}
    )
    user.roadmaps.append(roadmap)

    bookmark = SavedReturnship(returnship_id="ret-1", notes="Interested in AWS fellowship")
    user.saved_returnships.append(bookmark)

    test_db.add(user)
    test_db.commit()

    user_id = user.id
    assert test_db.query(CandidateProfile).filter_by(user_id=user_id).count() == 1
    assert test_db.query(ResumeAnalysisRecord).filter_by(user_id=user_id).count() == 1
    assert test_db.query(RoadmapRecord).filter_by(user_id=user_id).count() == 1
    assert test_db.query(SavedReturnship).filter_by(user_id=user_id).count() == 1

    # Delete parent user
    test_db.delete(user)
    test_db.commit()

    # All child rows must be automatically removed via CASCADE
    assert test_db.query(User).filter_by(id=user_id).count() == 0
    assert test_db.query(CandidateProfile).filter_by(user_id=user_id).count() == 0
    assert test_db.query(ResumeAnalysisRecord).filter_by(user_id=user_id).count() == 0
    assert test_db.query(RoadmapRecord).filter_by(user_id=user_id).count() == 0
    assert test_db.query(SavedReturnship).filter_by(user_id=user_id).count() == 0


def test_json_columns_serialization_and_retrieval(test_db):
    """Verify that JSON-structured analyses, roadmaps, and checklist maps persist cleanly."""
    user = User(email="kavita.nair@example.com", hashed_password="password_hash_kavita")
    test_db.add(user)
    test_db.commit()

    sample_analysis_payload = {
        "resumeSummary": "Demonstrated expertise in cross-functional finance.",
        "verifiedSkills": [{"name": "Financial Modeling", "category": "Technical"}],
        "skillGaps": [{"name": "Modern BI Tools", "category": "Tooling"}]
    }

    analysis = ResumeAnalysisRecord(
        user_id=user.id,
        file_name="Kavita_Resume.pdf",
        structured_analysis=sample_analysis_payload
    )

    sample_roadmap_payload = {
        "targetRole": "Senior Financial Analyst",
        "durationWeeks": 4,
        "weeks": [{"weekNumber": 1, "theme": "Power BI & Automated Modeling"}]
    }
    progress_map = {"w1-t1": True, "w1-t2": False, "w1-t3": True}

    roadmap = RoadmapRecord(
        user_id=user.id,
        target_role="Senior Financial Analyst",
        duration_weeks=4,
        structured_roadmap=sample_roadmap_payload,
        tasks_progress=progress_map
    )

    test_db.add_all([analysis, roadmap])
    test_db.commit()

    # Re-query from database
    persisted_analysis = test_db.query(ResumeAnalysisRecord).filter_by(user_id=user.id).first()
    persisted_roadmap = test_db.query(RoadmapRecord).filter_by(user_id=user.id).first()

    assert persisted_analysis.structured_analysis == sample_analysis_payload
    assert persisted_analysis.structured_analysis["verifiedSkills"][0]["name"] == "Financial Modeling"

    assert persisted_roadmap.structured_roadmap == sample_roadmap_payload
    assert persisted_roadmap.tasks_progress == {"w1-t1": True, "w1-t2": False, "w1-t3": True}


def test_saved_returnship_unique_constraint(test_db):
    """Verify that a candidate cannot bookmark the exact same returnship twice."""
    user = User(email="roshni.das@example.com", hashed_password="password_hash_roshni")
    test_db.add(user)
    test_db.commit()

    bm1 = SavedReturnship(user_id=user.id, returnship_id="ret-1", notes="First bookmark")
    test_db.add(bm1)
    test_db.commit()

    # Attempt to add duplicate bookmark for the same returnship
    bm2 = SavedReturnship(user_id=user.id, returnship_id="ret-1", notes="Duplicate bookmark")
    test_db.add(bm2)

    with pytest.raises(IntegrityError):
        test_db.commit()

    test_db.rollback()


def test_foreign_key_enforcement_prevents_orphan_rows(test_db):
    """Verify SQLite foreign key enforcement rejects rows with non-existent parent user."""
    orphan_profile = CandidateProfile(
        user_id=999999,  # Non-existent user
        target_role="Software Engineer"
    )
    test_db.add(orphan_profile)

    with pytest.raises(IntegrityError):
        test_db.commit()

    test_db.rollback()


def test_persistence_across_independent_sessions():
    """Verify that data committed in one session persists and can be queried in a new session."""
    engine = create_engine("sqlite:///:memory:")
    init_db(target_engine=engine)
    Session = sessionmaker(bind=engine)

    # Session 1: Write
    session1 = Session()
    user = User(email="persistent.user@example.com", hashed_password="hashed_pass_test")
    session1.add(user)
    session1.commit()
    user_id = user.id
    session1.close()

    # Session 2: Read
    session2 = Session()
    queried_user = session2.query(User).filter_by(id=user_id).first()
    assert queried_user is not None
    assert queried_user.email == "persistent.user@example.com"
    session2.close()
    engine.dispose()
