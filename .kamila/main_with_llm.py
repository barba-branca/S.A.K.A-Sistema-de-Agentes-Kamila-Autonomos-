import os
import sys
import time
from dotenv import load_dotenv
import structlog

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(__file__))

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
    """
    Main loop for Kamila with LLM integration.
    """
    # Load .env relative to this script
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=env_path)

    print("🤖 Initializing Kamila (with Gemini AI)...")

    # Initialize Engine
    # We use a dummy key if not present just to allow the script to run in 'simulated' mode if we add one,
    # but the engine checks for key.
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    if not api_key:
        print("⚠️  Warning: GOOGLE_AI_API_KEY not found in .env. LLM calls will fail.")
        print("   Create .kamila/.env and add your key to test real generation.")

    engine = GeminiEngine(api_key=api_key)

    print("\n✨ Kamila is ready! Type 'exit' to quit.")
    print("   (Note: Voice input is disabled in this CLI mode)\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "tchau"]:
                print("Kamila: Tchau! Até logo! 👋")
                break

            if not user_input.strip():
                continue

            # Generate response
            print("Kamila: (thinking...)")
            response = engine.chat(user_input)

            # Clear line and print response
            # \033[A moves cursor up, \033[K clears line
            print(f"\033[A\033[KKamila: {response}")

        except KeyboardInterrupt:
            print("\nKamila: Forced exit. Bye!")
            break
        except Exception as e:
            logger.error("Critical error in main loop", error=str(e))

if __name__ == "__main__":
    main()
