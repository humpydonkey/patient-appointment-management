import pytest
from datetime import datetime, timedelta
from app.domain.models import SessionState, VerificationState, PatientPublic
from app.repositories.mock_session import MockSessionRepository
from app.utils.time import get_pst_now


@pytest.fixture
def session_repo():
    return MockSessionRepository()


def test_session_storage_and_retrieval(session_repo):
    """Test storing and retrieving session state"""
    now = get_pst_now()
    session_id = "test_session_123"
    
    # Create session state
    state = SessionState(
        session_id=session_id,
        verified=True,
        patient_id="p_001",
        last_activity=now,
        expires_at=now + timedelta(minutes=30)
    )
    
    # Store as dict
    session_repo.set(session_id, state.model_dump())
    
    # Retrieve
    stored = session_repo.get(session_id)
    
    assert stored is not None
    assert stored["session_id"] == session_id
    assert stored["verified"] is True
    assert stored["patient_id"] == "p_001"


def test_session_not_found(session_repo):
    """Test retrieving non-existent session"""
    result = session_repo.get("nonexistent_session")
    assert result is None


def test_session_deletion(session_repo):
    """Test deleting session"""
    session_id = "test_session_456"
    
    # Store session
    state_dict = {"session_id": session_id, "verified": False}
    session_repo.set(session_id, state_dict)
    
    # Verify it exists
    assert session_repo.get(session_id) is not None
    
    # Delete it
    session_repo.delete(session_id)
    
    # Verify it's gone
    assert session_repo.get(session_id) is None


def test_session_state_serialization():
    """Test SessionState model serialization"""
    now = get_pst_now()
    
    state = SessionState(
        session_id="test",
        verified=True,
        patient_public=PatientPublic(
            patient_id="p_001",
            name_masked="J. Doe",
            phone_masked="***-***-1234",
            dob_masked="1985-07"
        ),
        verification=VerificationState(
            failed_attempts=1,
            otp_required=False
        ),
        last_list_snapshot=[
            {"ordinal": 1, "appointment_id": "a_001"},
            {"ordinal": 2, "appointment_id": "a_002"}
        ],
        last_activity=now,
        expires_at=now + timedelta(minutes=30)
    )
    
    # Serialize to dict
    state_dict = state.model_dump()
    
    # Should contain all fields
    assert state_dict["session_id"] == "test"
    assert state_dict["verified"] is True
    assert state_dict["patient_public"]["name_masked"] == "J. Doe"
    assert state_dict["verification"]["failed_attempts"] == 1
    assert len(state_dict["last_list_snapshot"]) == 2
    
    # Deserialize back
    restored_state = SessionState(**state_dict)
    
    assert restored_state.session_id == state.session_id
    assert restored_state.verified == state.verified
    assert restored_state.patient_public.name_masked == state.patient_public.name_masked