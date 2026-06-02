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
            'message': {'content': 'Hello! I am Vector.'}
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
        
        mock_robot_instance.behavior.say_text.assert_called_with('Hello! I am Vector.')

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
