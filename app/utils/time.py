from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


PST = ZoneInfo("America/Los_Angeles")


def get_pst_now() -> datetime:
    """Get current time in PST"""
    return datetime.now(PST)


def format_appointment_time(dt: datetime) -> str:
    """Format appointment time for display in PST"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=PST)
    elif dt.tzinfo != PST:
        dt = dt.astimezone(PST)

    return dt.strftime("%a, %b %d, %I:%M %p")


def is_within_24_hours(appointment_time: datetime, now: datetime = None) -> bool:
    """Check if appointment is within 24 hours"""
    if now is None:
        now = get_pst_now()

    if appointment_time.tzinfo is None:
        appointment_time = appointment_time.replace(tzinfo=PST)
    if now.tzinfo is None:
        now = now.replace(tzinfo=PST)

    return (appointment_time - now) <= timedelta(hours=24)


def create_session_expiry(now: datetime = None) -> tuple[datetime, datetime]:
    """Create session expiry times (idle timeout, absolute timeout)"""
    if now is None:
        now = get_pst_now()

    idle_timeout = now + timedelta(minutes=15)
    absolute_timeout = now + timedelta(minutes=30)

    return idle_timeout, absolute_timeout
