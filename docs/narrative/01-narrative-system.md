# Narrative System

**Path:** `tsukuyomi/narrative/`

**Last Updated:** 2026-02-26

---

## Overview

The Narrative System provides dramatic direction for simulations, maintaining tension and injecting context-aware events to create engaging narratives. It monitors the simulation's "Tension Vector" and manages catalyst injections.

## Philosophy

Per the MVP v0.1 narrative architecture:
- **Tension Monitoring**: Track conflict, mystery, social, and emotional tension
- **Context-Aware Events**: Inject events matched to world state and agent states
- **Narrative Beats**: Follow pre-defined story beats with branching support
- **Dynamic Adjustment**: Maintain engagement through automatic tension management

---

## Component Structure

```
narrative/
├── core/
│   ├── catalyst.py      # Catalyst event injection
│   └── director.py      # NarrativeDirector (DramaDirector)
├── events/
│   └── library.py       # EventLibrary for context-aware selection
├── context/
│   └── context_aware.py # ContextAwareDramaDirector
└── flow/
    └── branching.py     # BranchManager for narrative branching
```

---

## 1. Catalyst System (`catalyst.py`)

**Location:** `tsukuyomi/narrative/core/catalyst.py`

Handles creation and injection of "Catalyst" events to drive narrative tension.

### CatalystTemplate

```python
@dataclass
class CatalystTemplate:
    """Template for a catalyst event."""
    id: str
    name: str
    description: str
    tags: List[str]
    parameters: Dict[str, str]
```

### CatalystSystem Class

```python
class CatalystSystem:
    """Manages narrative triggers called 'Catalysts'."""

    def __init__(self, fate_engine)

    # Pre-defined templates
    templates: Dict[str, CatalystTemplate] = {
        "leaked_evidence": ...,
        "witness_outburst": ...,
        "anonymous_tip": ...,
        "social_media_trend": ...,
        "jury_conflict": ...,
        "time_pressure": ...,
        "new_testimony": ...,
        "media_pressure": ...,
    }

    def trigger_random_catalyst(self, tick: int) -> str:
        """Pick a random template and trigger it."""

    def trigger_catalyst(self, template_id: str, tick: int) -> str:
        """Inject a catalyst event into the FateEngine's global events list."""
```

### Pre-defined Catalysts

| Template ID | Name | Description |
|-------------|------|-------------|
| `leaked_evidence` | Leaked Evidence | Confidential documents about the trial found |
| `witness_outburst` | Witness Outburst | Key witness interrupts with emotional testimony |
| `anonymous_tip` | Anonymous Tip | Anonymous source contacts court with info |
| `social_media_trend` | Social Media Trend | Trending topic affects public perception |
| `jury_conflict` | Jury Conflict | Two jurors have heated disagreement |
| `time_pressure` | Time Pressure | Judge announces verdict deadline |
| `new_testimony` | New Testimony | Previously unavailable witness becomes available |
| `media_pressure` | Media Pressure | Reporters gather outside courthouse |

---

## 2. NarrativeDirector / DramaDirector (`director.py`)

**Location:** `tsukuyomi/narrative/core/director.py`

Monitors world events and computes the Tension Vector. Can trigger catalyst events when tension falls below thresholds.

### TensionVector

```python
@dataclass
class TensionVector:
    """
    Numeric representation of simulation's narrative tension.
    Values typically 0.0 to 1.0.
    """
    conflict: float = 0.0    # Based on damage/aggressive events
    mystery: float = 0.0     # Based on unresolved information gaps
    social: float = 0.0      # Based on dialogue frequency and gossip
    emotion: float = 0.0     # Based on aggregate agent sentiment
    aggregate: float = 0.0   # Average of all components
```

### NarrativeDirector Class

```python
class NarrativeDirector:
    """
    Monitors simulation's 'Tension Vector' and manages catalyst injections.
    Ensures narrative maintains appropriate pace and engagement.

    Hooks into the engine as a post-resolution hook.
    """

    def __init__(
        self,
        fate_engine,
        boredom_threshold: float = 0.2,
        tension_decay_rate: float = 0.001,
        window_size_ticks: int = 400,
    )

    # Tension tracking
    current_tension: TensionVector
    event_counts: Dict[str, int]   # conflict, social, mystery counts
    sentiment_sum: float
    sentiment_count: int

    # Catalyst management
    catalyst_system: CatalystSystem
    last_catalyst_tick: int
    catalyst_cooldown: int = 1200

    async def on_tick_resolved(self, tick: int, resolutions: List[Resolution]):
        """Post-resolution hook to update tension based on outcomes."""

    def _update_tension_vector(self):
        """Compute Tension Vector based on rolling metrics."""

    def _check_for_catalysts(self, tick: int):
        """Check if tension too low and trigger catalyst if needed."""

    def update_sentiment(self, sentiment_score: float):
        """Update aggregate sentiment metric."""

    def get_status(self) -> Dict:
        """Return current tension data."""
```

