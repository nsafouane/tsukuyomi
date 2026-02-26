# Services Layer

**Path:** `tsukuyomi/services/`

**Last Updated:** 2026-02-26

---

## Overview

The Services Layer provides infrastructure services for the Tsukuyomi engine, including database persistence, LLM integration, embedding generation, and vector storage for semantic search.

## Philosophy

Per the MVP v0.1 services architecture:
- **Modular**: Each service is independent and can be swapped
- **Provider-Agnostic**: LLM service supports multiple providers
- **Persistent**: Database for tick history and replay
- **Semantic**: Vector store for memory retrieval

---

## Component Structure

```
services/
├── database/
│   └── manager.py       # SQLite persistence for tick history
├── llm/
│   ├── service.py       # Main LLM service class
│   ├── provider.py      # LLM provider interface
│   ├── openai_provider.py  # OpenAI-compatible providers
│   └── prompts.py       # Prompt templates
├── embedding/
│   └── service.py       # Embedding generation service
└── vector/
    └── store.py         # Vector database abstraction (Qdrant)
```

---

## 1. Database Manager (`database/manager.py`)

**Location:** `tsukuyomi/services/database/manager.py`

SQLite-based persistence for simulation tick history.

### DBManager Class

```python
class DBManager:
    """
    Manages SQLite storage for Tsukuyomi simulation data.

    Stores TickHistory including:
    - World snapshots
    - Proposals
    - Resolutions

    Schema:
        ticks: tick_number, timestamp, tick_state_json
        metadata: key, value
    """

    def __init__(self, db_path: str = "tsukuyomi_history.db")

    def save_tick(self, tick_state: core_pb2.TickState):
        """
        Save a single tick state to the database.

        Converts Protobuf to JSON for storage.
        """

    def get_tick(self, tick_number: int) -> Optional[core_pb2.TickState]:
        """Retrieve a specific tick state from the database."""

    def get_latest_tick_number(self) -> int:
        """Get the highest tick number recorded (-1 if empty)."""

    def list_ticks(self, limit: int = 100, offset: int = 0) -> List[int]:
        """List available tick numbers (most recent first)."""
```

### Usage Example

```python
# Initialize
db = DBManager("my_simulation.db")

# Save tick
db.save_tick(tick_state)

# Resume simulation
latest = db.get_latest_tick_number()
if latest >= 0:
    last_state = db.get_tick(latest)
    # Resume from last_state
```

---

## 2. LLM Service (`llm/`)

**Location:** `tsukuyomi/services/llm/`

### LLMProvider Interface (`provider.py`)

```python
class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is accessible."""

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Generate a response from the LLM."""

    @abstractmethod
    async def stream_response(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float
    ) -> AsyncIterator[str]:
        """Stream a response token by token."""
```

### LLMResponse

```python
@dataclass
class LLMResponse:
    """Response from LLM service."""
    thought: str          # Internal reasoning
    action: str           # Action to perform
    params: Dict[str, str] # Action parameters
    provider: str         # Provider name
```

### LLMService (`service.py`)

```python
class LLMService:
    """
    Main service class for LLM integration.

    Serves as the bridge between AgentBrain and external LLM providers.
    Manages provider instances, prompt templates, and response generation.

    Supported Providers:
    - OpenAI (api.openai.com)
    - Groq (groq.com)
    - Any OpenAI-compatible endpoint

    Environment Variables:
        LLM_API_KEY: API key for authentication
        LLM_MODEL: Model identifier (default: gpt-3.5-turbo)
        LLM_BASE_URL: Base URL for API
        LLM_PROVIDER: "openai" or "groq"
    """

    DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    DEFAULT_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    DEFAULT_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))

    # Rate limiting (for Groq 30 RPM)
    _min_request_interval = 2.1  # seconds

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    )

    async def initialize(self) -> bool:
        """Initialize service and verify connectivity."""

    async def generate_agent_response(
        self,
        context: LLMRequestContext,
        scenario_type: ScenarioType = DELIBERATION
    ) -> LLMResponse:
        """
        Generate a complete agent response.

        Returns LLMResponse with thought, action, and params.
        """

    async def stream_agent_response(
        self,
        context: LLMRequestContext,
        scenario_type: ScenarioType = DELIBERATION
    ) -> AsyncIterator[str]:
        """Stream response token by token."""

    def _build_system_prompt(self, scenario_type: ScenarioType) -> str:
        """Build system prompt based on scenario type."""

    def _build_user_prompt(self, context: LLMRequestContext, scenario_type: ScenarioType) -> str:
        """Build user prompt from context and template."""
```

### ScenarioType Enum

```python
class ScenarioType(Enum):
    """Types of simulation scenarios."""
    DELIBERATION = "deliberation"  # Group decision-making
    SOCIAL = "social"            # Social interaction
    COMBAT = "combat"            # Combat/tactical
    STORYTELLING = "storytelling" # Narrative-focused
    REFLECTION = "reflection"     # Internal reflection
```

