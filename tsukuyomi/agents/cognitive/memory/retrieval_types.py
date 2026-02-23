"""
Memory Retrieval Types
=========================

Type definitions for memory retrieval.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class RetrievalMode(Enum):
    """Memory retrieval modes."""
    HYBRID = "hybrid"
    SEMANTIC = "semantic"
    EMOTIONAL = "emotional"
    PARTICIPANT = "participant"
    IMPORTANCE = "importance"
    RECENCY = "recency"


@dataclass
class RetrievalContext:
    """Context for memory retrieval operations."""
    situation: str = ""
    participants: List[str] = field(default_factory=list)
    current_tick: int = 0
    emotional_state: Optional[str] = None
    working_memory: Optional[List[str]] = field(default_factory=list)
    active_goals: Optional[List[str]] = field(default_factory=list)


@dataclass
class RetrievalWeights:
    """Weights for different retrieval factors."""
    semantic_similarity: float = 0.35
    participant_match: float = 0.25
    emotional_similarity: float = 0.15
    decay_adjusted_importance: float = 0.10
    recency: float = 0.15

    def __post_init__(self):
        total = (
            self.semantic_similarity +
            self.participant_match +
            self.emotional_similarity +
            self.decay_adjusted_importance +
            self.recency
        )
        return 1.0

    @property
    def normalized_weights(self) -> Dict[str, float]:
        return {k: v / total for k, v in self.__dict__}


@dataclass
class ScoredMemory:
    """A memory with its retrieval score breakdown."""
    memory: Any
    total_score: float = 0.0
    semantic_score: float = 0.0
    participant_score: float = 0.0
    importance_score: float = 0.0
    emotional_score: float = 0.0
    recency_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory.memory_id,
            "summary": self.memory.summary,
            "total_score": self.total_score,
            "breakdown": {
                "semantic": self.semantic_score,
                "participant": self.participant_score,
                "importance": self.importance_score,
                "emotional": self.emotional_score,
                "recency": self.recency_score
            }
        }
