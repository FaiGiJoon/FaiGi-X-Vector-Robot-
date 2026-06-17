import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import anki_vector.util
# Import the module where the monkeypatch is applied to trigger the patch
from src.core import vector_ollama

class TestMonkeyPatch(unittest.TestCase):

    def test_read_configuration_with_env_vars(self):
        # Set environment variables
        env_vars = {
            "VECTOR_IP": "192.168.1.10",
            "VECTOR_NAME": "Vector-T8R2",
            "VECTOR_SERIAL": "00e20100",
            "VECTOR_GUID": "test-guid",
            "VECTOR_CERT_PATH": "/path/to/cert"
        }

        with patch.dict(os.environ, env_vars):
            # Call the patched function
            config = anki_vector.util.read_configuration(None, None, MagicMock())

            # Assertions
            self.assertEqual(config["ip"], "192.168.1.10")
            self.assertEqual(config["name"], "Vector-T8R2")
            self.assertEqual(config["serial"], "00e20100")
            self.assertEqual(config["guid"], "test-guid")
            self.assertEqual(config["cert"], "/path/to/cert")

    def test_read_configuration_fallback(self):
        # Ensure environment variables are NOT set
        env_vars = ["VECTOR_IP", "VECTOR_NAME", "VECTOR_GUID", "VECTOR_CERT_PATH"]

        with patch.dict(os.environ, {k: "" for k in env_vars}):
            # We expect the original read_configuration to be called, which will fail if no config file exists
            # We mock the original to verify it's called
            with patch('src.core.vector_ollama._original_read_configuration') as mock_orig:
                mock_orig.return_value = {"status": "original_called"}

                config = anki_vector.util.read_configuration("serial", "name", "logger")

                self.assertEqual(config["status"], "original_called")
                mock_orig.assert_called_once_with("serial", "name", "logger")

if __name__ == '__main__':
    unittest.main()
