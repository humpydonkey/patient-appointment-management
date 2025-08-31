import pytest
from datetime import datetime, timedelta
from app.graph.state import GraphState
from app.graph.nodes import GraphNodes
from app.services.verification import VerificationService
from app.services.appointments import AppointmentService
from app.repositories.mock_patients import MockPatientRepository
from app.repositories.mock_appointments import MockAppointmentRepository
from app.repositories.mock_otp import MockOTPRepository
from app.utils.time import get_pst_now
from app.llm.mock_client import MockLLMClient
import app.llm.client


@pytest.fixture
def repositories():
    return {
        'patient': MockPatientRepository(),
        'appointment': MockAppointmentRepository(), 
        'otp': MockOTPRepository()
    }


@pytest.fixture(autouse=True)
def mock_llm_client():
    """Replace the global LLM client with mock for testing"""
    original_client = app.llm.client.llm_client
    app.llm.client.llm_client = MockLLMClient()
    yield
    app.llm.client.llm_client = original_client


@pytest.fixture
def services(repositories):
    verification_service = VerificationService(repositories['patient'], repositories['otp'])
    appointment_service = AppointmentService(repositories['appointment'])
    return verification_service, appointment_service


@pytest.fixture
def graph_nodes(services):
    verification_service, appointment_service = services
    return GraphNodes(verification_service, appointment_service)


@pytest.fixture
def base_state():
    return GraphState(
        session_id="test_session",
        now=get_pst_now(),
        user_message="",
        verified=False
    )


def test_guard_node_unverified(graph_nodes, base_state):
    """Test guard node routes to verify for unverified users"""
    state = base_state.model_copy()
    state.verified = False
    
    result = graph_nodes.guard_node(state)
    
    assert result.next_action == "verify"


def test_guard_node_verified(graph_nodes, base_state):
    """Test guard node routes to router for verified users"""
    state = base_state.model_copy()
    state.verified = True
    
    result = graph_nodes.guard_node(state)
    
    assert result.next_action == "router"


def test_router_node_intent_classification(graph_nodes, base_state):
    """Test router node classifies intents correctly"""
    state = base_state.model_copy()
    state.verified = True
    
    test_cases = [
        ("show my appointments", "list"),
        ("list my upcoming visits", "list"),
        ("confirm #1", "confirm"),
        ("confirm my appointment", "confirm"),
        ("cancel #2", "cancel"),
        ("cancel my visit", "cancel"),
        ("help me", "help"),
        ("hello", "smalltalk"),
        ("thank you", "smalltalk"),
        ("something random", "fallback")
    ]
    
    for message, expected_action in test_cases:
        test_state = state.model_copy()
        test_state.user_message = message
        
        result = graph_nodes.router_node(test_state)
        
        assert result.next_action == expected_action, f"Message '{message}' should route to '{expected_action}', got '{result.next_action}'"


def test_list_node_with_appointments(graph_nodes, base_state):
    """Test list node with existing appointments"""
    state = base_state.model_copy()
    state.verified = True
    state.patient_id = "p_001"  # Patient with appointments
    
    result = graph_nodes.list_node(state)
    
    assert result.assistant_message
    assert "appointments" in result.assistant_message.lower()
    assert len(result.last_list_snapshot) > 0
    assert result.next_action == "router"


def test_list_node_no_appointments(graph_nodes, base_state):
    """Test list node with no appointments"""
    state = base_state.model_copy()
    state.verified = True
    state.patient_id = "nonexistent_patient"
    
    result = graph_nodes.list_node(state)
    
    assert result.assistant_message
    assert "don't have any" in result.assistant_message.lower()
    assert len(result.last_list_snapshot) == 0


def test_help_node(graph_nodes, base_state):
    """Test help node provides guidance"""
    state = base_state.model_copy()
    state.verified = True
    
    result = graph_nodes.help_node(state)
    
    assert result.assistant_message
    assert "list" in result.assistant_message.lower()
    assert "confirm" in result.assistant_message.lower() 
    assert "cancel" in result.assistant_message.lower()
    assert len(result.suggestions) > 0


def test_smalltalk_node(graph_nodes, base_state):
    """Test smalltalk node handles greetings"""
    state = base_state.model_copy()
    state.verified = True
    
    test_messages = ["hello", "hi", "thank you", "thanks"]
    
    for message in test_messages:
        test_state = state.model_copy()
        test_state.user_message = message
        
        result = graph_nodes.smalltalk_node(test_state)
        
        assert result.assistant_message
        assert result.next_action == "router"


def test_fallback_node(graph_nodes, base_state):
    """Test fallback node for unclear requests"""
    state = base_state.model_copy()
    state.verified = True
    state.user_message = "something completely unclear"
    
    result = graph_nodes.fallback_node(state)
    
    assert result.assistant_message
    assert "not sure" in result.assistant_message.lower() or "help" in result.assistant_message.lower()
    assert len(result.suggestions) > 0


def test_appointment_reference_resolution(graph_nodes, base_state):
    """Test appointment reference resolution"""
    state = base_state.model_copy()
    state.verified = True
    state.last_list_snapshot = [
        {"ordinal": 1, "appointment_id": "a_001"},
        {"ordinal": 2, "appointment_id": "a_002"}
    ]
    
    # Test ordinal resolution
    state.ordinal = 2
    appointment_id = graph_nodes._resolve_appointment_reference(state)
    assert appointment_id == "a_002"
    
    # Test fallback to first appointment
    state.ordinal = None
    appointment_id = graph_nodes._resolve_appointment_reference(state)
    assert appointment_id == "a_001"