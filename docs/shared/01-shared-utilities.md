# Shared Utilities and Types

**Path:** `tsukuyomi/shared/`

**Last Updated:** 2026-02-26

---

## Overview

The Shared module provides common utilities, type definitions, and exception classes used across all Tsukuyomi systems.

## Philosophy

Per the MVP v0.1 shared architecture:
- **DRY**: Single source of truth for common types
- **Type Safety**: Strong typing throughout
- **Validation**: Input sanitization and validation
- **Error Handling**: Structured exception hierarchy

---

## Component Structure

```
shared/
├── utils.py        # Common utility functions
├── types.py        # Shared type definitions
└── exceptions.py   # Exception hierarchy
```

---

## 1. Utility Functions (`utils.py`)

**Location:** `tsukuyomi/shared/utils.py`

Common utility functions used across multiple systems.

### ID Generation

```python
def generate_id() -> str:
    """
    Generate a unique identifier using UUID4.

    Returns:
        A unique UUID string.
    """
    return str(uuid.uuid4())
```

**Usage:**
```python
from tsukuyomi.shared.utils import generate_id

agent_id = generate_id()  # "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### Timestamp Conversion

```python
def to_pb_timestamp(t: float) -> Any:
    """
    Convert a float timestamp to protobuf Timestamp.

    Args:
        t: Unix timestamp as float.

    Returns:
        Protobuf Timestamp object.
    """

def from_pb_timestamp(pb_timestamp: Any) -> float:
    """
    Convert protobuf Timestamp to float timestamp.

    Args:
        pb_timestamp: Protobuf Timestamp object.

    Returns:
        Unix timestamp as float.
    """
```

**Usage:**
```python
from tsukuyomi.shared.utils import to_pb_timestamp, from_pb_timestamp

import time
now = time.time()
pb_ts = to_pb_timestamp(now)
back_to_float = from_pb_timestamp(pb_ts)
```

### Input Sanitization

```python
def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input to prevent injection attacks.

    Args:
        text: Input text to sanitize.
        max_length: Maximum allowed length.

    Returns:
        Sanitized text.
    """
```

**Features:**
- Type checking (must be string)
- Length truncation
- Null byte removal
- Whitespace trimming

### Validation

```python
def validate_agent_id(agent_id: str) -> bool:
    """
    Validate agent ID format.

    Args:
        agent_id: Agent ID to validate.

    Returns:
        True if valid, False otherwise.
    """
```

### Utility Functions

```python
def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""

def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary."""
```

---

## 2. Type Definitions (`types.py`)

**Location:** `tsukuyomi/shared/types.py`

Common data structures and types used across systems.

### Enumerations

```python
class AgentStatus(Enum):
    """Agent lifecycle status."""
    INITIALIZING = "initializing"
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class EmotionDimension(Enum):
    """PAD emotion model dimensions."""
    PLEASURE = "pleasure"
    AROUSAL = "arousal"
    DOMINANCE = "dominance"

class MemoryType(Enum):
    """Types of memories."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    WORKING = "working"
    PROCEDURAL = "procedural"
```

### Spatial Types

```python
@dataclass
class Vector3:
    """3D vector for spatial coordinates."""
    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: "Vector3") -> float:
        """Calculate Euclidean distance to another vector."""

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert to tuple."""
```

**Usage:**
```python
from tsukuyomi.shared.types import Vector3

pos1 = Vector3(0, 0, 0)
pos2 = Vector3(3, 4, 0)
distance = pos1.distance_to(pos2)  # 5.0
```

### Emotional Types

```python
@dataclass
class EmotionState:
    """PAD emotional state."""
    pleasure: float = 0.0   # -1.0 to 1.0
    arousal: float = 0.0    # -1.0 to 1.0
    dominance: float = 0.0  # -1.0 to 1.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "EmotionState":
        """Create from dictionary."""
```

**Usage:**
```python
from tsukuyomi.shared.types import EmotionState

emotion = EmotionState(pleasure=0.5, arousal=0.8, dominance=-0.2)
emotion_dict = emotion.to_dict()
```

### Memory Types

```python
@dataclass
class Memory:
    """Base memory structure."""
    memory_id: str
    agent_id: str
    content: str
    memory_type: MemoryType
    timestamp: float
    importance: float = 0.5           # 0.0 to 1.0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

### Belief Types

