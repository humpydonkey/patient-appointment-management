from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from app.domain.models import PatientPublic, VerificationState


class ChatRequest(BaseModel):
    session_id: str
    message: str
    trace: bool = False
    client_meta: Optional[Dict[str, str]] = None


class AssistantResponse(BaseModel):
    message: str
    suggestions: List[str] = []


class StateResponse(BaseModel):
    verified: bool
    verification: VerificationState
    patient: PatientPublic
    last_list_snapshot: List[Dict] = []
    session: Dict[str, Any]


class MetaResponse(BaseModel):
    session_id: str
    turn_id: str
    timestamp: str


class ChatResponse(BaseModel):
    assistant: AssistantResponse
    state: StateResponse
    meta: MetaResponse
    trace: Optional[Dict] = None


class ErrorResponse(BaseModel):
    error: str
    retry_after_seconds: Optional[int] = None
