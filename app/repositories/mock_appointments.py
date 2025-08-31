from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.domain.models import Appointment, AppointmentStatus


class MockAppointmentRepository:
    def __init__(self):
        # PST timezone
        pst = ZoneInfo("America/Los_Angeles")
        now = datetime.now(pst)

        # Seed data - use future dates that won't expire during testing
        self.appointments = {
            "a_001": Appointment(
                appointment_id="a_001",
                patient_id="p_001",
                provider_name="Dr. Lee",
                start_time=now
                + timedelta(days=14, hours=10),  # 2 weeks from now at 10 AM
                location="Main Clinic",
                status=AppointmentStatus.scheduled,
            ),
            "a_002": Appointment(
                appointment_id="a_002",
                patient_id="p_001",
                provider_name="Dr. Kim",
                start_time=now
                + timedelta(days=21, hours=14),  # 3 weeks from now at 2 PM
                location="Main Clinic",
                status=AppointmentStatus.scheduled,
            ),
            "a_003": Appointment(
                appointment_id="a_003",
                patient_id="p_001",
                provider_name="Dr. Lee",
                start_time=now - timedelta(days=1, hours=21),  # Yesterday 3 PM
                location="Main Clinic",
                status=AppointmentStatus.past,
            ),
            "a_004": Appointment(
                appointment_id="a_004",
                patient_id="p_002",
                provider_name="Dr. Patel",
                start_time=now
                + timedelta(hours=3),  # Today + 3h (triggers <24h warning)
                location="Main Clinic",
                status=AppointmentStatus.scheduled,
            ),
            "a_005": Appointment(
                appointment_id="a_005",
                patient_id="p_002",
                provider_name="Dr. Kim",
                start_time=now
                + timedelta(days=7, hours=-14, minutes=30),  # Next Mon 9:30 AM
                location="Main Clinic",
                status=AppointmentStatus.confirmed,
            ),
        }

    def list_upcoming_by_patient(
        self, patient_id: str, now: datetime
    ) -> list[Appointment]:
        upcoming = []
        for appt in self.appointments.values():
            if (
                appt.patient_id == patient_id
                and appt.start_time > now
                and appt.status != AppointmentStatus.canceled
            ):
                upcoming.append(appt)
        return sorted(upcoming, key=lambda a: a.start_time)

    def get_by_id(self, appointment_id: str) -> Appointment | None:
        return self.appointments.get(appointment_id)

    def update_status(
        self, appointment_id: str, status: AppointmentStatus
    ) -> Appointment:
        if appointment_id in self.appointments:
            self.appointments[appointment_id].status = status
            return self.appointments[appointment_id]
        raise ValueError(f"Appointment {appointment_id} not found")
