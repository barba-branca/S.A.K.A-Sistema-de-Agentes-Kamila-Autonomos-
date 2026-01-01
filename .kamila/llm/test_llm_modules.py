import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Adjust path to include the .kamila directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm.gemini_engine import GeminiEngine
from llm.ai_studio_integration import AIStudioIntegration

class TestLLMModules(unittest.TestCase):

    def setUp(self):
        self.mock_api_key = "dummy_key"

    @patch("google.generativeai.GenerativeModel")
    @patch("google.generativeai.configure")
    def test_gemini_initialization(self, mock_configure, mock_model):
        engine = GeminiEngine(api_key=self.mock_api_key)
        mock_configure.assert_called_with(api_key=self.mock_api_key)
        self.assertIsNotNone(engine.model)
        self.assertIsNotNone(engine.chat_session)

    @patch("google.generativeai.GenerativeModel")
    def test_generate_content(self, mock_model_class):
        # Setup mock
        mock_model_instance = mock_model_class.return_value
        mock_response = MagicMock()
        mock_response.text = "Hello there!"
        mock_model_instance.generate_content.return_value = mock_response

        engine = GeminiEngine(api_key=self.mock_api_key)
        response = engine.generate_content("Hi")

        self.assertEqual(response, "Hello there!")
        mock_model_instance.generate_content.assert_called_with("Hi")

    @patch("google.generativeai.GenerativeModel")
    def test_chat_interaction(self, mock_model_class):
        # Setup mock
        mock_model_instance = mock_model_class.return_value
        mock_chat_session = mock_model_instance.start_chat.return_value
        mock_response = MagicMock()
        mock_response.text = "I am fine."
        mock_chat_session.send_message.return_value = mock_response

        engine = GeminiEngine(api_key=self.mock_api_key)
        response = engine.chat("How are you?")

        self.assertEqual(response, "I am fine.")
        mock_chat_session.send_message.assert_called_with("How are you?")

    def test_ai_studio_integration(self):
        integration = AIStudioIntegration()
        models = integration.list_tuned_models()
        self.assertIn("kamila-empathetic-v1", models)
        config = integration.get_model_config("any")
        self.assertEqual(config["temperature"], 0.7)

if __name__ == '__main__':
    unittest.main()
