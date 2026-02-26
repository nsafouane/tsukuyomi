# Internal Agent Systems

**Path:** `tsukuyomi/agents/internal/`

**Last Updated:** 2026-02-26

---

## Overview

The Internal Agent Systems provide the core cognitive, emotional, belief, personality, and motivational frameworks that drive agent behavior. These systems are unified across both simulation and standalone modes.

## Philosophy

Per the MVP v0.1 unified internal architecture:
- **Stable Core**: Identity, personality, and core beliefs are immutable
- **Dynamic State**: Emotions and needs evolve over time
- **Evidence-Based Beliefs**: Stances calculated from weighted evidence
- **Motivational Drive**: Internal needs drive behavior when external stimuli are absent

---

## Component Structure

```
internal/
├── emotion/               # PAD-based emotional system
│   ├── types.py           # Emotional data structures
│   ├── personality.py     # PersonalityBaseline presets
│   ├── impact_rules.py    # Event-to-emotional-impact mapping
│   ├── state_manager.py   # Core emotional state management
│   ├── contagion.py       # Emotional contagion between agents
│   └── emotional_expression.py  # Tone generation for LLM output
├── beliefs/               # Evidence-based belief system
│   ├── structures.py      # Belief data structures
│   ├── manager.py         # BeliefManager for evidence tracking
│   ├── system.py          # BeliefSystem with contradictions
│   ├── contradiction.py   # Belief contradiction detection
│   └── decay.py           # Belief decay over time
├── personality/           # Personality integrity system
│   └── profile.py         # PersonalityProfile with Big Five
├── needs/                 # Motivational drive system
│   └── needs_system.py    # NeedsSystem for internal drives
└── relationships/         # (Deprecated/Empty - moved to social/)
```

---

## 1. Emotion System

**Location:** `tsukuyomi/agents/internal/emotion/`

### Core Types (`types.py`)

#### MoodLabel

```python
class MoodLabel(Enum):
    """Mood labels derived from PAD combinations."""
    SERENE = "serene"
    RELAXED = "relaxed"
    CONTENT = "content"
    HAPPY = "happy"
    EXCITED = "excited"
    ELATED = "elated"
    BORED = "bored"
    DROWSY = "drowsy"
    CALM = "calm"
    TIRED = "tired"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    FEARFUL = "fearful"
    FRUSTRATED = "frustrated"
    HOSTILE = "hostile"
    SUBMISSIVE = "submissive"
    DOCILE = "docile"
    SHY = "shy"
    INSECURE = "insecure"
    CONFIDENT = "confident"
    ASSERTIVE = "assertive"
    DOMINANT = "dominant"
```

#### EmotionalTone

```python
class EmotionalTone(Enum):
    """Categorical emotional tones for LLM prompts."""
    NEUTRAL = "neutral"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SAD = "sad"
    HAPPY = "happy"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    EXCITED = "excited"
    CALM = "calm"
    ANXIOUS = "anxious"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
```

#### EmotionalState

```python
@dataclass
class EmotionalState:
    """
    Current emotional state based on the PAD model.

    PAD Dimensions:
    - Valence (Pleasure): -1.0 (distress) to +1.0 (joy)
    - Arousal: 0.0 (calm) to 1.0 (agitated/excited)
    - Dominance: -1.0 (submissive) to +1.0 (dominant)
    """
    valence: float = 0.0
    arousal: float = 0.5
    dominance: float = 0.0
    mood_label: str = MoodLabel.CALM.value
    active_episodes: List[EmotionalEpisode] = []
```

#### EmotionalEpisode

```python
@dataclass
class EmotionalEpisode:
    """
    A temporary emotional spike triggered by a specific event.

    Episodes represent intense emotional reactions that decay over time.
    """
    trigger_event_id: str
    emotion_type: str
    intensity: float
    onset_tick: int
    decay_rate: float
```

### StateManager (`state_manager.py`)

