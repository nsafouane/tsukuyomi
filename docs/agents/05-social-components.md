# Social Components

**Path:** `tsukuyomi/agents/social/`

**Last Updated:** 2026-02-26

---

## Overview

The Social Components provide multi-agent interaction capabilities including conversation management, gossip/information propagation, persuasion dynamics, and relationship tracking. These are **GENERAL SYSTEMS** applicable to any social simulation.

## Philosophy

Per the MVP v0.1 unified social architecture:
- **Asymmetric Influence**: A→B influence ≠ B→A influence
- **Information Leakage**: Agents "overhear" each other's deliberations
- **Response Variety**: Agents avoid repetitive statements
- **Turn-Taking**: Structured conversation flow

---

## Component Structure

```
social/
├── conversation.py        # Turn-taking and response tracking
├── gossip_protocol.py     # Information leakage between agents
├── persuasion.py          # Persuasion dynamics engine
├── persuasion_types.py    # Persuasion data structures
├── influence.py           # Social influence calculation
└── relationship_manager.py # Relationship tracking
```

---

## 1. Conversation System (`conversation.py`)

**Location:** `tsukuyomi/agents/social/conversation.py`

Manages turn-taking and response variety in multi-agent conversations.

### ResponseRecord

```python
@dataclass
class ResponseRecord:
    """Record of a single agent response."""
    tick: int
    content: str
    prompt_type: str  # "deliberation", "vote", "reaction"
    tone: str
    word_count: int
    timestamp: datetime

    @property
    def content_hash(self) -> str:
        """Hash of content for quick comparison."""

    def key_phrases(self) -> List[str]:
        """Extract 2-3 word n-grams for similarity checking."""

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
```

### ResponseHistory

```python
@dataclass
class ResponseHistory:
    """
    Tracks an agent's recent responses to prevent repetition.

    Features:
    - Rolling window of recent responses
    - Repetitive phrase detection
    - Similarity scoring
    - Prompt modifier generation
    """
    max_history: int = 10
    repetition_threshold: int = 3
    responses: List[ResponseRecord] = []
    phrase_counts: Dict[str, int] = {}

    def add(self, response: ResponseRecord):
        """Add response and update phrase counts."""

    def get_repetitive_phrases(self) -> List[str]:
        """Get phrases used too often (>= threshold)."""

    def similarity_score(self, new_content: str) -> float:
        """Calculate similarity to recent responses (0.0-1.0)."""

    def is_too_similar(self, new_content: str, threshold: float = 0.6) -> bool:
        """Check if content is too similar to recent responses."""

    def get_variety_warning(self) -> Optional[str]:
        """Get warning about repetitive phrases for prompt injection."""

    def clear(self):
        """Clear history and phrase counts."""

    def to_dict() -> Dict:
        """Serialize for persistence."""

    @classmethod
    def from_dict(cls, data: Dict) -> 'ResponseHistory':
        """Deserialize from dict."""
```

### ConversationManager

```python
class ConversationManager:
    """
    Manages turn-taking in multi-agent conversations.

    Features:
    - Turn-taking protocols
    - Speaker queue management
    - Response tracking
    - Variety enforcement
    """

    def __init__(
        self,
        participants: List[str],
        max_turns_per_speaker: int = 3,
        min_silence_ticks: int = 5
    )

    def request_turn(self, agent_id: str, context: TurnContext) -> TurnResult:
        """
        Request a turn for an agent.

        Returns:
            TurnResult with decision (CONTINUE, YIELD, INTERRUPT, SILENT)
        """

    def end_turn(self, agent_id: str) -> None:
        """End the current turn."""

    def tick(self) -> None:
        """Advance silence counter."""

    def get_next_speaker(self) -> Optional[str]:
        """Get who should speak next based on rules."""

    def record_response(
        self,
        agent_id: str,
        content: str,
        tick: int,
        prompt_type: str = "deliberation",
        tone: str = "neutral"
    ) -> None:
        """Record a response for variety tracking."""

    def get_response_history(self, agent_id: str) -> Optional[ResponseHistory]:
        """Get response history for an agent."""

    def reset_turn_counts(self) -> None:
        """Reset turn counts for new round."""

    def get_stats(self) -> Dict:
        """Get conversation statistics."""
```

### Turn Types

```python
class TurnDecision(Enum):
    """Decision about who speaks next."""
    CONTINUE = "continue"
    YIELD = "yield"
    INTERRUPT = "interrupt"
    SILENT = "silent"

@dataclass
class TurnContext:
    """Context for turn-taking decisions."""
    current_speaker: str
    last_speaker: str
    turn_count: int
    time_since_last_speech: int
    topic: str = ""
    active_participants: List[str] = []
    conversation_tension: float = 0.0

@dataclass
class TurnResult:
    """Result of a turn-taking decision."""
    decision: TurnDecision
    next_speaker: Optional[str] = None
    reason: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = {}
```

### Helper Functions

