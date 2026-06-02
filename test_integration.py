import unittest
from unittest.mock import MagicMock, patch
import json
import vector_ollama

class TestVectorOllamaIntegration(unittest.TestCase):

    @patch('ollama.chat')
    @patch('anki_vector.Robot')
    def test_on_user_intent_knowledge_question(self, mock_robot, mock_ollama_chat):
        # Setup mocks
        mock_robot_instance = MagicMock()
        mock_ollama_chat.return_value = {
            'message': {'content': 'Hello! **I am Vector.** (Internal: robot mode).'}
        }

        # Simulate a knowledge_question event as a UserIntent object
        # which is what the SDK often passes to the callback
        mock_event = MagicMock(spec=vector_ollama.UserIntent)
        mock_event.intent_event = vector_ollama.UserIntentEvent.knowledge_question
        mock_event.intent_data = json.dumps({'queryText': 'Who are you?'})

        # Call the function
        vector_ollama.on_user_intent(mock_robot_instance, 'user_intent', mock_event, MagicMock())

        # Assertions
        mock_ollama_chat.assert_called_once()
        args, kwargs = mock_ollama_chat.call_args
        self.assertEqual(kwargs['messages'][1]['content'], 'Who are you?')
        self.assertEqual(kwargs['messages'][0]['content'], vector_ollama.SYSTEM_PROMPT)
        
        # Should be sanitized (no markdown, no parentheses)
        mock_robot_instance.behavior.say_text.assert_called_with('Hello! I am Vector.')

    def test_sanitize_for_tts(self):
        # Test markdown removal
        self.assertEqual(vector_ollama.sanitize_for_tts("Hello **World**!"), "Hello World!")

        # Test apostrophes (natural contractions)
        self.assertEqual(vector_ollama.sanitize_for_tts("Don't stop now."), "Don't stop now.")

        # Test special characters removal
        self.assertEqual(vector_ollama.sanitize_for_tts("Vector_robot #1 is `cool`."), "Vectorrobot 1 is cool.")

        # Test brackets and parentheses removal
        self.assertEqual(vector_ollama.sanitize_for_tts("I am (thinking) [processing]."), "I am thinking processing.")

        # Test emoji/unsupported char removal (handled by isalnum)
        self.assertEqual(vector_ollama.sanitize_for_tts("Happy! 😊"), "Happy!")

        # Test sentence cap (max 2)
        long_text = "Sentence one. Sentence two. Sentence three. Sentence four."
        sanitized = vector_ollama.sanitize_for_tts(long_text)
        self.assertEqual(sanitized, "Sentence one. Sentence two.")

        # Test word cap (max 35)
        many_words = " ".join(["word"] * 50) + "."
        sanitized = vector_ollama.sanitize_for_tts(many_words)
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

    @patch('ollama.chat')
    @patch('anki_vector.Robot')
    def test_on_user_intent_ollama_error(self, mock_robot, mock_ollama_chat):
        mock_robot_instance = MagicMock()
        mock_ollama_chat.side_effect = Exception("General error")
        mock_event = MagicMock(spec=vector_ollama.UserIntent)
        mock_event.intent_event = vector_ollama.UserIntentEvent.knowledge_question
        mock_event.intent_data = json.dumps({'queryText': 'Hi'})

        vector_ollama.on_user_intent(mock_robot_instance, 'user_intent', mock_event, MagicMock())

        mock_robot_instance.behavior.say_text.assert_called_with(
            "That transaction history is too dense for my core buffer. Streamline the instruction."
        )

    @patch('ollama.chat')
    @patch('anki_vector.Robot')
    def test_on_user_intent_other_event(self, mock_robot, mock_ollama_chat):
        # Setup mocks
        mock_robot_instance = MagicMock()

        # Simulate a different event (e.g., greeting_hello = 6)
        mock_event = MagicMock()
        mock_event.intent_id = 6
        mock_event.json_data = json.dumps({})

        # Call the function
        vector_ollama.on_user_intent(mock_robot_instance, 'user_intent', mock_event, MagicMock())

        # Assertions: Ollama should NOT be called
        mock_ollama_chat.assert_not_called()
        mock_robot_instance.behavior.say_text.assert_not_called()

if __name__ == '__main__':
    unittest.main()
