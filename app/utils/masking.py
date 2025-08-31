from app.domain.models import Patient, PatientPublic


def mask_phone(phone_e164: str) -> str:
    """Mask phone number to show only last 4 digits"""
    if len(phone_e164) >= 4:
        return "***-***-" + phone_e164[-4:]
    return "***-***-****"


def mask_dob(dob_str: str) -> str:
    """Mask DOB to show only year and month"""
    if len(dob_str) >= 7:  # YYYY-MM-DD
        return dob_str[:7]  # YYYY-MM
    return "****-**"


def mask_name(full_name: str) -> str:
    """Mask name to show first initial and last name"""
    parts = full_name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return full_name[0] + "." if full_name else "***"


def create_patient_public(patient: Patient) -> PatientPublic:
    """Create masked public version of patient data"""
    return PatientPublic(
        patient_id=patient.patient_id,
        name_masked=mask_name(patient.full_name),
        phone_masked=mask_phone(patient.phone_e164),
        dob_masked=mask_dob(patient.dob.strftime("%Y-%m-%d")),
    )
