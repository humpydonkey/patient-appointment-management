import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    AssistantResponse,
    StateResponse,
    MetaResponse,
)
from app.domain.models import SessionState, VerificationState, PatientPublic, ConversationTurn
from app.graph.state import GraphState
from app.graph.builder import ConversationGraph
from app.graph.nodes import GraphNodes
from app.services.verification import VerificationService
from app.services.appointments import AppointmentService
from app.repositories.mock_patients import MockPatientRepository
from app.repositories.mock_appointments import MockAppointmentRepository
from app.repositories.mock_session import MockSessionRepository
from app.repositories.mock_otp import MockOTPRepository
from app.utils.time import get_pst_now, create_session_expiry


router = APIRouter()

# Initialize repositories and services
patient_repo = MockPatientRepository()
appointment_repo = MockAppointmentRepository()
session_repo = MockSessionRepository()
otp_repo = MockOTPRepository()

verification_service = VerificationService(patient_repo, otp_repo)
appointment_service = AppointmentService(appointment_repo)

# Initialize graph
nodes = GraphNodes(verification_service, appointment_service)
conversation_graph = ConversationGraph(nodes)


def create_session_state(session_id: str) -> SessionState:
    """Create new session state"""
    now = get_pst_now()
    idle_timeout, absolute_timeout = create_session_expiry(now)

    return SessionState(
        session_id=session_id,
        verified=False,
        patient_public=PatientPublic(),
        patient_id=None,
        verification=VerificationState(),
        last_list_snapshot=[],
        last_intent=None,
        last_activity=now,
        expires_at=absolute_timeout,
        phone_input=None,
        dob_input=None,
        conversation_history=[],
    )


def load_session_state(session_id: str) -> SessionState:
    """Load or create session state"""
    stored = session_repo.get(session_id)
    if stored:
        # Add default values for new fields if they don't exist (backward compatibility)
        if 'phone_input' not in stored:
            stored['phone_input'] = None
        if 'dob_input' not in stored:
            stored['dob_input'] = None
        if 'conversation_history' not in stored:
            stored['conversation_history'] = []
        # Convert back to SessionState
        session_state = SessionState(**stored)

        # Check expiry
        now = get_pst_now()
        if now > session_state.expires_at or (
            now - session_state.last_activity
        ) > timedelta(minutes=15):
            # Session expired - reset verification but keep session
            session_state.verified = False
            session_state.patient_id = None
            session_state.patient_public = PatientPublic()
            session_state.verification = VerificationState()
            session_state.last_list_snapshot = []
            session_state.phone_input = None
            session_state.dob_input = None
            session_state.conversation_history = []

        # Update activity
        session_state.last_activity = now
        return session_state
    else:
        return create_session_state(session_id)


def save_session_state(session_state: SessionState):
    """Save session state"""
    session_repo.set(session_state.session_id, session_state.model_dump())


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        # Load session state
        session_state = load_session_state(request.session_id)

        # Check for lockout
        if verification_service.is_locked_out(session_state):
            lockout_seconds = int(
                (
                    session_state.verification.lockout_until - get_pst_now()
                ).total_seconds()
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "locked_out",
                    "retry_after_seconds": max(lockout_seconds, 0),
                },
            )

        # Create graph state
        now = get_pst_now()
        graph_state = GraphState(
            session_id=request.session_id,
            verified=session_state.verified,
            patient_id=session_state.patient_id,
            patient_public=session_state.patient_public,
            verification=session_state.verification,
            last_list_snapshot=session_state.last_list_snapshot,
            last_intent=session_state.last_intent,
            now=now,
            user_message=request.message,
            phone_input=session_state.phone_input,
            dob_input=session_state.dob_input,
            conversation_history=session_state.conversation_history,
        )

        # Run conversation graph
        result_state = conversation_graph.run(graph_state)

        # Update session state from graph result
        session_state.verified = result_state.verified
        session_state.patient_id = result_state.patient_id
        session_state.patient_public = result_state.patient_public
        session_state.verification = result_state.verification
        session_state.last_list_snapshot = result_state.last_list_snapshot
        session_state.last_intent = result_state.last_intent
        session_state.last_activity = now
        session_state.phone_input = result_state.phone_input
        session_state.dob_input = result_state.dob_input
        
        # Add this conversation turn to history (keep last 50 turns)
        new_turn = ConversationTurn(
            user_message=request.message,
            assistant_message=result_state.assistant_message,
            timestamp=now
        )
        session_state.conversation_history.append(new_turn)
        # Keep only the most recent 50 turns to avoid memory bloat
        if len(session_state.conversation_history) > 50:
            session_state.conversation_history = session_state.conversation_history[-50:]

        # Save updated session
        save_session_state(session_state)

        # Build response
        response = ChatResponse(
            assistant=AssistantResponse(
                message=result_state.assistant_message,
                suggestions=result_state.suggestions,
            ),
            state=StateResponse(
                verified=session_state.verified,
                verification=session_state.verification,
                patient=session_state.patient_public,
                last_list_snapshot=session_state.last_list_snapshot,
                session={
                    "last_activity": session_state.last_activity.isoformat(),
                    "expires_at": session_state.expires_at.isoformat(),
                },
            ),
            meta=MetaResponse(
                session_id=request.session_id,
                turn_id=str(uuid.uuid4()),
                timestamp=now.isoformat(),
            ),
        )

        if request.trace:
            response.trace = {
                "path": ["Guard", "Verify" if not result_state.verified else "Router"]
            }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/dev/reset_session")
def reset_session(request: dict):
    """Dev endpoint to reset session"""
    session_id = request.get("session_id")
    if session_id:
        session_repo.delete(session_id)
        otp_repo.clear_otp(session_id)
    return {"status": "reset"}


@router.get("/dev/state")
def get_session_state(session_id: str):
    """Dev endpoint to get session state"""
    stored = session_repo.get(session_id)
    return stored or {"error": "Session not found"}


@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": get_pst_now().isoformat()}
