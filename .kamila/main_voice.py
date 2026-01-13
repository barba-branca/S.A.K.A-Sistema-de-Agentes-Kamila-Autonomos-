import os
import sys
import structlog
from dotenv import load_dotenv

# Ensure we can import from local modules
sys.path.append(os.path.dirname(__file__))

from core.stt_engine import STTEngine
from core.tts_engine import TTSEngine
from llm.gemini_engine import GeminiEngine

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

def main():
    # Load .env relative to this script
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=env_path)

    print("🎤 Initializing Kamila Voice Assistant...")

    # Initialize Modules
    try:
        stt = STTEngine()
        tts = TTSEngine()

        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            print("⚠️  Warning: GOOGLE_AI_API_KEY not found. Brain will be lobotomized.")

        brain = GeminiEngine(api_key=api_key)

    except Exception as e:
        logger.error("Failed to initialize modules", error=str(e))
        return

    tts.speak("Olá! Eu sou a Kamila. Estou pronta para ouvir.")
    print("✨ Kamila Ready! Press Ctrl+C to exit.")

    while True:
        try:
            print("\n👂 Listening...")
            user_text = stt.listen()

            if user_text:
                print(f"👤 You: {user_text}")

                # Check for exit commands
                if user_text.lower() in ["tchau", "sair", "encerrar", "exit"]:
                    tts.speak("Tchau! Até mais.")
                    break

                # Generate response
                print("🧠 Thinking...")
                response = brain.chat(user_text)
                print(f"🤖 Kamila: {response}")

                # Speak response
                tts.speak(response)
            else:
                # No speech detected or error
                pass

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            logger.error("Error in main loop", error=str(e))

if __name__ == "__main__":
    main()
