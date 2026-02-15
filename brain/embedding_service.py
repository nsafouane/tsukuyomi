"""
Embedding Service - Multi-provider embedding generation

This module provides a unified interface for generating text embeddings
with support for multiple providers: OpenAI, HuggingFace, and local models.
"""

import logging
from typing import List, Optional, Union
from enum import Enum
import os

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai not installed. Install with: pip install openai")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")

logger = logging.getLogger(__name__)


class EmbeddingProvider(Enum):
    """Supported embedding providers."""
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service."""
    provider: EmbeddingProvider
    model_name: str
    api_key: Optional[str] = None
    dimensions: Optional[int] = None
    batch_size: int = 32
    cache_embeddings: bool = True

from dataclasses import dataclass


class EmbeddingService:
    """
    Unified embedding service supporting multiple providers.

    Provides consistent interface for generating text embeddings
    across different embedding models and providers.
    """

    def __init__(self, config: EmbeddingConfig):
        """
        Initialize the embedding service.

        Args:
            config: EmbeddingConfig with provider settings
        """
        self.config = config
        self._model = None
        self._client = None
        self._embedding_cache: dict = {}

        self._initialize_provider()

    def _initialize_provider(self) -> None:
        """Initialize the selected embedding provider."""
        if self.config.provider == EmbeddingProvider.OPENAI:
            self._initialize_openai()
        elif self.config.provider == EmbeddingProvider.HUGGINGFACE:
            self._initialize_huggingface()
        elif self.config.provider == EmbeddingProvider.LOCAL:
            self._initialize_local()
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _initialize_openai(self) -> None:
        """Initialize OpenAI embedding client."""
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai is required for OpenAI embeddings. "
                "Install with: pip install openai"
            )

        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY not set")

        self._client = openai.OpenAI(api_key=api_key)

        # Set default dimensions based on model
        if not self.config.dimensions:
            if "ada-002" in self.config.model_name:
                self.config.dimensions = 1536
            elif "3-small" in self.config.model_name:
                self.config.dimensions = 1536
            elif "3-large" in self.config.model_name:
                self.config.dimensions = 3072
            else:
                self.config.dimensions = 1536

        logger.info(f"Initialized OpenAI embeddings with model: {self.config.model_name}")

    def _initialize_huggingface(self) -> None:
        """Initialize HuggingFace embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for HuggingFace embeddings. "
                "Install with: pip install sentence-transformers"
            )

        try:
            self._model = SentenceTransformer(self.config.model_name)

            if not self.config.dimensions:
                self.config.dimensions = self._model.get_sentence_embedding_dimension()

            logger.info(f"Initialized HuggingFace embeddings with model: {self.config.model_name}")

        except Exception as e:
            logger.error(f"Error loading HuggingFace model: {e}")
            raise

    def _initialize_local(self) -> None:
        """Initialize local embedding model (same as HuggingFace)."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Install with: pip install sentence-transformers"
            )

        try:
            # Use a good default local model if not specified
            model_name = self.config.model_name or "all-MiniLM-L6-v2"
            self._model = SentenceTransformer(model_name)

            if not self.config.dimensions:
                self.config.dimensions = self._model.get_sentence_embedding_dimension()

            logger.info(f"Initialized local embeddings with model: {model_name}")

        except Exception as e:
            logger.error(f"Error loading local model: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if self.config.cache_embeddings:
            cache_key = f"single:{hash(text)}"
            if cache_key in self._embedding_cache:
                return self._embedding_cache[cache_key]

        embedding = self._generate_embeddings([text])[0]

        if self.config.cache_embeddings:
            self._embedding_cache[cache_key] = embedding

        return embedding

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Use cache for individual texts if enabled
        if self.config.cache_embeddings:
            cached_embeddings = []
            uncached_texts = []
            uncached_indices = []

            for i, text in enumerate(texts):
                cache_key = f"single:{hash(text)}"
                if cache_key in self._embedding_cache:
                    cached_embeddings.append((i, self._embedding_cache[cache_key]))
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)

            # Generate embeddings for uncached texts
            if uncached_texts:
                new_embeddings = self._generate_embeddings(uncached_texts)
                for idx, embedding in zip(uncached_indices, new_embeddings):
                    cache_key = f"single:{hash(texts[idx])}"
                    self._embedding_cache[cache_key] = embedding
                    cached_embeddings.append((idx, embedding))

            # Sort by original index and return
            cached_embeddings.sort(key=lambda x: x[0])
            return [emb for _, emb in cached_embeddings]
        else:
            return self._generate_embeddings(texts)

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using the configured provider.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if self.config.provider == EmbeddingProvider.OPENAI:
            return self._generate_openai_embeddings(texts)
        elif self.config.provider in (EmbeddingProvider.HUGGINGFACE, EmbeddingProvider.LOCAL):
            return self._generate_local_embeddings(texts)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API."""
        try:
            # Process in batches
            all_embeddings = []
            for i in range(0, len(texts), self.config.batch_size):
                batch = texts[i:i + self.config.batch_size]
                response = self._client.embeddings.create(
                    model=self.config.model_name,
                    input=batch
                )
                all_embeddings.extend([item.embedding for item in response.data])

            return all_embeddings

        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {e}")
            raise

    def _generate_local_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        try:
            embeddings = self._model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"Error generating local embeddings: {e}")
            raise

    def get_dimensions(self) -> int:
        """Get the embedding dimension size."""
        return self.config.dimensions or 0

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")

    @classmethod
    def create_openai(
        cls,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small"
    ) -> "EmbeddingService":
        """
        Factory method to create OpenAI embedding service.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name (default: text-embedding-3-small)

        Returns:
            EmbeddingService instance
        """
        config = EmbeddingConfig(
            provider=EmbeddingProvider.OPENAI,
            model_name=model,
            api_key=api_key
        )
        return cls(config)

    @classmethod
    def create_huggingface(
        cls,
        model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> "EmbeddingService":
        """
        Factory method to create HuggingFace embedding service.

        Args:
            model: HuggingFace model name

        Returns:
            EmbeddingService instance
        """
        config = EmbeddingConfig(
            provider=EmbeddingProvider.HUGGINGFACE,
            model_name=model
        )
        return cls(config)

    @classmethod
    def create_local(
        cls,
        model: str = "all-MiniLM-L6-v2"
    ) -> "EmbeddingService":
        """
        Factory method to create local embedding service.

        Args:
            model: Local model name (sentence-transformers model)

        Returns:
            EmbeddingService instance
        """
        config = EmbeddingConfig(
            provider=EmbeddingProvider.LOCAL,
            model_name=model
        )
        return cls(config)
