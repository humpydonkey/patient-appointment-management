import re
from datetime import date


def normalize_phone_to_e164(phone_input: str) -> str:
    """Normalize phone input to E.164 format"""
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone_input)

    # Add country code if missing (assume US)
    if len(digits) == 10:
        digits = "1" + digits
    elif len(digits) == 11 and digits.startswith("1"):
        pass  # Already has country code
    else:
        raise ValueError(f"Invalid phone number format: {phone_input}")

    return "+" + digits


def parse_dob(dob_input: str) -> date:
    """Parse date of birth from various formats to date object"""
    # Try different formats
    formats = [
        "%Y-%m-%d",  # 1985-07-14
        "%m/%d/%Y",  # 07/14/1985
        "%m-%d-%Y",  # 07-14-1985
        "%d/%m/%Y",  # 14/07/1985 (European)
    ]

    for fmt in formats:
        try:
            if fmt == "%Y-%m-%d":
                return date.fromisoformat(dob_input)
            else:
                from datetime import datetime
                return datetime.strptime(dob_input, fmt).date()
        except (ValueError, TypeError):
            continue

    raise ValueError(f"Invalid date format: {dob_input}")
