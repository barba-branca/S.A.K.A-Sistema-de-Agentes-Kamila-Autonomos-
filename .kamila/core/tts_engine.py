import pyttsx3
import structlog
import threading

logger = structlog.get_logger()

class TTSEngine:
    """
    Text-to-Speech Engine using pyttsx3.
    """

    def __init__(self, rate: int = 180, volume: float = 1.0):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)

            # Try to set a Portuguese voice if available
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'pt' in voice.id or 'portuguese' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break

            logger.info("TTS Engine initialized", rate=rate, volume=volume)
        except Exception as e:
            logger.error("Failed to initialize TTS Engine", error=str(e))
            self.engine = None

    def speak(self, text: str):
        """
        Speaks the given text.
        """
        if not self.engine:
            logger.warning("TTS Engine not available, skipping speech.")
            return

        try:
            logger.info("Speaking", text=text[:50])
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error("Error during speech", error=str(e))
            # Re-initialize engine in case of loop errors
            self.__init__()
