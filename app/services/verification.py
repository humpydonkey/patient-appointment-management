import hashlib
import secrets
from datetime import datetime, timedelta, date
from app.domain.models import Patient, SessionState, PatientPublic
from app.repositories.interfaces import PatientRepository, OTPRepository
from app.utils.masking import create_patient_public
from app.utils.time import get_pst_now


class VerificationService:
    def __init__(self, patient_repo: PatientRepository, otp_repo: OTPRepository):
        self.patient_repo = patient_repo
        self.otp_repo = otp_repo

    def attempt_match(self, phone_e164: str, dob: date) -> Patient | None:
        """Find patient by phone and DOB, return single match or None"""
        matches = self.patient_repo.find_by_phone_and_dob(phone_e164, dob)
        return matches[0] if len(matches) == 1 else None

    def require_otp_if_needed(self, session: SessionState) -> bool:
        """Check if OTP is required based on failed attempts"""
        return session.verification.failed_attempts >= 3

    def send_otp(self, patient: Patient, session: SessionState) -> None:
        """Generate and 'send' OTP (mock implementation)"""
        # Generate 6-digit OTP
        otp_code = str(secrets.randbelow(1000000)).zfill(6)
        otp_hash = hashlib.sha256(otp_code.encode()).hexdigest()

        # Set expiry to 5 minutes
        expires_at = get_pst_now() + timedelta(minutes=5)

        # Store hash (not plaintext)
        self.otp_repo.set_otp(session.session_id, otp_hash, expires_at)

        # Update session state
        session.verification.otp_required = True
        session.verification.otp_expires_at = expires_at
        session.verification.otp_attempts = 0

        # In real implementation, would send SMS here
        print(f"Mock SMS to {patient.phone_e164}: Your verification code is {otp_code}")

    def verify_otp(self, session: SessionState, code: str) -> bool:
        """Verify OTP code against stored hash"""
        stored = self.otp_repo.get_otp(session.session_id)
        if not stored:
            return False

        stored_hash, expires_at = stored

        # Check expiry
        if get_pst_now() > expires_at:
            self.otp_repo.clear_otp(session.session_id)
            return False

        # Check code
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        if code_hash == stored_hash:
            # Success - clear OTP and reset verification state
            self.otp_repo.clear_otp(session.session_id)
            session.verification.otp_required = False
            session.verification.failed_attempts = 0
            session.verification.otp_attempts = 0
            session.verification.lockout_until = None
            return True
        else:
            # Failed attempt
            session.verification.otp_attempts += 1
            if session.verification.otp_attempts >= 3:
                # Lockout for 5 minutes
                session.verification.lockout_until = get_pst_now() + timedelta(
                    minutes=5
                )
                self.otp_repo.clear_otp(session.session_id)
            return False

    def is_locked_out(self, session: SessionState) -> bool:
        """Check if session is locked out"""
        if not session.verification.lockout_until:
            return False
        return get_pst_now() < session.verification.lockout_until

    def mask_identifiers(self, patient: Patient) -> PatientPublic:
        """Create masked version of patient identifiers"""
        return create_patient_public(patient)
