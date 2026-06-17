import unittest
import os
import sys
from unittest.mock import patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.tts_utils import sanitize_for_tts
from src.utils.config_loader import load_config

class TestUtils(unittest.TestCase):

    def test_sanitize_for_tts(self):
        # Basic alphanumeric and punctuation
        self.assertEqual(sanitize_for_tts("Hello, world!"), "Hello, world!")

        # Abbreviation expansion
        self.assertEqual(sanitize_for_tts("Battery is 4V."), "Battery is four volts.")
        self.assertEqual(sanitize_for_tts("Speed is 10km/h."), "Speed is ten kilometers per hour.")

        # Number expansion (0-99)
        self.assertEqual(sanitize_for_tts("I have 42 cubes."), "I have forty two cubes.")
        self.assertEqual(sanitize_for_tts("Agent 7."), "Agent seven.")

        # Markdown removal
        self.assertEqual(sanitize_for_tts("This is **bold** and `code`."), "This is bold and code.")

        # Special character removal
        self.assertEqual(sanitize_for_tts("Hello_World #1!"), "Hello World one!")

        # Sentence cap
        self.assertEqual(sanitize_for_tts("First. Second. Third."), "First. Second.")

        # Word cap
        long_text = " ".join(["word"] * 40)
        sanitized = sanitize_for_tts(long_text)
        self.assertEqual(len(sanitized.split()), 35)

    @patch.dict(os.environ, {
        "OLLAMA_BASE_URL": "http://test:11434",
        "OLLAMA_MODEL": "test-model",
        "OLLAMA_API_KEY": "test-key",
        "WIRE_POD_IP": "1.2.3.4",
        "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": "python"
    })
    def test_load_config(self):
        config = load_config()
        self.assertEqual(config["OLLAMA_BASE_URL"], "http://test:11434")
        self.assertEqual(config["OLLAMA_MODEL"], "test-model")
        self.assertEqual(config["OLLAMA_API_KEY"], "test-key")
        self.assertEqual(config["WIRE_POD_IP"], "1.2.3.4")
        self.assertEqual(config["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"], "python")
        self.assertEqual(os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"], "python")

if __name__ == '__main__':
    unittest.main()
