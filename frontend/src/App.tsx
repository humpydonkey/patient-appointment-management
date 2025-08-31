import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, ChatResponse, SessionState } from './types';
import { apiClient } from './api';

const generateSessionId = () => {
  return 'session_' + Math.random().toString(36).substring(2, 15);
};

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const [sessionState, setSessionState] = useState<SessionState>({
    verified: false,
    verification: {
      failed_attempts: 0,
      otp_required: false,
      otp_attempts: 0,
      otp_expires_at: null,
      lockout_until: null
    },
    patient: {
      patient_id: null,
      name_masked: null,
      phone_masked: null,
      dob_masked: null
    },
    last_list_snapshot: [],
    session: {
      last_activity: new Date().toISOString(),
      expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString()
    }
  });
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (role: 'user' | 'assistant', content: string) => {
    const message: ChatMessage = {
      id: Date.now().toString(),
      role,
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };

  const handleSendMessage = async (messageText?: string) => {
    const text = messageText || inputValue.trim();
    if (!text || isLoading) return;

    setInputValue('');
    setIsLoading(true);
    setError(null);
    
    addMessage('user', text);

    try {
      const response: ChatResponse = await apiClient.sendMessage({
        session_id: sessionId,
        message: text,
        trace: false
      });

      addMessage('assistant', response.assistant.message);
      setSessionState(response.state);
      setSuggestions(response.assistant.suggestions);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      addMessage('assistant', `Error: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleResetSession = async () => {
    try {
      await apiClient.resetSession(sessionId);
      setMessages([]);
      setSessionState({
        verified: false,
        verification: {
          failed_attempts: 0,
          otp_required: false,
          otp_attempts: 0,
          otp_expires_at: null,
          lockout_until: null
        },
        patient: {
          patient_id: null,
          name_masked: null,
          phone_masked: null,
          dob_masked: null
        },
        last_list_snapshot: [],
        session: {
          last_activity: new Date().toISOString(),
          expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString()
        }
      });
      setSuggestions([]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset session');
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getQuickActions = () => {
    if (!sessionState.verified) {
      return [
        "Hello, I need help with my appointments",
        "My phone is (415) 555-0123 and DOB is 07/14/1985",
        "Yes, that's me"
      ];
    } else {
      return [
        "List my appointments",
        "Confirm #1", 
        "Cancel #2",
        "Help"
      ];
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Patient Appointment Management</h1>
        <p>Conversational AI Assistant - Test Interface</p>
      </header>

      <div className="chat-container">
        <div className="chat-area">
          <div className="messages">
            {messages.length === 0 && (
              <div style={{ 
                textAlign: 'center', 
                color: '#64748b', 
                padding: '2rem',
                fontStyle: 'italic'
              }}>
                Start a conversation by saying hello or asking for help with your appointments.
              </div>
            )}
            
            {messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <div className="message-content">
                  {message.content.split('\n').map((line, index) => (
                    <React.Fragment key={index}>
                      {line}
                      {index < message.content.split('\n').length - 1 && <br />}
                    </React.Fragment>
                  ))}
                </div>
                <div className="message-time">
                  {formatTime(message.timestamp)}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="message assistant">
                <div className="message-content">
                  <div className="loading">
                    <div className="spinner"></div>
                    Thinking...
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <div className="input-area">
            <div className="input-container">
              <textarea
                ref={inputRef}
                className="message-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message here..."
                disabled={isLoading}
                rows={1}
              />
              <button
                className="send-button"
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim() || isLoading}
              >
                Send
              </button>
            </div>
            
            {error && (
              <div style={{ 
                marginTop: '0.5rem', 
                padding: '0.5rem', 
                background: '#fee2e2', 
                border: '1px solid #fecaca', 
                borderRadius: '4px', 
                color: '#dc2626', 
                fontSize: '0.875rem' 
              }}>
                {error}
              </div>
            )}
          </div>
        </div>

        <div className="sidebar">
          <div className="panel">
            <h3>Session Status</h3>
            <div className="session-info">
              Session ID: {sessionId.slice(-8)}
            </div>
            
            <div className="status-item">
              <span className="status-label">Verified</span>
              <span className={`status-value ${sessionState.verified ? 'status-verified' : 'status-unverified'}`}>
                {sessionState.verified ? '✓ Yes' : '✗ No'}
              </span>
            </div>
            
            {sessionState.patient.name_masked && (
              <div className="status-item">
                <span className="status-label">Patient</span>
                <span className="status-value">{sessionState.patient.name_masked}</span>
              </div>
            )}
            
            {sessionState.patient.phone_masked && (
              <div className="status-item">
                <span className="status-label">Phone</span>
                <span className="status-value">{sessionState.patient.phone_masked}</span>
              </div>
            )}
            
            <div className="status-item">
              <span className="status-label">Failed Attempts</span>
              <span className="status-value">{sessionState.verification.failed_attempts}</span>
            </div>
            
            {sessionState.verification.otp_required && (
              <div className="status-item">
                <span className="status-label">OTP Required</span>
                <span className="status-value status-unverified">Yes</span>
              </div>
            )}
            
            {sessionState.last_list_snapshot.length > 0 && (
              <div className="status-item">
                <span className="status-label">Appointments</span>
                <span className="status-value">{sessionState.last_list_snapshot.length}</span>
              </div>
            )}
          </div>

          {suggestions.length > 0 && (
            <div className="panel">
              <h3>Suggestions</h3>
              <div className="suggestions">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    className="suggestion-button"
                    onClick={() => handleSendMessage(suggestion)}
                    disabled={isLoading}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="panel">
            <h3>Quick Actions</h3>
            <div className="quick-actions">
              {getQuickActions().map((action, index) => (
                <button
                  key={index}
                  className="quick-action"
                  onClick={() => handleSendMessage(action)}
                  disabled={isLoading}
                >
                  {action}
                </button>
              ))}
            </div>
          </div>

          <div className="panel">
            <h3>Development</h3>
            <div className="quick-actions">
              <button
                className="quick-action"
                onClick={handleResetSession}
                disabled={isLoading}
              >
                Reset Session
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;