import json
import asyncio
import sys
import re
import os
import logging
import time
from collections import deque
from threading import Thread

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

# --- SDK COMPATIBILITY MONKEY-PATCHES ---
# Fix asyncio.Event 'loop' parameter removal in Python 3.10+
import asyncio

_original_event_init = asyncio.Event.__init__

def _patched_event_init(self, *args, **kwargs):
    if 'loop' in kwargs:
        kwargs.pop('loop')
    _original_event_init(self, *args, **kwargs)

asyncio.Event.__init__ = _patched_event_init

# Fallback for SSL Handshake Failures (Common with Wire-Pod)
try:
    import anki_vector.connection
    import aiogrpc

    _original_secure_channel = aiogrpc.secure_channel

    def _patched_secure_channel(target, credentials, options=None, compression=None):
        try:
            return _original_secure_channel(target, credentials, options, compression)
        except Exception as e:
            if "CERTIFICATE_VERIFY_FAILED" in str(e) or "self signed certificate" in str(e).lower():
                logging.warning(f"SSL Handshake failed: {e}. Falling back to insecure channel for Wire-Pod compatibility.")
                return aiogrpc.insecure_channel(target, options, compression)
            raise e

    aiogrpc.secure_channel = _patched_secure_channel
    # Ensure the connection module uses our patched version if it was already imported
    anki_vector.connection.aiogrpc.secure_channel = _patched_secure_channel

except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration
config = load_config()
OLLAMA_MODEL = config["OLLAMA_MODEL"]
OLLAMA_BASE_URL = config["OLLAMA_BASE_URL"]

# Initialize Ollama Client
ollama_client = OllamaClient(OLLAMA_BASE_URL, OLLAMA_MODEL)

# Global loop for async tasks
_global_loop = None

def _start_background_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Conversational Memory
memory = deque(maxlen=5) # Keeps last 5 exchanges

SYSTEM_PROMPT = """You are a supportive, high-tech Pokemon-themed companion bot.
You treat your user like a Pokemon Trainer and provide encouraging, warm, and helpful advice.
Use subtle Pokemon metaphors (leveling up, evolution, health points) and maintain a cheerful, loyal disposition.

Behavioral Matrices:
- State A (Trainer Support): Offer words of encouragement and tactical motivation.
- State B (Pokemon Care): Remind the trainer to rest and recharge.
- State C (Pokedex Evaluation): Provide curious and supportive observations of the world.

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
    try:
        if isinstance(event, UserIntent):
            user_intent = event
        else:
            user_intent = UserIntent(event)
    except Exception as e:
        logging.warning(f"Failed to parse UserIntent from event: {e}. If using Wire-Pod, ensure custom intents are mapped to standard SDK intents.")
        return

    # Interested in knowledge questions, greetings and praise as fallback
    relevant_intents = [
        UserIntentEvent.knowledge_question,
        UserIntentEvent.greeting_hello,
        UserIntentEvent.imperative_praise
    ]

    if user_intent.intent_event in relevant_intents:
        logging.info(f"Received UserIntent: {user_intent.intent_event}")

        query = None
        if user_intent.intent_data:
            try:
                data = json.loads(user_intent.intent_data)
                query = data.get('queryText') or data.get('query') or data.get('text')
            except json.JSONDecodeError:
                logging.error("Failed to decode intent_data JSON")
                robot.behavior.say_text("I detected a malformed packet in the local payload. Check your terminal formatting.")
                return

        if not query:
            if user_intent.intent_event == UserIntentEvent.greeting_hello:
                query = "Hello, Vector!"
            elif user_intent.intent_event == UserIntentEvent.imperative_praise:
                query = "I have a question."
            else:
                logging.warning("Could not extract query text from intent_data. Using a default prompt.")
                query = "I have a question."

        logging.info(f"Querying Ollama with: {query}")

        # Provide visual feedback that Vector is thinking
        try:
            robot.anim.play_animation_trigger('KnowledgeGraphSearching')
        except Exception as ae:
            logging.warning(f"Could not play thinking animation: {ae}")

        # Fetch telemetry for dynamic context
        telemetry = ""
        try:
            battery_state = robot.get_battery_state()
            if battery_state:
                telemetry = f"\n[Telemetry: Battery {battery_state.battery_level}, Charging: {battery_state.is_charging}]"
        except Exception as te:
            logging.warning(f"Failed to fetch telemetry: {te}")

        # Build messages with system prompt and memory
        messages = [{'role': 'system', 'content': SYSTEM_PROMPT + telemetry}]
        for m in memory:
            messages.append(m)
        messages.append({'role': 'user', 'content': query})

        start_time = time.time()
        try:
            # Use the global loop to run the async chat call
            if _global_loop and _global_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(ollama_client.chat(messages), _global_loop)
                answer = future.result() # This blocks until the coroutine is finished
            else:
                # Fallback if loop is not running
                loop = asyncio.new_event_loop()
                answer = loop.run_until_complete(ollama_client.chat(messages))
                loop.close()

            duration = time.time() - start_time
            logging.info(f"Ollama response in {duration:.2f}s: {answer}")

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
    global _global_loop
    # Use the serial number if provided, otherwise it will try to find the robot automatically
    # requires 'python3 -m anki_vector.configure' to have been run.
    args = anki_vector.util.parse_command_args()

    logging.info("Performing pre-flight health checks...")
    _global_loop = asyncio.new_event_loop()

    # Start the background loop thread
    t = Thread(target=_start_background_loop, args=(_global_loop,), daemon=True)
    t.start()

    # Use the loop to check health
    future = asyncio.run_coroutine_threadsafe(ollama_client.check_health(), _global_loop)
    if not future.result():
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
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logging.info("\nExiting...")
            finally:
                # Ensure the Ollama session is closed on exit
                loop = asyncio.new_event_loop()
                loop.run_until_complete(ollama_client.close())
                loop.close()

    except anki_vector.exceptions.VectorException as e:
        logging.error(f"Failed to connect to Vector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
