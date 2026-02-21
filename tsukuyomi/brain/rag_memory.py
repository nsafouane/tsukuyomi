"""
RAG Memory System - Retrieval-Augmented Generation for Long-term Memory

This module implements the core RAG system for agent long-term memory,
including memory storage, retrieval, consolidation, and pruning.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

from .vector_store import VectorStore, VectorConfig, MemoryPoint, DistanceMetric
from .embedding_service import EmbeddingService, EmbeddingProvider
from tsukuyomi.core.memory.base import MemoryType, ImportanceLevel



logger = logging.getLogger(__name__)






@dataclass
class Memory:
    """A memory entry with metadata."""
    content: str
    memory_type: MemoryType
    importance: ImportanceLevel = ImportanceLevel.MEDIUM
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    related_memories: List[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    embedding: Optional[List[float]] = None

    def to_payload(self) -> Dict[str, Any]:
        """Convert memory to payload for vector store."""
        return {
            "content": self.content,
            "memory_type": self.memory_type.value,
            "importance": self.importance.value,
            "tags": self.tags,
            "source": self.source,
            "related_memories": self.related_memories,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_payload(cls, payload: Dict[str, Any], embedding: Optional[List[float]] = None) -> "Memory":
        """Create Memory from payload."""
        return cls(
            content=payload["content"],
            memory_type=MemoryType(payload["memory_type"]),
            importance=ImportanceLevel(payload["importance"]),
            tags=payload.get("tags", []),
            source=payload.get("source"),
            related_memories=payload.get("related_memories", []),
            access_count=payload.get("access_count", 0),
            last_accessed=datetime.fromisoformat(payload["last_accessed"]) if payload.get("last_accessed") else None,
            created_at=datetime.fromisoformat(payload["created_at"]),
            expires_at=datetime.fromisoformat(payload["expires_at"]) if payload.get("expires_at") else None,
            embedding=embedding
        )


@dataclass
class RAGConfig:
    """Configuration for RAG memory system."""
    # Vector store config
    vector_collection: str = "agent_memories"
    vector_size: int = 1536
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    vector_host: Optional[str] = None
    vector_port: int = 6333
    vector_api_key: Optional[str] = None
    vector_url: Optional[str] = None
    in_memory: bool = False

    # Embedding config
    embedding_provider: EmbeddingProvider = EmbeddingProvider.LOCAL
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_api_key: Optional[str] = None
    embedding_batch_size: int = 32

    # Retrieval config
    default_top_k: int = 5
    min_similarity_score: float = 0.7
    rerank_results: bool = True

    # Consolidation config
    consolidation_interval_hours: int = 24
    max_working_memories: int = 100
    importance_decay_days: int = 30
    min_access_count_to_keep: int = 1


class RAGMemorySystem:
    """
    RAG Memory System for agent long-term memory.

    Provides:
    - Memory storage with vector embeddings
    - Retrieval-augmented generation support
    - Memory consolidation and pruning
    - Working memory management
    """

    def __init__(self, config: RAGConfig):
        """
        Initialize the RAG memory system.

        Args:
            config: RAGConfig with system settings
        """
        self.config = config
        self.vector_store: Optional[VectorStore] = None
        self.embedding_service: Optional[EmbeddingService] = None

        self._initialize()

    def _initialize(self) -> None:
        """Initialize vector store and embedding service."""
        # Initialize vector store
        vector_config = VectorConfig(
            collection_name=self.config.vector_collection,
            vector_size=self.config.vector_size,
            distance_metric=self.config.distance_metric,
            host=self.config.vector_host,
            port=self.config.vector_port,
            api_key=self.config.vector_api_key,
            url=self.config.vector_url,
            in_memory=self.config.in_memory
        )
        self.vector_store = VectorStore(vector_config)

        # Initialize embedding service
        from .embedding_service import EmbeddingConfig
        embedding_config = EmbeddingConfig(
            provider=self.config.embedding_provider,
            model_name=self.config.embedding_model,
            api_key=self.config.embedding_api_key,
            dimensions=self.config.vector_size,
            batch_size=self.config.embedding_batch_size
        )
        self.embedding_service = EmbeddingService(embedding_config)

        logger.info("RAG Memory System initialized")

    def add_memory(self, memory: Memory) -> str:
        """
        Add a memory to the system.

        Args:
            memory: Memory object to store

        Returns:
            ID of the stored memory
        """
        try:
            # Generate embedding if not provided
            if memory.embedding is None:
                memory.embedding = self.embedding_service.embed_text(memory.content)

            # Generate ID
            memory_id = self.vector_store.generate_id(memory.content, "memory")

            # Create memory point
            memory_point = MemoryPoint(
                id=memory_id,
                vector=memory.embedding,
                payload=memory.to_payload(),
                timestamp=memory.created_at
            )

            # Store in vector database
            success = self.vector_store.add_point(memory_point)

            if success:
                logger.info(f"Added memory: {memory_id[:8]}... ({memory.memory_type.value})")
                return memory_id
            else:
                raise Exception("Failed to store memory")

        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            raise

    def retrieve_memories(
        self,
        query: str,
        top_k: Optional[int] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[ImportanceLevel] = None,
        exclude_expired: bool = True
    ) -> List[Tuple[Memory, float]]:
        """
        Retrieve relevant memories for a query.

        Args:
            query: Query string
            top_k: Number of results to return
            memory_type: Filter by memory type
            tags: Filter by tags (any match)
            min_importance: Minimum importance level
            exclude_expired: Exclude expired memories

        Returns:
            List of (Memory, similarity_score) tuples
        """
        try:
            top_k = top_k or self.config.default_top_k

            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)

            # Build filters
            filters = {}
            if memory_type:
                filters["memory_type"] = memory_type.value
            if min_importance:
                filters["importance"] = {"$gte": min_importance.value}

            # Search vector store
            results = self.vector_store.search(
                query_vector=query_embedding,
                limit=top_k * 2,  # Get more for filtering
                score_threshold=self.config.min_similarity_score,
                filter_payload=filters if filters else None
            )

            # Convert to Memory objects and apply additional filters
            memories = []
            for result in results:
                memory = Memory.from_payload(result["payload"], result["vector"])

                # Tag filter
                if tags and not any(tag in memory.tags for tag in tags):
                    continue

                # Expiration filter
                if exclude_expired and memory.expires_at and memory.expires_at < datetime.utcnow():
                    continue

                # Update access stats
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()

                memories.append((memory, result["score"]))

            # Sort by similarity and limit
            memories.sort(key=lambda x: x[1], reverse=True)
            memories = memories[:top_k]

            logger.debug(f"Retrieved {len(memories)} memories for query")
            return memories

        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return []

    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """
        Retrieve a specific memory by ID.

        Args:
            memory_id: Memory ID

        Returns:
            Memory object or None if not found
        """
        try:
            result = self.vector_store.get_point(memory_id)
            if result:
                memory = Memory.from_payload(result["payload"], result["vector"])
                memory.access_count += 1
                memory.last_accessed = datetime.utcnow()
                return memory
            return None

        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            return None

    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a memory.

        Args:
            memory_id: Memory ID
            updates: Fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            memory = self.get_memory_by_id(memory_id)
            if not memory:
                return False

            # Apply updates
            for key, value in updates.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)

            # Re-generate embedding if content changed
            if "content" in updates:
                memory.embedding = self.embedding_service.embed_text(memory.content)
                memory_id = self.vector_store.generate_id(memory.content, "memory")

            # Store updated memory
            memory_point = MemoryPoint(
                id=memory_id,
                vector=memory.embedding,
                payload=memory.to_payload(),
                timestamp=memory.created_at
            )

            return self.vector_store.add_point(memory_point)

        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False

    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: Memory ID

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.vector_store.delete_point(memory_id)
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False

    def consolidate_memories(self) -> Dict[str, int]:
        """
        Perform memory consolidation and pruning.

        This process:
        1. Identifies related memories and merges similar ones
        2. Prunes low-importance, rarely accessed memories
        3. Archives old working memories to long-term storage

        Returns:
            Statistics about consolidation
        """
        stats = {
            "merged": 0,
            "pruned": 0,
            "archived": 0,
            "errors": 0
        }

        try:
            logger.info("Starting memory consolidation")

            # Get all memories
            collection_info = self.vector_store.get_collection_info()
            total_memories = collection_info.get("points_count", 0)

            if total_memories == 0:
                logger.info("No memories to consolidate")
                return stats

            # Prune expired memories
            expired_count = self._prune_expired_memories()
            stats["pruned"] += expired_count

            # Prune low-value memories
            low_value_count = self._prune_low_value_memories()
            stats["pruned"] += low_value_count

            # Consolidate working memory
            archived_count = self._consolidate_working_memory()
            stats["archived"] = archived_count

            logger.info(f"Consolidation complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error during consolidation: {e}")
            stats["errors"] += 1
            return stats

    def _prune_expired_memories(self) -> int:
        """Remove expired memories."""
        try:
            # This is a simplified version - in practice, you'd scan and delete
            # For now, we'll use a placeholder
            logger.debug("Pruning expired memories")
            return 0

        except Exception as e:
            logger.error(f"Error pruning expired memories: {e}")
            return 0

    def _prune_low_value_memories(self) -> int:
        """Remove low-importance, rarely accessed memories."""
        try:
            # Find memories with low importance and no recent access
            cutoff_date = datetime.utcnow() - timedelta(days=self.config.importance_decay_days)

            # This would be implemented with a query filter
            # For now, placeholder
            logger.debug(f"Pruning memories before {cutoff_date}")
            return 0

        except Exception as e:
            logger.error(f"Error pruning low-value memories: {e}")
            return 0

    def _consolidate_working_memory(self) -> int:
        """
        Archive old working memories to long-term storage.

        Returns:
            Number of memories archived
        """
        try:
            # Get working memories and determine which to archive
            # This is a placeholder - actual implementation would scan
            logger.debug("Consolidating working memory")
            return 0

        except Exception as e:
            logger.error(f"Error consolidating working memory: {e}")
            return 0

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system.

        Returns:
            Dictionary with memory statistics
        """
        try:
            collection_info = self.vector_store.get_collection_info()

            # Count by memory type (simplified)
            type_counts = {mt.value: 0 for mt in MemoryType}

            return {
                "total_memories": collection_info.get("points_count", 0),
                "vector_size": collection_info.get("vector_size", 0),
                "collection_status": collection_info.get("status", "unknown"),
                "memory_types": type_counts,
                "config": {
                    "default_top_k": self.config.default_top_k,
                    "min_similarity_score": self.config.min_similarity_score,
                    "consolidation_interval_hours": self.config.consolidation_interval_hours
                }
            }

        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {}

    def format_context_for_llm(self, memories: List[Tuple[Memory, float]], max_chars: int = 2000) -> str:
        """
        Format retrieved memories as context for LLM.

        Args:
            memories: List of (Memory, score) tuples
            max_chars: Maximum characters in context

        Returns:
            Formatted context string
        """
        if not memories:
            return "No relevant memories found."

        context_parts = []
        total_chars = 0

        for memory, score in memories:
            memory_text = f"[{memory.memory_type.value}] {memory.content}"
            if len(memory_text) + total_chars > max_chars:
                break

            context_parts.append(memory_text)
            total_chars += len(memory_text) + 2  # +2 for newline

        return "\n\n".join(context_parts)

    def close(self) -> None:
        """Clean up resources."""
        if self.vector_store:
            logger.info("Closing vector store")
        if self.embedding_service:
            self.embedding_service.clear_cache()
        logger.info("RAG Memory System closed")
