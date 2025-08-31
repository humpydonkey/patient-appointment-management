import os
import json
import re
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenAILLMClient:
    """OpenAI LLM client for production use"""

    def __init__(self, model: Optional[str] = None, temperature: float = 0.7):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", temperature))

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable is required")

    def chat(self, system_prompt: str, user_message: str) -> str:
        """Generate chat completion using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=self.temperature,
                max_tokens=500,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            # Fallback to a generic helpful message
            print(f"OpenAI API error: {e}")
            return "I'm here to help you manage your appointments. How can I assist you today?"

    def classify_intent(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Classify user intent using OpenAI with structured output and conversation context"""
        
        # Build context from conversation history
        context_str = ""
        if conversation_history:
            # Get last 5 turns for context (up to 10 messages total)
            recent_history = conversation_history[-5:]
            if recent_history:
                context_str = "\n\nRecent conversation context:\n"
                for i, turn in enumerate(recent_history, 1):
                    context_str += f"Turn {i}:\n"
                    context_str += f"User: {turn['user_message']}\n"
                    context_str += f"Assistant: {turn['assistant_message']}\n\n"
        
        classification_prompt = (
            """You are a healthcare appointment assistant. Classify the user's intent and extract entities based on their current message AND the conversation context.

Available intents:
- "list_appointments": wants to see their appointments (includes confirming they want to see updated list)
- "confirm_appointment": wants to confirm a specific appointment  
- "cancel_appointment": wants to cancel a specific appointment
- "help": asking for help or what they can do
- "smalltalk": greeting, thanks, casual conversation (NOT context-dependent responses)
- "fallback": unclear intent or doesn't match above

IMPORTANT CONTEXT RULES:
- If the assistant just offered to show updated appointments and user says "yes", "sure", "okay" → classify as "list_appointments"
- If the assistant just asked a yes/no question about appointments and user responds with agreement → use the appropriate appointment intent
- Single words like "yes", "no", "okay", "sure" should be interpreted based on what the assistant just offered or asked
- Generic greetings like "hi", "hello", "thanks" without context are "smalltalk"

Extract entities if present:
- ordinal: number reference like "#2", "second", "2nd" (return as integer)
- date: absolute dates like "Oct 2" or relative like "tomorrow"
- time: time references like "2 PM", "morning"
- provider: doctor names like "Dr. Kim", "Lee"

Return ONLY valid JSON in this exact format:
{"intent": "list_appointments", "entities": {"ordinal": 2, "date": null, "time": null, "provider": null}}"""
            + context_str
            + f"\n\nCurrent user message: {user_message}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": classification_prompt}],
                temperature=0.1,  # Lower temperature for consistent classification
                max_tokens=150,
            )

            content = response.choices[0].message.content.strip()

            # Try to parse the JSON response
            try:
                result = json.loads(content)

                # Validate the response structure
                if "intent" not in result or "entities" not in result:
                    raise ValueError("Invalid response structure")

                return result

            except (json.JSONDecodeError, ValueError):
                # Fallback to regex parsing if JSON parsing fails
                return self._fallback_classify(user_message, conversation_history)

        except Exception as e:
            print(f"OpenAI classification error: {e}")
            return self._fallback_classify(user_message, conversation_history)

    def _fallback_classify(self, user_message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Fallback classification using regex patterns with basic context awareness"""
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

        # Context-aware classification for simple responses
        if conversation_history and user_message.lower().strip() in ["yes", "sure", "okay", "ok"]:
            # Check last assistant message for context
            last_turn = conversation_history[-1]
            last_assistant_msg = last_turn['assistant_message'].lower()
            if "updated appointment list" in last_assistant_msg or "see your updated" in last_assistant_msg:
                intent = "list_appointments"
            else:
                intent = "smalltalk"  # Default for ambiguous yes/no
        elif "list" in user_lower or "show" in user_lower or "appointments" in user_lower:
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


# Global instance
llm_client = OpenAILLMClient()
