# Core Agent Components

**Path:** `tsukuyomi/agents/core/`

**Last Updated:** 2026-02-26

---

## Overview

The Core Agent components define the foundational abstractions for all Tsukuyomi agents. This module contains the base classes, identity system, and factory patterns that enable the unified agent architecture supporting both simulation and standalone modes.

## Philosophy

Per the MVP v0.1 philosophy: **"Simulation Mode" and "Standalone Mode" are merely different interfaces for the exact same underlying `BaseAgent` logic.**

All agent implementations inherit from `BaseAgent` and implement the same core lifecycle methods, ensuring behavioral consistency across deployment modes.

---

## Components

### 1. BaseAgent (`base_agent.py`)

**Location:** `tsukuyomi/agents/core/base_agent.py`

The unified abstract base class for all Tsukuyomi agents.

```python
class BaseAgent(ABC):
    """Unified abstract base class for all Tsukuyomi agents."""
```

**Attributes:**
| Attribute | Type | Description |
|-----------|------|-------------|
| `agent_id` | `str` | Unique identifier for the agent |
| `emotion_engine` | `Optional[BaseEmotionalEngine]` | Emotional processing module |
| `memory_system` | `Optional[BaseMemorySystem]` | Memory management module |
| `belief_tracker` | `Optional[BeliefManager]` | Belief system module |

**Abstract Methods:**

```python
@abstractmethod
async def perceive(self, *args, **kwargs) -> Any:
    """Process incoming stimuli or events."""

@abstractmethod
async def deliberate(self, *args, **kwargs) -> Any:
    """Internal reasoning cycle."""

@abstractmethod
async def act(self, *args, **kwargs) -> Any:
    """Produce an output or behavior."""

@abstractmethod
def start(self):
    """Start the agent lifecycle."""

@abstractmethod
def pause(self):
    """Pause agent processing."""

@abstractmethod
def resume(self):
    """Resume agent processing."""

@abstractmethod
def cleanup(self):
    """Clean up resources before shutdown."""
```

**Key Design Points:**
- All methods are async-ready for non-blocking operations
- Lifecycle management (start/pause/resume/cleanup) is mandatory
- Component composition pattern (emotion, memory, beliefs as optional components)

---

### 2. Identity System (`identity.py`)

**Location:** `tsukuyomi/agents/core/identity.py`

Defines the **IMMUTABLE** core identity of Tsukuyomi agents. This is who the agent IS - it never changes throughout the simulation.

#### CoreValue

A belief the agent will NOT compromise on.

```python
@dataclass
class CoreValue:
    value: str                    # The core belief
    source: str                   # Why they believe this
    intensity: float = 0.8        # 0.0-1.0 (how absolute)
    non_negotiable: bool = True   # Can they ever change this?
```

**Example:**
```python
cv = CoreValue(
    value="Justice must be served",
    source="My father was wrongly accused",
    intensity=0.9,
    non_negotiable=True
)
```

**Methods:**
- `to_dict()`: Serialize to dictionary
- Validation: `intensity` must be 0.0-1.0

#### DefiningMemory

A pivotal memory that shaped who the agent is.

```python
@dataclass
class DefiningMemory:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: str = ""
    emotional_impact: str = ""
    lesson_learned: str = ""
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0
    when_occurred: str = ""
```

**Example:**
```python
dm = DefiningMemory(
    event="Father abandoned family",
    emotional_impact="Deep sense of betrayal",
    lesson_learned="Never abandon those who depend on you",
    tags=["family", "betrayal"],
    importance=0.9,
    when_occurred="Age 12"
)
```

**Methods:**
- `to_dict()`: Serialize
- `from_dict()`: Deserialize
- Validation: `importance` must be 0.0-1.0

#### PersonalityTraits

Detailed personality beyond Big Five (OCEAN).

```python
@dataclass
class PersonalityTraits:
    # Big Five (-1.0 to +1.0)
    openness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    agreeableness: float = 0.0
    neuroticism: float = 0.0

    # Specific traits (0.0-1.0)
    stubbornness: float = 0.5
    empathy: float = 0.5
    patience: float = 0.5
    optimism: float = 0.5
    cynicism: float = 0.5

    # Communication style
    speaks_frankly: float = 0.5
    uses_complex_language: float = 0.5
    emotional_expression: float = 0.5
    humor_style: str = "dry"

    # Triggers
    triggers: List[str] = field(default_factory=list)
```

**Methods:**
- `get_big_five_dict()`: Get OCEAN values as dict
- `get_summary()`: Generate brief personality summary
- `to_dict()` / `from_dict()`: Serialization
- Validation: All traits validated on initialization

#### AgentIdentity

The complete immutable core identity.

```python
@dataclass
class AgentIdentity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    age: int = 30
    occupation: str = ""

    # Origin and history
    origin_story: str = ""
    current_location: str = ""
    how_they_got_here: str = ""

    # Core identity
    core_values: List[CoreValue] = field(default_factory=list)
    defining_memories: List[DefiningMemory] = field(default_factory=list)
    personality: Optional[PersonalityTraits] = None

    # Physical/emotional baseline (PAD model)
    baseline_valence: float = 0.0    # -1.0 to +1.0
    baseline_arousal: float = 0.5    # 0.0 to 1.0
    baseline_dominance: float = 0.0  # -1.0 to +1.0
```

