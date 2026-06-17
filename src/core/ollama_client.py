import aiohttp
import asyncio
import json
import logging

# Configure a named logger
logger = logging.getLogger('ollama.client')

class OllamaClient:
    def __init__(self, base_url, model, api_key=None):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=60)
        self._session = None

    async def get_session(self):
        """
        Returns the persistent aiohttp session, creating it if necessary.
        """
        if self._session is None or self._session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._session = aiohttp.ClientSession(timeout=self.timeout, headers=headers)
        return self._session

    async def close(self):
        """
        Closes the persistent session.
        """
        if self._session and not self._session.closed:
            await self._session.close()

    async def check_health(self):
        """
        Verifies the local Ollama endpoint is active.
        """
        try:
            session = await self.get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    return True
                else:
                    logger.error(f"Health check failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def chat(self, messages, retries=3, backoff_factor=1.5):
        """
        Sends a chat request to Ollama with retries and exponential backoff.
        Retries on 429 (rate limit) and 5xx (server errors).
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        logger.info(f"Sending chat request to Ollama (Model: {self.model}, Messages: {len(messages)})")

        last_exception = None
        for attempt in range(retries):
            try:
                session = await self.get_session()
                async with session.post(f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['message']['content']
                        logger.info(f"Received successful response from Ollama ({len(content)} chars)")
                        return content

                    error_text = await response.text()
                    logger.warning(f"Ollama API error ({response.status}) on attempt {attempt + 1}: {error_text}")

                    # Retry on 429 and 5xx
                    if response.status == 429 or response.status >= 500:
                        wait_time = backoff_factor ** attempt
                        logger.info(f"Retrying in {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        # For 4xx (other than 429), it's likely a client error that won't resolve with retry
                        raise Exception(f"Ollama API non-retryable error: {response.status}")

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                wait_time = backoff_factor ** attempt
                logger.warning(f"Network error on attempt {attempt + 1}: {e}. Retrying in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Unexpected error during Ollama API call: {e}")
                raise e

        logger.error(f"All {retries} attempts failed.")
        if last_exception:
            raise last_exception
        else:
            raise Exception("Failed to get response from Ollama after multiple retries.")
