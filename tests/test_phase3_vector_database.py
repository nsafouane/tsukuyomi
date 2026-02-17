"""
Test Vector Database Operations for Phase 3.

Tests:
- CRUD operations on vectors
- Index management
- Batch operations
- Distance metrics
- Connection pooling
"""

import pytest
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import time
from unittest.mock import Mock, MagicMock


class VectorDatabase:
    """Vector Database implementation for testing."""

    def __init__(self, dimension: int = 768, metric: str = "cosine"):
        self.dimension = dimension
        self.metric = metric
        self.vectors = {}
        self.indexes = {}
        self.metadata = {}

    def insert(self, entity_id: str, entity_type: str, vector: np.ndarray,
               metadata: Dict[str, Any] = None) -> bool:
        """Insert a vector."""
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension {len(vector)} != expected {self.dimension}")

        self.vectors[entity_id] = {
            'vector': vector,
            'type': entity_type,
        }
        self.metadata[entity_id] = metadata or {}
        self._update_indexes(entity_id)
        return True

    def get(self, entity_id: str) -> Optional[Tuple[np.ndarray, Dict]]:
        """Get a vector by ID."""
        if entity_id not in self.vectors:
            return None
        return self.vectors[entity_id]['vector'], self.metadata[entity_id]

    def update(self, entity_id: str, vector: np.ndarray,
               metadata: Dict[str, Any] = None) -> bool:
        """Update a vector."""
        if entity_id not in self.vectors:
            return False

        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch")

        self.vectors[entity_id]['vector'] = vector
        if metadata is not None:
            self.metadata[entity_id] = metadata
        self._update_indexes(entity_id)
        return True

    def delete(self, entity_id: str) -> bool:
        """Delete a vector."""
        if entity_id not in self.vectors:
            return False

        del self.vectors[entity_id]
        del self.metadata[entity_id]
        return True

    def search(self, query: np.ndarray, top_k: int = 10,
               metric: str = None, entity_type: str = None,
               filters: Dict[str, Any] = None) -> List[Tuple[str, float, Dict]]:
        """Search for similar vectors."""
        metric = metric or self.metric
        results = []

        for entity_id, data in self.vectors.items():
            if entity_type and data['type'] != entity_type:
                continue

            if filters:
                # Apply metadata filters
                metadata = self.metadata[entity_id]
                if not all(k in metadata and metadata[k] == v for k, v in filters.items()):
                    continue

            similarity = self._compute_similarity(query, data['vector'], metric)
            results.append((entity_id, similarity, self.metadata[entity_id]))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def search_radius(self, query: np.ndarray, radius: float,
                      metric: str = None, entity_type: str = None) -> List[Tuple[str, float, Dict]]:
        """Search for vectors within a radius."""
        metric = metric or self.metric
        results = []

        for entity_id, data in self.vectors.items():
            if entity_type and data['type'] != entity_type:
                continue

            similarity = self._compute_similarity(query, data['vector'], metric)
            if similarity >= (1.0 - radius):  # Convert radius to similarity threshold
                results.append((entity_id, similarity, self.metadata[entity_id]))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def batch_insert(self, entities: List[Tuple[str, str, np.ndarray, Dict]]) -> int:
        """Insert multiple vectors at once."""
        count = 0
        for entity_id, entity_type, vector, metadata in entities:
            if self.insert(entity_id, entity_type, vector, metadata):
                count += 1
        return count

    def batch_delete(self, entity_ids: List[str]) -> int:
        """Delete multiple vectors at once."""
        count = 0
        for entity_id in entity_ids:
            if self.delete(entity_id):
                count += 1
        return count

    def count(self, entity_type: str = None) -> int:
        """Count vectors, optionally filtered by type."""
        if entity_type:
            return sum(1 for data in self.vectors.values() if data['type'] == entity_type)
        return len(self.vectors)

    def create_index(self, index_name: str, config: Dict[str, Any] = None) -> bool:
        """Create an index for faster searching."""
        self.indexes[index_name] = config or {}
        return True

    def drop_index(self, index_name: str) -> bool:
        """Drop an index."""
        if index_name in self.indexes:
            del self.indexes[index_name]
            return True
        return False

    def _compute_similarity(self, v1: np.ndarray, v2: np.ndarray, metric: str) -> float:
        """Compute similarity between two vectors."""
        if metric == "cosine":
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        elif metric == "euclidean":
            distance = np.linalg.norm(v1 - v2)
            return 1.0 / (1.0 + distance)  # Convert to similarity
        elif metric == "dot":
            return np.dot(v1, v2)
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def _update_indexes(self, entity_id: str):
        """Update indexes with new vector."""
        pass  # Placeholder for index updates


