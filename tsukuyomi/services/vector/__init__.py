"""
Vector Store Service Module

Provides vector database abstraction layer for memory storage and retrieval.
"""

from .store import (
    VectorStore,
    VectorConfig,
    MemoryPoint,
    DistanceMetric
)

__all__ = [
    "VectorStore",
    "VectorConfig",
    "MemoryPoint",
    "DistanceMetric"
]
