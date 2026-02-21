"""
Memory Types for Tsukuyomi V2 Agent Quality Implementation.

This module defines the core memory data structures for the Deep Memory Architecture
(Phase 15 of the Agent Quality Specification).

The memory system supports five types of memories:
- EPISODIC: Specific events and experiences
- SEMANTIC: General facts and knowledge
- EMOTIONAL: Emotional imprints and associations
- SOCIAL: Knowledge about people and relationships
- PROCEDURAL: Skills and how-to knowledge

Author: Tanit (AI Co-founder) + Safouane
Date: 2026-02-17
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid
import time
from tsukuyomi.core.memory.base import MemoryType, ImportanceLevel





class MemoryPriority(Enum):
    """
    Priority levels for memory storage and retrieval.
    
    Higher priority memories are:
    - Retrieved more frequently
    - More resistant to decay
    - More likely to influence behavior
    """
    
    CRITICAL = "critical"    # Life-changing events, core beliefs
    HIGH = "high"           # Important relationships, key skills
    MEDIUM = "medium"       # Routine events, useful knowledge
    LOW = "low"            # Trivial details, rarely needed info
    ARCHIVED = "archived"   # Consolidated memories (reduced importance)


@dataclass
class MemoryContext:
    """
    Contextual information about when and where a memory was formed.
    
    This provides the "5W" structure (Who, What, When, Where, Why) for
    episodic memories and context for other memory types.
    """
    
    # Temporal context
    tick: int                          # Simulation tick when memory formed
    timestamp: Optional[float] = None  # Real-world timestamp
    
    # Spatial context
    location: str = ""                 # Where the memory was formed
    location_type: str = ""            # Type of location (market, home, etc.)
    
    # Social context
    participants: List[str] = field(default_factory=list)  # Who was involved
    witnesses: List[str] = field(default_factory=list)     # Who else was present
    
    # Situational context
    situation: str = ""                # Brief description of situation
    trigger: str = ""                  # What triggered this memory
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class MemoryImportance:
    """
    Importance metrics that determine memory persistence and retrieval.
    
    These values are used by the decay calculator and retrieval system
    to prioritize which memories to keep and which to surface.
    """
    
    # Core importance (0.0 to 1.0)
    base_importance: float = 0.5       # Initial importance rating
    
    # Emotional weight (how emotionally charged)
    emotional_weight: float = 0.0      # 0.0 (neutral) to 1.0 (intense)
    emotional_valence: float = 0.0     # -1.0 (negative) to 1.0 (positive)
    
    # Social weight (importance of relationships involved)
    social_weight: float = 0.0         # 0.0 (strangers) to 1.0 (close bonds)
    
    # Goal relevance (does this affect agent's goals)
    goal_relevance: float = 0.0        # 0.0 (irrelevant) to 1.0 (critical)
    
    # Novelty (first time experiencing something like this)
    novelty: float = 0.0               # 0.0 (routine) to 1.0 (unprecedented)
    
    def compute_importance(self) -> float:
        """
        Compute overall importance score from weighted components.
        
        Returns:
            float: Combined importance score (0.0 to 1.0)
        """
        # Weighted combination
        score = (
            self.base_importance * 0.25 +
            abs(self.emotional_weight) * 0.25 +
            self.social_weight * 0.20 +
            self.goal_relevance * 0.20 +
            self.novelty * 0.10
        )
        return min(1.0, max(0.0, score))


@dataclass
class MemoryAccess:
    """
    Track memory access patterns for decay and reinforcement.
    
    Frequently accessed memories are reinforced and decay more slowly.
    """
    
    access_count: int = 0              # How many times this memory was retrieved
    last_accessed_tick: int = 0        # Last tick this memory was accessed
    creation_tick: int = 0             # Tick when memory was created
    
    # Access history for pattern analysis
    access_history: List[int] = field(default_factory=list)  # Ticks when accessed
    max_history: int = 50              # Maximum history to keep
    
    def record_access(self, current_tick: int) -> None:
        """
        Record an access to this memory.
        
        Args:
            current_tick: The current simulation tick
        """
        self.access_count += 1
        self.last_accessed_tick = current_tick
        self.access_history.append(current_tick)
        
        # Trim history if needed
        if len(self.access_history) > self.max_history:
            self.access_history = self.access_history[-self.max_history:]
    
    def get_access_frequency(self, window_ticks: int = 100, current_tick: int = 0) -> float:
        """
        Calculate access frequency over a recent window.
        
        Args:
            window_ticks: Number of recent ticks to consider
            current_tick: Current simulation tick
            
        Returns:
            float: Access frequency (accesses per tick)
        """
        if not self.access_history:
            return 0.0
        
        recent = [t for t in self.access_history if current_tick - t <= window_ticks]
        if not recent:
            return 0.0
        
        return len(recent) / window_ticks


@dataclass 
class Memory:
    """
    A single memory with full context for the Deep Memory Architecture.
    
    This is the core memory data structure that captures:
    - Content: What the memory is about
    - Context: When, where, who, and why
    - Importance: How significant this memory is
    - Access: How often it's retrieved and used
    
    Memory types serve different cognitive functions:
    
    EPISODIC: Specific events with temporal context
    - Example: "Marcus sold me a rotten apple at the market yesterday"
    - Used for: Recalling specific experiences, learning from events
    
    SEMANTIC: General facts without temporal context
    - Example: "Apples are fruit that grow on trees"
    - Used for: World knowledge, reasoning about properties
    
    EMOTIONAL: Emotional associations and imprints
    - Example: "I feel angry when I think about Marcus"
    - Used for: Emotional responses, relationship dynamics
    
    SOCIAL: Knowledge about people and relationships
    - Example: "Marcus is known to be dishonest in trade"
    - Used for: Social reasoning, predicting behavior
    
    PROCEDURAL: Skills and how-to knowledge
    - Example: "To bargain effectively, start with a low offer"
    - Used for: Action selection, skill application
    """
    
    # Identity
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.EPISODIC
    priority: MemoryPriority = MemoryPriority.MEDIUM
    
    # Content
    content: str = ""                  # Full memory content
    summary: str = ""                  # One-line summary for quick retrieval
    
    # Context (when, where, who, why)
    context: MemoryContext = field(default_factory=MemoryContext)
    
    # Importance metrics
    importance: MemoryImportance = field(default_factory=MemoryImportance)
    
    # Access tracking
    access: MemoryAccess = field(default_factory=MemoryAccess)
    
    # Retrieval helpers
    tags: List[str] = field(default_factory=list)       # ["merchant", "trade", "betrayal"]
    keywords: List[str] = field(default_factory=list)   # Extracted keywords for search
    
    # Vector embedding for semantic search (computed on store)
    embedding: Optional[List[float]] = None
    
    # Related memories (for memory linking)
    related_memory_ids: List[str] = field(default_factory=list)
    
    # Source information
    source_type: str = "experience"    # "experience", "observation", "gossip", "inference"
    source_agent: Optional[str] = None # Who provided this info (for gossip)
    confidence: float = 1.0            # How confident in this memory (for gossip)
    
    # Consolidation tracking
    is_consolidated: bool = False      # Has this been consolidated into generalization
    consolidated_from: List[str] = field(default_factory=list)  # Original memory IDs if consolidated
    
    def __post_init__(self):
        """Initialize derived fields."""
        if not self.summary and self.content:
            # Auto-generate summary from content
            self.summary = self._generate_summary()
        
        # Sync creation tick
        if self.access.creation_tick == 0:
            self.access.creation_tick = self.context.tick
    
    def _generate_summary(self) -> str:
        """
        Generate a one-line summary from content.
        
        Returns:
            str: Brief summary of the memory
        """
        # Simple truncation for now
        if len(self.content) <= 80:
            return self.content
        
        # Find a good break point
        truncated = self.content[:77]
        last_space = truncated.rfind(' ')
        if last_space > 40:
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def compute_importance(self) -> float:
        """
        Compute current importance score.
        
        Returns:
            float: Importance score (0.0 to 1.0)
        """
        return self.importance.compute_importance()
    
    def record_access(self, current_tick: int) -> None:
        """
        Record that this memory was accessed.
        
        Args:
            current_tick: Current simulation tick
        """
        self.access.record_access(current_tick)
    
    def add_tag(self, tag: str) -> None:
        """Add a tag if not already present."""
        tag_lower = tag.lower()
        if tag_lower not in [t.lower() for t in self.tags]:
            self.tags.append(tag_lower)
    
    def add_related_memory(self, memory_id: str) -> None:
        """Add a related memory reference."""
        if memory_id not in self.related_memory_ids and memory_id != self.memory_id:
            self.related_memory_ids.append(memory_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert memory to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "priority": self.priority.value,
            "content": self.content,
            "summary": self.summary,
            "context": {
                "tick": self.context.tick,
                "timestamp": self.context.timestamp,
                "location": self.context.location,
                "participants": self.context.participants,
                "situation": self.context.situation,
            },
            "importance": {
                "base_importance": self.importance.base_importance,
                "emotional_weight": self.importance.emotional_weight,
                "emotional_valence": self.importance.emotional_valence,
                "social_weight": self.importance.social_weight,
                "goal_relevance": self.importance.goal_relevance,
                "computed": self.compute_importance(),
            },
            "access": {
                "access_count": self.access.access_count,
                "last_accessed_tick": self.access.last_accessed_tick,
                "creation_tick": self.access.creation_tick,
            },
            "tags": self.tags,
            "keywords": self.keywords,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "is_consolidated": self.is_consolidated,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """
        Create a Memory from a dictionary.
        
        Args:
            data: Dictionary representation
            
        Returns:
            Memory: Reconstructed memory object
        """
        context_data = data.get("context", {})
        importance_data = data.get("importance", {})
        access_data = data.get("access", {})
        
        return cls(
            memory_id=data.get("memory_id", str(uuid.uuid4())),
            memory_type=MemoryType(data.get("memory_type", "episodic")),
            priority=MemoryPriority(data.get("priority", "medium")),
            content=data.get("content", ""),
            summary=data.get("summary", ""),
            context=MemoryContext(
                tick=context_data.get("tick", 0),
                timestamp=context_data.get("timestamp"),
                location=context_data.get("location", ""),
                participants=context_data.get("participants", []),
                situation=context_data.get("situation", ""),
            ),
            importance=MemoryImportance(
                base_importance=importance_data.get("base_importance", 0.5),
                emotional_weight=importance_data.get("emotional_weight", 0.0),
                emotional_valence=importance_data.get("emotional_valence", 0.0),
                social_weight=importance_data.get("social_weight", 0.0),
                goal_relevance=importance_data.get("goal_relevance", 0.0),
            ),
            access=MemoryAccess(
                access_count=access_data.get("access_count", 0),
                last_accessed_tick=access_data.get("last_accessed_tick", 0),
                creation_tick=access_data.get("creation_tick", 0),
            ),
            tags=data.get("tags", []),
            keywords=data.get("keywords", []),
            source_type=data.get("source_type", "experience"),
            confidence=data.get("confidence", 1.0),
            is_consolidated=data.get("is_consolidated", False),
        )


# Type aliases for clarity
MemoryList = List[Memory]
MemoryDict = Dict[str, Memory]


def create_episodic_memory(
    content: str,
    tick: int,
    location: str = "",
    participants: List[str] = None,
    importance: float = 0.5,
    emotional_weight: float = 0.0,
    tags: List[str] = None,
) -> Memory:
    """
    Factory function to create an episodic memory.
    
    Args:
        content: What happened
        tick: When it happened
        location: Where it happened
        participants: Who was involved
        importance: How important (0.0 to 1.0)
        emotional_weight: How emotional (0.0 to 1.0)
        tags: Tags for retrieval
        
    Returns:
        Memory: Configured episodic memory
    """
    return Memory(
        memory_type=MemoryType.EPISODIC,
        content=content,
        context=MemoryContext(
            tick=tick,
            location=location,
            participants=participants or [],
        ),
        importance=MemoryImportance(
            base_importance=importance,
            emotional_weight=emotional_weight,
        ),
        tags=tags or [],
    )


def create_semantic_memory(
    content: str,
    tick: int,
    confidence: float = 1.0,
    tags: List[str] = None,
) -> Memory:
    """
    Factory function to create a semantic memory (fact/knowledge).
    
    Args:
        content: The fact or knowledge
        tick: When this was learned
        confidence: How confident in this fact
        tags: Tags for retrieval
        
    Returns:
        Memory: Configured semantic memory
    """
    return Memory(
        memory_type=MemoryType.SEMANTIC,
        content=content,
        context=MemoryContext(tick=tick),
        importance=MemoryImportance(base_importance=0.6),
        tags=tags or [],
        confidence=confidence,
    )


def create_emotional_memory(
    content: str,
    tick: int,
    emotional_weight: float = 0.8,
    emotional_valence: float = 0.0,
    trigger: str = "",
    tags: List[str] = None,
) -> Memory:
    """
    Factory function to create an emotional memory.
    
    Args:
        content: Description of the emotional imprint
        tick: When this emotion was felt
        emotional_weight: Intensity (0.0 to 1.0)
        emotional_valence: Positive (1.0) or negative (-1.0)
        trigger: What triggered this emotion
        tags: Tags for retrieval
        
    Returns:
        Memory: Configured emotional memory
    """
    return Memory(
        memory_type=MemoryType.EMOTIONAL,
        content=content,
        context=MemoryContext(tick=tick, trigger=trigger),
        importance=MemoryImportance(
            base_importance=0.7,
            emotional_weight=emotional_weight,
            emotional_valence=emotional_valence,
        ),
        tags=tags or [],
    )


def create_social_memory(
    content: str,
    tick: int,
    participants: List[str],
    social_weight: float = 0.5,
    tags: List[str] = None,
) -> Memory:
    """
    Factory function to create a social memory.
    
    Args:
        content: Social knowledge or observation
        tick: When this was learned
        participants: People this knowledge is about
        social_weight: Importance of these relationships
        tags: Tags for retrieval
        
    Returns:
        Memory: Configured social memory
    """
    return Memory(
        memory_type=MemoryType.SOCIAL,
        content=content,
        context=MemoryContext(tick=tick, participants=participants),
        importance=MemoryImportance(
            base_importance=0.6,
            social_weight=social_weight,
        ),
        tags=tags or [],
    )


def create_procedural_memory(
    content: str,
    tick: int,
    skill_name: str = "",
    tags: List[str] = None,
) -> Memory:
    """
    Factory function to create a procedural memory (skill/how-to).
    
    Args:
        content: The skill or procedure
        tick: When this was learned
        skill_name: Name of the skill
        tags: Tags for retrieval
        
    Returns:
        Memory: Configured procedural memory
    """
    tags = tags or []
    if skill_name and skill_name not in tags:
        tags.append(skill_name)
    
    return Memory(
        memory_type=MemoryType.PROCEDURAL,
        content=content,
        context=MemoryContext(tick=tick),
        importance=MemoryImportance(base_importance=0.7),
        tags=tags,
    )