@pytest.fixture
def vector_db():
    """Create a vector database for testing."""
    return VectorDatabase(dimension=768, metric="cosine")


def test_insert_vector(vector_db):
    """Test inserting a vector."""
    entity_id = "vec_1"
    entity_type = "memory"
    vector = np.random.randn(768).astype(np.float32)
    metadata = {"tick": 100, "actor": "alice"}

    success = vector_db.insert(entity_id, entity_type, vector, metadata)

    assert success is True

    # Verify insertion
    stored_vector, stored_metadata = vector_db.get(entity_id)
    assert stored_vector is not None
    np.testing.assert_array_equal(stored_vector, vector)
    assert stored_metadata == metadata

    print(f"✓ Vector inserted: {entity_id}")


def test_insert_vector_dimension_mismatch(vector_db):
    """Test that inserting a vector with wrong dimension raises error."""
    entity_id = "vec_bad"
    vector = np.random.randn(512).astype(np.float32)  # Wrong dimension

    with pytest.raises(ValueError, match="Vector dimension"):
        vector_db.insert(entity_id, "memory", vector)

    print("✓ Dimension mismatch caught correctly")


def test_get_nonexistent_vector(vector_db):
    """Test getting a non-existent vector."""
    result = vector_db.get("nonexistent")
    assert result == (None, None)

    print("✓ Non-existent vector returns None")


def test_update_vector(vector_db):
    """Test updating a vector."""
    entity_id = "vec_update"

    # Insert initial vector
    vector1 = np.random.randn(768).astype(np.float32)
    vector_db.insert(entity_id, "memory", vector1, {"version": 1})

    # Update vector
    vector2 = np.random.randn(768).astype(np.float32)
    success = vector_db.update(entity_id, vector2, {"version": 2})

    assert success is True

    # Verify update
    stored_vector, stored_metadata = vector_db.get(entity_id)
    np.testing.assert_array_equal(stored_vector, vector2)
    assert stored_metadata["version"] == 2

    print(f"✓ Vector updated: {entity_id}")


def test_update_nonexistent_vector(vector_db):
    """Test updating a non-existent vector."""
    vector = np.random.randn(768).astype(np.float32)
    success = vector_db.update("nonexistent", vector)

    assert success is False

    print("✓ Update nonexistent vector returns False")


def test_delete_vector(vector_db):
    """Test deleting a vector."""
    entity_id = "vec_delete"

    # Insert vector
    vector = np.random.randn(768).astype(np.float32)
    vector_db.insert(entity_id, "memory", vector)

    # Verify it exists
    result = vector_db.get(entity_id)
    assert result[0] is not None

    # Delete vector
    success = vector_db.delete(entity_id)
    assert success is True

    # Verify it's gone
    result = vector_db.get(entity_id)
    assert result == (None, None)

    print(f"✓ Vector deleted: {entity_id}")


def test_delete_nonexistent_vector(vector_db):
    """Test deleting a non-existent vector."""
    success = vector_db.delete("nonexistent")
    assert success is False

    print("✓ Delete nonexistent vector returns False")


def test_search_basic(vector_db):
    """Test basic vector search."""
    # Insert test vectors
    vectors = {
        "vec_1": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        "vec_2": np.array([0.9, 0.1, 0.0], dtype=np.float32),
        "vec_3": np.array([0.0, 1.0, 0.0], dtype=np.float32),
    }

    for vec_id, vec in vectors.items():
        # Pad to full dimension
        padded = np.pad(vec, (0, 768 - len(vec)), 'constant')
        vector_db.insert(vec_id, "memory", padded)

    # Search
    query = np.pad(np.array([0.95, 0.05, 0.0]), (0, 765), 'constant')
    results = vector_db.search(query, top_k=2)

    assert len(results) == 2
    assert results[0][1] > results[1][1]  # Sorted by similarity

    print(f"✓ Search found {len(results)} results")


def test_search_with_type_filter(vector_db):
    """Test searching with entity type filter."""
    # Insert different types
    vector = np.random.randn(768).astype(np.float32)
    vector_db.insert("mem_1", "memory", vector)
    vector_db.insert("actor_1", "actor", vector)
    vector_db.insert("obj_1", "object", vector)

    # Search for memories only
    results = vector_db.search(vector, top_k=10, entity_type="memory")

    assert len(results) == 1
    assert results[0][0] == "mem_1"

    print("✓ Type filter works correctly")


