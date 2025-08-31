from datetime import datetime
from app.domain.models import Appointment, AppointmentStatus
from app.repositories.interfaces import AppointmentRepository
from app.utils.time import get_pst_now, is_within_24_hours


class AppointmentService:
    def __init__(self, appointment_repo: AppointmentRepository):
        self.appointment_repo = appointment_repo

    def list_upcoming(self, patient_id: str, now: datetime = None) -> list[Appointment]:
        """List upcoming appointments for patient"""
        if now is None:
            now = get_pst_now()
        return self.appointment_repo.list_upcoming_by_patient(patient_id, now)

    def confirm(self, appointment_id: str) -> Appointment:
        """Confirm an appointment"""
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")

        # If already confirmed, return idempotently
        if appointment.status == AppointmentStatus.confirmed:
            return appointment

        # Only allow confirming scheduled appointments
        if appointment.status != AppointmentStatus.scheduled:
            raise ValueError(
                f"Cannot confirm appointment with status {appointment.status}"
            )

        return self.appointment_repo.update_status(
            appointment_id, AppointmentStatus.confirmed
        )

    def cancel(
        self, appointment_id: str, now: datetime = None
    ) -> tuple[Appointment, bool]:
        """Cancel an appointment, returns (updated_appointment, is_within_24h)"""
        if now is None:
            now = get_pst_now()

        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")

        # Check if within 24 hours
        within_24h = is_within_24_hours(appointment.start_time, now)

        # Cancel the appointment
        updated_appointment = self.appointment_repo.update_status(
            appointment_id, AppointmentStatus.canceled
        )

        return updated_appointment, within_24h
