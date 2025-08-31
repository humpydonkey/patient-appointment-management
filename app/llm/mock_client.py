from typing import Dict, Any
import json
import re


class MockLLMClient:
    """Mock LLM client for testing - uses simple rule-based responses"""

    def __init__(self):
        pass

    def chat(self, system_prompt: str, user_message: str) -> str:
        """Mock chat completion"""
        user_lower = user_message.lower()

        # Handle lockout message
        if "account locked" in user_message.lower():
            return "Your account is temporarily locked for security. Please try again later."

        # Handle help requests
        if "help" in system_prompt.lower() and (
            "help" in user_message.lower() or "what can" in user_message.lower()
        ):
            return "I can help you manage your appointments! You can list, confirm, or cancel your appointments. What would you like to do?"

        # Handle smalltalk
        if "casual conversation" in system_prompt.lower():
            if any(word in user_lower for word in ["hello", "hi"]):
                return "Hello! I'm here to help you manage your appointments. How can I assist you today?"
            elif any(word in user_lower for word in ["thank", "thanks"]):
                return "You're welcome! Is there anything else I can help you with regarding your appointments?"
            else:
                return "I'm here to help with your appointments. What would you like to do?"

        # Handle fallback
        if "unclear" in system_prompt.lower():
            return "I'm not sure how to help with that. I can assist you with listing, confirming, or cancelling your appointments. What would you like to do?"

        # Default responses for appointment actions
        if "list" in user_lower or "show" in user_lower or "appointments" in user_lower:
            return "I'd be happy to show you your upcoming appointments. Let me get those for you."

        elif "confirm" in user_lower:
            if "#" in user_message or "first" in user_lower or "1" in user_message:
                return "I'll help you confirm that appointment. Let me verify which one you mean."
            return "I can help you confirm an appointment. Which one would you like to confirm?"

        elif "cancel" in user_lower:
            if "#" in user_message or "first" in user_lower or "1" in user_message:
                return "I'll help you cancel that appointment. Let me make sure I have the right one."
            return "I can help you cancel an appointment. Which one would you like to cancel?"

        elif "format" in user_lower and ("phone" in user_lower or "dob" in user_lower or "birth" in user_lower):
            return """I'm having trouble with that format. Please provide your information in these formats:

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
        
        else:
            return "I can help you with your appointments. You can ask me to list, confirm, or cancel appointments."

    def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """Mock intent classification"""
        user_lower = user_message.lower()

        # Extract ordinal numbers
        ordinal = None
        if "#" in user_message:
            match = re.search(r"#(\d+)", user_message)
            if match:
                ordinal = int(match.group(1))
        elif any(word in user_lower for word in ["first", "1st"]):
            ordinal = 1
        elif any(word in user_lower for word in ["second", "2nd"]):
            ordinal = 2
        elif any(word in user_lower for word in ["third", "3rd"]):
            ordinal = 3

        # Simple intent classification
        if "list" in user_lower or "show" in user_lower or "appointments" in user_lower:
            intent = "list_appointments"
        elif "confirm" in user_lower:
            intent = "confirm_appointment"
        elif "cancel" in user_lower:
            intent = "cancel_appointment"
        elif "help" in user_lower:
            intent = "help"
        elif (
            any(
                word in user_lower
                for word in ["hello", "hi", "thanks", "thank you", "good"]
            )
            and "random" not in user_lower
        ):
            intent = "smalltalk"
        else:
            intent = "fallback"

        return {
            "intent": intent,
            "entities": {
                "ordinal": ordinal,
                "date": None,
                "time": None,
                "provider": None,
            },
        }