```python
@dataclass
class Belief:
    """Agent belief structure."""
    belief_id: str
    agent_id: str
    proposition: str
    confidence: float                   # 0.0 to 1.0
    evidence: List[str] = []
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

### Action Types

```python
@dataclass
class ActionResult:
    """Result of an agent action."""
    success: bool
    action_id: str
    agent_id: str
    outcome: str
    changes: Dict[str, Any] = {}
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

### Social Types

```python
@dataclass
class Relationship:
    """Social relationship between agents."""
    agent_id: str
    target_id: str
    affinity: float           # -1.0 to 1.0
    familiarity: float        # 0.0 to 1.0
    trust: float              # 0.0 to 1.0
    last_interaction: float = 0.0
    shared_experiences: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

### Perception Types

```python
@dataclass
class Perception:
    """A single percept from the environment."""
    percept_id: str
    agent_id: str
    source: str              # What was perceived
    type: str                # visual, auditory, etc.
    content: str
    confidence: float
    timestamp: float
    location: Optional[Vector3] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

### Proposal Types

```python
@dataclass
class Proposal:
    """Action proposal from an agent."""
    proposal_id: str
    agent_id: str
    action_type: str
    parameters: Dict[str, Any]
    timestamp: float
    priority: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
```

---

## 3. Exception Hierarchy (`exceptions.py`)

**Location:** `tsukuyomi/shared/exceptions.py`

Structured exception hierarchy for error handling.

### Exception Tree

```
TsukuyomiError (base)
├── AgentError           # Agent system errors
├── EnvironmentError     # Environment system errors
├── NarrativeError       # Narrative system errors
├── ServiceError         # External service errors (LLM, DB)
├── ValidationError      # Input validation errors
├── ConfigurationError   # Configuration errors
└── TimeoutError         # Operation timeout
```

### Base Exception

```python
class TsukuyomiError(Exception):
    """Base exception for all Tsukuyomi errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message
```

### Specialized Exceptions

```python
class AgentError(TsukuyomiError):
    """Exception raised for agent system errors."""
    pass

class EnvironmentError(TsukuyomiError):
    """Exception raised for environment system errors."""
    pass

class NarrativeError(TsukuyomiError):
    """Exception raised for narrative system errors."""
    pass

class ServiceError(TsukuyomiError):
    """Exception raised for external service errors (LLM, database, vector store)."""
    pass

class ValidationError(TsukuyomiError):
    """Exception raised for input validation errors."""
    pass

class ConfigurationError(TsukuyomiError):
    """Exception raised for configuration errors."""
    pass

class TimeoutError(TsukuyomiError):
    """Exception raised when an operation times out."""
    pass
```

### Usage Examples

```python
from tsukuyomi.shared.exceptions import AgentError, ValidationError

# Basic exception
raise AgentError("Agent not found")

# With details
raise ValidationError(
    "Invalid agent ID",
    details={"agent_id": agent_id, "reason": "Too long"}
)

# Catching specific exceptions
try:
    validate_agent_id(agent_id)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    logger.debug(f"Details: {e.details}")
```

---

## Design Principles

1. **DRY**: Single source of truth for common types
2. **Type Safety**: Strong typing with dataclasses
3. **Serialization**: All types support to_dict()
4. **Validation**: Input sanitization functions
5. **Error Handling**: Structured exception hierarchy
6. **Immutability**: Dataclasses are frozen where appropriate

---

## Best Practices

### Type Usage

```python
# DO: Import from shared.types
from tsukuyomi.shared.types import EmotionState, Memory, AgentStatus

# DON'T: Define duplicate types
class EmotionState:  # ❌ Duplicates shared.types
    pass
```

### Exception Handling

```python
# DO: Use specific exceptions
from tsukuyomi.shared.exceptions import ValidationError, AgentError

try:
    validate_agent_id(agent_id)
except ValidationError as e:
    logger.error(f"Validation error: {e}")

# DON'T: Use generic Exception
try:
    validate_agent_id(agent_id)
except Exception as e:  # ❌ Too broad
    pass
```

### ID Generation

```python
# DO: Use shared utility
from tsukuyomi.shared.utils import generate_id

agent_id = generate_id()

# DON'T: Use random module directly
import random
agent_id = str(random.randint(0, 1000000))  # ❌ Not unique
```

---

## Dependencies

**External:**
- `dataclasses` - Data structures
- `enum` - Enumerations
- `typing` - Type hints
- `datetime` - Timestamps
- `uuid` - ID generation
