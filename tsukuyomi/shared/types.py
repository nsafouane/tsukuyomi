"""
Common type definitions for Tsukuyomi.

This module contains shared data structures and types used across systems.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime


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


@dataclass
class Vector3:
    """3D vector for spatial coordinates."""

    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: "Vector3") -> float:
        """Calculate Euclidean distance to another vector."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2) ** 0.5

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)


@dataclass
class EmotionState:
    """PAD emotional state."""

    pleasure: float = 0.0  # -1.0 to 1.0
    arousal: float = 0.0  # -1.0 to 1.0
    dominance: float = 0.0  # -1.0 to 1.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {"pleasure": self.pleasure, "arousal": self.arousal, "dominance": self.dominance}

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "EmotionState":
        """Create from dictionary."""
        return cls(pleasure=data.get("pleasure", 0.0), arousal=data.get("arousal", 0.0), dominance=data.get("dominance", 0.0))


@dataclass
class Memory:
    """Base memory structure."""

    memory_id: str
    agent_id: str
    content: str
    memory_type: MemoryType
    timestamp: float
    importance: float = 0.5  # 0.0 to 1.0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp,
            "importance": self.importance,
            "metadata": self.metadata,
        }


@dataclass
class Belief:
    """Agent belief structure."""

    belief_id: str
    agent_id: str
    proposition: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "belief_id": self.belief_id,
            "agent_id": self.agent_id,
            "proposition": self.proposition,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ActionResult:
    """Result of an agent action."""

    success: bool
    action_id: str
    agent_id: str
    outcome: str
    changes: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "action_id": self.action_id,
            "agent_id": self.agent_id,
            "outcome": self.outcome,
            "changes": self.changes,
            "error_message": self.error_message,
        }


@dataclass
class Relationship:
    """Social relationship between agents."""

    agent_id: str
    target_id: str
    affinity: float  # -1.0 to 1.0
    familiarity: float  # 0.0 to 1.0
    trust: float  # 0.0 to 1.0
    last_interaction: float = 0.0
    shared_experiences: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "target_id": self.target_id,
            "affinity": self.affinity,
            "familiarity": self.familiarity,
            "trust": self.trust,
            "last_interaction": self.last_interaction,
            "shared_experiences": self.shared_experiences,
        }


@dataclass
class Perception:
    """A single percept from the environment."""

    percept_id: str
    agent_id: str
    source: str  # What was perceived
    type: str  # visual, auditory, etc.
    content: str
    confidence: float
    timestamp: float
    location: Optional[Vector3] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "percept_id": self.percept_id,
            "agent_id": self.agent_id,
            "source": self.source,
            "type": self.type,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "location": self.location.to_tuple() if self.location else None,
        }


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
        return {
            "proposal_id": self.proposal_id,
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
            "priority": self.priority,
        }
