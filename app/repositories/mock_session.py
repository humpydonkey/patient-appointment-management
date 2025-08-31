class MockSessionRepository:
    def __init__(self):
        self.sessions = {}

    def get(self, session_id: str) -> dict | None:
        return self.sessions.get(session_id)

    def set(self, session_id: str, state_dict: dict) -> None:
        self.sessions[session_id] = state_dict

    def delete(self, session_id: str) -> None:
        if session_id in self.sessions:
            del self.sessions[session_id]
