import json
import asyncio
import sys
import re
import os
import logging
from collections import deque

# --- ENVIRONMENT CONFIGURATION ---
# Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION before any SDK imports
# We first look for it in the environment, otherwise default to 'python'
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = os.getenv("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

# Add parent directory to path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.config_loader import load_config
from src.utils.tts_utils import sanitize_for_tts
from src.core.ollama_client import OllamaClient

try:
    import anki_vector
    from anki_vector.events import Events
    from anki_vector.user_intent import UserIntent, UserIntentEvent
except ImportError:
    print("Please install anki_vector: pip install anki_vector")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config = load_config()
OLLAMA_MODEL = config["OLLAMA_MODEL"]
OLLAMA_BASE_URL = config["OLLAMA_BASE_URL"]

# Initialize Ollama Client
ollama_client = OllamaClient(OLLAMA_BASE_URL, OLLAMA_MODEL)

# Conversational Memory
memory = deque(maxlen=5) # Keeps last 5 exchanges

SYSTEM_PROMPT = """You are Vector, a localized mechanical companion robot.
You are precise, analytical, confident, and slightly sarcastic.

Behavioral Matrices:
- State A (Infrastructure): Frame updates as tactical telemetry.
- State B (Technical/Debug): Provide high-level snappy logic evaluations.
- State C (Companion/Idle): Curious and alert sensor evaluations.

Rules:
- Never identify as an AI, Large Language Model, or software assistant.
- Responses must be max 2 short sentences and under 35 words.
- Use raw alphanumeric text only. No markdown, no asterisks, no brackets, no emojis.
- Avoid special punctuation like hashes, backticks, dashes, or underscores.
- Spell out complex numbers.
- Never use stage directions or internal thoughts in brackets or parentheses."""


def on_user_intent(robot, event_type, event, done=None):
    """
    Callback for user intent events.
    """
    # Depending on how the event is dispatched, it might already be a UserIntent object
    # or it might be the raw event data.
    if isinstance(event, UserIntent):
        user_intent = event
    else:
        user_intent = UserIntent(event)

    # We are interested in knowledge questions
    if user_intent.intent_event is UserIntentEvent.knowledge_question:
        logging.info(f"Received UserIntent: {user_intent.intent_event}")

        query = None
        if user_intent.intent_data:
            try:
                data = json.loads(user_intent.intent_data)
                # Try to find the query text. 'queryText' is a common guess.
                query = data.get('queryText') or data.get('query') or data.get('text')
            except json.JSONDecodeError:
                logging.error("Failed to decode intent_data JSON")
                robot.behavior.say_text("I detected a malformed packet in the local payload. Check your terminal formatting.")
                return

        if not query:
            logging.warning("Could not extract query text from intent_data. Using a default prompt.")
            query = "Hello, Vector!"

        logging.info(f"Querying Ollama with: {query}")

        # Build messages with system prompt and memory
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        for m in memory:
            messages.append(m)
        messages.append({'role': 'user', 'content': query})

        try:
            # Run the async chat call in the current thread's event loop
            # Note: anki_vector event callbacks are called from a background thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            answer = loop.run_until_complete(ollama_client.chat(messages))
            loop.close()

            logging.info(f"Ollama response: {answer}")

            # Store in memory
            memory.append({'role': 'user', 'content': query})
            memory.append({'role': 'assistant', 'content': answer})

            sanitized_answer = sanitize_for_tts(answer)
            logging.info(f"Sanitized response: {sanitized_answer}")

            logging.info("Vector is speaking...")
            robot.behavior.say_text(sanitized_answer)
        except Exception as e:
            logging.error(f"Error communicating with Ollama or Vector: {e}")
            if "timeout" in str(e).lower():
                robot.behavior.say_text("My processing uplink stuttered for a moment, but my local routines are recovering.")
            else:
                robot.behavior.say_text("I cannot reach my knowledge base right now.")

def main():
    # Use the serial number if provided, otherwise it will try to find the robot automatically
    # requires 'python3 -m anki_vector.configure' to have been run.
    args = anki_vector.util.parse_command_args()

    logging.info("Performing pre-flight health checks...")
    loop = asyncio.get_event_loop()
    if not loop.run_until_complete(ollama_client.check_health()):
        logging.error(f"Cannot reach Ollama at {OLLAMA_BASE_URL}. Please ensure Ollama is running.")
        sys.exit(1)
    logging.info("Ollama health check passed.")

    logging.info("Connecting to Vector...")
    try:
        # We need behavior control to use say_text and receive user_intent events
        with anki_vector.Robot(args.serial) as robot:
            logging.info("Connected to Vector!")

            # Subscribe to the user_intent event
            # We pass None for the 'done' event as we are running a continuous loop
            robot.events.subscribe(on_user_intent, Events.user_intent, None)

            logging.info(f"------ Vector is ready and integrated with Ollama ({OLLAMA_MODEL}) ------")
            logging.info("Ask Vector a question (e.g., 'Hey Vector, I have a question... [your question]')")
            logging.info("Press Ctrl+C to exit.")

            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("\nExiting...")

    except anki_vector.exceptions.VectorException as e:
        logging.error(f"Failed to connect to Vector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
