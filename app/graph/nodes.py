import re
from datetime import date
from app.graph.state import GraphState
from app.services.verification import VerificationService
from app.services.appointments import AppointmentService
from app.llm.client import llm_client
from app.llm.prompts import (
    SYSTEM_PROMPT,
    ROUTER_PROMPT,
    VERIFY_PROMPT,
    APPOINTMENT_ACTION_PROMPT,
)
from app.utils.normalization import normalize_phone_to_e164, parse_dob
from app.utils.time import format_appointment_time


class GraphNodes:
    def __init__(
        self,
        verification_service: VerificationService,
        appointment_service: AppointmentService,
    ):
        self.verification_service = verification_service
        self.appointment_service = appointment_service

    def guard_node(self, state: GraphState) -> GraphState:
        """Check if user is verified, route accordingly"""
        if not state.verified:
            state.next_action = "verify"
        else:
            state.next_action = "router"
        return state

    def verify_node(self, state: GraphState) -> GraphState:
        """Handle identity verification flow"""
        user_msg = state.user_message.lower()

        # Check if locked out
        if self.verification_service.is_locked_out(state):
            lockout_time = state.verification.lockout_until
            lockout_prompt = f"{VERIFY_PROMPT}\n\nThe user's account is temporarily locked until {lockout_time.strftime('%I:%M %p')} for security. Explain this professionally and empathetically."
            state.assistant_message = llm_client.chat(lockout_prompt, "Account locked")
            return state

        # Handle OTP verification if required
        if state.verification.otp_required:
            # Extract 6-digit code
            otp_match = re.search(r"\b\d{6}\b", state.user_message)
            if otp_match:
                code = otp_match.group()
                if self.verification_service.verify_otp(state, code):
                    # OTP success - user is now verified
                    state.verified = True
                    state.assistant_message = "Thank you! Your identity has been verified. How can I help you with your appointments?"
                    state.suggestions = ["List my appointments", "Get help"]
                    state.next_action = "router"
                else:
                    attempts_left = 3 - state.verification.otp_attempts
                    if attempts_left > 0:
                        state.assistant_message = f"That code isn't correct. You have {attempts_left} attempts remaining. Please enter the 6-digit code sent to your phone."
                    else:
                        state.assistant_message = "Too many failed attempts. Your account is temporarily locked for 5 minutes for security."
            else:
                state.assistant_message = (
                    "Please enter the 6-digit verification code sent to your phone."
                )
            return state

        # Extract phone and DOB from message  
        # Phone patterns: (415) 555-0123, 415-555-0123, 415.555.0123, 4155550123
        phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", state.user_message)
        # DOB patterns: 07/14/1985, 07-14-1985, 1985-07-14
        dob_match = re.search(
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}",
            state.user_message,
        )

        try:
            # Collect phone if not already extracted
            if phone_match and not state.phone_input:
                state.phone_input = normalize_phone_to_e164(phone_match.group())

            # Collect DOB if not already extracted
            if dob_match and not state.dob_input:
                state.dob_input = parse_dob(dob_match.group()).strftime("%Y-%m-%d")

            # If we have both, attempt verification
            if state.phone_input and state.dob_input:
                dob_date = date.fromisoformat(state.dob_input)
                patient = self.verification_service.attempt_match(
                    state.phone_input, dob_date
                )

                if patient:
                    # Ask for name confirmation
                    if (
                        "yes" in user_msg
                        or "correct" in user_msg
                        or "that's me" in user_msg
                    ):
                        # Confirmed - user is verified
                        state.verified = True
                        state.patient_id = patient.patient_id
                        state.patient_public = (
                            self.verification_service.mask_identifiers(patient)
                        )
                        state.assistant_message = f"Perfect! I've confirmed your identity. Your phone ends in **{state.patient_public.phone_masked[-4:]}**. How can I help with your appointments?"
                        state.suggestions = ["List my appointments", "Get help"]
                        state.next_action = "router"
                    else:
                        # Show name for confirmation
                        state.assistant_message = f"I found your record. Is your name **{patient.full_name}**? Please say yes to confirm."
                else:
                    # No match found
                    state.verification.failed_attempts += 1
                    if state.verification.failed_attempts >= 3:
                        # Require OTP
                        # For demo, we'll use the first patient
                        from app.repositories.mock_patients import MockPatientRepository

                        mock_repo = MockPatientRepository()
                        demo_patient = list(mock_repo.patients.values())[0]
                        self.verification_service.send_otp(demo_patient, state)
                        state.assistant_message = "For security, I've sent a 6-digit verification code to your phone ending in **1234**. Please enter the code to continue."
                    else:
                        attempts_left = 3 - state.verification.failed_attempts
                        state.assistant_message = f"I couldn't find a match. Please double-check your information. {attempts_left} attempts remaining."

            else:
                # Ask for missing information
                if not state.phone_input:
                    state.assistant_message = """To verify your identity, I'll need your phone number and date of birth.

Please provide them in one message, for example:
"My phone is (415) 555-0123 and DOB is 07/14/1985"

Or you can provide them separately - what's your phone number?"""
                elif not state.dob_input:
                    state.assistant_message = "Thanks! Now what's your date of birth? Please use MM/DD/YYYY format (example: 07/14/1985)."

        except Exception as e:
            state.assistant_message = """I'm having trouble with that format. Please provide your information in these formats:

**Phone Number:**
• (415) 555-0123
• 415-555-0123  
• 415.555.0123
• 4155550123

**Date of Birth:**
• MM/DD/YYYY (07/14/1985)
• MM-DD-YYYY (07-14-1985)
• YYYY-MM-DD (1985-07-14)

Please try again with both your phone number and date of birth."""

        return state

    def router_node(self, state: GraphState) -> GraphState:
        """Route to appropriate action based on user intent"""
        # Prepare conversation history for context-aware classification
        conversation_context = []
        if hasattr(state, 'conversation_history') and state.conversation_history:
            conversation_context = [
                {
                    "user_message": turn.user_message,
                    "assistant_message": turn.assistant_message
                }
                for turn in state.conversation_history
            ]
        
        # Classify intent using LLM with conversation context
        classification = llm_client.classify_intent(state.user_message, conversation_context)


        # Extract entities
        if classification["entities"].get("ordinal"):
            state.ordinal = classification["entities"]["ordinal"]

        # Route based on intent - normalize to expected values
        if classification["intent"] == "list_appointments":
            state.last_intent = "list"
            state.next_action = "list"
        elif classification["intent"] == "confirm_appointment":
            state.last_intent = "confirm"
            state.next_action = "confirm"
        elif classification["intent"] == "cancel_appointment":
            state.last_intent = "cancel"
            state.next_action = "cancel"
        elif classification["intent"] == "help":
            state.last_intent = "help"
            state.next_action = "help"
        elif classification["intent"] == "smalltalk":
            state.last_intent = "smalltalk"
            state.next_action = "smalltalk"
        else:
            state.last_intent = "fallback"
            state.next_action = "fallback"

        return state

    def list_node(self, state: GraphState) -> GraphState:
        """List upcoming appointments"""
        try:
            appointments = self.appointment_service.list_upcoming(
                state.patient_id, state.now
            )

            if not appointments:
                state.assistant_message = "You don't have any upcoming appointments. Is there anything else I can help you with?"
                state.suggestions = ["Get help"]
            else:
                # Create numbered list and snapshot
                appointment_list = []
                snapshot = []

                for i, appt in enumerate(appointments, 1):
                    time_str = format_appointment_time(appt.start_time)
                    status_str = appt.status.title()
                    appointment_list.append(
                        f"{i}. **{time_str}** — {appt.provider_name} — **{status_str}**"
                    )
                    snapshot.append(
                        {"ordinal": i, "appointment_id": appt.appointment_id}
                    )

                state.last_list_snapshot = snapshot

                appointments_text = "\n".join(appointment_list)
                
                # Generate dynamic suggestions based on actual appointments
                if len(appointments) == 1:
                    # Only one appointment - suggest ordinal #1 and provider name
                    appt = appointments[0]
                    example_suggestions = f"You can say 'Confirm #1' or 'Cancel my appointment with {appt.provider_name}.'"
                    state.suggestions = ["Confirm #1", "Cancel #1", "Get help"]
                elif len(appointments) == 2:
                    # Two appointments - suggest both ordinals
                    appt1, appt2 = appointments[0], appointments[1]
                    example_suggestions = f"You can say 'Confirm #1' or 'Confirm #2' or 'Cancel my appointment with {appt2.provider_name}.'"
                    state.suggestions = ["Confirm #1", "Confirm #2", "Cancel #1", "Cancel #2", "Get help"]
                else:
                    # Multiple appointments - general guidance
                    example_suggestions = f"You can say 'Confirm #1', 'Cancel #2', or reference by provider name."
                    state.suggestions = ["Confirm #1", "Cancel #1", "Get help"]
                
                state.assistant_message = f"Here are your upcoming appointments (PST):\n\n{appointments_text}\n\n{example_suggestions}"

        except Exception as e:
            state.assistant_message = "I'm having trouble retrieving your appointments right now. Please try again in a moment."

        state.next_action = "router"
        return state

    def confirm_node(self, state: GraphState) -> GraphState:
        """Confirm an appointment"""
        try:
            # Resolve appointment reference
            appointment_id = self._resolve_appointment_reference(state)

            if not appointment_id:
                state.assistant_message = "I'm not sure which appointment you'd like to confirm. Could you be more specific? For example, 'Confirm #1' or 'Confirm my Oct 2 appointment'."
                state.next_action = "router"
                return state

            # Confirm the appointment
            appointment = self.appointment_service.confirm(appointment_id)
            time_str = format_appointment_time(appointment.start_time)

            state.assistant_message = f"✅ Confirmed! Your **{time_str}** appointment with **{appointment.provider_name}** is now confirmed. Would you like to see your updated appointment list?"
            state.suggestions = [
                "List my appointments",
                "Cancel an appointment",
                "Get help",
            ]

        except Exception as e:
            state.assistant_message = "I encountered an error confirming that appointment. Please try again or contact the clinic directly."

        state.next_action = "router"
        return state

    def cancel_node(self, state: GraphState) -> GraphState:
        """Cancel an appointment"""
        try:
            # Resolve appointment reference
            appointment_id = self._resolve_appointment_reference(state)

            if not appointment_id:
                state.assistant_message = "I'm not sure which appointment you'd like to cancel. Could you be more specific? For example, 'Cancel #1' or 'Cancel my Oct 2 appointment'."
                state.next_action = "router"
                return state

            # Cancel the appointment
            appointment, within_24h = self.appointment_service.cancel(
                appointment_id, state.now
            )
            time_str = format_appointment_time(appointment.start_time)

            if within_24h:
                state.assistant_message = f"⚠️ **Note:** This appointment with **{appointment.provider_name}** on **{time_str}** is within 24 hours. I've cancelled it, but please consider calling the clinic to ensure proper handling.\n\n✅ Appointment cancelled successfully."
            else:
                state.assistant_message = f"✅ Cancelled! Your **{time_str}** appointment with **{appointment.provider_name}** has been cancelled. Would you like to see your updated appointment list?"

            state.suggestions = ["List my appointments", "Get help"]

        except Exception as e:
            state.assistant_message = "I encountered an error cancelling that appointment. Please try again or contact the clinic directly."

        state.next_action = "router"
        return state

    def help_node(self, state: GraphState) -> GraphState:
        """Provide help information"""
        help_prompt = f"{SYSTEM_PROMPT}\n\nThe user is asking for help. Provide a concise, friendly overview of what you can help them with regarding their appointments. Keep it brief and actionable."

        state.assistant_message = llm_client.chat(help_prompt, state.user_message)

        state.suggestions = [
            "List my appointments",
            "Confirm an appointment",
            "Cancel an appointment",
        ]
        state.next_action = "router"
        return state

    def smalltalk_node(self, state: GraphState) -> GraphState:
        """Handle casual conversation"""
        smalltalk_prompt = f"{SYSTEM_PROMPT}\n\nThe user is making casual conversation. Respond warmly but briefly, then gently guide them toward appointment management tasks. Keep the response concise and professional."

        state.assistant_message = llm_client.chat(smalltalk_prompt, state.user_message)

        state.suggestions = ["List my appointments", "Get help"]
        state.next_action = "router"
        return state

    def fallback_node(self, state: GraphState) -> GraphState:
        """Handle unclear requests"""
        fallback_prompt = f"{SYSTEM_PROMPT}\n\nThe user's request is unclear or doesn't match appointment management tasks. Politely clarify what you can help with and provide guidance. Keep it concise and helpful."

        state.assistant_message = llm_client.chat(fallback_prompt, state.user_message)
        state.suggestions = [
            "List my appointments",
            "Confirm an appointment",
            "Cancel an appointment",
            "Get help",
        ]
        state.next_action = "router"
        return state

    def _resolve_appointment_reference(self, state: GraphState) -> str | None:
        """Resolve ordinal or natural appointment reference to appointment_id"""
        if state.ordinal and state.last_list_snapshot:
            # Use ordinal reference - must match exactly
            for item in state.last_list_snapshot:
                if item["ordinal"] == state.ordinal:
                    return item["appointment_id"]
            # If ordinal was specified but not found, return None (don't fallback)
            return None

        # For natural references without ordinal, would need more sophisticated parsing
        # Only fallback to first appointment if no ordinal was specified
        if not state.ordinal and state.last_list_snapshot:
            return state.last_list_snapshot[0]["appointment_id"]

        return None
