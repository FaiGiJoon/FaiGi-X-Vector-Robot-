import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
from src.core.ollama_client import OllamaClient

class TestOllamaClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.base_url = "http://localhost:11434"
        self.model = "test-model"
        self.api_key = "test-key"
        self.client = OllamaClient(self.base_url, self.model, self.api_key)

    async def asyncTearDown(self):
        await self.client.close()

    @patch('aiohttp.ClientSession.post')
    async def test_chat_success(self, mock_post):
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'message': {'content': 'Hello!'}
        }
        mock_post.return_value.__aenter__.return_value = mock_response

        messages = [{'role': 'user', 'content': 'Hi'}]
        response = await self.client.chat(messages)

        self.assertEqual(response, 'Hello!')
        mock_post.assert_called_once()
        # Verify headers (api key)
        session = await self.client.get_session()
        self.assertEqual(session._default_headers['Authorization'], 'Bearer test-key')

    @patch('aiohttp.ClientSession.post')
    async def test_chat_retry_on_500(self, mock_post):
        # Setup mock responses: first two fail with 500, third succeeds
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500
        mock_response_fail.text.return_value = "Internal Server Error"

        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json.return_value = {
            'message': {'content': 'Success after retry'}
        }

        mock_post.side_effect = [
            MagicMock(__aenter__=AsyncMock(return_value=mock_response_fail)),
            MagicMock(__aenter__=AsyncMock(return_value=mock_response_fail)),
            MagicMock(__aenter__=AsyncMock(return_value=mock_response_success))
        ]

        messages = [{'role': 'user', 'content': 'Hi'}]
        # Using small backoff to speed up test
        response = await self.client.chat(messages, retries=3, backoff_factor=0.1)

        self.assertEqual(response, 'Success after retry')
        self.assertEqual(mock_post.call_count, 3)

    @patch('aiohttp.ClientSession.post')
    async def test_chat_non_retryable_error(self, mock_post):
        # Setup mock response: 400 Bad Request
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text.return_value = "Bad Request"
        mock_post.return_value.__aenter__.return_value = mock_response

        messages = [{'role': 'user', 'content': 'Hi'}]

        with self.assertRaises(Exception) as cm:
            await self.client.chat(messages, retries=3, backoff_factor=0.1)

        self.assertIn("Ollama API non-retryable error: 400", str(cm.exception))
        self.assertEqual(mock_post.call_count, 1)

if __name__ == '__main__':
    unittest.main()
