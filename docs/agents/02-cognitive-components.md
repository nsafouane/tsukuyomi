# Cognitive Components

**Path:** `tsukuyomi/agents/cognitive/`

**Last Updated:** 2026-02-26

---

## Overview

The Cognitive components provide the mental processing capabilities for Tsukuyomi agents. These modules handle perception, decision-making, deliberation, behavior control, working memory, and reasoning validation.

## Philosophy

Per the MVP v0.1 unified cognitive architecture:
- **Perception-Deliberation-Action Loop**: All cognitive processing follows this unified pattern
- **General Systems**: Components are scenario-agnostic (applicable to jury, marketplace, social, etc.)
- **Cognitive Bounds**: Working memory bounded by Miller's Law (7±2 items)

---

## Component Structure

```
cognitive/
├── behavior.py              # Behavioral traits and decision patterns
├── decision_engine.py       # Decision-making with reasoning chains
├── deliberation.py          # Internal deliberation before action
├── perception_pipeline.py   # Sensory perception processing
├── working_memory.py        # Bounded active cognitive context
├── spatial_utils.py         # Spatial calculations for perception (raycasting, FOV)
├── memory/                  # Memory system (separate documentation)
├── rag/                     # RAG capabilities (currently minimal/empty)
└── reasoning/               # Reasoning validation and transparency
    ├── reasoning_validator.py
    ├── confidence_calibration.py
    ├── decision_record.py
    ├── reasoning_logger.py
    └── validation_types.py
```

---

## 1. Behavioral Diversity System (`behavior.py`)

**Location:** `tsukuyomi/agents/cognitive/behavior.py`

Defines agent behavioral traits and decision-making for social interactions. This is a **GENERAL** system applicable to any social simulation.

### BehavioralTraits

```python
@dataclass
class BehavioralTraits:
    # Social behavior (Big Five derived)
    introversion: float = 0.5      # 0=extrovert, 1=introvert
    dominance: float = 0.5         # 0=follower, 1=leader
    agreeableness: float = 0.5     # 0=challenging, 1=accommodating

    # Conversation behavior
    speak_probability: float = 0.3         # Base chance to speak per turn
    interrupt_probability: float = 0.1     # Chance to interrupt
    topic_initiation_prob: float = 0.2     # Chance to start new topic

    # Responsiveness
    response_latency: float = 0.5          # 0=instant, 1=delayed
    reply_probability: float = 0.7         # Chance to respond when addressed

    # Attention
    attention_span: float = 0.5             # How long to focus
    distractibility: float = 0.3            # Chance to shift attention

    # Persistence
    stubbornness: float = 0.5              # How hard to change mind
    persuasibility: float = 0.5            # How easily persuaded
```

**Key Methods:**

| Method | Description |
|--------|-------------|
| `should_speak(tick, addressing_me)` | Determine if agent should speak this turn |
| `should_initiate_topic(topic_age, threshold)` | Determine if agent should change subject |
| `should_interrupt(speaker_dominance)` | Determine if agent should interrupt |
| `get_leadership_style()` | Returns "leader", "follower", or "peer" |
| `get_conversation_role()` | Returns "initiator", "responder", "listener", or "mediator" |

**Serialization:**
- `to_dict()` / `from_dict()` - Full serialization support

### BehavioralDecider

Decides agent actions based on behavioral traits and context.

```python
class BehavioralDecider:
    def __init__(self, traits: BehavioralTraits)

    def decide_action(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decide what the agent should do.

        Returns:
            Dict with 'action' and parameters:
            - "silent": {}
            - "respond": {"to": agent_id, "interrupt": bool}
            - "new_topic": {"topic": str or None}
        """
```

**Key Methods:**

| Method | Description |
|--------|-------------|
| `decide_action(context)` | Main decision logic |
| `select_respond_target(agents, interactions)` | Choose who to respond to |
| `get_influence_weight(speaker_traits, trust)` | Calculate ASYMMETRIC influence |
| `reset_topic_age()` | Reset topic age counter |

### Behavioral Presets

Pre-configured trait templates for common archetypes:

```python
BEHAVIOR_PRESETS = {
    "leader": BehavioralTraits(dominance=0.8, speak_probability=0.6, ...),
    "follower": BehavioralTraits(dominance=0.2, persuasibility=0.7, ...),
    "skeptic": BehavioralTraits(persuasibility=0.2, stubbornness=0.8, ...),
    "listener": BehavioralTraits(introversion=0.8, speak_probability=0.15, ...),
    "agitator": BehavioralTraits(dominance=0.7, interrupt_probability=0.3, ...),
    "mediator": BehavioralTraits(agreeableness=0.8, ...),
}

def get_behavior_preset(name: str) -> Optional[BehavioralTraits]
def create_behavior_from_traits(big_five: Dict, role: str = None) -> BehavioralTraits
```

---

## 2. Decision Engine (`decision_engine.py`)

**Location:** `tsukuyomi/agents/cognitive/decision_engine.py`

Models how agents make decisions with reasoning chains, decision factors, and multi-criteria analysis.

### Core Data Structures

```python
class DecisionType(Enum):
    ACTION = "action"
    JUDGMENT = "judgment"
    CHOICE = "choice"
    PLAN = "plan"
    VERDICT = "verdict"

class DecisionPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DecisionOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    MIXED = "mixed"
    PENDING = "pending"
    UNKNOWN = "unknown"
```

### DecisionFactor

```python
@dataclass
class DecisionFactor:
    id: str = field(default_factory=lambda: f"df_{uuid.uuid4()}")
    description: str = ""
    weight: float = 0.5              # How much this factors in (0-1)
    belief_id: Optional[str] = None   # Related belief
    source: str = ""                  # Where this factor came from
```

### ReasoningStep

```python
@dataclass
class ReasoningStep:
    id: str = field(default_factory=lambda: f"rs_{uuid.uuid4()}")
    step_number: int = 0
    premise: str = ""                # What we know/assume
    inference: str = ""              # What we infer from premise
    confidence: float = 0.5          # How confident in this step
    evidence_ids: List[str] = []     # Supporting evidence
```

### Decision

```python
@dataclass
class Decision:
    id: str
    decision_type: DecisionType
    question: str = ""               # What we're deciding
    choice: str = ""                 # The chosen option
    alternatives: List[str] = []     # Options considered

    # Reasoning
    reasoning_chain: List[ReasoningStep] = []
    factors: List[DecisionFactor] = []

    # Context
    tick: int = 0
    context: Dict[str, Any] = {}

    # Metadata
    priority: DecisionPriority = MEDIUM
    deadline_tick: Optional[int] = None

    # Outcome
    outcome: DecisionOutcome = PENDING
    outcome_tick: Optional[int] = None
    evaluation: str = ""

    # Confidence
    confidence: float = 0.5
```

**Properties:**
- `reasoning_text` - Get formatted reasoning chain
- `factors_summary` - Get summary of decision factors

### DecisionEngine

```python
class DecisionEngine:
    def __init__(self, agent_id: str)

    # Decision Creation
    def create_decision(
        self,
        question: str,
        decision_type: DecisionType = ACTION,
        alternatives: Optional[List[str]] = None,
        priority: DecisionPriority = MEDIUM,
        deadline_tick: Optional[int] = None,
        context: Optional[Dict] = None,
        tick: int = 0
    ) -> Decision

    def add_reasoning_step(
        self,
        decision_id: str,
        premise: str,
        inference: str,
        confidence: float = 0.5,
        evidence_ids: Optional[List[str]] = None
    ) -> ReasoningStep

    def add_factor(
        self,
        decision_id: str,
        description: str,
        weight: float,
        belief_id: Optional[str] = None,
        source: str = ""
    ) -> DecisionFactor

    # Decision Making
    def make_decision(
        self,
        decision_id: str,
        choice: str,
        confidence: float = 0.5,
        tick: int = 0
    ) -> Decision

    def evaluate_decision(
        self,
        decision_id: str,
        outcome: DecisionOutcome,
        evaluation: str,
        tick: int = 0
    )

    # Multi-Criteria Analysis
    def score_alternatives(
        self,
        decision_id: str,
        score_functions: Dict[str, callable]
    ) -> Dict[str, float]

    def recommend_choice(
        self,
        decision_id: str,
        score_functions: Dict[str, callable]
    ) -> Tuple[str, float]

    # Analysis
    def get_pending_decisions() -> List[Decision]
    def get_completed_decisions() -> List[Decision]
    def get_decision_history(
        decision_type: Optional[DecisionType] = None,
        limit: int = 10
    ) -> List[Decision]
    def get_success_rate(
        decision_type: Optional[DecisionType] = None
    ) -> float
    def get_decision_summary() -> str
```