```python
class StateManager:
    """
    The Emotional Core of the agent.

    Manages dynamic emotional states based on the PAD model, handles
    event processing, regression to personality baseline, and
    emotional inertia.
    """

    def __init__(
        self,
        baseline: PersonalityBaseline,
        initial_state: Optional[EmotionalState] = None
    )

    def update(self, tick_number: int, percepts: List) -> None:
        """
        Update emotional state based on percepts and time.

        Process:
        1. Classify percept impacts
        2. Apply emotional shifts with inertia factor
        3. Decay active episodes
        4. Regress to baseline
        5. Derive mood label
        """

    def apply_event(self, event_type: str, tick_number: int) -> None:
        """Apply a direct emotional event (not from perception)."""

    def get_emotional_context(self) -> str:
        """Generate human-readable description of current emotional state."""

    def get_state_dict(self) -> Dict:
        """Serialize emotional state."""

    def reset_to_baseline(self) -> None:
        """Reset emotional state to personality baseline."
```

### Emotional Contagion (`contagion.py`)

#### ContagionEmotionalState

```python
@dataclass
class ContagionEmotionalState:
    """
    Emotional state with contagion dynamics using PAD model.

    Each dimension ranges from -1.0 to 1.0:
    - Pleasure: positive/negative affect
    - Arousal: activation level
    - Dominance: control/agency
    """
    pleasure: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0

    history: List[EmotionalEvent] = []
    max_history: int = 100

    susceptibility: float = 0.3    # How affected by others
    expressiveness: float = 0.5    # How affects others

    decay_rate: float = 0.001
    baseline_pleasure: float = 0.0
    baseline_arousal: float = 0.0
    baseline_dominance: float = 0.0

    @property
    def tone(self) -> EmotionalTone:
        """Determine categorical tone from PAD values."""

    def update(
        self,
        event_type: str,
        intensity: float = 0.1,
        tick: int = 0,
        source: Optional[str] = None,
        source_emotion: Optional['ContagionEmotionalState'] = None
    ) -> EmotionalEvent:
        """Update emotional state based on event."""

    def decay(self, tick: int = 0):
        """Apply decay towards baseline emotional state."""

    def apply_to_prompt(self, base_prompt: str) -> str:
        """Add emotional context to LLM prompt."""

    def to_dict() -> Dict
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContagionEmotionalState'
```

#### Group Functions

```python
def apply_group_contagion(
    agents: List[Dict],
    proximity_matrix: Dict[str, Dict[str, float]],
    tick: int
) -> List[str]:
    """
    Apply emotional contagion between nearby agents.

    Args:
        agents: List with 'id' and 'emotional_state'
        proximity_matrix: agent_id -> {other_agent_id -> proximity (0-1)}
        tick: Current simulation tick

    Returns:
        List of agent IDs that were affected
    """

def calculate_group_mood(agents: List[Dict]) -> Dict:
    """Calculate the overall group mood."""
```

### Presets (`personality.py`)

```python
# Pre-defined personality baseline profiles

ANGRY_MAN = PersonalityBaseline(...)
BANK_TELLER = PersonalityBaseline(...)
STOCKBROKER = PersonalityBaseline(...)
ANALYTICAL_JUROR = PersonalityBaseline(...)
EMPATHETIC_JUROR = PersonalityBaseline(...)

PRESET_PROFILES = {
    "angry_man": ANRY_MAN,
    "bank_teller": BANK_TELLER,
    "stockbroker": STOCKBROKER,
    "analytical_juror": ANALYTICAL_JUROR,
    "empathetic_juror": EMPATHETIC_JUROR,
}
```

### Emotional Expression (`emotional_expression.py`)

**Location:** `tsukuyomi/agents/internal/emotional_expression.py`

Provides emotional expression generation and tone modifiers for LLM output.

#### ToneModifiers

```python
class ToneModifiers(Enum):
    """Modifiers for emotional tones."""
    INTENSIFY = "intensify"   # Make expression stronger
    SOFTEN = "soften"         # Make expression gentler
    NEUTRAL = "neutral"       # No modification
    DRAMATIC = "dramatic"     # Theatrical emphasis
```

#### ToneModifierResult

```python
@dataclass
class ToneModifierResult:
    """Result from tone modifier calculation."""
    modifiers: List[str] = []

    def get_prompt_additions(self) -> str:
        """Get prompt additions from modifiers.

        Example: "[Tone: intense, direct, forceful]"
        """
```

#### EmotionalExpression

