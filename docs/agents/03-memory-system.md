# Memory System

**Path:** `tsukuyomi/agents/cognitive/memory/`

**Last Updated:** 2026-02-26

---

## Overview

The Memory System implements the Deep Memory Architecture for Tsukuyomi agents, providing tiered episodic and semantic memory with RAG-based retrieval, decay calculation, and consolidation.

## Philosophy

Per the MVP v0.1 unified memory architecture:
- **5W Structure**: WHO, WHAT, WHEN, WHERE, WHY for all episodic memories
- **Decay & Reinforcement**: Memories fade over time but are reinforced by access
- **Emotional Imprinting**: Emotional memories persist longer
- **Bounded Storage**: Automatic consolidation prevents memory overflow

---

## Component Structure

```
memory/
├── base.py              # Abstract base and enums
├── memory_types.py      # Core memory data structures
├── memory_system.py     # LongTermMemory implementation
├── memory_manager.py    # 5W Memory Manager (simulation mode)
├── memory_store.py      # Storage backend
├── decay_calculator.py  # Memory decay over time
├── retrieval.py         # Context-aware retrieval
└── retrieval_types.py   # Retrieval configuration types
```

---

## 1. Base Types (`base.py`)

**Location:** `tsukuyomi/agents/cognitive/memory/base.py`

Defines unified enums and abstract base for memory systems.

```python
class MemoryType(Enum):
    """Types of memories stored in the system."""
    EPISODIC = "episodic"      # Specific events and experiences
    SEMANTIC = "semantic"      # General facts and knowledge
    PROCEDURAL = "procedural"  # Skills and how-to knowledge
    WORKING = "working"        # Active cognitive context
    EMOTIONAL = "emotional"    # Emotional imprints
    SOCIAL = "social"          # Knowledge about people

class ImportanceLevel(Enum):
    """Importance levels for memory consolidation."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TRIVIAL = 1

class BaseMemorySystem(ABC):
    """Unified tiered memory architecture."""

    @abstractmethod
    def add_memory(self, *args, **kwargs) -> str:
        """Add a memory to the system."""
        pass

    @abstractmethod
    def retrieve_memories(self, *args, **kwargs) -> List[Any]:
        """Retrieve relevant memories."""
        pass
```

---

## 2. Memory Types (`memory_types.py`)

**Location:** `tsukuyomi/agents/cognitive/memory/memory_types.py`

Defines the core memory data structures for the Deep Memory Architecture.

### MemoryPriority

```python
class MemoryPriority(Enum):
    """Priority levels for memory storage and retrieval."""
    CRITICAL = "critical"    # Life-changing events, core beliefs
    HIGH = "high"           # Important relationships, key skills
    MEDIUM = "medium"       # Routine events, useful knowledge
    LOW = "low"            # Trivial details, rarely needed info
    ARCHIVED = "archived"   # Consolidated memories
```

### MemoryContext

**The 5W Structure:**

```python
@dataclass
class MemoryContext:
    """Contextual information about when and where a memory was formed."""

    # Temporal context
    tick: int                          # Simulation tick when formed
    timestamp: Optional[float] = None  # Real-world timestamp

    # Spatial context
    location: str = ""                 # Where the memory was formed
    location_type: str = ""            # Type of location

    # Social context
    participants: List[str] = []       # Who was involved
    witnesses: List[str] = []          # Who else was present

    # Situational context
    situation: str = ""                # Brief description
    trigger: str = ""                  # What triggered this memory
```

### MemoryImportance

```python
@dataclass
class MemoryImportance:
    """Importance metrics that determine memory persistence."""

    # Core importance (0.0 to 1.0)
    base_importance: float = 0.5

    # Emotional weight
    emotional_weight: float = 0.0      # 0.0 (neutral) to 1.0 (intense)
    emotional_valence: float = 0.0     # -1.0 (negative) to 1.0 (positive)

    # Social weight
    social_weight: float = 0.0         # 0.0 (strangers) to 1.0 (close bonds)

    # Goal relevance
    goal_relevance: float = 0.0        # 0.0 (irrelevant) to 1.0 (critical)

    # Novelty
    novelty: float = 0.0               # 0.0 (routine) to 1.0 (unprecedented)

    def compute_importance(self) -> float:
        """Compute overall importance score."""
```

### MemoryAccess

