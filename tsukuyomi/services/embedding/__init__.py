"""
Embedding Service Package

Provides unified embedding generation with support for multiple providers:
- OpenAI (text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002)
- HuggingFace (sentence-transformers models)
- Local (sentence-transformers models)
"""

from tsukuyomi.services.embedding.service import (
    EmbeddingService,
    EmbeddingConfig,
    EmbeddingProvider,
)

__all__ = [
    "EmbeddingService",
    "EmbeddingConfig",
    "EmbeddingProvider",
]
