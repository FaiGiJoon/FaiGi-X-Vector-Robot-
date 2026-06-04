import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import json
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core import vector_ollama
from src.utils.tts_utils import sanitize_for_tts

class TestVectorOllamaIntegration(unittest.TestCase):

    @patch('src.core.vector_ollama.ollama_client.chat', new_callable=AsyncMock)
    @patch('anki_vector.Robot')
    def test_on_user_intent_knowledge_question(self, mock_robot, mock_ollama_chat):
        # Setup mocks
        mock_robot_instance = MagicMock()
        mock_ollama_chat.return_value = 'Hello! **I am Vector.** (Internal: robot mode).'

        # Simulate a knowledge_question event as a UserIntent object
        mock_event = MagicMock(spec=vector_ollama.UserIntent)
        mock_event.intent_event = vector_ollama.UserIntentEvent.knowledge_question
        mock_event.intent_data = json.dumps({'queryText': 'Who are you?'})

        # Call the function (updated signature: 4 args)
        vector_ollama.on_user_intent(mock_robot_instance, 'user_intent', mock_event, MagicMock())

        # Assertions
        mock_ollama_chat.assert_called_once()
        args, kwargs = mock_ollama_chat.call_args
        # messages[0] is system, the last message is the current query
        self.assertEqual(args[0][-1]['content'], 'Who are you?')
        self.assertEqual(args[0][0]['content'], vector_ollama.SYSTEM_PROMPT)
        
        # Should be sanitized (no markdown, no parentheses)
        mock_robot_instance.behavior.say_text.assert_called_with('Hello! I am Vector.')

    @patch('src.core.vector_ollama.ollama_client.chat', new_callable=AsyncMock)
    @patch('anki_vector.Robot')
    def test_on_user_intent_greeting_hello(self, mock_robot, mock_ollama_chat):
        # Setup mocks
        mock_robot_instance = MagicMock()
        mock_ollama_chat.return_value = 'Hello there! How can I help?'

        # Simulate a greeting_hello event
        mock_event = MagicMock(spec=vector_ollama.UserIntent)
        mock_event.intent_event = vector_ollama.UserIntentEvent.greeting_hello
        mock_event.intent_data = None # Common for greetings

        # Call the function
        vector_ollama.on_user_intent(mock_robot_instance, 'user_intent', mock_event, MagicMock())

        # Assertions
        mock_ollama_chat.assert_called_once()
        args, kwargs = mock_ollama_chat.call_args
        self.assertEqual(args[0][-1]['content'], 'Hello, Vector!')
        mock_robot_instance.behavior.say_text.assert_called_with('Hello there! How can I help?')

    def test_sanitize_for_tts(self):
        # Test markdown removal
        self.assertEqual(sanitize_for_tts("Hello **World**!"), "Hello World!")
        self.assertEqual(sanitize_for_tts("Vector is #1"), "Vector is one")
        self.assertEqual(sanitize_for_tts("Check `this` out"), "Check this out")
        self.assertEqual(sanitize_for_tts("It is _italic_"), "It is italic")

        # Test digit to word conversion
        self.assertEqual(sanitize_for_tts("I have 2 cubes"), "I have two cubes")
        self.assertEqual(sanitize_for_tts("0 to 9"), "zero to nine")

        # Test apostrophes (natural contractions)
        self.assertEqual(sanitize_for_tts("Don't stop now."), "Don't stop now.")

        # Test special characters removal
        self.assertEqual(sanitize_for_tts("Vector_robot #1 is cool."), "Vectorrobot one is cool.")

        # Test brackets and parentheses removal
        self.assertEqual(sanitize_for_tts("I am (thinking) [processing]."), "I am thinking processing.")

        # Test emoji/unsupported char removal (handled by isalnum)
        self.assertEqual(sanitize_for_tts("Happy! 😊"), "Happy!")

        # Test sentence cap (max 2)
        long_text = "Sentence one. Sentence two. Sentence three. Sentence four."
        sanitized = sanitize_for_tts(long_text)
        self.assertEqual(sanitized, "Sentence one. Sentence two.")

        # Test word cap (max 35)
        many_words = " ".join(["word"] * 50) + "."
        sanitized = sanitize_for_tts(many_words)
        word_count = len(sanitized.split())
        self.assertTrue(word_count <= 35)

    @patch('anki_vector.Robot')
    def test_on_user_intent_malformed_json(self, mock_robot):
        mock_robot_instance = MagicMock()
        mock_event = MagicMock(spec=vector_ollama.UserIntent)
        mock_event.intent_event = vector_ollama.UserIntentEvent.knowledge_question
        mock_event.intent_data = "{ malformed json }"

        vector_ollama.on_user_intent(mock_robot_instance, 'user_intent', mock_event, MagicMock())

        mock_robot_instance.behavior.say_text.assert_called_with(
            "I detected a malformed packet in the local payload. Check your terminal formatting."
        )

    @patch('src.core.vector_ollama.ollama_client.chat', new_callable=AsyncMock)
    @patch('anki_vector.Robot')
    def test_on_user_intent_ollama_error(self, mock_robot, mock_ollama_chat):
        mock_robot_instance = MagicMock()
        mock_ollama_chat.side_effect = Exception("General error")
        mock_event = MagicMock(spec=vector_ollama.UserIntent)
        mock_event.intent_event = vector_ollama.UserIntentEvent.knowledge_question
        mock_event.intent_data = json.dumps({'queryText': 'Hi'})

        vector_ollama.on_user_intent(mock_robot_instance, 'user_intent', mock_event, MagicMock())

        mock_robot_instance.behavior.say_text.assert_called_with(
            "I cannot reach my knowledge base right now."
        )

if __name__ == '__main__':
    unittest.main()
