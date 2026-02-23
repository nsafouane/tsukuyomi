"""
OpenAI-Compatible Provider Implementation

This module provides concrete implementations for OpenAI-compatible APIs,
including OpenAI, Groq, and other compatible providers.
"""

import asyncio
import json
import logging
from typing import Optional, AsyncIterator, Dict, Any

import aiohttp

from .provider import LLMProvider
from .prompts import LLMResponse

logger = logging.getLogger("LLMService")


class OpenAICompatibleProvider(LLMProvider):
    """
    Concrete implementation for OpenAI-compatible APIs.

    Supports:
    - OpenAI (GPT-3.5, GPT-4)
    - Groq (Llama models via OpenAI-compatible API)
    - Other providers with OpenAI-compatible endpoints
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 30
    ):
        super().__init__(api_key, model, timeout)
        self.base_url = base_url.rstrip('/')
        self.endpoint = f"{self.base_url}/chat/completions"

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> LLMResponse:
        """Generate a response using OpenAI-compatible API."""
        async with self._semaphore:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.endpoint,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"API error {response.status}: {error_text}")
                            raise Exception(f"API returned status {response.status}: {error_text}")

                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data.get("usage", {}).get("total_tokens")

                        # Parse JSON response
                        parsed = self._parse_json_response(content)

                        return LLMResponse(
                            thought=parsed.get("thought", ""),
                            action=parsed.get("action", "IDLE"),
                            params=parsed.get("params", {}),
                            raw_response=content,
                            provider=self.__class__.__name__,
                            tokens_used=tokens_used
                        )

            except asyncio.TimeoutError:
                logger.error(f"Request timed out after {self.timeout}s")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """Stream a response token by token."""
        async with self._semaphore:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "stream": True
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.endpoint,
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"API error {response.status}: {error_text}")
                            raise Exception(f"API returned status {response.status}")

                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]
                                if data_str == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    token = delta.get("content", "")
                                    if token:
                                        yield token
                                except json.JSONDecodeError:
                                    continue

            except asyncio.TimeoutError:
                logger.error(f"Stream timed out after {self.timeout}s")
                raise

    async def health_check(self) -> bool:
        """Check if the API is accessible."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try direct parsing first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from content: {content[:200]}")
            return {
                "thought": "I am processing the environment carefully.",
                "action": "IDLE",
                "params": {"duration": 10}
            }


class GroqProvider(OpenAICompatibleProvider):
    """Concrete implementation for Groq API."""

    def __init__(self, api_key: str, model: str, timeout: int = 30):
        super().__init__(api_key, model, "https://api.groq.com/openai/v1", timeout)