```python
@dataclass
class EmotionalExpression:
    """
    Manages emotional expression and tone generation.

    Translates PAD (Pleasure-Arousal-Dominance) states into
    categorical tones and text modifiers for LLM prompts.
    """

    pad_state: Dict[str, float] = {"valence": 0.0, "arousal": 0.5, "dominance": 0.0}
    personality: Dict[str, Any] = {}

    # Cached values for performance
    _cached_tone: Optional[EmotionalTone] = None
    _cached_modifiers: Optional[List[str]] = None

    def get_tone(self) -> EmotionalTone:
        """
        Get the current emotional tone.

        Maps PAD values to categorical tones:
        - High arousal + positive valence → EXCITED
        - High arousal + negative valence → ANGRY
        - Low arousal + negative valence → SAD
        - Low arousal + positive valence → CALM
        - High dominance → CONFIDENT
        - Low dominance → UNCERTAIN
        """

    def _calculate_tone(self) -> EmotionalTone:
        """Calculate tone from PAD state."""

    def get_modifiers(self) -> List[str]:
        """
        Get tone modifiers for expression.

        Returns descriptive adjectives for each tone:
        - ANGRY: ["intense", "direct", "forceful"]
        - HAPPY: ["warm", "enthusiastic", "positive"]
        - SAD: ["subdued", "quiet", "melancholic"]
        - ANXIOUS: ["hesitant", "uncertain", "nervous"]
        - EXCITED: ["energetic", "animated", "enthusiastic"]
        - CALM: ["measured", "peaceful", "relaxed"]
        - CONFIDENT: ["assertive", "decisive", "bold"]
        - UNCERTAIN: ["tentative", "cautious", "doubtful"]
        """

    def get_tone_modifiers(self) -> ToneModifierResult:
        """Get tone modifiers as a result object."""

    def apply_to_text(self, text: str) -> str:
        """
        Apply emotional tone to text.

        Example:
            expression.apply_to_text("I disagree.")
            # Returns: "[intense] I disagree."
        """

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalExpression":
        """Deserialize from dictionary."""
```

#### Helper Functions

```python
def create_emotional_expression(
    valence: float = 0.0,
    arousal: float = 0.5,
    dominance: float = 0.0,
    personality: Optional[Dict] = None
) -> EmotionalExpression:
    """Factory function to create an emotional expression."""

def pad_from_baseline(baseline: Dict) -> Dict[str, float]:
    """Create PAD state from personality baseline."""
```

#### Usage Example

```python
from tsukuyomi.agents.internal.emotional_expression import (
    EmotionalExpression,
    create_emotional_expression
)

# Create expression with angry PAD state
expression = create_emotional_expression(
    valence=-0.6,   # Negative
    arousal=0.8,    # High arousal (agitated)
    dominance=0.3
)

# Get tone and modifiers
tone = expression.get_tone()  # EmotionalTone.ANGRY
modifiers = expression.get_modifiers()  # ["intense", "direct", "forceful"]

# Apply to text
text = expression.apply_to_text("This is unacceptable.")
# Returns: "[intense] This is unacceptable."

# Get prompt additions
result = expression.get_tone_modifiers()
prompt_addition = result.get_prompt_additions()
# Returns: "[Tone: intense, direct, forceful]"
```

---

## 2. Belief System

**Location:** `tsukuyomi/agents/internal/beliefs/`

### BeliefManager (`manager.py`)

```python
class BeliefManager:
    """
    Manages evidence-based beliefs and calculates stances.

    Usage:
        bm = BeliefManager(agent_id, PersonalityBias())
        bm.add_evidence("defendant_guilt", {"position": "against", "weight": 0.8})
        stance = bm.calculate_stance("defendant_guilt")
    """

    def __init__(self, agent_id: str, bias: PersonalityBias)

    # Evidence ledger: topic -> List[EvidenceItem]
    evidence_ledger: Dict[str, List[EvidenceItem]] = {}

    def add_evidence(
        self,
        topic: str,
        position: str,
        weight: float,
        source_type: str,
        description: str,
        tick_added: int,
        confidence: float = 1.0
    ) -> str:
        """Add evidence for a topic. Returns evidence_id."""

    def calculate_stance(self, topic: str) -> Optional[StanceResult]:
        """
        Calculate stance for a topic based on weighted evidence.

        Returns:
            StanceResult with position ("for", "against", "neutral")
        """

    def format_beliefs(self, topics: Optional[List[str]] = None) -> str:
        """Format beliefs for LLM prompt context."""

    def get_evidence_summary(self, topic: str, limit: int = 5) -> str:
        """Get summary of recent evidence for a topic."""

    def prune_evidence(
        self,
        tick_threshold: int,
        max_per_side: int = 20
    ):
        """Remove old and low-weight evidence to prevent ledger bloat."""

    def _apply_confirmation_bias(
        self,
        weight: float,
        position: str,
        current_stance: Optional[StanceResult] = None
    ) -> float:
        """Apply personality bias to evidence weighting."""
```

