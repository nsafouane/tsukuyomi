"""
LLM Provider Abstract Base Class

This module defines the abstract interface that all LLM providers must implement.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator

from .prompts import LLMResponse


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All concrete implementations must inherit from this class and implement
    the required methods for generating responses and streaming.
    """

    def __init__(self, api_key: str, model: str, timeout: int = 30):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for authentication
            model: Model identifier to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(5)  # Concurrent request limit

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> LLMResponse:
        """
        Generate a complete response from the LLM.

        Args:
            prompt: The user prompt to send
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse containing parsed action and thought
        """
        pass

    @abstractmethod
    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """
        Stream a response token by token.

        Args:
            prompt: The user prompt to send
            system_prompt: Optional system prompt for context
            temperature: Sampling temperature (0.0-1.0)

        Yields:
            Individual tokens as they arrive
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider API is accessible."""
        pass
