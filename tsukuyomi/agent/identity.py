"""
Agent Identity System
=====================

Defines the core identity of Tsukuyomi agents:
- Core values (beliefs that cannot be compromised)
- Defining memories (pivotal life moments)
- Personality traits (beyond Big Five)
- Full agent identity (combines everything)

This is the IMMUTABLE core of who an agent IS.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid
from tsukuyomi.core.memory.base import MemoryType, ImportanceLevel





@dataclass
class CoreValue:
    """
    A belief the agent will NOT compromise on.
    
    These are the fundamental values that define who the agent is at their core.
    They may bend on minor issues, but these are non-negotiable.
    """
    value: str                    # The core belief (e.g., "Justice must be served")
    source: str                   # Why they believe this (e.g., "My father was wrongly accused")
    intensity: float = 0.8        # 0.0-1.0 (how absolute this belief is)
    non_negotiable: bool = True   # Can they ever change this belief?
    
    def __post_init__(self):
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError(f"Intensity must be 0.0-1.0, got {self.intensity}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "source": self.source,
            "intensity": self.intensity,
            "non_negotiable": self.non_negotiable
        }


@dataclass
class DefiningMemory:
    """
    A pivotal memory that shaped who the agent is.
    
    These are the defining moments in an agent's life that made them who they are.
    They are emotionally charged and inform how the agent responds to situations.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: str = ""                       # What happened
    emotional_impact: str = ""            # How it made them feel
    lesson_learned: str = ""               # What they learned from it
    tags: List[str] = field(default_factory=list)  # For RAG retrieval
    importance: float = 1.0               # 0.0-1.0
    when_occurred: str = ""               # When it happened (e.g., "age 15")
    
    def __post_init__(self):
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError(f"Importance must be 0.0-1.0, got {self.importance}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event": self.event,
            "emotional_impact": self.emotional_impact,
            "lesson_learned": self.lesson_learned,
            "tags": self.tags,
            "importance": self.importance,
            "when_occurred": self.when_occurred
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DefiningMemory':
        return cls(**data)


@dataclass
class PersonalityTraits:
    """
    Detailed personality beyond Big Five.
    
    Combines the OCEAN model with specific traits that make each agent unique.
    """
    # Big Five (OCEAN) scores: -1.0 to +1.0
    openness: float = 0.0          # Creative vs conventional
    conscientiousness: float = 0.0  # Organized vs spontaneous
    extraversion: float = 0.0      # Outgoing vs reserved
    agreeableness: float = 0.0      # Cooperative vs competitive
    neuroticism: float = 0.0        # Emotional vs stable
    
    # Specific traits (0.0-1.0)
    stubbornness: float = 0.5      # How resistant to change
    empathy: float = 0.5           # Ability to understand others
    patience: float = 0.5          # Tolerance for frustration
    optimism: float = 0.5          # Positive vs negative outlook
    cynicism: float = 0.5          # Skeptical vs trusting
    
    # Communication style
    speaks_frankly: float = 0.5   # Direct vs diplomatic
    uses_complex_language: float = 0.5  # Complex vs simple
    emotional_expression: float = 0.5  # Expressive vs reserved
    humor_style: str = "dry"       # dry, self-deprecating, witty, none
    
    # Emotional triggers (what causes strong reactions)
    triggers: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        for trait in ['openness', 'conscientiousness', 'extraversion', 
                      'agreeableness', 'neuroticism']:
            val = getattr(self, trait)
            if not -1.0 <= val <= 1.0:
                raise ValueError(f"{trait} must be -1.0 to 1.0, got {val}")
        
        for trait in ['stubbornness', 'empathy', 'patience', 'optimism', 
                      'cynicism', 'speaks_frankly', 'uses_complex_language', 
                      'emotional_expression']:
            val = getattr(self, trait)
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{trait} must be 0.0-1.0, got {val}")
    
    def get_big_five_dict(self) -> Dict[str, float]:
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism
        }
    
    def get_summary(self) -> str:
        """Generate a brief personality summary."""
        traits = []
        
        if self.openness > 0.3:
            traits.append("open-minded")
        elif self.openness < -0.3:
            traits.append("traditional")
            
        if self.agreeableness > 0.3:
            traits.append("cooperative")
        elif self.agreeableness < -0.3:
            traits.append("competitive")
            
        if self.neuroticism > 0.3:
            traits.append("emotional")
            
        if self.stubbornness > 0.7:
            traits.append("stubborn")
            
        if self.cynicism > 0.6:
            traits.append("cynical")
            
        return ", ".join(traits) if traits else "balanced"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "big_five": self.get_big_five_dict(),
            "specific_traits": {
                "stubbornness": self.stubbornness,
                "empathy": self.empathy,
                "patience": self.patience,
                "optimism": self.optimism,
                "cynicism": self.cynicism,
                "speaks_frankly": self.speaks_frankly,
                "uses_complex_language": self.uses_complex_language,
                "emotional_expression": self.emotional_expression,
                "humor_style": self.humor_style
            },
            "triggers": self.triggers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalityTraits':
        big_five = data.get("big_five", {})
        traits = data.get("specific_traits", {})
        
        return cls(
            openness=big_five.get("openness", 0.0),
            conscientiousness=big_five.get("conscientiousness", 0.0),
            extraversion=big_five.get("extraversion", 0.0),
            agreeableness=big_five.get("agreeableness", 0.0),
            neuroticism=big_five.get("neuroticism", 0.0),
            stubbornness=traits.get("stubbornness", 0.5),
            empathy=traits.get("empathy", 0.5),
            patience=traits.get("patience", 0.5),
            optimism=traits.get("optimism", 0.5),
            cynicism=traits.get("cynicism", 0.5),
            speaks_frankly=traits.get("speaks_frankly", 0.5),
            uses_complex_language=traits.get("uses_complex_language", 0.5),
            emotional_expression=traits.get("emotional_expression", 0.5),
            humor_style=traits.get("humor_style", "dry"),
            triggers=data.get("triggers", [])
        )