### Core Structures

#### PersonalityBias

```python
@dataclass
class PersonalityBias:
    confirmation_bias: float = 1.0
    disconfirmation_resistance: float = 1.0
    social_pressure_immunity: float = 1.0
```

#### EvidenceItem

```python
@dataclass
class EvidenceItem:
    evidence_id: str
    topic: str
    position: str  # "for" or "against"
    weight: float
    source_type: str  # "observation", "reasoning", "social_pressure", "hearsay"
    description: str
    tick_added: int
    confidence: float
```

#### StanceResult

```python
@dataclass
class StanceResult:
    topic: str
    position: str  # "for", "against", "neutral"
    confidence: float
    for_score: float
    against_score: float
    total_evidence_count: int
```

### BeliefSystem Components

| Component | Description |
|-----------|-------------|
| `BeliefSystem` | Complete belief system with contradiction detection |
| `ContradictionDetector` | Detects and resolves belief contradictions |
| `BeliefDecayManager` | Handles belief decay over time |
| `ExistentialChallengeProcessor` | Processes challenges to core beliefs |

---

## 3. Personality System

**Location:** `tsukuyomi/agents/internal/personality/`

### PersonalityProfile (`profile.py`)

```python
@dataclass
class PersonalityProfile:
    """
    Complete personality definition for an agent.

    Big Five Personality Traits (OCEAN):
    - Openness: Curiosity vs. caution (-1.0 to 1.0)
    - Conscientiousness: Organization vs. spontaneity (-1.0 to 1.0)
    - Extraversion: Sociability vs. reserve (-1.0 to 1.0)
    - Agreeableness: Cooperation vs. competition (-1.0 to 1.0)
    - Neuroticism: Sensitivity vs. stability (-1.0 to 1.0)

    These traits are IMMUTABLE during normal operation.
    """

    # === Identity ===
    name: str
    age: int
    role: str

    # === Core Traits (Big Five) - STABLE ===
    openness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    agreeableness: float = 0.0
    neuroticism: float = 0.0

    # === Behavioral Patterns ===
    speaking_style: str = "neutral, measured"
    decision_style: str = "balanced, thoughtful"
    conflict_style: str = "diplomatic, compromising"

    # === Core Beliefs ===
    core_values: List[str] = []
    biases: List[str] = []

    # === Backstory ===
    backstory: str = ""
    motivation: str = ""
    fear: str = ""

    # === Voice ===
    vocabulary_level: str = "educated"  # SIMPLE, EDUCATED, FORMAL
    common_phrases: List[str] = []
    speech_quirks: str = ""

    # Methods
    def get_trait_label(self, trait_name: str) -> str:
        """Get human-readable label for a trait value."""

    def to_dict() -> Dict[str, Any]:
        """Serialize to dictionary."""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalityProfile':
        """Deserialize from dictionary."""
```

### VocabularyLevel

```python
class VocabularyLevel(Enum):
    """Vocabulary complexity levels for voice enforcement."""
    SIMPLE = "simple"
    EDUCATED = "educated"
    FORMAL = "formal"
```

### Helper Functions

```python
def build_personality_context(profile: PersonalityProfile) -> str:
    """
    Generate personality enforcement section for LLM prompt.

    Returns:
        Formatted string with all traits, values, and enforcement instructions
    """
```

### Sample Profiles

