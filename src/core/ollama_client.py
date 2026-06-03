import aiohttp
import asyncio
import json
import logging

class OllamaClient:
    def __init__(self, base_url, model):
        self.base_url = base_url
        self.model = model
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def check_health(self):
        """
        Verifies the local Ollama endpoint is active.
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return False

    async def chat(self, messages, retries=3, backoff_factor=1.5):
        """
        Sends a chat request to Ollama with retries and exponential backoff.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        last_exception = None
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(f"{self.base_url}/api/chat", json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result['message']['content']
                        else:
                            error_text = await response.text()
                            logging.error(f"Ollama API error ({response.status}): {error_text}")
                            raise Exception(f"Ollama API error: {response.status}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                wait_time = backoff_factor ** attempt
                logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logging.error(f"Unexpected error during Ollama API call: {e}")
                raise e

        logging.error(f"All {retries} attempts failed.")
        raise last_exception