@dataclass
class AgentIdentity:
    """
    Immutable core identity - WHO the agent IS.
    
    This never changes throughout the agent's life in the simulation.
    Everything about the agent's fundamental identity is defined here.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    age: int = 30
    occupation: str = ""
    
    # Origin and history
    origin_story: str = ""              # 2-3 paragraphs of life history
    current_location: str = ""           # Where they are now
    how_they_got_here: str = ""         # Why they're in this situation
    
    # Core identity
    core_values: List[CoreValue] = field(default_factory=list)
    defining_memories: List[DefiningMemory] = field(default_factory=list)
    personality: Optional[PersonalityTraits] = None
    
    # Physical/emotional baseline (PAD model)
    baseline_valence: float = 0.0       # -1.0 (distress) to +1.0 (joy)
    baseline_arousal: float = 0.5        # 0.0 (calm) to 1.0 (agitated)
    baseline_dominance: float = 0.0      # -1.0 (submissive) to +1.0 (dominant)
    
    def __post_init__(self):
        if self.personality is None:
            self.personality = PersonalityTraits()
    
    def get_baseline_pad(self) -> Dict[str, float]:
        return {
            "valence": self.baseline_valence,
            "arousal": self.baseline_arousal,
            "dominance": self.baseline_dominance
        }
    
    def get_core_values_summary(self) -> str:
        """Get a formatted summary of core values."""
        if not self.core_values:
            return "No core values defined."
        
        lines = []
        for cv in self.core_values:
            lines.append(f"- {cv.value} (source: {cv.source})")
        return "\n".join(lines)
    
    def get_defining_memories_summary(self) -> str:
        """Get a formatted summary of defining memories."""
        if not self.defining_memories:
            return "No defining memories."
        
        lines = []
        for dm in self.defining_memories:
            lines.append(f"- [{dm.when_occurred}] {dm.event}")
            lines.append(f"  How it felt: {dm.emotional_impact}")
            lines.append(f"  Lesson: {dm.lesson_learned}")
        return "\n".join(lines)
    
    def get_immersive_description(self) -> str:
        """
        Generate a rich, immersive description of who this agent is.
        This is used to make the LLM truly believe it IS the character.
        """
        parts = []
        
        # Header
        parts.append(f"# {self.name}")
        parts.append(f"Age {self.age}, {self.occupation}")
        parts.append("")
        
        # Origin story
        parts.append("## WHO YOU ARE")
        parts.append(self.origin_story)
        parts.append("")
        
        # Core values
        parts.append("## YOUR CORE VALUES")
        for cv in self.core_values:
            if cv.intensity > 0.7:
                parts.append(f"- **{cv.value}** (This is sacred to you)")
            else:
                parts.append(f"- {cv.value}")
        parts.append("")
        
        # Defining memories
        parts.append("## DEFINING MOMENTS THAT SHAPED YOU")
        for dm in self.defining_memories:
            parts.append(f"- {dm.when_occurred}: {dm.event}")
            parts.append(f"  It made you feel: {dm.emotional_impact}")
            parts.append(f"  You learned: {dm.lesson_learned}")
        parts.append("")
        
        # Personality summary
        if self.personality:
            parts.append("## YOUR PERSONALITY")
            parts.append(self.personality.get_summary())
            if self.personality.triggers:
                parts.append(f"Things that trigger strong emotions: {', '.join(self.personality.triggers)}")
        
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "occupation": self.occupation,
            "origin_story": self.origin_story,
            "current_location": self.current_location,
            "how_they_got_here": self.how_they_got_here,
            "core_values": [cv.to_dict() for cv in self.core_values],
            "defining_memories": [dm.to_dict() for dm in self.defining_memories],
            "personality": self.personality.to_dict() if self.personality else None,
            "baseline_pad": self.get_baseline_pad()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentIdentity':
        core_values = [CoreValue(**cv) for cv in data.get("core_values", [])]
        defining_memories = [DefiningMemory.from_dict(dm) for dm in data.get("defining_memories", [])]
        
        personality = None
        if data.get("personality"):
            personality = PersonalityTraits.from_dict(data["personality"])
        
        pad = data.get("baseline_pad", {})
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            age=data.get("age", 30),
            occupation=data.get("occupation", ""),
            origin_story=data.get("origin_story", ""),
            current_location=data.get("current_location", ""),
            how_they_got_here=data.get("how_they_got_here", ""),
            core_values=core_values,
            defining_memories=defining_memories,
            personality=personality,
            baseline_valence=pad.get("valence", 0.0),
            baseline_arousal=pad.get("arousal", 0.5),
            baseline_dominance=pad.get("dominance", 0.0)
        )


# Convenience function to create a complete identity
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
    """
    Helper to create a fully configured AgentIdentity.
    
    Args:
        name: Agent's name
        age: Agent's age
        occupation: Agent's job
        origin_story: Life history
        core_values: List of core value dicts
        defining_memories: List of defining memory dicts
        personality: Personality traits dict
        **kwargs: Additional fields
    
    Returns:
        Fully configured AgentIdentity
    """
    cv_objects = [CoreValue(**cv) for cv in core_values]
    dm_objects = [DefiningMemory(**dm) for dm in defining_memories]
    personality_obj = PersonalityTraits.from_dict(personality) if personality else None
    
    return AgentIdentity(
        name=name,
        age=age,
        occupation=occupation,
        origin_story=origin_story,
        core_values=cv_objects,
        defining_memories=dm_objects,
        personality=personality_obj,
        **kwargs
    )


__all__ = [
    "MemoryType",
    "CoreValue",
    "DefiningMemory", 
    "PersonalityTraits",
    "AgentIdentity",
    "create_identity"
]