```python
@dataclass
class MemoryAccess:
    """Track memory access patterns for decay and reinforcement."""

    access_count: int = 0
    last_accessed_tick: int = 0
    creation_tick: int = 0
    access_history: List[int] = []     # Ticks when accessed
    max_history: int = 50

    def record_access(self, current_tick: int) -> None:
        """Record an access to this memory."""

    def get_access_frequency(
        self,
        window_ticks: int = 100,
        current_tick: int = 0
    ) -> float:
        """Calculate access frequency over a recent window."""
```

### Memory (Core Data Structure)

```python
@dataclass
class Memory:
    """
    A single memory with full context for the Deep Memory Architecture.

    Memory types serve different cognitive functions:

    EPISODIC: "Marcus sold me a rotten apple at the market yesterday"
    SEMANTIC: "Apples are fruit that grow on trees"
    EMOTIONAL: "I feel angry when I think about Marcus"
    SOCIAL: "Marcus is known to be dishonest in trade"
    PROCEDURAL: "To bargain effectively, start with a low offer"
    """

    # Identity
    memory_id: str
    memory_type: MemoryType
    priority: MemoryPriority

    # Content
    content: str                  # Full memory content
    summary: str                  # One-line summary

    # Context (5W)
    context: MemoryContext

    # Importance metrics
    importance: MemoryImportance

    # Access tracking
    access: MemoryAccess

    # Retrieval helpers
    tags: List[str] = []
    keywords: List[str] = []
    embedding: Optional[List[float]] = None

    # Related memories
    related_memory_ids: List[str] = []

    # Source information
    source_type: str = "experience"  # "experience", "observation", "gossip"
    source_agent: Optional[str] = None
    confidence: float = 1.0

    # Consolidation
    is_consolidated: bool = False
    consolidated_from: List[str] = []

    # Key Methods
    def compute_importance(self) -> float:
        """Calculate current importance score."""

    def record_access(self, current_tick: int) -> None:
        """Record that this memory was accessed."""

    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""

    def add_related_memory(self, memory_id: str) -> None:
        """Add a related memory reference."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Deserialize from dictionary."""
```

### Factory Functions

```python
def create_episodic_memory(
    content: str,
    tick: int,
    location: str = "",
    participants: List[str] = None,
    importance: float = 0.5,
    emotional_weight: float = 0.0,
    tags: List[str] = None,
) -> Memory

def create_semantic_memory(
    content: str,
    tick: int,
    confidence: float = 1.0,
    tags: List[str] = None,
) -> Memory

def create_emotional_memory(
    content: str,
    tick: int,
    emotional_weight: float = 0.8,
    emotional_valence: float = 0.0,
    trigger: str = "",
    tags: List[str] = None,
) -> Memory

def create_social_memory(
    content: str,
    tick: int,
    participants: List[str],
    social_weight: float = 0.5,
    tags: List[str] = None,
) -> Memory

def create_procedural_memory(
    content: str,
    tick: int,
    skill_name: str = "",
    tags: List[str] = None,
) -> Memory
```

---

## 3. LongTermMemory (`memory_system.py`)

**Location:** `tsukuyomi/agents/cognitive/memory/memory_system.py`

Persistent memory system with RAG-like retrieval.

### Memory (Simplified)

```python
@dataclass
class Memory:
    """A single memory unit."""
    id: str
    memory_type: MemoryType

    # Content
    content: str
    context: str
    summary: str

    # Emotional tagging
    emotional_tags: List[str]
    emotional_valence: float    # -1.0 to +1.0
    emotional_arousal: float    # 0.0 to 1.0

    # Importance and retrieval
    importance: float            # 0.0-1.0
    keywords: List[str]

    # Temporal
    created_at: int
    last_accessed: int
    access_count: int

    # Association
    associated_ids: List[str]

    # Consolidation
    is_consolidated: bool
    consolidation_level: int

    # Methods
    def access(self, tick: int) -> None
    def get_recency_score(self, current_tick: int, decay_rate: float) -> float
    def get_relevance_score(self, query: str) -> float
    def to_dict() -> Dict
    @classmethod
    def from_dict(cls, data: Dict) -> "Memory"
```

### LongTermMemory