```python
def generate_variety_prompt_modifier(
    history: ResponseHistory,
    style_guidelines: Optional[str] = None
) -> str:
    """Generate prompt modifier to encourage response variety."""

def check_response_quality(
    content: str,
    history: ResponseHistory,
    min_words: int = 5,
    max_similarity: float = 0.7
) -> Dict:
    """Check if response meets quality standards."""

def create_conversation_manager(
    participants: List[str],
    **kwargs
) -> ConversationManager:
    """Factory function to create a ConversationManager."""
```

---

## 2. Gossip Protocol (`gossip_protocol.py`)

**Location:** `tsukuyomi/agents/social/gossip_protocol.py`

Enables information leakage between deliberating agents.

### GossipItem

```python
@dataclass
class GossipItem:
    """A single piece of gossip information."""
    id: str
    content: str
    source_actor_id: str
    original_tick: int
    propagation_count: int = 0
    accuracy: float = 1.0  # Decays as gossip spreads
    tags: List[str] = []
```

### GossipEvent

```python
@dataclass
class GossipEvent:
    """Records when gossip was shared between actors."""
    tick: int
    from_actor_id: str
    to_actor_id: str
    gossip_id: str
    method: str  # "overhearing", "conversation", "observation"
```

### GossipProtocol

```python
class GossipProtocol:
    """
    Manages information exchange between deliberating agents.

    The protocol works by:
    1. Agents register their current deliberation thoughts
    2. There's a probability that other agents "overhear" these thoughts
    3. Overheard information becomes gossip items
    4. Gossip propagates through the agent network

    Configuration:
        base_leakage_probability: 10% chance of overhearing per tick
        proximity_multiplier: 2x chance if actors are close
        accuracy_decay: 10% accuracy loss per propagation
        max_propagation_depth: Gossip stops after 5 hops
    """

    def __init__(
        self,
        base_leakage_probability: float = 0.1,
        proximity_multiplier: float = 2.0,
        accuracy_decay: float = 0.1,
        max_propagation_depth: int = 5
    )

    def register_deliberation(
        self,
        actor_id: str,
        thought: str,
        action: str,
        tick: int,
        world_state_context: Optional[Dict] = None
    ):
        """Register an agent's current deliberation thought."""

    def process_gossip(self, tick: int) -> List[GossipEvent]:
        """
        Process gossip for this tick.

        Returns list of new gossip events that occurred.
        """

    def prune_history(self, current_tick: int, max_age: int = 1000):
        """Prune old gossip events and memory to prevent memory leaks."""

    def get_gossip_for_agent(self, actor_id: str) -> List[GossipItem]:
        """Get all gossip items known to an agent."""

    def get_gossip_summary_for_agent(self, actor_id: str) -> str:
        """Get formatted summary of gossip known to an agent (for LLM prompts)."""

    def export_events(self) -> str:
        """Export all gossip events to JSON string."""

    def get_statistics(self) -> Dict:
        """Get statistics about gossip propagation."""
```

### Global Instance

```python
def get_gossip_protocol() -> GossipProtocol:
    """Get or create the global gossip protocol instance."""
```

---

## 3. Persuasion System (`persuasion.py`)

**Location:** `tsukuyomi/agents/social/persuasion.py`

Models how agents persuade and are persuaded by others.

### PersuasionEngine

```python
class PersuasionEngine:
    """Main persuasion engine for modeling persuasive dynamics."""

    def __init__(
        self,
        agent_id: str,
        profile: Optional[PersuasionProfile] = None,
        personality: Optional[Dict[str, float]] = None
    )

    def create_argument(
        self,
        claim: str,
        strategy: PersuasionStrategy,
        target_belief_id: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        strength_score: Optional[float] = None,
        confidence: float = 0.5,
        tick: int = 0,
        context: Optional[Dict] = None
    ) -> Argument:
        """Create a persuasive argument."""

    def calculate_persuasion_effect(
        self,
        argument: Argument,
        listener_id: str,
        belief_confidence: float,
        belief_is_core: bool = False,
        existing_evidence_count: int = 0,
        tick: int = 0
    ) -> Tuple[float, PersuasionAttempt]:
        """
        Calculate how much an argument persuades.

        Returns:
            (new_confidence, attempt_record)
        """

    def select_best_strategy(
        self,
        listener_id: str,
        belief_confidence: float,
        available_evidence: int = 0,
        relationship: float = 0.5
    ) -> PersuasionStrategy:
        """Select the best persuasion strategy for this situation."""

    def update_relationship(self, other_id: str, delta: float):
        """Update relationship modifier with another agent."""

    def get_relationship(self, other_id: str) -> float:
        """Get relationship score with another agent."""

    def get_statistics(self) -> Dict[str, Any]:
        """Get persuasion statistics."""

    def get_argument_effectiveness_report(self) -> str:
        """Generate a report on argument effectiveness."""

    def to_dict() -> Dict:
        """Serialize to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict) -> 'PersuasionEngine':
        """Deserialize from dictionary."""
```

### Helper Functions