def test_search_with_metadata_filter(vector_db):
    """Test searching with metadata filters."""
    # Insert vectors with different metadata
    vector1 = np.random.randn(768).astype(np.float32)
    vector2 = np.random.randn(768).astype(np.float32)
    vector3 = np.random.randn(768).astype(np.float32)

    vector_db.insert("mem_1", "memory", vector1, {"actor": "alice", "location": "tavern"})
    vector_db.insert("mem_2", "memory", vector2, {"actor": "bob", "location": "tavern"})
    vector_db.insert("mem_3", "memory", vector3, {"actor": "alice", "location": "market"})

    # Search with filter
    query = np.random.randn(768).astype(np.float32)
    results = vector_db.search(query, top_k=10, filters={"actor": "alice"})

    # Should only get alice's memories
    assert all(r[2].get("actor") == "alice" for r in results)

    print(f"✓ Metadata filter found {len(results)} results")


def test_search_radius(vector_db):
    """Test searching within a radius."""
    # Insert test vectors
    vectors = {
        "vec_1": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        "vec_2": np.array([0.8, 0.2, 0.0], dtype=np.float32),
        "vec_3": np.array([0.0, 1.0, 0.0], dtype=np.float32),
    }

    for vec_id, vec in vectors.items():
        padded = np.pad(vec, (0, 768 - len(vec)), 'constant')
        vector_db.insert(vec_id, "memory", padded)

    # Search within radius
    query = np.pad(np.array([0.9, 0.1, 0.0]), (0, 765), 'constant')
    results = vector_db.search_radius(query, radius=0.3)

    # vec_1 and vec_2 should be within radius
    result_ids = [r[0] for r in results]
    assert "vec_1" in result_ids
    assert "vec_2" in result_ids

    print(f"✓ Radius search found {len(results)} results")


def test_batch_insert(vector_db):
    """Test batch insert operation."""
    entities = []

    for i in range(100):
        vector = np.random.randn(768).astype(np.float32)
        metadata = {"index": i}
        entities.append((f"vec_{i}", "memory", vector, metadata))

    count = vector_db.batch_insert(entities)

    assert count == 100
    assert vector_db.count() == 100

    print(f"✓ Batch insert: {count} vectors inserted")


def test_batch_delete(vector_db):
    """Test batch delete operation."""
    # Insert vectors
    for i in range(50):
        vector = np.random.randn(768).astype(np.float32)
        vector_db.insert(f"vec_{i}", "memory", vector)

    assert vector_db.count() == 50

    # Delete half
    to_delete = [f"vec_{i}" for i in range(25)]
    count = vector_db.batch_delete(to_delete)

    assert count == 25
    assert vector_db.count() == 25

    print(f"✓ Batch delete: {count} vectors deleted")


def test_count(vector_db):
    """Test counting vectors."""
    # Insert different types
    for i in range(10):
        vector = np.random.randn(768).astype(np.float32)
        vector_db.insert(f"mem_{i}", "memory", vector)
    for i in range(5):
        vector = np.random.randn(768).astype(np.float32)
        vector_db.insert(f"actor_{i}", "actor", vector)

    # Count all
    assert vector_db.count() == 15

    # Count by type
    assert vector_db.count(entity_type="memory") == 10
    assert vector_db.count(entity_type="actor") == 5
    assert vector_db.count(entity_type="object") == 0

    print("✓ Count works correctly")


def test_index_management(vector_db):
    """Test creating and dropping indexes."""
    # Create index
    success = vector_db.create_index("idx_test", {"type": "HNSW"})
    assert success is True
    assert "idx_test" in vector_db.indexes

    # Drop index
    success = vector_db.drop_index("idx_test")
    assert success is True
    assert "idx_test" not in vector_db.indexes

    print("✓ Index management works")


def test_cosine_similarity(vector_db):
    """Test cosine similarity computation."""
    vector1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vector2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    vector3 = np.array([1.0, 0.0, 0.0], dtype=np.float32)

    # Pad to full dimension
    pad = 768 - 3
    vector1 = np.pad(vector1, (0, pad), 'constant')
    vector2 = np.pad(vector2, (0, pad), 'constant')
    vector3 = np.pad(vector3, (0, pad), 'constant')

    vector_db.insert("v1", "test", vector1)
    vector_db.insert("v2", "test", vector2)
    vector_db.insert("v3", "test", vector3)

    # Search with vector1
    results = vector_db.search(vector1, top_k=3, metric="cosine")

    # v1 should be most similar to itself (v3)
    assert results[0][0] in ["v1", "v3"]
    assert results[0][1] > 0.99  # Should be nearly 1.0

    print("✓ Cosine similarity computed correctly")