```python
class LongTermMemory:
    """
    Persistent memory system with RAG-like retrieval.

    Features:
    - Store memories with importance weighting
    - Keyword-based retrieval
    - Temporal decay
    - Memory consolidation
    - Association chaining
    """

    def __init__(
        self,
        agent_id: str,
        max_memories: int = 10000,
        consolidation_threshold: int = 100
    )

    async def store(
        self,
        content: str,
        memory_type: MemoryType = EPISODIC,
        context: str = "",
        importance: float = 0.5,
        keywords: List[str] = None,
        emotional_tags: List[str] = None,
        emotional_valence: float = 0.0,
        emotional_arousal: float = 0.5,
        associated_memories: List[str] = None,
        tick: int = 0
    ) -> str:
        """Store a new memory. Returns memory ID."""

    async def retrieve(
        self,
        query: str,
        k: int = 10,
        tick: int = 0,
        memory_types: List[MemoryType] = None,
        min_importance: float = 0.0
    ) -> List[Memory]:
        """
        Retrieve relevant memories using keyword matching and importance.

        Combines:
        - Keyword matching (40%)
        - Content match (30%)
        - Importance (20%)
        - Recency (10%)
        """

    async def retrieve_by_emotion(
        self,
        emotion: str,
        k: int = 5,
        tick: int = 0
    ) -> List[Memory]

    async def get_recent(
        self,
        count: int = 10,
        memory_type: MemoryType = None
    ) -> List[Memory]

    async def get_memories_for_prompt(
        self,
        current_situation: str,
        max_memories: int = 5,
        tick: int = 0
    ) -> str:
        """Get formatted memories for LLM prompts."""

    def get_memory_count(self) -> int
    def get_statistics(self) -> Dict[str, Any]
    def to_dict() -> Dict
    @classmethod
    def from_dict(cls, data: Dict) -> "LongTermMemory"
```

### Helper Function

```python
async def store_event_memory(
    memory_system: LongTermMemory,
    event: str,
    context: str = "",
    importance: float = 0.5,
    emotional_tags: List[str] = None,
    tick: int = 0
) -> str:
    """Helper to store an episodic memory of an event."""
```

---

## 4. MemoryManager (`memory_manager.py`)

**Location:** `tsukuyomi/agents/cognitive/memory/memory_manager.py`

The 5W Memory Manager for simulation mode agents.

```python
class MemoryManager:
    """
    Structures observations into 5W format.
    - WHO (Actors involved)
    - WHAT (Action performed)
    - WHEN (Tick number)
    - WHERE (Location)
    - WHY (Inferred intent)

    Includes Semantic Memory layer (Knowledge Graph).
    """

    def __init__(self, agent_id: str)

    # Episodic Memory
    episodic_memory: List[Dict]
    keyword_index: Dict[str, List[int]]  # O(1) lookup

    # Semantic Memory (Knowledge Graph)
    semantic_memory: Dict[str, Dict[str, List[Dict]]]

    # Long-term storage
    long_term_memory: Dict[str, Any]

    # Semantic Methods
    def add_fact(
        self,
        subject: str,
        predicate: str,
        obj: Any,
        confidence: float = 1.0,
        timestamp: int = 0
    ):
        """Add or update a fact in the Knowledge Graph."""

    def get_relations(self, subject: str) -> Dict[str, List[Any]]:
        """Get all relations for a given subject."""

    def ingest_tick(self, tick_state: core_pb2.TickState):
        """Transform TickState into 5W episodic memories and semantic facts."""

    # Episodic Methods
    def query_recent(self, limit: int = 10) -> List[Dict]:
        """Retrieve recent episodic memories."""

    def query_by_relevance(
        self,
        topics: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve memories by topic relevance + emotional intensity.
        Uses keyword_index for O(1) lookup.
        """

    def tick_decay(self, current_tick: int):
        """Run memory decay. Call periodically."""

    def get_semantic_summary(self) -> List[str]:
        """Get key semantic facts for LLM context."""
```

---

## 5. Conversation Memory (`memory.py`)

**Location:** `tsukuyomi/agents/cognitive/memory/memory.py`

Provides `ConversationMemory` and `Utterance` classes for tracking raw dialogue history and turn-taking. This is **distinct** from the Deep Memory Architecture (5W system) - it's a specialized parallel memory system for conversational context.

### Utterance