### Helper Functions

```python
def create_verdict_decision(
    engine: DecisionEngine,
    case: str,
    options: List[str] = None,
    factors: Optional[List[Dict]] = None,
    tick: int = 0
) -> Decision

def create_action_decision(
    engine: DecisionEngine,
    action: str,
    alternatives: List[str] = None,
    context: Optional[Dict] = None,
    tick: int = 0
) -> Decision
```

---

## 3. Deliberation Engine (`deliberation.py`)

**Location:** `tsukuyomi/agents/cognitive/deliberation.py`

Adds internal deliberation before an agent speaks - creates the "thinking before speaking" behavior.

### Core Types

```python
class DeliberationType(Enum):
    REFLECTION = "reflection"      # Thinking about own beliefs
    EVALUATION = "evaluation"      # Evaluating others' arguments
    DECISION = "decision"         # Deciding what to say/do
    PLANNING = "planning"         # Planning response strategy

@dataclass
class DeliberationResult:
    deliberation_type: DeliberationType
    content: str                         # Internal monologue
    reasoning_chain: List[str] = []
    emotional_reaction: str = ""
    confidence: float = 0.5
    should_speak: bool = True
    speak_urgency: float = 0.5          # 0-1, how urgent to speak
```

### DeliberationEngine

```python
class DeliberationEngine:
    def __init__(
        self,
        agent_id: str,
        belief_system: Any = None,
        emotional_state: Dict[str, float] = None,
        personality: Dict[str, float] = None,
        llm_call: Callable = None
    )

    async def deliberate(
        self,
        context: Dict[str, Any],
        tick: int = 0,
        style: str = "brief"  # brief, standard, deep
    ) -> DeliberationResult:
        """
        Generate internal deliberation before speaking.

        Args:
            context: Dict with 'stimulus', 'recent_arguments',
                    'current_topic', 'others_votes'
            tick: Current simulation tick
            style: Deliberation depth

        Returns:
            DeliberationResult with internal monologue
        """

    def update_emotional_state(self, state: Dict[str, float])
    def update_belief_system(self, belief_system)
    def get_recent_deliberations(self, k: int = 5) -> List[DeliberationResult]
    def has_deliberated_recently(self, tick: int, window: int = 50) -> bool
    def to_dict() -> Dict[str, Any]
```

### Helper Function

```python
def create_deliberation_engine(
    agent_id: str,
    belief_system: Any = None,
    emotional_state: Dict[str, float] = None,
    personality: Dict[str, float] = None,
    llm_call: Callable = None
) -> DeliberationEngine
```

---

## 4. Perception Pipeline (`perception_pipeline.py`)

**Location:** `tsukuyomi/agents/cognitive/perception_pipeline.py`

Provides perception processing for agents, converting world state into percepts.

### Core Types

```python
class PerceptionChannel(Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    PROPRIOCEPTIVE = "proprioceptive"
    MEMORY = "memory"
    SOCIAL = "social"
    INTERNAL = "internal"

@dataclass
class SensoryProfile:
    vision_range: float = 20.0
    vision_fov: float = 120.0
    hearing_range: float = 15.0

    def can_see(self, distance: float, angle: float = 0.0) -> bool
    def can_hear(self, distance: float) -> bool

@dataclass
class AgentInternalState:
    emotional_state: Dict[str, float]
    current_needs: Dict[str, float]
    active_beliefs: List[str]
    attention_focus: Optional[str]

    def get_salience_modifier(self) -> float

@dataclass
class Percept:
    percept_id: str
    channel: PerceptionChannel
    content: Dict[str, Any]
    salience: float = 0.5
    tick: int = 0
```

### PerceptionPipeline

```python
class PerceptionPipeline:
    def __init__(self, actor_id: str, profile: SensoryProfile)

    def set_spatial_index(self, spatial_index)

    def process(
        self,
        world_state,
        internal_state: Optional[AgentInternalState] = None
    ) -> List[Percept]:
        """Process world state into percepts."""

    def get_last_percepts(self) -> List[Percept]
    def filter_by_salience(
        self,
        percepts: List[Percept],
        threshold: float = 0.5
    ) -> List[Percept]
    def get_visual_percepts(self, percepts: List[Percept]) -> List[Percept]
    def get_auditory_percepts(self, percepts: List[Percept]) -> List[Percept]
```

---

## 5. Working Memory (`working_memory.py`)