**Key Methods:**

| Method | Description |
|--------|-------------|
| `get_baseline_pad()` | Get baseline emotional state |
| `get_core_values_summary()` | Get formatted core values |
| `get_defining_memories_summary()` | Get formatted memories |
| `get_immersive_description()` | Generate rich LLM prompt |
| `to_dict()` / `from_dict()` | Full serialization |

**Example Usage:**
```python
identity = AgentIdentity(
    name="Arthur Miller",
    age=58,
    occupation="Retired Factory Worker",
    origin_story="Grew up in the slums...",
    core_values=[CoreValue(value="Responsibility", source="Father")],
    defining_memories=[DefiningMemory(event="Son walked out", ...)],
    personality=PersonalityTraits(openness=0.3, stubbornness=0.8)
)
```

#### Helper Function

```python
def create_identity(
    name: str,
    age: int,
    occupation: str,
    origin_story: str,
    core_values: List[Dict],
    defining_memories: List[Dict],
    personality: Dict,
    **kwargs
) -> AgentIdentity:
    """Helper to create a fully configured AgentIdentity."""
```

---

### 3. Agent Builder (`agent_builder.py`)

**Location:** `tsukuyomi/agents/core/agent_builder.py`

Factory class for assembling initialized Tsukuyomi agents.

```python
class AgentBuilder:
    """Factory class for assembling initialized Tsukuyomi agents."""

    @staticmethod
    def build_agent_brain(
        actor_id: str,
        profile: Dict[str, Any],
        server_addr: str = "localhost:50051"
    ) -> AgentBrain:
        """Assembles and configures an AgentBrain for simulation mode."""

    @staticmethod
    def build_universal_agent(
        config: AgentConfig
    ) -> UniversalAgent:
        """Assembles and configures a UniversalAgent for standalone mode."""
```

**Usage Examples:**

```python
# Simulation mode
agent_brain = AgentBuilder.build_agent_brain(
    actor_id="agent_001",
    profile={"name": "Juror #1", "personality_baseline": {...}},
    server_addr="localhost:50051"
)

# Standalone mode
config = AgentConfig(scenario_name="jury")
agent = AgentBuilder.build_universal_agent(config)
```

---

## Related Runtime Implementations

The core components are implemented by:

1. **UniversalAgent** (`agents/runtime/standalone_agent.py`)
   - Full-featured standalone agent
   - Implements BaseAgent interface
   - Supports direct LLM interaction

2. **AgentBrain** (`agents/runtime/simulation_agent.py`)
   - Simulation-mode agent with gRPC
   - Connected to FateEngine
   - Alias: `SimulationAgent`

---

## Tests

**Test File:** `tests/test_identity.py`

**Coverage:**

| Test Class | Description |
|------------|-------------|
| `TestCoreValue` | Creation, validation, serialization |
| `TestDefiningMemory` | UUID generation, bounds checking |
| `TestPersonalityTraits` | Big Five validation, summaries |
| `TestAgentIdentity` | Full identity composition, immersive descriptions |
| `TestCreateIdentity` | Helper function |
| `TestRoundTripSerialization` | Full serialization/deserialization |

**Test File:** `tests/test_universal_agent.py`

**Coverage:**

| Test Class | Description |
|------------|-------------|
| `TestAgentState` | State enum values |
| `TestAgentConfig` | Default and custom configuration |
| `TestUniversalAgentInit` | Initialization |
| `TestUniversalAgentIdentity` | Identity loading from file/dict |
| `TestUniversalAgentLLM` | LLM integration |
| `TestUniversalAgentRespond` | Response generation |
| `TestUniversalAgentObserve` | Memory storage |
| `TestUniversalAgentReflect` | Reflection capabilities |
| `TestUniversalAgentSaveLoad` | State persistence |

---

## Dependencies

**Internal:**
- `tsukuyomi.agents.cognitive.memory.base` - Memory types (MemoryType, ImportanceLevel)

**External:**
- `dataclasses` - Data structures
- `enum` - Enumerations
- `uuid` - Unique identifier generation
- `typing` - Type hints

---

## Module Exports

**`agents/core/__init__.py`:**
```python
from .base_agent import BaseAgent

__all__ = ['BaseAgent']
```

**`agents/core/identity.py`:**
```python
__all__ = [
    "CoreValue",
    "DefiningMemory",
    "PersonalityTraits",
    "AgentIdentity",
    "create_identity"
]
```

**`agents/core/agent_builder.py`:**
```python
__all__ = ["AgentBuilder"]
```

---

## Design Principles

1. **Unified Base:** All agents inherit from `BaseAgent`
2. **Immutable Identity:** AgentIdentity never changes after creation
3. **Composition over Inheritance:** Emotion, memory, beliefs as components
4. **Factory Pattern:** AgentBuilder for consistent agent creation
5. **Validation First:** Type checking and bounds validation on init
6. **Serialization Ready:** All components support to_dict/from_dict
