import os
import google.generativeai as genai
import structlog
from dotenv import load_dotenv

# Configure logging
logger = structlog.get_logger()

class GeminiEngine:
    """
    Engine for interacting with Google's Gemini Pro model.
    Handles configuration, session management, and response generation.
    """

    def __init__(self, api_key: str = None, model_name: str = "gemini-pro"):
        """
        Initialize the Gemini Engine.

        Args:
            api_key: Google AI API Key. If None, tries to load from environment.
            model_name: The name of the model to use (default: gemini-pro).
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_AI_API_KEY")
        self.model_name = model_name
        self.chat_history = []

        if not self.api_key:
            logger.warning("Google AI API Key not found. Gemini Engine will fail if called.")
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.chat_session = self.model.start_chat(history=[])
            logger.info("Gemini Engine initialized", model=self.model_name)

    def generate_content(self, prompt: str) -> str:
        """
        Generates a single response from a prompt (non-conversational).
        """
        if not self.api_key:
            return "Error: API Key missing."

        try:
            logger.info("Generating content", prompt_preview=prompt[:50])
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error("Error generating content", error=str(e))
            return f"Error: {str(e)}"

    def chat(self, user_input: str) -> str:
        """
        Sends a message to the chat session and returns the response.
        Maintains history automatically via the genai ChatSession.
        """
        if not self.api_key:
            return "Error: API Key missing."

        try:
            logger.info("Sending chat message", input_preview=user_input[:50])
            response = self.chat_session.send_message(user_input)
            return response.text
        except Exception as e:
            logger.error("Error in chat", error=str(e))
            return f"Error: {str(e)}"

    def set_system_instruction(self, instruction: str):
        """
        Sets the system instruction (context/persona) for the model.
        Note: Gemini Pro via API works best when persona is passed in the first message
        or via system_instruction parameter in newer versions.
        Here we simulate it by resetting chat with a system prompt if supported,
        or just logging it for now as a placeholder for advanced config.
        """
        # In current SDK, system instructions are set at model creation or via initial prompt.
        # We'll re-initialize the chat with this context if needed,
        # but for simplicity we'll just acknowledge it.
        logger.info("System instruction set (implementation pending model support or restart)", instruction=instruction[:50])