### OpenAI-Compatible Providers (`openai_provider.py`)

```python
class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI and compatible APIs."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 30
    )

class GroqProvider(OpenAICompatibleProvider):
    """Provider for Groq (fast inference)."""

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        timeout: int = 30
    )
```

---

## 3. Embedding Service (`embedding/service.py`)

**Location:** `tsukuyomi/services/embedding/service.py`

Generates embeddings for semantic search.

### EmbeddingService Class

```python
class EmbeddingService:
    """
    Service for generating text embeddings.

    Supports:
    - OpenAI embeddings (text-embedding-ada-002)
    - Local models (via sentence-transformers)
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "text-embedding-ada-002"
    )

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
```

---

## 4. Vector Store (`vector/store.py`)

**Location:** `tsukuyomi/services/vector/store.py`

Vector database abstraction layer for semantic memory search.

### Core Classes

```python
class DistanceMetric(Enum):
    """Supported distance metrics."""
    COSINE = "cosine"
    DOT = "dot"
    EUCLID = "euclid"

@dataclass
class VectorConfig:
    """Configuration for vector store."""
    collection_name: str
    vector_size: int = 1536  # OpenAI ada-002 dimension
    distance_metric: DistanceMetric = COSINE
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
    timestamp: Optional[datetime]
```

### VectorStore Class

```python
class VectorStore:
    """
    Vector database abstraction layer.

    Provides unified interface for vector storage and retrieval.
    Primary backend: Qdrant

    Requirements:
        pip install qdrant-client
    """

    def __init__(self, config: VectorConfig)

    # Point Management
    def add_point(self, point: MemoryPoint) -> bool:
        """Add a single memory point."""

    def add_points(self, points: List[MemoryPoint], batch_size: int = 100) -> bool:
        """Add multiple memory points in batches."""

    def get_point(self, point_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific point by ID."""

    def delete_point(self, point_id: str) -> bool:
        """Delete a specific point."""

    def delete_by_filter(self, filter_payload: Dict[str, Any]) -> int:
        """Delete points matching filter."""

    # Search
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_payload: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Returns results with:
        - id: Point ID
        - score: Similarity score (0-1)
        - payload: Metadata
        - vector: Embedding
        """

    # Collection Management
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection metadata."""

    def clear_collection(self) -> bool:
        """Clear all points from collection."""

    # Utilities
    def generate_id(self, content: str, namespace: str = "memory") -> str:
        """Generate deterministic ID via SHA256 hash."""
```

### Usage Example

```python
# Initialize
config = VectorConfig(
    collection_name="agent_memories",
    vector_size=1536,
    in_memory=True
)
store = VectorStore(config)

# Add memories
point = MemoryPoint(
    id=store.generate_id("I bought an apple"),
    vector=await embedding_service.embed("I bought an apple"),
    payload={"type": "episodic", "tick": 100}
)
store.add_point(point)

# Search
query_vector = await embedding_service.embed("purchased fruit")
results = store.search(query_vector, limit=5)
```

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_db_manager.py` | DBManager CRUD operations |
| `test_llm_service.py` | LLMService integration |
| `test_providers.py` | Provider implementations |
| `test_vector_store.py` | VectorStore operations |

---

## Dependencies

**Internal:**
- `tsukuyomi.transport.proto.core_pb2` - TickState

**External:**

**Database:**
- `sqlite3` - Built-in

**LLM:**
- `openai` - OpenAI client
- `groq` - Groq client
- `python-dotenv` - Environment variables
- `httpx` - Async HTTP
- `pydantic` - Data validation

**Vector Store:**
- `qdrant-client` - Qdrant client
- `qdrant-client.models` - Qdrant types

**General:**
- `dataclasses` - Data structures
- `enum` - Enumerations
- `asyncio` - Async operations
- `typing` - Type hints
- `hashlib` - Hashing
- `json` - JSON serialization
- `logging` - Logging

---

## Design Principles

1. **Modular**: Each service is independent
2. **Provider-Agnostic**: Support multiple LLM providers
3. **Persistent**: SQLite for tick history
4. **Semantic**: Vector store for memory retrieval
5. **Rate-Limited**: Built-in rate limiting for API limits
6. **Abstracted**: Clean interfaces for easy swapping

---

## Configuration

### Environment Variables

```bash
# LLM Service
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-3.5-turbo
LLM_BASE_URL=https://api.openai.com/v1
LLM_PROVIDER=openai
LLM_TIMEOUT=30

# Vector Store
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=optional_api_key
```

### Provider Configuration

```python
# OpenAI
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4

# Groq
LLM_PROVIDER=groq
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile

# Custom OpenAI-compatible
LLM_PROVIDER=openai
LLM_BASE_URL=https://custom-endpoint.com/v1
LLM_MODEL=custom-model
```
