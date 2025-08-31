from datetime import datetime


class MockOTPRepository:
    def __init__(self):
        self.otps = {}  # session_id -> (otp_hash, expires_at)

    def set_otp(self, session_id: str, otp_hash: str, expires_at: datetime) -> None:
        self.otps[session_id] = (otp_hash, expires_at)

    def get_otp(self, session_id: str) -> tuple[str, datetime] | None:
        return self.otps.get(session_id)

    def clear_otp(self, session_id: str) -> None:
        if session_id in self.otps:
            del self.otps[session_id]
