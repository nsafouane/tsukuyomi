from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple
from enum import Enum
from datetime import datetime
import uuid

# BeliefManager Constants and Enums

class BeliefType(Enum):
    """Types of beliefs an agent can hold."""
    FACTUAL = "factual"        # Beliefs about facts (can be verified)
    OPINION = "opinion"        # Personal opinions (subjective)
    VALUE = "value"            # Core values (from identity)
    PREDICTION = "prediction"  # Beliefs about future events
    SOCIAL = "social"          # Beliefs about other agents
    METAPHYSICAL = "metaphysical"  # Existential/philosophical beliefs (identity, meaning)


# Saturation constants
MAX_CONFIDENCE = 0.95  # Beliefs can never reach 100%
MIN_CONFIDENCE = 0.05  # Beliefs can never reach 0%
ENTRENCHED_THRESHOLD = 0.85  # Above this, beliefs become resistant
SATURATION_DECAY = 0.002  # Decay per tick for saturated beliefs


@dataclass
class EvidenceItem:
    """A single piece of evidence about a topic."""
    evidence_id: str
    topic: str
    position: str
    weight: float
    source_type: str
    description: str
    tick_added: int
    confidence: float = 1.0


@dataclass
class PersonalityBias:
    """Personality traits that modulate evidence weighting."""
    confirmation_bias: float = 1.0
    disconfirmation_resistance: float = 1.0
    social_pressure_immunity: float = 1.0


@dataclass
class StanceResult:
    """Calculated stance for a topic."""
    topic: str
    position: str
    confidence: float
    for_score: float
    against_score: float
    total_evidence_count: int


@dataclass
class DecayConfig:
    """
    Configuration for belief decay.
    
    Controls how beliefs lose confidence over time without reinforcement.
    """
    base_rate: float = 0.005           # Base decay per tick
    time_factor: float = 0.0001        # Exponential time component
    min_confidence: float = 0.1        # Floor for decay
    saturation_threshold: float = 0.85 # Confidence level for perturbation
    perturbation_chance: float = 0.02  # Chance to perturb saturated beliefs
    perturbation_strength: float = 0.15 # How much to reduce confidence


class EvidenceStrength(Enum):
    """Strength levels for evidence."""
    STRONG = 0.9
    MODERATE = 0.6
    WEAK = 0.3
    SPECULATIVE = 0.1


@dataclass
class Evidence:
    """
    A piece of evidence that affects a belief.
    
    Evidence can support or contradict a belief.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""                    # What the evidence says
    supports_belief: bool = True         # True = supports, False = contradicts
    strength: float = 0.5                # How strong is this evidence (0.0-1.0)
    source: str = ""                     # Where evidence came from
    source_reliability: float = 0.5      # How reliable is the source (0.0-1.0)
    tick: int = 0                        # When evidence was added
    emotional_weight: float = 0.0        # Emotional impact (-1.0 to 1.0)
    
    def __post_init__(self):
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"Evidence strength must be 0.0-1.0, got {self.strength}")
        if not 0.0 <= self.source_reliability <= 1.0:
            raise ValueError(f"Source reliability must be 0.0-1.0, got {self.source_reliability}")
        if not -1.0 <= self.emotional_weight <= 1.0:
            raise ValueError(f"Emotional weight must be -1.0 to 1.0, got {self.emotional_weight}")
    
    @property
    def effective_strength(self) -> float:
        """Calculate effective strength considering source reliability."""
        return self.strength * self.source_reliability
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "supports_belief": self.supports_belief,
            "strength": self.strength,
            "source": self.source,
            "source_reliability": self.source_reliability,
            "tick": self.tick,
            "emotional_weight": self.emotional_weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Evidence':
        return cls(**data)


@dataclass
class Belief:
    """
    A belief held by an agent.
    
    Beliefs have confidence levels that can be updated by evidence.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    statement: str = ""                   # What the agent believes
    belief_type: BeliefType = BeliefType.OPINION
    
    # Confidence tracking
    confidence: float = 0.5               # Current confidence (0.0-1.0)
    initial_confidence: float = 0.5       # Confidence when first formed
    confidence_history: List[Tuple[int, float]] = field(default_factory=list)
    
    # Evidence
    supporting_evidence: List[str] = field(default_factory=list)   # Evidence IDs
    contradicting_evidence: List[str] = field(default_factory=list)  # Evidence IDs
    
    # Metadata
    source: str = ""                      # Where belief originated
    formed_tick: int = 0                  # When belief was formed
    last_updated: int = 0                 # Last update tick
    update_count: int = 0                 # How many times updated
    
    # Mutability
    mutable: bool = True                  # Can this belief change?
    is_core_value: bool = False           # Is this a core value from identity?
    
    # Tags for retrieval
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if not 0.0 <= self.initial_confidence <= 1.0:
            raise ValueError(f"Initial confidence must be 0.0-1.0, got {self.initial_confidence}")
    
    @property
    def is_certain(self) -> bool:
        """Check if belief is held with high certainty."""
        return self.confidence >= 0.8
    
    @property
    def is_doubtful(self) -> bool:
        """Check if belief is held with doubt."""
        return self.confidence <= 0.3
    
    @property
    def evidence_count(self) -> int:
        """Total evidence count."""
        return len(self.supporting_evidence) + len(self.contradicting_evidence)
    
    def record_confidence(self, tick: int):
        """Record current confidence in history."""
        self.confidence_history.append((tick, self.confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "belief_type": self.belief_type.value,
            "confidence": self.confidence,
            "initial_confidence": self.initial_confidence,
            "confidence_history": self.confidence_history,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "source": self.source,
            "formed_tick": self.formed_tick,
            "last_updated": self.last_updated,
            "update_count": self.update_count,
            "mutable": self.mutable,
            "is_core_value": self.is_core_value,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Belief':
        data = data.copy()
        data["belief_type"] = BeliefType(data["belief_type"])
        return cls(**data)


@dataclass
class BeliefUpdate:
    """Records a belief update event."""
    belief_id: str
    old_confidence: float
    new_confidence: float
    evidence_id: str
    reason: str
    tick: int
    
    @property
    def change(self) -> float:
        """Magnitude of confidence change."""
        return abs(self.new_confidence - self.old_confidence)
    
    @property
    def direction(self) -> str:
        """Direction of change."""
        if self.new_confidence > self.old_confidence:
            return "increased"
        elif self.new_confidence < self.old_confidence:
            return "decreased"
        return "unchanged"