```python
# Pre-configured personality profiles

ANGRY_MAN_PROFILE = PersonalityProfile(
    name="Arthur Miller",
    age=52,
    role="Juror #3",
    openness=-0.2,
    conscientiousness=0.3,
    extraversion=0.6,
    agreeableness=-0.5,
    neuroticism=0.7,
    speaking_style="aggressive, interrupts often",
    ...
)

ANALYTICAL_JUROR_PROFILE = PersonalityProfile(...)
STOCKBROKER_PROFILE = PersonalityProfile(...)
BANK_TELLER_PROFILE = PersonalityProfile(...)
ELDERLY_MAN_PROFILE = PersonalityProfile(...)

SAMPLE_PROFILES = {
    'angry_man': ANGRY_MAN_PROFILE,
    'analytical_juror': ANALYTICAL_JUROR_PROFILE,
    'stockbroker': STOCKBROKER_PROFILE,
    'bank_teller': BANK_TELLER_PROFILE,
    'elderly_man': ELDERLY_MAN_PROFILE,
}
```

---

## 4. Needs System

**Location:** `tsukuyomi/agents/internal/needs/`

### NeedsSystem (`needs_system.py`)

```python
class NeedsSystem:
    """
    Manages all needs for an agent.

    This system drives agent behavior by increasing needs over time.
    When needs reach critical thresholds, agents are motivated to act.

    Prevents the "Static Loop" where agents do nothing because
    no external stimulus exists.
    """

    # Core needs
    hunger: Need       # Physical drive to eat/drink
    fatigue: Need      # Physical drive to rest
    boredom: Need      # Cognitive drive to explore/socialize
    social: Need       # Psychological drive to interact

    def update_all(self, tick_rate: float = 20.0) -> None:
        """Update all needs based on time since last update."""

    def get_dominant_need(self) -> Optional[NeedType]:
        """Get the most pressing need based on motivation scores."""

    def get_critical_needs(self) -> List[NeedType]:
        """Get list of all needs that are currently critical."""

    def satisfy_need(self, need_type: NeedType, amount: float = 0.5) -> None:
        """Satisfy a specific need."""

    def get_prompt_context(self) -> str:
        """Generate human-readable summary for LLM prompt."""

    def to_dict() -> Dict:
        """Serialize needs system."""

    @classmethod
    def from_dict(cls, data: Dict) -> 'NeedsSystem':
        """Deserialize needs system."""
```

### Need

```python
@dataclass
class Need:
    """A single need with its current value and decay rate."""
    need_type: NeedType
    value: float = 0.0           # 0.0 (satisfied) to 1.0 (critical)
    decay_rate: float = 0.001     # How fast need increases per tick
    threshold: float = 0.8        # Threshold for motivated action

    def update(self, dt: float) -> None:
        """Update need value based on time delta."""

    def satisfy(self, amount: float = 0.5) -> None:
        """Reduce need value by specified amount."""

    def is_critical(self) -> bool:
        """Check if need is above critical threshold."""

    def get_motivation(self) -> float:
        """Get motivation score (0.0 to 1.0)."""

    def to_dict(self) -> Dict:
        """Serialize need to dictionary."""
```

### NeedType

```python
class NeedType(Enum):
    """Types of needs an agent can have."""
    HUNGER = "hunger"
    FATIGUE = "fatigue"
    BOREDOM = "boredom"
    SOCIAL = "social"
```

---

## Tests

**Test Files:**

| Test File | Coverage |
|-----------|----------|
| `test_emotional_integration.py` | StateManager, emotional episodes |
| `test_emotional_expression.py` | Emotional expression and prompts |
| `test_belief_manager.py` | BeliefManager evidence tracking |
| `test_belief_system.py` | BeliefSystem contradictions |
| `test_belief_plasticity.py` | Belief changes over time |
| `test_personality.py` | PersonalityProfile creation |
| `test_personality_persuasion.py` | Personality in persuasion |

---

## Dependencies

**Internal:**
- `tsukuyomi.shared.exceptions` - Custom exceptions

**External:**
- `dataclasses` - Data structures
- `enum` - Enumerations
- `time` - Timestamps
- `math` - Calculations
- `logging` - Logging

---

## Design Principles

1. **Stable Core**: Identity and personality are immutable
2. **Dynamic State**: Emotions and needs evolve over time
3. **Evidence-Based**: Beliefs calculated from weighted evidence
4. **Motivational Drive**: Internal needs prevent static behavior
5. **PAD Model**: All emotions use Pleasure-Arousal-Dominance
6. **Contagion**: Emotions spread between nearby agents