def test_euclidean_distance(vector_db):
    """Test euclidean distance metric."""
    vector1 = np.array([0.0, 0.0], dtype=np.float32)
    vector2 = np.array([1.0, 0.0], dtype=np.float32)
    vector3 = np.array([2.0, 0.0], dtype=np.float32)

    # Pad to 2D for this test
    pad = 768 - 2
    vector1 = np.pad(vector1, (0, pad), 'constant')
    vector2 = np.pad(vector2, (0, pad), 'constant')
    vector3 = np.pad(vector3, (0, pad), 'constant')

    vector_db.insert("v1", "test", vector1)
    vector_db.insert("v2", "test", vector2)
    vector_db.insert("v3", "test", vector3)

    # Search with vector1
    results = vector_db.search(vector1, top_k=3, metric="euclidean")

    # v1 should be closest to itself
    assert results[0][0] == "v1"

    print("✓ Euclidean distance computed correctly")


def test_dot_product(vector_db):
    """Test dot product metric."""
    vector1 = np.array([1.0, 0.0], dtype=np.float32)
    vector2 = np.array([0.5, 0.0], dtype=np.float32)
    vector3 = np.array([-1.0, 0.0], dtype=np.float32)

    pad = 768 - 2
    vector1 = np.pad(vector1, (0, pad), 'constant')
    vector2 = np.pad(vector2, (0, pad), 'constant')
    vector3 = np.pad(vector3, (0, pad), 'constant')

    vector_db.insert("v1", "test", vector1)
    vector_db.insert("v2", "test", vector2)
    vector_db.insert("v3", "test", vector3)

    # Search with vector1
    results = vector_db.search(vector1, top_k=3, metric="dot")

    # v2 should have highest dot product with v1
    assert results[0][0] == "v2"

    print("✓ Dot product computed correctly")


@pytest.mark.benchmark
def test_insert_performance(vector_db):
    """Benchmark insert performance."""
    num_vectors = 1000
    start_time = time.time()

    for i in range(num_vectors):
        vector = np.random.randn(768).astype(np.float32)
        vector_db.insert(f"vec_{i}", "memory", vector)

    elapsed = time.time() - start_time
    rate = num_vectors / elapsed

    assert rate > 1000, f"Insert performance too slow: {rate:.0f} vectors/s"

    print(f"✓ Insert performance: {rate:.0f} vectors/s")


@pytest.mark.benchmark
def test_search_performance(vector_db):
    """Benchmark search performance."""
    # Insert many vectors
    num_vectors = 10000
    for i in range(num_vectors):
        vector = np.random.randn(768).astype(np.float32)
        vector_db.insert(f"vec_{i}", "memory", vector)

    # Benchmark search
    query = np.random.randn(768).astype(np.float32)

    start_time = time.time()
    results = vector_db.search(query, top_k=10)
    elapsed = time.time() - start_time

    assert len(results) == 10
    assert elapsed < 0.1, f"Search too slow: {elapsed:.4f}s"

    print(f"✓ Search performance: {elapsed:.4f}s for top-10 in {num_vectors} vectors")


@pytest.mark.benchmark
def test_batch_insert_performance(vector_db):
    """Benchmark batch insert performance."""
    num_vectors = 10000
    entities = []

    for i in range(num_vectors):
        vector = np.random.randn(768).astype(np.float32)
        entities.append((f"vec_{i}", "memory", vector))

    start_time = time.time()
    count = vector_db.batch_insert(entities)
    elapsed = time.time() - start_time

    rate = num_vectors / elapsed

    assert count == num_vectors
    assert rate > 5000, f"Batch insert too slow: {rate:.0f} vectors/s"

    print(f"✓ Batch insert performance: {rate:.0f} vectors/s")


def test_metadata_complex_values(vector_db):
    """Test that complex metadata values are stored correctly."""
    complex_metadata = {
        "string": "test",
        "number": 42,
        "float": 3.14,
        "bool": True,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
        "null": None,
    }

    vector = np.random.randn(768).astype(np.float32)
    vector_db.insert("mem_complex", "memory", vector, complex_metadata)

    # Retrieve
    stored_vector, stored_metadata = vector_db.get("mem_complex")

    assert stored_metadata == complex_metadata

    print("✓ Complex metadata stored correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
