# Tsukuyomi V2 Phase 3 - RAG API Reference

## Overview

The RAG (Retrieval-Augmented Generation) system provides long-term memory capabilities for Tsukuyomi agents. This document describes the Python API for interacting with the RAG system, including embedding generation, vector storage, and semantic search.

## Table of Contents

1. [Installation](#installation)
2. [Core Components](#core-components)
3. [API Reference](#api-reference)
4. [Usage Examples](#usage-examples)
5. [Configuration](#configuration)
6. [Performance Tuning](#performance-tuning)

## Installation

```bash
pip install -r requirements.txt
```

Required dependencies:
- `numpy`: Vector operations
- `psycopg2`: PostgreSQL connectivity
- `pgvector`: Vector similarity search
- `sentence-transformers` (optional): For HuggingFace embeddings

## Core Components

### `EmbeddingModel`

Base class for text embedding generation.

```python
from tsukuyomi.rag import EmbeddingModel
```

#### Methods

##### `encode(text: str) -> np.ndarray`

Generate an embedding for a single text.

**Parameters:**
- `text` (str): Input text to encode

**Returns:**
- `np.ndarray`: Embedding vector

**Example:**
```python
model = EmbeddingModel(dimension=768)
embedding = model.encode("Alice went to the tavern")
# Returns: np.array([0.123, -0.456, ...]) of shape (768,)
```

##### `encode_batch(texts: List[str]) -> List[np.ndarray]`

Generate embeddings for multiple texts.

**Parameters:**
- `texts` (List[str]): List of input texts

**Returns:**
- `List[np.ndarray]`: List of embedding vectors

**Example:**
```python
texts = [
    "The sun rises in the east",
    "The cat sat on the mat",
    "Hello, world!"
]
embeddings = model.encode_batch(texts)
# Returns: [np.array([...]), np.array([...]), np.array([...])]
```

### `VectorDatabase`

Interface for storing and searching vectors.

```python
from tsukuyomi.rag import VectorDatabase
```

#### Constructor

```python
def __init__(
    db_url: str,
    dimension: int = 768,
    metric: str = "cosine"
)
```

**Parameters:**
- `db_url` (str): PostgreSQL connection URL
- `dimension` (int): Embedding dimension (default: 768)
- `metric` (str): Distance metric ("cosine", "euclidean", "dot")

**Example:**
```python
db = VectorDatabase(
    db_url="postgresql://user:pass@localhost/tsukuyomi",
    dimension=768,
    metric="cosine"
)
```

#### Methods

##### `insert(entity_id: str, entity_type: str, vector: np.ndarray, metadata: Dict[str, Any]) -> bool`

Insert a vector into the database.

**Parameters:**
- `entity_id` (str): Unique identifier for the entity
- `entity_type` (str): Type of entity ("memory", "actor", "object")
- `vector` (np.ndarray): Embedding vector
- `metadata` (Dict[str, Any]): Optional metadata

**Returns:**
- `bool`: True if successful

**Example:**
```python
import numpy as np

vector = np.random.randn(768).astype(np.float32)
success = db.insert(
    entity_id="mem_1",
    entity_type="memory",
    vector=vector,
    metadata={"actor": "alice", "tick": 100}
)
```

##### `get(entity_id: str) -> Optional[Tuple[np.ndarray, Dict[str, Any]]]`

Retrieve a vector by ID.

**Parameters:**
- `entity_id` (str): Entity identifier

**Returns:**
- `Tuple[np.ndarray, Dict]` or `None`: (vector, metadata) tuple if found, None otherwise

**Example:**
```python
vector, metadata = db.get("mem_1")
if vector is not None:
    print(f"Found memory: {metadata}")
```

##### `update(entity_id: str, vector: np.ndarray, metadata: Dict[str, Any] = None) -> bool`

Update an existing vector.

**Parameters:**
- `entity_id` (str): Entity identifier
- `vector` (np.ndarray): New embedding vector
- `metadata` (Dict[str, Any]): Optional new metadata

**Returns:**
- `bool`: True if successful, False if entity not found

**Example:**
```python
new_vector = np.random.randn(768).astype(np.float32)
success = db.update("mem_1", new_vector, {"tick": 101})
```

##### `delete(entity_id: str) -> bool`

Delete a vector from the database.

**Parameters:**
- `entity_id` (str): Entity identifier

**Returns:**
- `bool`: True if successful, False if entity not found

**Example:**
```python
success = db.delete("mem_1")
```

##### `search(query: np.ndarray, top_k: int = 10, metric: str = None, entity_type: str = None, filters: Dict[str, Any] = None) -> List[Tuple[str, float, Dict]]`

Search for similar vectors.

**Parameters:**
- `query` (np.ndarray): Query embedding vector
- `top_k` (int): Number of results to return (default: 10)
- `metric` (str): Distance metric (overrides default)
- `entity_type` (str): Filter by entity type
- `filters` (Dict[str, Any]): Filter by metadata

**Returns:**
- `List[Tuple[str, float, Dict]]`: List of (entity_id, similarity, metadata) tuples

**Example:**
```python
query_vector = model.encode("What did Alice do?")
results = db.search(
    query_vector,
    top_k=5,
    entity_type="memory",
    filters={"actor": "alice"}
)

for entity_id, similarity, metadata in results:
    print(f"{similarity:.3f} - {entity_id}: {metadata}")
```

##### `search_radius(query: np.ndarray, radius: float, metric: str = None, entity_type: str = None) -> List[Tuple[str, float, Dict]]`

Search for vectors within a radius.

**Parameters:**
- `query` (np.ndarray): Query embedding vector
- `radius` (float): Maximum distance (0.0 to 1.0)
- `metric` (str): Distance metric
- `entity_type` (str): Filter by entity type

**Returns:**
- `List[Tuple[str, float, Dict]]`: List of (entity_id, similarity, metadata) tuples

**Example:**
```python
query_vector = model.encode("sword")
results = db.search_radius(query_vector, radius=0.3)
```

##### `batch_insert(entities: List[Tuple[str, str, np.ndarray, Dict]]) -> int`

Insert multiple vectors at once.

**Parameters:**
- `entities` (List[Tuple]): List of (entity_id, entity_type, vector, metadata) tuples

**Returns:**
- `int`: Number of vectors inserted

**Example:**
```python
entities = []
for i in range(100):
    vector = model.encode(f"Memory {i}")
    entities.append((f"mem_{i}", "memory", vector, {"index": i}))

count = db.batch_insert(entities)
print(f"Inserted {count} memories")
```

##### `batch_delete(entity_ids: List[str]) -> int`

Delete multiple vectors at once.

**Parameters:**
- `entity_ids` (List[str]): List of entity identifiers

**Returns:**
- `int`: Number of vectors deleted

**Example:**
```python
count = db.batch_delete(["mem_1", "mem_2", "mem_3"])
```

##### `count(entity_type: str = None) -> int`

Count vectors in the database.

**Parameters:**
- `entity_type` (str): Optional filter by entity type

**Returns:**
- `int`: Number of vectors

**Example:**
```python
total_count = db.count()
memory_count = db.count(entity_type="memory")
```

### `RAGSystem`

Main interface for RAG operations, combining embedding generation and vector storage.

```python
from tsukuyomi.rag import RAGSystem
```

#### Constructor

```python
def __init__(
    embedding_model: EmbeddingModel,
    vector_db: VectorDatabase
)
```

**Parameters:**
- `embedding_model` (EmbeddingModel): Embedding generation model
- `vector_db` (VectorDatabase): Vector database instance

**Example:**
```python
model = EmbeddingModel(dimension=768)
db = VectorDatabase(db_url="postgresql://...", dimension=768)
rag = RAGSystem(model, db)
```

#### Methods

##### `store_memory(memory_id: str, entity_type: str, text: str, metadata: Dict[str, Any] = None) -> bool`

Store a memory as an embedding.

**Parameters:**
- `memory_id` (str): Unique identifier for the memory
- `entity_type` (str): Type of entity ("memory", "fact", "event")
- `text` (str): Text content of the memory
- `metadata` (Dict[str, Any]): Optional metadata

**Returns:**
- `bool`: True if successful

**Example:**
```python
success = rag.store_memory(
    memory_id="mem_1",
    entity_type="memory",
    text="Alice bought a sword at the blacksmith",
    metadata={"actor": "alice", "location": "blacksmith", "tick": 150}
)
```

##### `retrieve_memories(query: str, top_k: int = 5, entity_type: str = None) -> List[Dict[str, Any]]`

Retrieve similar memories.

**Parameters:**
- `query` (str): Query text
- `top_k` (int): Number of results to return (default: 5)
- `entity_type` (str): Optional filter by entity type

**Returns:**
- `List[Dict]`: List of memory results with keys:
  - `entity_id` (str): Memory identifier
  - `similarity` (float): Similarity score (0.0 to 1.0)
  - `metadata` (Dict): Memory metadata

**Example:**
```python
memories = rag.retrieve_memories(
    query="What did Alice buy?",
    top_k=3,
    entity_type="memory"
)

for memory in memories:
    print(f"{memory['similarity']:.3f} - {memory['metadata']}")
```

##### `update_memory(memory_id: str, text: str, metadata: Dict[str, Any] = None)`

Update an existing memory.

**Parameters:**
- `memory_id` (str): Memory identifier
- `text` (str): New text content
- `metadata` (Dict[str, Any]): Optional new metadata

**Example:**
```python
rag.update_memory(
    memory_id="mem_1",
    text="Alice bought a powerful sword at the blacksmith",
    metadata={"actor": "alice", "location": "blacksmith", "tick": 151}
)
```

##### `delete_memory(memory_id: str) -> bool`

Delete a memory.

**Parameters:**
- `memory_id` (str): Memory identifier

**Returns:**
- `bool`: True if successful

**Example:**
```python
success = rag.delete_memory("mem_1")
```

## Usage Examples

### Basic Usage

```python
from tsukuyomi.rag import RAGSystem, EmbeddingModel, VectorDatabase

# Initialize components
model = EmbeddingModel(dimension=768)
db = VectorDatabase(
    db_url="postgresql://user:pass@localhost/tsukuyomi",
    dimension=768,
    metric="cosine"
)
rag = RAGSystem(model, db)

# Store memories
rag.store_memory("mem_1", "memory", "Alice fought a dragon", {"actor": "alice", "tick": 100})
rag.store_memory("mem_2", "memory", "Bob found treasure", {"actor": "bob", "tick": 150})

# Retrieve memories
memories = rag.retrieve_memories("What did Alice do?", top_k=3)

for memory in memories:
    print(f"{memory['similarity']:.3f} - {memory['metadata']}")
```

### Integration with AgentBrain

```python
from tsukuyomi.brain.AgentBrain import AgentBrain
from tsukuyomi.rag import RAGSystem, EmbeddingModel, VectorDatabase

class EnhancedAgentBrain(AgentBrain):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize RAG system
        model = EmbeddingModel(dimension=768)
        db = VectorDatabase(
            db_url="postgresql://...",
            dimension=768
        )
        self.rag = RAGSystem(model, db)

    async def store_experience(self, experience: str, metadata: dict):
        """Store an experience in long-term memory."""
        memory_id = f"{self.actor_id}_{self.tick_count}"
        self.rag.store_memory(
            memory_id=memory_id,
            entity_type="experience",
            text=experience,
            metadata=metadata
        )

    async def recall_memories(self, query: str, top_k: int = 5):
        """Recall relevant memories."""
        return self.rag.retrieve_memories(query, top_k=top_k)
```

### Batch Operations

```python
# Store many memories at once
memories = []
for i in range(1000):
    text = f"Event {i}: Something interesting happened"
    metadata = {"tick": i * 10, "actor": f"actor_{i % 10}"}
    memories.append((f"mem_{i}", "memory", text, metadata))

entities = []
for mem_id, entity_type, text, metadata in memories:
    embedding = model.encode(text)
    entities.append((mem_id, entity_type, embedding, metadata))

count = db.batch_insert(entities)
print(f"Inserted {count} memories")
```

### Advanced Filtering

```python
# Search with metadata filters
results = db.search(
    query_vector=model.encode("Alice's actions"),
    top_k=10,
    entity_type="memory",
    filters={
        "actor": "alice",
        "tick": {"$gte": 100, "$lte": 200}  # Range query
    }
)

# Search within radius
nearby = db.search_radius(
    query_vector=model.encode("sword"),
    radius=0.3,
    entity_type="object"
)
```

## Configuration

### Environment Variables

```bash
# PostgreSQL connection
TSUKUYOMI_DB_URL=postgresql://user:pass@localhost:5432/tsukuyomi

# Embedding model
TSUKUYOMI_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
TSUKUYOMI_EMBEDDING_DIMENSION=384

# RAG configuration
TSUKUYOMI_RAG_TOP_K=5
TSUKUYOMI_RAG_THRESHOLD=0.7
TSUKUYOMI_RAG_CACHE_SIZE=1000
```

### Configuration File

```python
# rag_config.py
RAG_CONFIG = {
    "embedding": {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": 384,
        "batch_size": 32
    },
    "vector_db": {
        "url": "postgresql://user:pass@localhost/tsukuyomi",
        "metric": "cosine",
        "index_type": "ivfflat"
    },
    "retrieval": {
        "top_k": 5,
        "threshold": 0.7,
        "cache_size": 1000
    }
}
```

## Performance Tuning

### Batch Size

For optimal performance when encoding multiple texts:

```python
# Good: Batch encoding
texts = ["text1", "text2", ..., "text100"]
embeddings = model.encode_batch(texts)

# Bad: Individual encoding
embeddings = [model.encode(text) for text in texts]
```

### Connection Pooling

Use connection pooling for database operations:

```python
from psycopg2 import pool

connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=5,
    maxconn=20,
    dsn="postgresql://user:pass@localhost/tsukuyomi"
)

db = VectorDatabase(
    db_url="postgresql://...",
    connection_pool=connection_pool
)
```

### Index Tuning

For large datasets (>100k vectors), use IVFFlat index:

```sql
CREATE INDEX idx_vector_embedding_ivfflat ON vector_embeddings
    USING ivfflat(embedding vector_cosine_ops)
    WITH (lists = 100);
```

For faster queries, use HNSW index:

```sql
CREATE INDEX idx_vector_embedding_hnsw ON vector_embeddings
    USING hnsw(embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

### Caching

Cache frequently accessed embeddings:

```python
from functools import lru_cache

class CachedEmbeddingModel(EmbeddingModel):
    @lru_cache(maxsize=1000)
    def encode(self, text: str) -> np.ndarray:
        return super().encode(text)
```

## Error Handling

```python
from tsukuyomi.rag import RAGSystemError, VectorDatabaseError

try:
    rag.store_memory("mem_1", "memory", "Test text", {})
except RAGSystemError as e:
    print(f"RAG system error: {e}")
except VectorDatabaseError as e:
    print(f"Database error: {e}")
```

## Best Practices

1. **Always use batch operations** for multiple inserts
2. **Set appropriate top_k** values (5-10 is usually sufficient)
3. **Use metadata filtering** to narrow down search space
4. **Monitor database size** and archive old memories periodically
5. **Use connection pooling** in production
6. **Cache embeddings** for frequently accessed texts
7. **Set similarity thresholds** to filter low-quality results

## Conclusion

The RAG API provides a comprehensive interface for managing long-term memory in Tsukuyomi V2. By combining vector similarity search with metadata filtering, agents can efficiently recall relevant experiences and make better decisions.

---

**Version:** 3.0
**Last Updated:** 2026-02-15
**Phase:** Tsukuyomi V2 Phase 3 (Persistence & Scale)