```python
@dataclass
class Utterance:
    """A single utterance in conversation."""
    tick: int = 0
    content: str = ""
    topic: str = ""
    position: str = ""              # Stance/position on the topic
    speaker_id: str = ""

    def __post_init__(self):
        if not self.speaker_id:
            self.speaker_id = str(uuid.uuid4())[:8]

    def key_topics(self) -> List[str]:
        """
        Extract key topics from the utterance content.

        Keywords detected:
        - Verdict: guilty, innocent, vote, verdict, decision
        - Evidence: evidence, testimony, witness, proof, fact
        - Procedure: rule, law, procedure, process, requirement
        """

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict) -> "Utterance":
        """Deserialize from dictionary."""
```

### ConversationMemory

```python
@dataclass
class ConversationMemory:
    """
    Manages conversation history and narrative tracking.

    Parallel to long-term episodic memory - specifically tracks:
    - Raw dialogue history
    - Turn-taking sequence
    - Discussed topics
    - Speaker positions

    Distinct from Deep Memory (5W) which captures:
    - Structured episodic events with full context
    - Semantic knowledge and facts
    - Emotional imprints
    """

    max_utterances: int = 100
    utterances: List[Utterance] = []
    discussed_topics: List[str] = []

    def add(self, utterance: Utterance) -> None:
        """Add an utterance to memory and extract topics."""

    def get_recent(self, n: int = 5) -> List[Utterance]:
        """Get the n most recent utterances."""

    def get_by_topic(self, topic: str) -> List[Utterance]:
        """Get all utterances related to a topic."""

    def get_by_speaker(self, speaker_id: str) -> List[Utterance]:
        """Get all utterances by a speaker."""

    def get_speaker_positions(self) -> Dict[str, str]:
        """Get the latest position of each speaker."""

    def summarize(self) -> str:
        """
        Generate a summary of the conversation.

        Returns:
            Formatted summary with utterance count, topics discussed,
            and current speaker positions.
        """

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationMemory":
        """Deserialize from dictionary."""
```

### Usage Example

```python
from tsukuyomi.agents.cognitive.memory.memory import ConversationMemory, Utterance

# Initialize
conv_memory = ConversationMemory(max_utterances=100)

# Add utterances
conv_memory.add(Utterance(
    tick=100,
    content="I believe the defendant is guilty based on the evidence.",
    topic="guilty",
    position="for-guilt",
    speaker_id="juror_3"
))

conv_memory.add(Utterance(
    tick=105,
    content="The evidence is circumstantial at best.",
    topic="evidence",
    position="against-guilt",
    speaker_id="juror_8"
))

# Query
recent = conv_memory.get_recent(3)
guilty_talk = conv_memory.get_by_topic("guilty")
juror_3_pos = conv_memory.get_speaker_positions().get("juror_3")

# Summary
print(conv_memory.summarize())
# Output:
# Conversation has 2 utterances.
# Topics discussed: guilty, evidence, position
# Current positions:
#   juror_3: for-guilt
#   juror_8: against-guilt
```

### Key Differences: ConversationMemory vs Deep Memory

| Aspect | ConversationMemory | Deep Memory (5W) |
|--------|---------------------|------------------|
| **Purpose** | Track dialogue flow | Store structured experiences |
| **Structure** | Sequential utterances | 5W (Who, What, When, Where, Why) |
| **Retrieval** | By speaker, topic, recency | By relevance, importance, decay |
| **Persistence** | Short-term (max 100 utterances) | Long-term with consolidation |
| **Content** | Raw speech content | Processed episodic/semantic facts |

---

## 6. Decay Calculator (`decay_calculator.py`)

**Location:** `tsukuyomi/agents/cognitive/memory/decay_calculator.py`

Implements memory decay ensuring important memories persist.

### DecayStrategy

```python
class DecayStrategy(Enum):
    EXPONENTIAL = "exponential"  # Standard (default)
    LINEAR = "linear"             # Simple linear
    LOGARITHMIC = "logarithmic"   # Slow initial, fast later
    STEP = "step"                 # Discrete steps
```

### DecayConfig

```python
@dataclass
class DecayConfig:
    base_decay_rate: float = 0.001
    emotional_resistance: float = 0.5
    access_reinforcement: float = 0.1
    min_importance_threshold: float = 0.05
    max_access_boost: float = 2.0
    strategy: DecayStrategy = EXPONENTIAL

    # Type-specific multipliers
    type_decay_multipliers: dict = {
        EPISODIC: 1.0,     # Standard
        SEMANTIC: 0.5,     # Slower
        EMOTIONAL: 0.3,    # Slowest
        SOCIAL: 0.7,       # Moderate
        PROCEDURAL: 0.4,   # Skills persist
    }

    # Priority modifiers
    priority_decay_modifiers: dict = {
        CRITICAL: 0.1,   # Very slow
        HIGH: 0.3,       # Slow
        MEDIUM: 1.0,     # Standard
        LOW: 2.0,        # Fast
        ARCHIVED: 3.0,   # Fastest
    }
```

