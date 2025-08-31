from enum import Enum
from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional, List, Dict


class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    canceled = "canceled"
    past = "past"


class Appointment(BaseModel):
    appointment_id: str
    patient_id: str
    provider_name: str
    start_time: datetime  # timezone-aware (PST in v1)
    location: Optional[str] = None  # or "Telehealth"
    status: AppointmentStatus
    notes: Optional[str] = None


class Patient(BaseModel):
    patient_id: str
    full_name: str  # canonical on-file name
    phone_e164: str  # +1XXXXXXXXXX
    dob: date


class VerificationState(BaseModel):
    failed_attempts: int = 0
    otp_required: bool = False
    otp_attempts: int = 0
    otp_expires_at: Optional[datetime] = None
    lockout_until: Optional[datetime] = None


class PatientPublic(BaseModel):  # masked safe-to-send
    patient_id: Optional[str] = None
    name_masked: Optional[str] = None
    phone_masked: Optional[str] = None
    dob_masked: Optional[str] = None


class ConversationTurn(BaseModel):
    """Single conversation turn for context"""
    user_message: str
    assistant_message: str
    timestamp: datetime


class SessionState(BaseModel):
    session_id: str
    verified: bool = False
    patient_public: PatientPublic = PatientPublic()
    patient_id: Optional[str] = None
    verification: VerificationState = VerificationState()
    last_list_snapshot: list[dict] = []  # [{ordinal, appointment_id}]
    last_intent: Optional[str] = None
    last_activity: datetime
    expires_at: datetime
    # Verification state persistence
    phone_input: Optional[str] = None
    dob_input: Optional[str] = None
    # Conversation history for context-aware intent classification
    conversation_history: List[ConversationTurn] = []