```python
def create_persuasion_profile_from_personality(
    personality_traits: Dict[str, float]
) -> PersuasionProfile:
    """Create a persuasion profile from personality traits."""

def argument_strength_category(strength: float) -> ArgumentStrength:
    """Categorize argument strength."""

def calculate_persuasion_effectiveness_by_personality(
    agent_personality: Dict[str, float],
    argument_strategy: PersuasionStrategy
) -> float:
    """Calculate how effective a specific argument type is for an agent."""

def calculate_persuasion_resistance_by_personality(
    agent_personality: Dict[str, float],
    argument_strategy: PersuasionStrategy
) -> float:
    """Calculate how resistant an agent is to a specific argument type."""

def get_personality_persuasion_summary(
    agent_personality: Dict[str, float]
) -> Dict[str, Dict[str, float]]:
    """Get summary of how agent responds to all argument types."""

def apply_personality_to_persuasion_engine(
    engine: PersuasionEngine,
    agent_personality: Dict[str, float]
) -> None:
    """Apply personality weights to an existing PersuasionEngine."""
```

### Personality-Strategy Mapping

```python
ARGUMENT_EFFECTIVENESS_BY_PERSONALITY = {
    "logic": {
        "openness": 0.8,
        "conscientiousness": 0.6,
    },
    "emotion": {
        "neuroticism": 0.9,
        "agreeableness": 0.5,
    },
    "authority": {
        "conscientiousness": 0.8,
        "openness": 0.3,
    },
    "social_proof": {
        "extraversion": 0.7,
        "agreeableness": 0.6,
    },
    # ... more strategies
}
```

---

## 4. Relationship Manager (`relationship_manager.py`)

**Location:** `tsukuyomi/agents/social/relationship_manager.py`

Tracks and manages social relationships from the perspective of a single agent.

### Data Structures

```python
@dataclass
class SocialEvent:
    tick: int
    actor_id: str
    target_id: str
    event_type: str  # "interact", "gossip_share", "conflict", etc.
    impact: float    # -1.0 to 1.0
    description: str

@dataclass
class Relationship:
    affinity: float = 0.0        # -1.0 to 1.0
    events: List[SocialEvent] = []
    reputation_score: float = 0.0
```

### RelationshipManager

```python
class RelationshipManager:
    """
    Tracks social relationships from a single agent's perspective.
    """

    def __init__(self, owner_id: str)

    def record_event(
        self,
        target_id: str,
        tick: int,
        event_type: str,
        impact: float,
        description: str
    ):
        """Update affinity and record a social event."""

    def get_affinity(self, target_id: str) -> float:
        """Get affinity score with target."""

    def get_relationship_status(self, target_id: str) -> str:
        """
        Get relationship status.

        Returns: "friendly", "acquaintance", "neutral",
                 "unfriendly", "hostile"
        """

    def to_llm_context(self) -> str:
        """Generate context for LLM regarding all known relationships."""
```

### Affinity Levels

| Affinity Range | Status |
|---------------|---------|
| > 0.6 | friendly |
| 0.2 to 0.6 | acquaintance |
| -0.2 to 0.2 | neutral |
| -0.6 to -0.2 | unfriendly |
| < -0.6 | hostile |

---

## 5. Influence System (`influence.py`)

**Location:** `tsukuyomi/agents/social/influence.py`

Calculates asymmetric social influence between agents.

### Key Concepts

- **Asymmetric Influence**: A's influence on B ≠ B's influence on A
- **Factors**: dominance, extraversion, speaking_style, relationship_affinity
- **Capped**: Maximum influence limited to prevent dominance cascade

### Influence Factors

```python
def calculate_influence(
    speaker_traits: Dict,
    listener_traits: Dict,
    relationship_affinity: float
) -> float:
    """
    Calculate speaker's influence on listener.

    Factors:
    - Speaker dominance (high = more influential)
    - Listener extraversion (low = more influenced)
    - Speaking style (authoritative = more influential)
    - Relationship affinity (positive = more influential)

    Returns:
        Influence score (0.0 to 1.0)
    """
```

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_response_history.py` | ResponseHistory, variety detection |
| `test_conversation_manager.py` | ConversationManager, turn-taking |
| `test_gossip_protocol.py` | GossipProtocol, information leakage |
| `test_persuasion.py` | PersuasionEngine, strategy selection |
| `test_persuasion_by_personality.py` | Personality-based persuasion |
| `test_influence.py` | Asymmetric influence calculation |
| `test_relationship_manager.py` | Relationship tracking |

---

## Dependencies

**Internal:**
- `tsukuyomi.agents.social.persuasion_types` - Persuasion data structures

**External:**
- `dataclasses` - Data structures
- `datetime` - Timestamps
- `hashlib` - Content hashing
- `random` - Probabilistic gossip
- `json` - Export format
- `logging` - Logging

---

## Design Principles

1. **Asymmetric Influence**: A→B ≠ B→A (based on traits)
2. **Information Leakage**: Deliberations can be overheard
3. **Response Variety**: Agents avoid repetitive statements
4. **Turn-Taking**: Structured conversation flow
5. **Personality-Driven**: Strategy preferences based on Big Five
6. **Relationship Tracking**: Affinity evolves based on interactions
