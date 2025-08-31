# Patient Appointment Management - React Frontend

A React TypeScript frontend for testing the Patient Appointment Management API.

## Features

- **Real-time Chat Interface**: Conversational UI with message history
- **Session Management**: Shows verification status, patient info, and session state
- **Interactive Suggestions**: Click on AI-generated suggestions to send messages
- **Quick Actions**: Pre-defined buttons for common tasks based on verification status
- **Development Tools**: Reset session and view session details
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

1. **Install dependencies:**
   ```bash
   cd frontend
   pnpm install
   ```

2. **Start the development server:**
   ```bash
   pnpm start
   ```

3. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Using the Interface

### Before Verification
- Click "Hello, I need help with my appointments" to start
- Use "My phone is (415) 555-0123 and DOB is 07/14/1985" for test patient
- Confirm identity with "Yes, that's me"

### After Verification
- "List my appointments" - View upcoming appointments
- "Confirm #1" - Confirm first appointment
- "Cancel #2" - Cancel second appointment
- "Help" - Get assistance

### Test Data
The system includes pre-seeded test patients:
- **John Adam Doe**: Phone `(415) 555-0123`, DOB `07/14/1985`
- **Maria G. Santos**: Phone `(415) 555-0999`, DOB `02/01/1990`

## Features Overview

### Chat Interface
- **Message History**: Persistent conversation history
- **Real-time Responses**: Powered by OpenAI GPT-4o-mini
- **Error Handling**: Clear error messages and retry options

### Session Status Panel
- **Verification State**: Shows if patient is verified
- **Patient Info**: Masked phone and name after verification
- **Appointment Count**: Number of appointments in current list
- **Failed Attempts**: Security monitoring

### Quick Actions
- **Context-Aware**: Different actions based on verification status
- **One-Click Testing**: Pre-filled common messages
- **Development Tools**: Session reset and debugging

### API Integration
- **RESTful Communication**: JSON-based API calls
- **Error Handling**: 429 lockout detection and user feedback
- **Session Persistence**: Automatic session ID generation

## Development

### Available Scripts
- `pnpm start` - Start development server
- `pnpm build` - Build for production
- `pnpm test` - Run tests
- `pnpm eject` - Eject from Create React App

### Configuration
The frontend automatically connects to the backend at `http://localhost:8000` through the proxy configuration in `package.json`.

### File Structure
```
frontend/
├── src/
│   ├── App.tsx          # Main application component
│   ├── api.ts           # API client for backend communication
│   ├── types.ts         # TypeScript type definitions
│   ├── index.tsx        # Application entry point
│   └── index.css        # Global styles
├── public/
│   └── index.html       # HTML template
└── package.json         # Dependencies and scripts
```

## Testing Scenarios

### Full Verification Flow
1. Start conversation: "Hello"
2. Provide credentials: "My phone is (415) 555-0123 and DOB is 07/14/1985"
3. Confirm identity: "Yes, that's me"
4. List appointments: "List my appointments"
5. Manage appointments: "Confirm #1" or "Cancel #2"

### OTP Testing
1. Use wrong credentials 3 times to trigger OTP
2. System will show OTP requirement in sidebar
3. Check backend console for OTP code
4. Enter the 6-digit code to complete verification

### Error Scenarios
- Invalid credentials
- Account lockout (429 error)
- Network failures
- Session expiry

The interface provides clear feedback for all scenarios and maintains a smooth user experience.