**Location:** `tsukuyomi/agents/cognitive/working_memory.py`

Implements Miller's Law: 7 ± 2 chunks. Refreshed each deliberation cycle.

### MemoryChunk

```python
@dataclass
class MemoryChunk:
    source: str          # "percept", "episodic", "semantic"
    content: Any
    relevance: float

    def to_text(self) -> str:
        """Format for LLM context."""
```

### WorkingMemory

```python
class WorkingMemory:
    """
    Active cognitive context. Bounded by Miller's Law (7 ± 2).

    Usage:
        wm = WorkingMemory()
        wm.refresh(percepts, episodic_memory, semantic_memory, emotional_state)
        context = wm.to_llm_context()
    """

    MAX_SLOTS = 7

    def __init__(self)

    @property
    def slot_count(self) -> int

    def refresh(
        self,
        percepts: list,
        episodic_memories: list,
        semantic_memory: dict,
        emotional_state: Any,
        current_topics: Optional[List[str]] = None
    ):
        """
        Select the most relevant items for current working memory.
        Called each deliberation cycle.
        """

    def to_llm_context(self) -> str:
        """
        Format working memory for LLM prompt.

        Returns:
            Formatted string with sections:
            - WORKING MEMORY header
            - [IMMEDIATE AWARENESS] - percepts
            - [RELEVANT MEMORIES] - episodic
            - [KNOWN FACTS] - semantic
        """
```

---

## 6. Spatial Utilities (`spatial_utils.py`)

**Location:** `tsukuyomi/agents/cognitive/spatial_utils.py`

Provides spatial calculations for the perception pipeline, including raycasting, field-of-view calculations, and line-of-sight determination.

### Core Classes

```python
@dataclass
class SensoryProfile:
    """Configuration for an agent's sensory capabilities."""
    vision_range: float = 20.0        # Max vision distance (meters)
    vision_fov: float = 120.0        # Field of view in degrees
    hearing_range: float = 15.0       # Max hearing distance (meters)
    vision_certainty_decay: float = 0.1   # Visual certainty decay per meter
    hearing_certainty_decay: float = 0.15  # Auditory certainty decay per meter

@dataclass
class AgentInternalState:
    """Simplified agent internal state for perception calculations."""
    current_concerns: List[str]           # Topics the agent is concerned about
    mood_label: str                       # "frustrated", "anxious", "calm", etc.
    arousal: float                        # 0.0 - 1.0
    last_seen_entities: Dict[str, int]    # entity_id -> last_seen_tick
    facing_direction: Optional[Tuple[float, float]] = None  # (dx, dy) normalized

@dataclass
class Wall:
    """Represents a wall or occluding obstacle for raycasting."""
    start: Tuple[float, float]
    end: Tuple[float, float]
    thickness: float = 0.5
    transparent: bool = False
```

### Raycaster Class

```python
class Raycaster:
    """
    Implements raycasting for line-of-sight and field-of-view calculations.

    Uses Bresenham-like line sampling combined with segment intersection
    for efficient and accurate line-of-sight determination.
    """

    def __init__(self, spatial_index=None)

    def register_room_walls(self, room_id: str, walls: List[Wall]) -> None:
        """Register walls for a specific room."""

    def cast_ray(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        room_id: Optional[str] = None,
        max_distance: Optional[float] = None,
        step_size: float = 0.5,
    ) -> Tuple[bool, Optional[Tuple[float, float]], float]:
        """
        Cast a ray from start to end and check for wall intersections.

        Returns:
            (is_blocked, intersection_point, distance_traveled)
        """

    def cast_cone(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        fov_degrees: float,
        max_distance: float,
        room_id: Optional[str] = None,
        num_rays: int = 16,
    ) -> List[Tuple[float, float, float]]:
        """
        Cast multiple rays in a cone (field of view).

        Returns:
            List of (x, y, distance) tuples for ray endpoints
        """

    def get_visible_polygon(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        fov_degrees: float,
        max_distance: float,
        room_id: Optional[str] = None,
        num_rays: int = 32,
    ) -> List[Tuple[float, float]]:
        """
        Get the visible polygon (shape) of the agent's field of view.

        Returns:
            List of (x, y) vertices forming the visible polygon
        """

    def is_point_visible(
        self,
        observer_pos: Tuple[float, float],
        target_pos: Tuple[float, float],
        room_id: Optional[str] = None,
        step_size: float = 0.5,
    ) -> bool:
        """Check if a target point is visible from observer position."""
```

