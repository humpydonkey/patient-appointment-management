import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.services.appointments import AppointmentService
from app.repositories.mock_appointments import MockAppointmentRepository
from app.domain.models import AppointmentStatus
from app.utils.time import get_pst_now


PST = ZoneInfo("America/Los_Angeles")


@pytest.fixture
def appointment_repo():
    return MockAppointmentRepository()


@pytest.fixture
def appointment_service(appointment_repo):
    return AppointmentService(appointment_repo)


def test_list_upcoming_appointments(appointment_service):
    """Test listing upcoming appointments"""
    now = get_pst_now()
    appointments = appointment_service.list_upcoming("p_001", now)
    
    # Should return future appointments only
    assert len(appointments) >= 1
    for appt in appointments:
        assert appt.start_time > now
        assert appt.status != AppointmentStatus.canceled


def test_list_no_appointments(appointment_service):
    """Test listing appointments for patient with none"""
    now = get_pst_now()
    appointments = appointment_service.list_upcoming("nonexistent_patient", now)
    
    assert len(appointments) == 0


def test_confirm_appointment_success(appointment_service, appointment_repo):
    """Test successful appointment confirmation"""
    # Get a scheduled appointment
    scheduled_appt = None
    for appt in appointment_repo.appointments.values():
        if appt.status == AppointmentStatus.scheduled:
            scheduled_appt = appt
            break
    
    assert scheduled_appt is not None
    
    # Confirm the appointment
    confirmed = appointment_service.confirm(scheduled_appt.appointment_id)
    
    assert confirmed.status == AppointmentStatus.confirmed
    assert confirmed.appointment_id == scheduled_appt.appointment_id


def test_confirm_already_confirmed_appointment(appointment_service, appointment_repo):
    """Test confirming already confirmed appointment (idempotent)"""
    # Get an already confirmed appointment
    confirmed_appt = None
    for appt in appointment_repo.appointments.values():
        if appt.status == AppointmentStatus.confirmed:
            confirmed_appt = appt
            break
    
    assert confirmed_appt is not None
    
    # Confirm again - should be idempotent
    result = appointment_service.confirm(confirmed_appt.appointment_id)
    
    assert result.status == AppointmentStatus.confirmed


def test_confirm_nonexistent_appointment(appointment_service):
    """Test confirming non-existent appointment"""
    with pytest.raises(ValueError, match="not found"):
        appointment_service.confirm("nonexistent_id")


def test_cancel_appointment_success(appointment_service, appointment_repo):
    """Test successful appointment cancellation"""
    # Get a scheduled appointment
    scheduled_appt = None
    for appt in appointment_repo.appointments.values():
        if appt.status == AppointmentStatus.scheduled:
            scheduled_appt = appt
            break
    
    assert scheduled_appt is not None
    
    now = get_pst_now()
    cancelled, within_24h = appointment_service.cancel(scheduled_appt.appointment_id, now)
    
    assert cancelled.status == AppointmentStatus.canceled
    assert isinstance(within_24h, bool)


def test_cancel_within_24_hours(appointment_service, appointment_repo):
    """Test cancelling appointment within 24 hours"""
    # Get appointment that's within 24 hours (a_004 is set to now + 3h)
    near_appt = appointment_repo.get_by_id("a_004")
    assert near_appt is not None
    
    now = get_pst_now()
    cancelled, within_24h = appointment_service.cancel("a_004", now)
    
    assert cancelled.status == AppointmentStatus.canceled
    assert within_24h is True


def test_cancel_nonexistent_appointment(appointment_service):
    """Test cancelling non-existent appointment"""
    with pytest.raises(ValueError, match="not found"):
        appointment_service.cancel("nonexistent_id")