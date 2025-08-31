import pytest
from datetime import datetime, date, timedelta
from app.services.verification import VerificationService
from app.repositories.mock_patients import MockPatientRepository
from app.repositories.mock_otp import MockOTPRepository
from app.domain.models import SessionState, VerificationState
from app.utils.time import get_pst_now


@pytest.fixture
def patient_repo():
    return MockPatientRepository()


@pytest.fixture
def otp_repo():
    return MockOTPRepository()


@pytest.fixture
def verification_service(patient_repo, otp_repo):
    return VerificationService(patient_repo, otp_repo)


@pytest.fixture
def session_state():
    now = get_pst_now()
    return SessionState(
        session_id="test_session",
        verified=False,
        last_activity=now,
        expires_at=now + timedelta(minutes=30)
    )


def test_attempt_match_success(verification_service):
    """Test successful patient matching"""
    # Use data from mock repo
    phone = "+14155550123"
    dob = date(1985, 7, 14)
    
    patient = verification_service.attempt_match(phone, dob)
    
    assert patient is not None
    assert patient.patient_id == "p_001"
    assert patient.full_name == "John Adam Doe"


def test_attempt_match_failure(verification_service):
    """Test failed patient matching"""
    phone = "+19999999999"  # Non-existent
    dob = date(1990, 1, 1)
    
    patient = verification_service.attempt_match(phone, dob)
    
    assert patient is None


def test_otp_flow(verification_service, session_state, patient_repo):
    """Test complete OTP verification flow"""
    patient = list(patient_repo.patients.values())[0]
    
    # Send OTP
    verification_service.send_otp(patient, session_state)
    
    assert session_state.verification.otp_required is True
    assert session_state.verification.otp_expires_at is not None
    
    # Get the generated OTP from the mock (in real app this would be sent via SMS)
    stored_otp = verification_service.otp_repo.get_otp(session_state.session_id)
    assert stored_otp is not None
    
    # For testing, we need to simulate the OTP code
    # In the real service, the code is only printed in mock, so we'll test with a known hash
    import hashlib
    test_code = "123456"
    test_hash = hashlib.sha256(test_code.encode()).hexdigest()
    
    # Manually set known OTP for testing
    verification_service.otp_repo.set_otp(
        session_state.session_id, 
        test_hash, 
        session_state.verification.otp_expires_at
    )
    
    # Verify OTP
    result = verification_service.verify_otp(session_state, test_code)
    
    assert result is True
    assert session_state.verification.otp_required is False
    assert session_state.verification.failed_attempts == 0


def test_otp_failure_and_lockout(verification_service, session_state, patient_repo):
    """Test OTP failure and lockout mechanism"""
    patient = list(patient_repo.patients.values())[0]
    
    # Send OTP
    verification_service.send_otp(patient, session_state)
    
    # Fail OTP attempts
    for i in range(3):
        result = verification_service.verify_otp(session_state, "wrong_code")
        assert result is False
    
    # After 3 failures, should be locked out
    assert session_state.verification.lockout_until is not None
    assert verification_service.is_locked_out(session_state) is True


def test_mask_identifiers(verification_service, patient_repo):
    """Test patient data masking"""
    patient = list(patient_repo.patients.values())[0]
    
    masked = verification_service.mask_identifiers(patient)
    
    assert masked.patient_id == patient.patient_id
    assert masked.name_masked == "J. Doe"
    assert masked.phone_masked == "***-***-0123"
    assert "1985-07" in masked.dob_masked


def test_require_otp_threshold(verification_service, session_state):
    """Test OTP requirement threshold"""
    # Should not require OTP initially
    assert verification_service.require_otp_if_needed(session_state) is False
    
    # After 3 failures, should require OTP
    session_state.verification.failed_attempts = 3
    assert verification_service.require_otp_if_needed(session_state) is True