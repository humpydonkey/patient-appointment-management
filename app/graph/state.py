from datetime import datetime
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel
from app.domain.models import PatientPublic, VerificationState, ConversationTurn


class GraphState(BaseModel):
    """State object passed through the LangGraph"""

    # Session tracking
    session_id: str
    verified: bool = False
    patient_id: Optional[str] = None
    patient_public: PatientPublic = PatientPublic()
    verification: VerificationState = VerificationState()
    last_list_snapshot: List[Dict] = []  # [{ordinal: int, appointment_id: str}]
    last_intent: Optional[
        Literal["verify", "list", "confirm", "cancel", "help", "smalltalk", "fallback"]
    ] = None

    # Current turn data
    now: datetime
    user_message: str
    assistant_message: str = ""
    suggestions: List[str] = []

    # Flow control
    next_action: Optional[str] = None
    error_message: Optional[str] = None

    # Extracted entities for appointment actions
    ordinal: Optional[int] = None
    appointment_id: Optional[str] = None
    otp_code: Optional[str] = None
    phone_input: Optional[str] = None
    dob_input: Optional[str] = None
    confirmation_needed: bool = False
    conversation_history: List[ConversationTurn] = []