### Tension Calculation

```python
# Conflict tension
conf_val = (event_counts["conflict"] / (window_size_ticks / 200))

# Social tension
soc_val = (event_counts["social"] / (window_size_ticks / 20))

# Mystery tension
mys_val = (event_counts["mystery"] / (window_size_ticks / 100))

# Emotional tension
emotion_val = abs(sentiment_sum / sentiment_count) if sentiment_count > 0 else 0

# Aggregate (average)
aggregate = (conflict + social + mystery + emotion) / 4.0
```

---

## 3. EventLibrary (`events/library.py`)

**Location:** `tsukuyomi/narrative/events/library.py`

Context-aware event selection for narrative injection.

### Core Classes

```python
class EventCategory(Enum):
    """Categories of events."""
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    CHARACTER_SPECIFIC = "character_specific"
    NARRATIVE = "narrative"

@dataclass
class Event:
    """A narrative event that can be injected."""
    id: str
    category: EventCategory
    description: str
    context_tags: List[str]
    target_agent: Optional[str]
    broadcast: bool
    params: Dict[str, Any]

@dataclass
class CharacterTrigger:
    """A trigger condition for character-specific events."""
    trigger_id: str
    condition: str              # e.g., "neuroticism > 0.5 AND tension > 0.6"
    events: List[str]           # Event templates
    priority: float

    def matches(self, agent_state: Dict, tension: float, agent_id: str) -> bool:
        """Check if trigger matches current state."""
```

### EventLibrary Class

```python
class EventLibrary:
    """
    Library of narrative events with context-aware selection.

    Maintains categorized event pools and provides methods for selecting
    events based on context, tension, and agent states.
    """

    def __init__(self)

    # Event pools
    _environmental_events: Dict[str, List[str]]   # weather/location based
    _social_events: Dict[str, List[str]]           # tension based
    _narrative_events: Dict[str, List[str]]
    _character_triggers: Dict[str, CharacterTrigger]

    # Configuration
    _selection_mode: str = "context_weighted"
    _category_weights: Dict[str, float]

    def configure(
        self,
        environmental: Optional[Dict] = None,
        social: Optional[Dict] = None,
        character_specific: Optional[Dict] = None,
        selection_mode: str = "context_weighted",
        category_weights: Optional[Dict] = None,
        context_match_weights: Optional[Dict] = None,
    ):
        """Configure library from scenario config."""

    def select_event(
        self,
        context: Dict[str, Any],
        tension: float,
        agent_states: Optional[Dict] = None,
    ) -> Event:
        """
        Select appropriate event based on current context.

        Priority:
        1. Check character-specific triggers
        2. Select category based on weights/context
        3. Select event from category pool
        """

    def get_all_events(self) -> Dict:
        """Get all event pools for debugging/inspection."""
```

### Default Event Pools

**Environmental:**
- `outdoor_stormy`: Thunder, lightning, rain, wind
- `outdoor_clear`: Breeze, sunlight, birds
- `indoor_generic`: Lights flicker, AC hum, draft
- `indoor_tense`: AC breaks, pipe bursts, door slams

**Social:**
- `neutral`: Clock ticks, throat clearing, paper shuffling
- `conflict`: Arguments, fist slamming, storming out
- `cooperative`: Compromises, common ground, agreements

**Character Triggers:**
- `anger_spike`: When neuroticism > 0.5 AND tension > 0.6
- `introvert_discomfort`: When extraversion < -0.3 AND heat > 0.5
- `calm_under_pressure`: When neuroticism < 0.3 AND tension > 0.7

---

## 4. ContextAwareDramaDirector (`context/context_aware.py`)

**Location:** `tsukuyomi/narrative/context/context_aware.py`

Enhanced director with scenario awareness and context-aware event injection.

### Core Classes

```python
@dataclass
class TensionSnapshot:
    """Snapshot of tension at specific tick."""
    tick: int
    aggregate: float
    components: Dict[str, float]
    timestamp: str

@dataclass
class NarrativeBeat:
    """Represents a narrative beat."""
    id: str
    tick: int
    beat_type: str
    description: str
    triggered: bool
    trigger_tick: Optional[int]
```