### MemoryDecayCalculator

```python
class MemoryDecayCalculator:
    """Calculate effective importance of memories over time."""

    def __init__(self, config: Optional[DecayConfig] = None)

    def effective_importance(
        self,
        memory: Memory,
        current_tick: int
    ) -> float:
        """
        Calculate current effective importance with decay applied.

        Combines:
        1. Base decay factor (exponential by default)
        2. Emotional resistance factor
        3. Access reinforcement factor
        4. Memory type modifier
        5. Priority modifier
        """

    def should_prune(
        self,
        memory: Memory,
        current_tick: int
    ) -> bool:
        """Determine if a memory should be pruned."""

    def get_memories_to_prune(
        self,
        memories: List[Memory],
        current_tick: int
    ) -> List[Memory]

    def get_decay_report(
        self,
        memory: Memory,
        current_tick: int
    ) -> dict:
        """Get detailed breakdown of decay factors."""

    def rank_by_importance(
        self,
        memories: List[Memory],
        current_tick: int,
        limit: Optional[int] = None
    ) -> List[Tuple[Memory, float]]
```

### MemoryImportanceCalculator

```python
class MemoryImportanceCalculator:
    """Calculate initial importance for new memories."""

    def __init__(
        self,
        emotional_weight: float = 0.3,
        social_weight: float = 0.2,
        novelty_weight: float = 0.2,
        goal_weight: float = 0.2,
        base_weight: float = 0.1
    )

    def calculate_importance(
        self,
        emotional_intensity: float = 0.0,
        social_relevance: float = 0.0,
        novelty: float = 0.0,
        goal_relevance: float = 0.0,
        base_importance: float = 0.3
    ) -> float:
        """Calculate initial importance for a new memory."""

    def calculate_from_state(
        self,
        arousal: float,
        participants: List[str],
        relationship_affinities: dict,
        is_novel: bool,
        affects_goals: bool
    ) -> float:
        """Calculate importance from agent state."""
```

---

## 7. Memory Retrieval (`retrieval.py`)

**Location:** `tsukuyomi/agents/cognitive/memory/retrieval.py`

Context-aware memory retrieval system.

### MemoryRetrieval

```python
class MemoryRetrieval:
    """Context-aware memory retrieval system."""

    def __init__(
        self,
        decay_calculator: Optional[MemoryDecayCalculator] = None,
        weights: Optional[RetrievalWeights] = None,
        embedding_func: Optional[Callable] = None
    )

    def retrieve(
        self,
        memories: List[Memory],
        context: RetrievalContext
    ) -> List[Memory]:
        """Retrieve the most relevant memories for the given context."""

    def retrieve_with_scores(
        self,
        memories: List[Memory],
        context: RetrievalContext
    ) -> List[ScoredMemory]:
        """Retrieve memories with detailed score breakdown."""
```

**Scoring Factors:**
- Semantic similarity (keyword or embedding)
- Participant match
- Decay-adjusted importance
- Emotional similarity
- Recency

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_memory_system.py` | LongTermMemory store/retrieve |
| `test_memory_manager.py` | MemoryManager 5W structure |
| `test_memory_decay.py` | Decay calculation |
| `test_memory_retrieval.py` | Context retrieval |
| `test_memory_types.py` | Memory data structures |

---

## Dependencies

**Internal:**
- `tsukuyomi.transport.proto.core_pb2` - TickState for ingestion

**External:**
- `dataclasses` - Data structures
- `enum` - Enumerations
- `uuid` - Unique identifiers
- `math` - Decay calculations
- `time` - Timestamps
- `re` - Keyword extraction
- `typing` - Type hints

---

## Design Principles

1. **5W Structure**: All episodic memories capture Who, What, When, Where, Why
2. **Emotional Imprinting**: Emotional memories persist longer
3. **Access Reinforcement**: Frequently accessed memories are strengthened
4. **Bounded Storage**: Automatic consolidation prevents overflow
5. **Multi-Factor Scoring**: Relevance combines semantic, temporal, emotional factors
6. **Semantic Knowledge Graph**: Facts stored as subject-predicate-object triples
