import json
import threading
import time
import sys

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

        if not query:
            print("Could not extract query text from intent_data. Using a default prompt.")
            query = "Hello, Vector!"

        print(f"Querying Ollama with: {query}")
        
        try:
            response = ollama.chat(model=OLLAMA_MODEL, messages=[
                {
                    'role': 'system',
                    'content': 'You are a friendly, animated robot named Vector. Make responses creative, but informative. Try not to say more than 2 sentences, tops.'
                },
                {
                    'role': 'user',
                    'content': query,
                },
            ])
            
            answer = response['message']['content']
            print(f"Ollama response: {answer}")
            
            print("Vector is speaking...")
            robot.behavior.say_text(answer)
        except Exception as e:
            print(f"Error communicating with Ollama or Vector: {e}")
            robot.behavior.say_text("I'm sorry, I had trouble thinking about that.")

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
