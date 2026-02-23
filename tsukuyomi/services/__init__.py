"""
Tsukuyomi Services Package

This package contains service implementations for the Tsukuyomi engine,
including database, LLM, embedding, and vector services.

Subpackages:
- llm: LLM provider abstraction (OpenAI, Groq, etc.)
- embedding: Text embedding generation
- vector: Vector database abstraction (Qdrant, in-memory)
- database: Persistent storage services

Usage:
    from tsukuyomi.services import LLMService, EmbeddingService
    from tsukuyomi.services import VectorStore, DBManager
"""

from tsukuyomi.services.llm import (
    LLMProvider,
    LLMService,
    OpenAICompatibleProvider,
    GroqProvider,
    LLMRequestContext,
    LLMResponse,
    ScenarioType,
)
from tsukuyomi.services.embedding import (
    EmbeddingService,
    EmbeddingConfig,
    EmbeddingProvider,
)
from tsukuyomi.services.vector import (
    VectorStore,
    VectorConfig,
    MemoryPoint,
    DistanceMetric,
)
from tsukuyomi.services.database import DBManager

__all__ = [
    "LLMProvider",
    "LLMService",
    "OpenAICompatibleProvider",
    "GroqProvider",
    "LLMRequestContext",
    "LLMResponse",
    "ScenarioType",
    "EmbeddingService",
    "EmbeddingConfig",
    "EmbeddingProvider",
    "VectorStore",
    "VectorConfig",
    "MemoryPoint",
    "DistanceMetric",
    "DBManager",
]
