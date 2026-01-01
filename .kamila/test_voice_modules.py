import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.stt_engine import STTEngine
from core.tts_engine import TTSEngine

class TestVoiceModules(unittest.TestCase):

    @patch("speech_recognition.Recognizer")
    @patch("speech_recognition.Microphone")
    def test_stt_initialization(self, mock_mic, mock_recog):
        stt = STTEngine()
        self.assertIsNotNone(stt.recognizer)
        self.assertIsNotNone(stt.microphone)

    @patch("pyttsx3.init")
    def test_tts_initialization(self, mock_init):
        tts = TTSEngine()
        mock_init.assert_called_once()

    @patch("speech_recognition.Recognizer")
    @patch("speech_recognition.Microphone")
    def test_stt_listen_success(self, mock_mic, mock_recog):
        stt = STTEngine()
        mock_recog_instance = mock_recog.return_value
        mock_recog_instance.recognize_google.return_value = "Test message"

        # Mock context manager for microphone
        mock_mic.return_value.__enter__.return_value = MagicMock()

        text = stt.listen()
        self.assertEqual(text, "Test message")

    @patch("pyttsx3.init")
    def test_tts_speak(self, mock_init):
        mock_engine = MagicMock()
        mock_init.return_value = mock_engine

        tts = TTSEngine()
        tts.speak("Hello")

        mock_engine.say.assert_called_with("Hello")
        mock_engine.runAndWait.assert_called_once()

if __name__ == '__main__':
    unittest.main()