### ContextAwareDramaDirector Class

```python
class ContextAwareDramaDirector(DramaDirector):
    """
    Enhanced Drama Director with:
    - Narrative beats from scenario definitions
    - Context-aware event injection
    - Branching narrative support
    - Tension history tracking
    """

    def __init__(
        self,
        scenario_config: Optional[Any] = None,
        fate_engine=None,
        boredom_threshold: float = 0.2,
        tension_threshold_high: float = 0.8,
        tension_decay_rate: float = 0.001,
        window_size_ticks: int = 400,
    )

    # Narrative beat tracking
    _beat_index: int
    _completed_beats: Set[str]
    _beat_queue: List[NarrativeBeat]

    # Branch management
    _branch_manager: BranchManager
    _condition_evaluator: ConditionEvaluator
    _active_branch: Optional[str]

    # Event library
    _event_library: EventLibrary

    # Tension history
    _tension_history: List[TensionSnapshot]

    def evaluate_tick(
        self,
        tick: int,
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> Optional[Event]:
        """
        Main entry point. Evaluate tick for narrative intervention.

        Returns:
            Event to inject, or None if no intervention needed
        """

    def _check_beats(self, tick: int, world_state: Dict, agent_states: Dict) -> Optional[Event]:
        """Check if narrative beats should trigger."""

    def _check_tension(self, tick: int, world_state: Dict, agent_states: Dict) -> Optional[Event]:
        """Check if tension-based intervention needed."""

    def get_tension_trend(self, window_ticks: int = 100) -> str:
        """
        Analyze tension trend over recent ticks.

        Returns: 'rising', 'falling', or 'stable'
        """

    def get_status(self) -> Dict[str, Any]:
        """Get current director status for debugging."""

    def reset(self):
        """Reset director state for new simulation."""
```

---

## 5. Branch Manager (`flow/branching.py`)

**Location:** `tsukuyomi/narrative/flow/branching.py`

Manages branching narratives with condition evaluation.

### BranchManager Class

```python
class BranchManager:
    """Manages branching narrative flow."""

    def evaluate_branch(
        self,
        branches: List[Dict],
        world_state: Dict,
        agent_states: Dict,
        tick: int
    ) -> Optional[str]:
        """
        Evaluate branch conditions and return selected branch ID.
        """

    def mark_beat_completed(self, beat_id: str):
        """Mark a narrative beat as completed."""

    def is_beat_completed(self, beat_id: str) -> bool:
        """Check if beat is completed."""

    def get_branch_history(self) -> List[Dict]:
        """Get history of branch selections."""

    def reset(self):
        """Reset branch state."""
```

### ConditionEvaluator Class

```python
class ConditionEvaluator:
    """Evaluates conditions for narrative beats."""

    def evaluate(
        self,
        condition: str,
        world_state: Dict,
        agent_states: Dict
    ) -> bool:
        """
        Evaluate a condition string.

        Supports:
        - Comparisons: attr > value, attr >= value, attr < value, etc.
        - Logical: condition1 AND condition2, condition1 OR condition2
        - Nested: agent_id.attr_name
        - Tension: tension > 0.5

        Examples:
            "neuroticism > 0.5 AND tension > 0.6"
            "juror_3.agreeableness < 0.0 OR tension > 0.8"
        """
```

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_catalyst.py` | CatalystSystem triggers |
| `test_director.py` | NarrativeDirector tension tracking |
| `test_event_library.py` | EventLibrary selection |
| `test_context_aware.py` | ContextAwareDramaDirector beats |
| `test_branching.py` | BranchManager conditions |

---

## Dependencies

**Internal:**
- `tsukuyomi.transport.proto.core_pb2` - TickState, Resolution
- `tsukuyomi.narrative.events.library` - EventLibrary
- `tsukuyomi.narrative.flow.branching` - BranchManager

**External:**
- `dataclasses` - Data structures
- `enum` - Enumerations
- `json` - JSON serialization
- `logging` - Logging
- `random` - Random selection
- `re` - Condition parsing
- `typing` - Type hints
- `uuid` - Unique ID generation
- `datetime` - Timestamps

---

## Design Principles

1. **Tension Monitoring**: Track conflict, mystery, social, and emotional tension
2. **Context Awareness**: Events match world state and agent states
3. **Narrative Beats**: Follow pre-defined story structure
4. **Branching**: Support conditional narrative paths
5. **Automatic Intervention**: Maintain engagement through tension management
6. **Cooldown Periods**: Prevent over-stimulation with injection limits
