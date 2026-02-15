"""
Vector Store Abstraction Layer - Qdrant-compatible

This module provides a clean abstraction for vector database operations,
with support for Qdrant and future backends.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
        SearchRequest,
        Filter as SearchFilter
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning("qdrant-client not installed. Install with: pip install qdrant-client")

from datetime import datetime


logger = logging.getLogger(__name__)


class DistanceMetric(Enum):
    """Supported distance metrics for similarity search."""
    COSINE = "cosine"
    DOT = "dot"
    EUCLID = "euclid"


@dataclass
class VectorConfig:
    """Configuration for vector store."""
    collection_name: str
    vector_size: int = 1536  # Default OpenAI ada-002 dimension
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    host: Optional[str] = None
    port: int = 6333
    api_key: Optional[str] = None
    url: Optional[str] = None
    in_memory: bool = False


@dataclass
class MemoryPoint:
    """A memory point with metadata."""
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    timestamp: Optional[datetime] = None

    def to_qdrant_point(self) -> PointStruct:
        """Convert to Qdrant PointStruct."""
        return PointStruct(
            id=self.id,
            vector=self.vector,
            payload={
                **self.payload,
                "timestamp": self.timestamp.isoformat() if self.timestamp else datetime.utcnow().isoformat()
            }
        )


class VectorStore:
    """
    Vector database abstraction layer.

    Provides a unified interface for vector storage and retrieval,
    currently supporting Qdrant as the primary backend.
    """

    def __init__(self, config: VectorConfig):
        """
        Initialize the vector store.

        Args:
            config: VectorConfig instance with store settings
        """
        self.config = config
        self.client: Optional[Any] = None

        if not QDRANT_AVAILABLE:
            raise ImportError(
                "qdrant-client is required but not installed. "
                "Install with: pip install qdrant-client"
            )

        self._initialize_client()
        self._ensure_collection()

    def _initialize_client(self) -> None:
        """Initialize Qdrant client based on configuration."""
        if self.config.in_memory:
            logger.info("Initializing in-memory Qdrant client")
            self.client = QdrantClient(":memory:")
        elif self.config.url:
            logger.info(f"Initializing Qdrant client at {self.config.url}")
            self.client = QdrantClient(url=self.config.url, api_key=self.config.api_key)
        elif self.config.host:
            logger.info(f"Initializing Qdrant client at {self.config.host}:{self.config.port}")
            self.client = QdrantClient(
                host=self.config.host,
                port=self.config.port,
                api_key=self.config.api_key
            )
        else:
            logger.info("Initializing local Qdrant client")
            self.client = QdrantClient("localhost", port=6333)

    def _ensure_collection(self) -> None:
        """Ensure the collection exists, create if not."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.config.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.config.collection_name}")
                self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=VectorParams(
                        size=self.config.vector_size,
                        distance=self._map_distance_metric(self.config.distance_metric)
                    )
                )
            else:
                logger.info(f"Collection already exists: {self.config.collection_name}")

        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise

    def _map_distance_metric(self, metric: DistanceMetric) -> Distance:
        """Map our DistanceMetric enum to Qdrant Distance."""
        mapping = {
            DistanceMetric.COSINE: Distance.COSINE,
            DistanceMetric.DOT: Distance.DOT,
            DistanceMetric.EUCLID: Distance.EUCLID
        }
        return mapping.get(metric, Distance.COSINE)

    def add_points(self, points: List[MemoryPoint], batch_size: int = 100) -> bool:
        """
        Add multiple memory points to the vector store.

        Args:
            points: List of MemoryPoint objects
            batch_size: Number of points to upload per batch

        Returns:
            True if successful, False otherwise
        """
        try:
            qdrant_points = [p.to_qdrant_point() for p in points]

            # Upload in batches
            for i in range(0, len(qdrant_points), batch_size):
                batch = qdrant_points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.config.collection_name,
                    points=batch
                )
                logger.debug(f"Uploaded batch of {len(batch)} points")

            logger.info(f"Successfully added {len(points)} points to vector store")
            return True

        except Exception as e:
            logger.error(f"Error adding points: {e}")
            return False

    def add_point(self, point: MemoryPoint) -> bool:
        """
        Add a single memory point to the vector store.

        Args:
            point: MemoryPoint object

        Returns:
            True if successful, False otherwise
        """
        return self.add_points([point])

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_payload: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query vector to search with
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            filter_payload: Optional filter conditions on payload

        Returns:
            List of results with payload and score
        """
        try:
            search_filter = self._build_filter(filter_payload) if filter_payload else None

            results = self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter,
                score_threshold=score_threshold
            )

            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                    "vector": result.vector
                })

            logger.debug(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def _build_filter(self, filter_payload: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from payload dictionary."""
        conditions = []
        for key, value in filter_payload.items():
            conditions.append(
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
            )

        return Filter(must=conditions)

    def get_point(self, point_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific point by ID.

        Args:
            point_id: ID of the point to retrieve

        Returns:
            Point data or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=self.config.collection_name,
                ids=[point_id]
            )

            if result:
                return {
                    "id": result[0].id,
                    "payload": result[0].payload,
                    "vector": result[0].vector
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving point: {e}")
            return None

    def delete_point(self, point_id: str) -> bool:
        """
        Delete a specific point.

        Args:
            point_id: ID of the point to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=[point_id]
            )
            logger.info(f"Deleted point: {point_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting point: {e}")
            return False

    def delete_by_filter(self, filter_payload: Dict[str, Any]) -> int:
        """
        Delete points matching a filter.

        Args:
            filter_payload: Filter conditions

        Returns:
            Number of points deleted
        """
        try:
            search_filter = self._build_filter(filter_payload)
            result = self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=search_filter
            )
            logger.info(f"Deleted points matching filter")
            return 1  # Qdrant doesn't return exact count

        except Exception as e:
            logger.error(f"Error deleting by filter: {e}")
            return 0

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.

        Returns:
            Collection metadata
        """
        try:
            info = self.client.get_collection(self.config.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vector_size": info.config.params.vectors.size,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}

    def clear_collection(self) -> bool:
        """
        Clear all points from the collection.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(self.config.collection_name)
            self._ensure_collection()
            logger.info(f"Cleared collection: {self.config.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False

    def generate_id(self, content: str, namespace: str = "memory") -> str:
        """
        Generate a deterministic ID for a memory.

        Args:
            content: Content to hash
            namespace: Namespace for the ID

        Returns:
            SHA256 hash as hex string
        """
        hash_input = f"{namespace}:{content}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
