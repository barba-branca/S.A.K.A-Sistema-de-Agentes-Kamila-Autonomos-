import speech_recognition as sr
import structlog
import os

logger = structlog.get_logger()

class STTEngine:
    """
    Speech-to-Text Engine handling microphone input and audio transcription.
    Uses Google Speech Recognition (online) by default, with hooks for offline fallback.
    """

    def __init__(self, energy_threshold: int = 1000, pause_threshold: float = 0.8):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
        self.microphone = sr.Microphone()
        logger.info("STT Engine initialized", energy_threshold=energy_threshold)

    def listen(self) -> str:
        """
        Listens to the microphone and returns text.
        Returns None if nothing was understood or an error occurred.
        """
        with self.microphone as source:
            logger.info("Listening...")
            # Adjust for ambient noise to handle varying environments
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                logger.info("Processing audio...")

                # Attempt recognition
                text = self.recognizer.recognize_google(audio, language="pt-BR")
                logger.info("Speech recognized", text=text)
                return text

            except sr.WaitTimeoutError:
                logger.info("Listening timed out (silence)")
                return None
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error("STT Service Error", error=str(e))
                return None
            except Exception as e:
                logger.error("Unexpected STT Error", error=str(e))
                return None
