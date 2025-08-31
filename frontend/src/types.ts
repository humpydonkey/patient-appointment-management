export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface PatientPublic {
  patient_id: string | null;
  name_masked: string | null;
  phone_masked: string | null;
  dob_masked: string | null;
}

export interface VerificationState {
  failed_attempts: number;
  otp_required: boolean;
  otp_attempts: number;
  otp_expires_at: string | null;
  lockout_until: string | null;
}

export interface SessionState {
  verified: boolean;
  verification: VerificationState;
  patient: PatientPublic;
  last_list_snapshot: Array<{ordinal: number; appointment_id: string}>;
  session: {
    last_activity: string;
    expires_at: string;
  };
}

export interface ChatRequest {
  session_id: string;
  message: string;
  trace?: boolean;
  client_meta?: {
    user_agent?: string;
    app_version?: string;
  };
}

export interface ChatResponse {
  assistant: {
    message: string;
    suggestions: string[];
  };
  state: SessionState;
  meta: {
    session_id: string;
    turn_id: string;
    timestamp: string;
  };
  trace?: any;
}