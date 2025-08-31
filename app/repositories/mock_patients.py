from datetime import date
from app.domain.models import Patient


class MockPatientRepository:
    def __init__(self):
        # Seed data
        self.patients = {
            "p_001": Patient(
                patient_id="p_001",
                full_name="John Adam Doe",
                phone_e164="+14155550123",
                dob=date(1985, 7, 14),
            ),
            "p_002": Patient(
                patient_id="p_002",
                full_name="Maria G. Santos",
                phone_e164="+14155550999",
                dob=date(1990, 2, 1),
            ),
        }

    def find_by_phone_and_dob(self, phone_e164: str, dob: date) -> list[Patient]:
        matches = []
        for patient in self.patients.values():
            if patient.phone_e164 == phone_e164 and patient.dob == dob:
                matches.append(patient)
        return matches

    def get_by_id(self, patient_id: str) -> Patient | None:
        return self.patients.get(patient_id)
