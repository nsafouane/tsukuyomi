"""
Persuasion Types and Data Structures
====================================

Type definitions for the persuasion dynamics engine.
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any


ENTRENCHED_THRESHOLD = 0.85
MAX_CONFIDENCE = 0.95


class PersuasionStrategy(Enum):
    """Types of persuasion strategies."""
    LOGIC = "logic"
    EMOTION = "emotion"
    AUTHORITY = "authority"
    SOCIAL_PROOF = "social_proof"
    RECIPROCITY = "reciprocity"
    SCARCITY = "scarcity"
    COMMITMENT = "commitment"
    LIKING = "liking"


class ArgumentStrength(Enum):
    """Strength categories for arguments."""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class Argument:
    """A persuasive argument made by an agent."""
    id: str = field(default_factory=lambda: f"arg_{str(uuid.uuid4())}")
    claim: str = ""
    strategy: PersuasionStrategy = PersuasionStrategy.LOGIC
    evidence_ids: List[str] = field(default_factory=list)
    target_belief_id: Optional[str] = None
    speaker_id: str = ""
    tick: int = 0
    strength_score: float = 0.5
    confidence: float = 0.5
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "claim": self.claim,
            "strategy": self.strategy.value,
            "evidence_ids": self.evidence_ids,
            "target_belief_id": self.target_belief_id,
            "speaker_id": self.speaker_id,
            "tick": self.tick,
            "strength_score": self.strength_score,
            "confidence": self.confidence,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Argument":
        return cls(
            id=data["id"],
            claim=data["claim"],
            strategy=PersuasionStrategy(data["strategy"]),
            evidence_ids=data.get("evidence_ids", []),
            target_belief_id=data.get("target_belief_id"),
            speaker_id=data["speaker_id"],
            tick=data["tick"],
            strength_score=data.get("strength_score", 0.5),
            confidence=data.get("confidence", 0.5),
            context=data.get("context", {})
        )


@dataclass
class PersuasionAttempt:
    """Record of a persuasion attempt between agents."""
    id: str = field(default_factory=lambda: f"pa_{str(uuid.uuid4())}")
    arg_id: str = ""
    speaker_id: str = ""
    listener_id: str = ""
    tick: int = 0
    initial_confidence: float = 0.5
    final_confidence: float = 0.5
    change: float = 0.0
    resistance_factors: List[str] = field(default_factory=list)
    effectiveness_factors: List[str] = field(default_factory=list)
    
    @property
    def was_effective(self) -> bool:
        return abs(self.change) > 0.05
    
    @property
    def direction(self) -> str:
        if self.change > 0.01:
            return "strengthened"
        elif self.change < -0.01:
            return "weakened"
        return "unchanged"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "arg_id": self.arg_id,
            "speaker_id": self.speaker_id,
            "listener_id": self.listener_id,
            "tick": self.tick,
            "initial_confidence": self.initial_confidence,
            "final_confidence": self.final_confidence,
            "change": self.change,
            "resistance_factors": self.resistance_factors,
            "effectiveness_factors": self.effectiveness_factors
        }


@dataclass
class PersuasionProfile:
    """An agent's persuasion tendencies and resistances."""
    agent_id: str = ""
    
    strategy_preferences: Dict[PersuasionStrategy, float] = field(default_factory=lambda: {
        PersuasionStrategy.LOGIC: 0.5,
        PersuasionStrategy.EMOTION: 0.5,
        PersuasionStrategy.AUTHORITY: 0.5,
        PersuasionStrategy.SOCIAL_PROOF: 0.5,
        PersuasionStrategy.RECIPROCITY: 0.5,
        PersuasionStrategy.SCARCITY: 0.5,
        PersuasionStrategy.COMMITMENT: 0.5,
        PersuasionStrategy.LIKING: 0.5,
    })
    
    base_resistance: float = 0.5
    strategy_resistance: Dict[PersuasionStrategy, float] = field(default_factory=lambda: {
        PersuasionStrategy.LOGIC: 0.5,
        PersuasionStrategy.EMOTION: 0.5,
        PersuasionStrategy.AUTHORITY: 0.5,
        PersuasionStrategy.SOCIAL_PROOF: 0.5,
        PersuasionStrategy.RECIPROCITY: 0.5,
        PersuasionStrategy.SCARCITY: 0.5,
        PersuasionStrategy.COMMITMENT: 0.5,
        PersuasionStrategy.LIKING: 0.5,
    })
    
    arguments_made: List[str] = field(default_factory=list)
    arguments_heard: List[str] = field(default_factory=list)
    successful_persuasions: int = 0
    failed_persuasions: int = 0
    times_persuaded: int = 0
    times_resisted: int = 0
    
    @property
    def persuasion_success_rate(self) -> float:
        total = self.successful_persuasions + self.failed_persuasions
        if total == 0:
            return 0.5
        return self.successful_persuasions / total
    
    @property
    def resistance_rate(self) -> float:
        total = self.times_persuaded + self.times_resisted
        if total == 0:
            return 0.5
        return self.times_resisted / total
    
    def get_preferred_strategy(self) -> PersuasionStrategy:
        return max(self.strategy_preferences.items(), key=lambda x: x[1])[0]
    
    def get_weakest_resistance(self) -> PersuasionStrategy:
        return min(self.strategy_resistance.items(), key=lambda x: x[1])[0]
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "strategy_preferences": {k.value: v for k, v in self.strategy_preferences.items()},
            "base_resistance": self.base_resistance,
            "strategy_resistance": {k.value: v for k, v in self.strategy_resistance.items()},
            "arguments_made": self.arguments_made,
            "arguments_heard": self.arguments_heard,
            "successful_persuasions": self.successful_persuasions,
            "failed_persuasions": self.failed_persuasions,
            "times_persuaded": self.times_persuaded,
            "times_resisted": self.times_resisted
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PersuasionProfile":
        profile = cls(agent_id=data["agent_id"])
        profile.strategy_preferences = {
            PersuasionStrategy(k): v for k, v in data.get("strategy_preferences", {}).items()
        }
        profile.base_resistance = data.get("base_resistance", 0.5)
        profile.strategy_resistance = {
            PersuasionStrategy(k): v for k, v in data.get("strategy_resistance", {}).items()
        }
        profile.arguments_made = data.get("arguments_made", [])
        profile.arguments_heard = data.get("arguments_heard", [])
        profile.successful_persuasions = data.get("successful_persuasions", 0)
        profile.failed_persuasions = data.get("failed_persuasions", 0)
        profile.times_persuaded = data.get("times_persuaded", 0)
        profile.times_resisted = data.get("times_resisted", 0)
        return profile
