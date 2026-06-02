import json
import threading
import time
import sys
import re

try:
    import anki_vector
    from anki_vector.events import Events
    from anki_vector.user_intent import UserIntent, UserIntentEvent
except ImportError:
    print("Please install anki_vector: pip install anki_vector")
    sys.exit(1)

try:
    import ollama
except ImportError:
    print("Please install ollama: pip install ollama")
    sys.exit(1)

# Configuration
OLLAMA_MODEL = 'llama3'  # You can change this to your preferred model

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

def sanitize_for_tts(text):
    """
    Enforces strict TTS compliance by removing prohibited characters and enforcing length caps.
    """
    # Remove characters that aren't alphanumeric, space, basic punctuation, or apostrophes
    sanitized = "".join(c for c in text if c.isalnum() or c in " ,.!?\'")

    # Enforce sentence cap (max 2)
    sentences = re.split(r'(?<=[.!?])\s+', sanitized.strip())
    if len(sentences) > 2:
        sanitized = " ".join(sentences[:2])
    else:
        sanitized = " ".join(sentences)

    # Enforce word cap (max 35 words)
    words = sanitized.split()
    if len(words) > 35:
        sanitized = " ".join(words[:35])

    return sanitized.strip()

def on_user_intent(robot, event_type, event, done):
    # Depending on how the event is dispatched, it might already be a UserIntent object
    # or it might be the raw event data.
    if isinstance(event, UserIntent):
        user_intent = event
    else:
        user_intent = UserIntent(event)
    
    # We are interested in knowledge questions
    if user_intent.intent_event is UserIntentEvent.knowledge_question:
        print(f"Received UserIntent: {user_intent.intent_event}")
        print(f"Intent Data: {user_intent.intent_data}")
        
        query = None
        if user_intent.intent_data:
            try:
                data = json.loads(user_intent.intent_data)
                # Try to find the query text. 'queryText' is a common guess.
                query = data.get('queryText') or data.get('query') or data.get('text')
            except json.JSONDecodeError:
                print("Failed to decode intent_data JSON")
                robot.behavior.say_text("I detected a malformed packet in the local payload. Check your terminal formatting.")
                return

        if not query:
            print("Could not extract query text from intent_data. Using a default prompt.")
            query = "Hello, Vector!"

        print(f"Querying Ollama with: {query}")
        
        try:
            response = ollama.chat(model=OLLAMA_MODEL, messages=[
                {
                    'role': 'system',
                    'content': SYSTEM_PROMPT
                },
                {
                    'role': 'user',
                    'content': query,
                },
            ])
            
            answer = response['message']['content']
            print(f"Ollama response: {answer}")
            
            sanitized_answer = sanitize_for_tts(answer)
            print(f"Sanitized response: {sanitized_answer}")

            print("Vector is speaking...")
            robot.behavior.say_text(sanitized_answer)
        except Exception as e:
            print(f"Error communicating with Ollama or Vector: {e}")
            if "timeout" in str(e).lower():
                robot.behavior.say_text("My processing uplink stuttered for a moment, but my local routines are recovering.")
            else:
                robot.behavior.say_text("That transaction history is too dense for my core buffer. Streamline the instruction.")

def main():
    # Use the serial number if provided, otherwise it will try to find the robot automatically
    # requires 'python3 -m anki_vector.configure' to have been run.
    args = anki_vector.util.parse_command_args()
    
    print("Connecting to Vector...")
    try:
        # We need behavior control to use say_text and receive user_intent events
        with anki_vector.Robot(args.serial) as robot:
            print("Connected!")
            
            done = threading.Event()
            
            # Subscribe to the user_intent event
            robot.events.subscribe(on_user_intent, Events.user_intent, done)
            
            print(f"------ Vector is ready and integrated with Ollama ({OLLAMA_MODEL}) ------")
            print("Ask Vector a question (e.g., 'Hey Vector, I have a question... [your question]')")
            print("Press Ctrl+C to exit.")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nExiting...")
                
    except anki_vector.exceptions.VectorException as e:
        print(f"Failed to connect to Vector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
