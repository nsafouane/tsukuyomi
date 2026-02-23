"""
Perception Pipeline Module
=========================

Provides perception processing for agents.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


@dataclass
class SensoryProfile:
    """Sensory capabilities of an agent."""
    vision_range: float = 20.0
    vision_fov: float = 120.0
    hearing_range: float = 15.0
    
    def can_see(self, distance: float, angle: float = 0.0) -> bool:
        """Check if something at distance and angle is visible."""
        return distance <= self.vision_range and abs(angle) <= self.vision_fov / 2
    
    def can_hear(self, distance: float) -> bool:
        """Check if something at distance is audible."""
        return distance <= self.hearing_range


@dataclass
class AgentInternalState:
    """Internal state that affects perception."""
    emotional_state: Dict[str, float] = field(default_factory=lambda: {"valence": 0.0, "arousal": 0.5, "dominance": 0.0})
    current_needs: Dict[str, float] = field(default_factory=dict)
    active_beliefs: List[str] = field(default_factory=list)
    attention_focus: Optional[str] = None
    
    def get_salience_modifier(self) -> float:
        """Get a modifier for salience based on internal state."""
        arousal = self.emotional_state.get("arousal", 0.5)
        return 0.5 + (arousal * 0.5)


class PerceptionChannel(Enum):
    """Types of perception channels."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    PROPRIOCEPTIVE = "proprioceptive"
    MEMORY = "memory"
    SOCIAL = "social"
    INTERNAL = "internal"


@dataclass
class Percept:
    """A single percept from perception processing."""
    percept_id: str
    channel: PerceptionChannel
    content: Dict[str, Any]
    salience: float = 0.5
    tick: int = 0
    
    def __post_init__(self):
        if not self.percept_id:
            import uuid
            self.percept_id = str(uuid.uuid4())


class PerceptionPipeline:
    """
    Processes world state into percepts for an agent.
    """
    
    def __init__(self, actor_id: str, profile: SensoryProfile):
        self.actor_id = actor_id
        self.profile = profile
        self.spatial_index = None
        self._last_percepts: List[Percept] = []
    
    def set_spatial_index(self, spatial_index):
        """Set the spatial index for proximity queries."""
        self.spatial_index = spatial_index
    
    def process(self, world_state, internal_state: Optional[AgentInternalState] = None) -> List[Percept]:
        """Process world state into percepts."""
        percepts = []
        
        if world_state is None:
            return percepts
        
        salience_modifier = 1.0
        if internal_state:
            salience_modifier = internal_state.get_salience_modifier()
        
        percepts.append(Percept(
            percept_id=f"tick_{getattr(world_state, 'tick_number', 0)}",
            channel=PerceptionChannel.PROPRIOCEPTIVE,
            content={"message": "World state received"},
            salience=0.3 * salience_modifier,
            tick=getattr(world_state, 'tick_number', 0)
        ))
        
        self._last_percepts = percepts
        return percepts
    
    def get_last_percepts(self) -> List[Percept]:
        """Get the most recent percepts."""
        return self._last_percepts
    
    def filter_by_salience(self, percepts: List[Percept], threshold: float = 0.5) -> List[Percept]:
        """Filter percepts by salience threshold."""
        return [p for p in percepts if p.salience >= threshold]
    
    def get_visual_percepts(self, percepts: List[Percept]) -> List[Percept]:
        """Get only visual percepts."""
        return [p for p in percepts if p.channel == PerceptionChannel.VISUAL]
    
    def get_auditory_percepts(self, percepts: List[Percept]) -> List[Percept]:
        """Get only auditory percepts."""
        return [p for p in percepts if p.channel == PerceptionChannel.AUDITORY]


__all__ = [
    "PerceptionPipeline",
    "SensoryProfile",
    "AgentInternalState",
    "PerceptionChannel",
    "Percept"
]
