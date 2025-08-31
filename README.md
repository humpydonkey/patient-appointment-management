# Patient Appointment Management API

A conversational AI backend service for healthcare providers, built with FastAPI and a custom state machine. Allows patients to manage their appointments through natural language interactions.

## Features

- **Identity Verification**: Secure two-step verification (phone + DOB, then name confirmation)
- **OTP Security**: Risk-based OTP for failed verification attempts with lockout protection
- **Appointment Management**: List, confirm, and cancel appointments with natural language
- **Conversational Flow**: Free navigation between actions with context awareness
- **Session Management**: Automatic timeout and state persistence
- **PHI Protection**: All personally identifiable information is masked in responses

## Quick Start

### Backend Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key:
   # OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the server:**
   ```bash
   uv run python -m app.main
   ```

### Frontend Setup (Optional)

4. **Install frontend dependencies:**
   ```bash
   cd frontend
   pnpm install
   ```

5. **Start the React development server:**
   ```bash
   pnpm start
   ```

6. **Open the web interface:**
   Navigate to [http://localhost:3000](http://localhost:3000)

### API Testing (Alternative)

**Test via curl:**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_123", 
    "message": "Hello, I need help with my appointments"
  }'
```

## API Endpoints

### Main Chat Endpoint
- `POST /chat` - Main conversational interface

### Development Endpoints
- `POST /dev/reset_session` - Reset a session for testing
- `GET /dev/state?session_id=...` - View session state
- `GET /health` - Health check

## Example Conversation Flow

1. **Start conversation** (triggers verification):
   ```
   User: "Hello, I need help with my appointments"
   Assistant: "To verify your identity, I'll need your phone number and date of birth. What's your phone number?"
   ```

2. **Identity verification**:
   ```
   User: "My phone is 415-555-0123 and DOB is 07/14/1985"
   Assistant: "I found your record. Is your name John Adam Doe? Please say yes to confirm."
   ```

3. **Appointment management**:
   ```
   User: "Yes, that's me"
   Assistant: "Perfect! I've confirmed your identity. How can I help with your appointments?"
   
   User: "List my appointments"
   Assistant: "Here are your upcoming appointments:
   1. Thu, Sep 12, 10:00 AM — Dr. Lee — Scheduled
   2. Wed, Oct 2, 2:00 PM — Dr. Kim — Scheduled"
   
   User: "Confirm #1"
   Assistant: "✅ Confirmed! Your Thu, Sep 12, 10:00 AM appointment with Dr. Lee is now confirmed."
   ```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

Tests cover:
- Verification flow and OTP handling
- Appointment operations (list/confirm/cancel)
- Session management and expiry
- Intent routing and conversation flow

## Mock Data

The system includes pre-seeded mock data:

**Patients:**
- John Adam Doe: `(415) 555-0123`, DOB: `07/14/1985`
- Maria G. Santos: `(415) 555-0999`, DOB: `02/01/1990`

**Test Scenarios:**
- Multiple upcoming appointments
- <24h cancellation warnings
- Already confirmed appointments
- Session timeouts and lockouts

## Architecture

- **FastAPI**: Web framework and API layer
- **Pydantic**: Data validation and serialization  
- **Custom State Machine**: Conversation flow management
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic encapsulation
- **Mock Implementations**: In-memory data for development
- **React Frontend**: Optional web interface for testing
- **OpenAI Integration**: GPT-4o-mini for natural language processing

## Security Features

- Phone number normalization to E.164 format
- Failed attempt tracking with progressive lockout
- OTP generation with SHA-256 hashing
- Session expiry (15min idle, 30min absolute)
- PHI masking in all responses
- Audit logging (non-PHI events only)

## Time Zone

All appointments are displayed in PST (America/Los_Angeles) timezone.
