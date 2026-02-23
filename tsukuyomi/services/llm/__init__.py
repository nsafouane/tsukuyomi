"""
Tsukuyomi LLM Service Package

This package provides the production-ready service for managing external AI connections,
prompt generation, and response streaming.

Key Components:
- LLMProvider: Abstract base class for LLM providers
- OpenAICompatibleProvider: OpenAI-compatible API implementation
- GroqProvider: Groq API implementation
- LLMService: Main service class for LLM integration
- Prompt templates and data structures for agent interactions
"""

from .provider import LLMProvider
from .openai_provider import OpenAICompatibleProvider, GroqProvider
from .service import LLMService
from .prompts import (
    ScenarioType,
    LLMRequestContext,
    LLMResponse,
    generate_plan_v2,
    generate_plan
)

__all__ = [
    # Abstract Provider
    "LLMProvider",

    # Concrete Providers
    "OpenAICompatibleProvider",
    "GroqProvider",

    # Main Service
    "LLMService",

    # Data Structures
    "ScenarioType",
    "LLMRequestContext",
    "LLMResponse",

    # Legacy Compatibility Functions
    "generate_plan_v2",
    "generate_plan",
]