### Usage Example

```python
from tsukuyomi.agents.cognitive.spatial_utils import Raycaster, Wall

# Create raycaster
raycaster = Raycaster()

# Register walls for a room
walls = [
    Wall((0, 0), (10, 0)),   # North wall
    Wall((10, 0), (10, 10)), # East wall
    Wall((10, 10), (0, 10)), # South wall
    Wall((0, 10), (0, 0)),   # West wall
]
raycaster.register_room_walls("jury_room", walls)

# Check if target is visible
visible = raycaster.is_point_visible(
    observer_pos=(5, 5),
    target_pos=(8, 8),
    room_id="jury_room"
)

# Get visible polygon for FOV
polygon = raycaster.get_visible_polygon(
    origin=(5, 5),
    direction=(1, 0),  # Facing East
    fov_degrees=120,
    max_distance=20.0,
    room_id="jury_room"
)
```

---

## 7. RAG Directory (`rag/`)

**Location:** `tsukuyomi/agents/cognitive/rag/`

Currently minimal/empty. Reserved for future Retrieval-Augmented Generation capabilities that will integrate with the memory system for enhanced context retrieval.

---

## 8. Reasoning System (`reasoning/`)

**Location:** `tsukuyomi/agents/cognitive/reasoning/`

### Reasoning Validator (`reasoning_validator.py`)

Provides consistency checks for agent reasoning against personality, beliefs, and needs.

**Key Classes:**

```python
class TraitChecker:
    """Check if decisions align with personality traits."""
    def check_trait_consistency(
        self,
        action: str,
        params: Dict[str, Any],
        emotional_state: str,
        reasoning: str,
        heat_level: float = 0.0
    ) -> List[ReasoningViolation]

class BeliefChecker:
    """Check if actions align with stated beliefs."""
    def check_belief_consistency(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str,
        personality_drivers: List[str]
    ) -> List[ReasoningViolation]

class NeedsChecker:
    """Check if decisions address critical needs."""
    def check_needs_consistency(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str
    ) -> List[ReasoningViolation]

class ReasoningValidator:
    """Main validation orchestrator."""
    def validate(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str,
        emotional_state: str = "neutral",
        heat_level: float = 0.0,
        personality_drivers: Optional[List[str]] = None
    ) -> ValidationResult
```

**Violation Types (from `validation_types.py`):**

```python
class ViolationType(Enum):
    TRAIT_INCONSISTENCY = "trait_inconsistency"
    BELIEF_CONTRADICTION = "belief_contradiction"
    EMOTIONAL_INCOHERENCE = "emotional_incoherence"
    NEEDS_IGNORED = "needs_ignored"

class ViolationSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
```

### Other Reasoning Components

| Component | Description |
|-----------|-------------|
| `confidence_calibration.py` | Adjust decision confidence based on track record |
| `decision_record.py` | Record complete decision chains |
| `reasoning_logger.py` | Log reasoning for analysis and replay |

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_behavioral_diversity.py` | BehavioralTraits, BehavioralDecider, presets |
| `test_decision_engine.py` | Decision creation, reasoning chains, multi-criteria |
| `test_deliberation.py` | DeliberationEngine, internal monologue |
| `test_perception_pipeline.py` | PerceptionPipeline, SensoryProfile |
| `test_working_memory.py` | WorkingMemory bounds, refresh, LLM context |
| `test_reasoning.py` | Reasoning validation |
| `test_visual_perception_phase2.py` | Visual perception in context |
| `test_visual_perception_simple.py` | Basic visual perception |

---

## Dependencies

**Internal:**
- `tsukuyomi.shared.types` - Shared type definitions
- `tsukuyomi.shared.exceptions` - Custom exceptions

**External:**
- `dataclasses` - Data structures
- `enum` - Enumerations
- `uuid` - Unique identifier generation
- `typing` - Type hints
- `random` - Probabilistic decisions
- `re` - Pattern matching (reasoning validator)
- `logging` - Logging

---

## Design Principles

1. **General Systems**: All components are scenario-agnostic
2. **Cognitive Bounds**: Working memory enforces Miller's Law
3. **Asymmetric Influence**: Social influence is directional (A→B ≠ B→A)
4. **Reasoning Transparency**: All decisions can be explained
5. **Validation First**: Consistency checks against personality/beliefs/needs
6. **Serialization Ready**: All components support to_dict/from_dict
