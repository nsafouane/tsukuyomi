"""
Long-Term Memory System
======================

Persistent episodic memory with RAG-based retrieval.
This system allows agents to remember everything that matters to them.
"""

import uuid
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from collections import defaultdict
from tsukuyomi.agents.cognitive.memory.base import MemoryType, ImportanceLevel


logger = logging.getLogger("MemorySystem")




class MemoryImportance(Enum):
    """Memory importance levels."""
    CRITICAL = 1.0    # Life-changing events
    HIGH = 0.8        # Significant moments
    MEDIUM = 0.5     # Notable events
    LOW = 0.3        # Minor details
    TRIVIAL = 0.1    # Barely worth remembering


@dataclass
class Memory:
    """
    A single memory unit.
    
    This is the core data structure for all memories an agent stores.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.EPISODIC
    
    # Content
    content: str = ""                    # What happened/is true
    context: str = ""                    # Circumstances around it
    summary: str = ""                    # Compressed summary for long memories
    
    # Emotional tagging
    emotional_tags: List[str] = field(default_factory=list)  # Emotions attached
    emotional_valence: float = 0.0     # -1.0 (negative) to +1.0 (positive)
    emotional_arousal: float = 0.5     # 0.0 (calm) to 1.0 (intense)
    
    # Importance and retrieval
    importance: float = 0.5             # 0.0-1.0
    keywords: List[str] = field(default_factory=list)  # For keyword search
    
    # Temporal
    created_at: int = 0                 # Tick when created
    last_accessed: int = 0              # Last retrieval tick
    access_count: int = 0               # How many times retrieved
    
    # Association (for memory chaining)
    associated_ids: List[str] = field(default_factory=list)  # Related memories
    
    # Consolidation
    is_consolidated: bool = False       # Has been summarized?
    consolidation_level: int = 0         # How many times consolidated
    
    def __post_init__(self):
        if not 0.0 <= self.importance <= 1.0:
            raise ValueError(f"Importance must be 0.0-1.0, got {self.importance}")
        if not -1.0 <= self.emotional_valence <= 1.0:
            raise ValueError(f"Emotional valence must be -1.0 to 1.0")
        if not 0.0 <= self.emotional_arousal <= 1.0:
            raise ValueError(f"Emotional arousal must be 0.0 to 1.0")
        
        if self.created_at == 0:
            self.created_at = int(time.time())
    
    def access(self, tick: int) -> None:
        """Record that this memory was accessed."""
        self.last_accessed = tick
        self.access_count += 1
    
    def get_recency_score(self, current_tick: int, decay_rate: float = 0.001) -> float:
        """Calculate how recently this memory was accessed."""
        if self.last_accessed == 0:
            self.last_accessed = self.created_at
        
        age = current_tick - self.last_accessed
        return max(0.0, 1.0 - (age * decay_rate))
    
    def get_relevance_score(self, query: str) -> float:
        """Calculate keyword-based relevance to a query."""
        if not query or not self.keywords:
            return 0.0
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        memory_words = set(w.lower() for w in self.keywords)
        
        # Jaccard similarity
        intersection = query_words & memory_words
        union = query_words | memory_words
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.memory_type.value,
            "content": self.content,
            "context": self.context,
            "summary": self.summary,
            "emotional_tags": self.emotional_tags,
            "emotional_valence": self.emotional_valence,
            "emotional_arousal": self.emotional_arousal,
            "importance": self.importance,
            "keywords": self.keywords,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "associated_ids": self.associated_ids,
            "is_consolidated": self.is_consolidated,
            "consolidation_level": self.consolidation_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Memory':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            memory_type=MemoryType(data.get("type", "episodic")),
            content=data.get("content", ""),
            context=data.get("context", ""),
            summary=data.get("summary", ""),
            emotional_tags=data.get("emotional_tags", []),
            emotional_valence=data.get("emotional_valence", 0.0),
            emotional_arousal=data.get("emotional_arousal", 0.5),
            importance=data.get("importance", 0.5),
            keywords=data.get("keywords", []),
            created_at=data.get("created_at", 0),
            last_accessed=data.get("last_accessed", 0),
            access_count=data.get("access_count", 0),
            associated_ids=data.get("associated_ids", []),
            is_consolidated=data.get("is_consolidated", False),
            consolidation_level=data.get("consolidation_level", 0)
        )


class LongTermMemory:
    """
    Persistent memory system with RAG-like retrieval.
    
    Features:
    - Store memories with importance weighting
    - Keyword-based retrieval
    - Temporal decay (recent memories are more accessible)
    - Memory consolidation for long sessions
    - Association chaining (related memories)
    """
    
    def __init__(
        self,
        agent_id: str,
        max_memories: int = 10000,
        consolidation_threshold: int = 100
    ):
        self.agent_id = agent_id
        self.max_memories = max_memories
        self.consolidation_threshold = consolidation_threshold
        
        # Primary storage
        self.memories: Dict[str, Memory] = {}
        
        # Indexes for fast retrieval
        self._by_type: Dict[MemoryType, Set[str]] = defaultdict(set)
        self._by_keyword: Dict[str, Set[str]] = defaultdict(set)
        self._by_emotion: Dict[str, Set[str]] = defaultdict(set)
        
        # Statistics
        self.total_stored = 0
        self.total_retrieved = 0
        self.consolidation_count = 0
        
        logger.info(f"LongTermMemory initialized for agent {agent_id}")
    
    def store(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        context: str = "",
        importance: float = 0.5,
        keywords: List[str] = None,
        emotional_tags: List[str] = None,
        emotional_valence: float = 0.0,
        emotional_arousal: float = 0.5,
        associated_memories: List[str] = None,
        tick: int = 0
    ) -> str:
        """
        Store a new memory.
        
        Args:
            content: What happened/is true
            memory_type: Type of memory
            context: Circumstances around it
            importance: 0.0-1.0 importance
            keywords: Keywords for retrieval
            emotional_tags: Emotions associated
            emotional_valence: -1.0 to +1.0
            emotional_arousal: 0.0 to 1.0
            associated_memories: IDs of related memories
            tick: Current simulation tick
        
        Returns:
            Memory ID
        """
        keywords = keywords or []
        emotional_tags = emotional_tags or []
        associated_memories = associated_memories or []
        
        memory = Memory(
            memory_type=memory_type,
            content=content,
            context=context,
            importance=importance,
            keywords=keywords,
            emotional_tags=emotional_tags,
            emotional_valence=emotional_valence,
            emotional_arousal=emotional_arousal,
            created_at=tick,
            associated_ids=associated_memories
        )
        
        # Store
        self.memories[memory.id] = memory
        self.total_stored += 1
        
        # Update indexes
        self._by_type[memory_type].add(memory.id)
        for kw in keywords:
            self._by_keyword[kw.lower()].add(memory.id)
        for tag in emotional_tags:
            self._by_emotion[tag.lower()].add(memory.id)
        
        # Update associations
        for assoc_id in associated_memories:
            if assoc_id in self.memories:
                self.memories[assoc_id].associated_ids.append(memory.id)
        
        # Check if consolidation needed
        if len(self.memories) > self.max_memories:
            self._consolidate_old_memories()
        
        logger.debug(f"Stored memory {memory.id}: {content[:50]}...")
        return memory.id
    
    async def retrieve(
        self,
        query: str,
        k: int = 10,
        tick: int = 0,
        memory_types: List[MemoryType] = None,
        min_importance: float = 0.0
    ) -> List[Memory]:
        """
        Retrieve relevant memories using keyword matching and importance weighting.
        
        This is a simplified RAG-like retrieval that combines:
        - Keyword matching
        - Importance weighting
        - Recency (recent memories score higher)
        
        Args:
            query: Search query
            k: Number of memories to return
            tick: Current tick (for recency calculation)
            memory_types: Filter by memory types
            min_importance: Minimum importance threshold
        
        Returns:
            List of relevant memories, sorted by relevance
        """
        if not self.memories:
            return []
        
        memory_types = memory_types or list(MemoryType)
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        candidates = []
        
        for memory in self.memories.values():
            # Type filter
            if memory.memory_type not in memory_types:
                continue
            
            # Importance filter
            if memory.importance < min_importance:
                continue
            
            # Calculate relevance score
            score = 0.0
            
            # Keyword match (40% weight)
            if memory.keywords:
                memory_words = set(w.lower() for w in memory.keywords)
                keyword_overlap = query_words & memory_words
                if keyword_overlap:
                    score += 0.4 * (len(keyword_overlap) / len(memory_words))
            
            # Content contains query (30% weight)
            if query_lower in memory.content.lower():
                score += 0.3
            
            # Importance (20% weight)
            score += 0.2 * memory.importance
            
            # Recency (10% weight)
            score += 0.1 * memory.get_recency_score(tick)
            
            if score > 0:
                candidates.append((score, memory))
        
        # Sort by score descending
        candidates.sort(key=lambda x: -x[0])
        
        # Record access for top results
        results = []
        for score, memory in candidates[:k]:
            memory.access(tick)
            results.append(memory)
            self.total_retrieved += 1
        
        logger.debug(f"Retrieved {len(results)} memories for query: {query[:30]}...")
        return results
    
    async def retrieve_by_emotion(
        self,
        emotion: str,
        k: int = 5,
        tick: int = 0
    ) -> List[Memory]:
        """Retrieve memories with specific emotional tag."""
        emotion_lower = emotion.lower()
        
        if emotion_lower not in self._by_emotion:
            return []
        
        memory_ids = self._by_emotion[emotion_lower]
        memories = [self.memories[mid] for mid in list(memory_ids)[:k]]
        
        for m in memories:
            m.access(tick)
        
        return memories
    
    async def get_recent(
        self,
        count: int = 10,
        memory_type: MemoryType = None
    ) -> List[Memory]:
        """
        Get most recent memories.
        
        Args:
            count: Number of memories
            memory_type: Optional filter by type
        
        Returns:
            Most recent memories
        """
        all_memories = self.memories.values()
        
        if memory_type:
            all_memories = [m for m in all_memories if m.memory_type == memory_type]
        
        # Sort by last accessed
        sorted_memories = sorted(
            all_memories,
            key=lambda m: m.last_accessed or m.created_at,
            reverse=True
        )
        
        return sorted_memories[:count]
    
    async def get_memories_for_prompt(
        self,
        current_situation: str,
        max_memories: int = 5,
        tick: int = 0
    ) -> str:
        """
        Get a formatted string of relevant memories for LLM prompts.
        
        This is the key integration point with the LLM - it formats
        memories in a way the LLM can understand and use.
        
        Args:
            current_situation: What's happening now
            max_memories: How many to include
            tick: Current tick
        
        Returns:
            Formatted memory string for prompts
        """
        memories = await self.retrieve(
            query=current_situation,
            k=max_memories,
            tick=tick,
            min_importance=0.3
        )
        
        if not memories:
            return "No relevant memories."
        
        lines = ["## RELEVANT MEMORIES:"]
        
        for i, mem in enumerate(memories, 1):
            # Format emotional state
            emotion_str = ""
            if mem.emotional_tags:
                emotion_str = f" [Feeling: {', '.join(mem.emotional_tags)}]"
            
            # Format content
            content = mem.content
            if len(content) > 200:
                content = content[:200] + "..."
            
            lines.append(f"{i}. {content}{emotion_str}")
            
            # Add context if important
            if mem.importance > 0.7 and mem.context:
                lines.append(f"   Context: {mem.context[:100]}")
        
        return "\n".join(lines)
    
    def _consolidate_old_memories(self) -> None:
        """
        Consolidate old, rarely accessed memories.
        
        This prevents memory overflow by summarizing old memories
        and removing duplicates.
        """
        if len(self.memories) < self.max_memories * 0.9:
            return
        
        # Find low-access memories
        candidates = [
            m for m in self.memories.values()
            if m.access_count < 3 and not m.is_consolidated
        ]
        
        # Consolidate the oldest ones
        candidates.sort(key=lambda m: m.created_at)
        
        consolidated = 0
        for memory in candidates[:10]:  # Consolidate 10 at a time
            if memory.content and not memory.summary:
                # Create summary
                memory.summary = memory.content[:100] + "..."
                memory.is_consolidated = True
                memory.consolidation_level += 1
                consolidated += 1
        
        if consolidated > 0:
            self.consolidation_count += consolidated
            logger.info(f"Consolidated {consolidated} memories for agent {self.agent_id}")
    
    def get_memory_count(self) -> int:
        """Get total number of stored memories."""
        return len(self.memories)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        return {
            "total_memories": len(self.memories),
            "total_stored": self.total_stored,
            "total_retrieved": self.total_retrieved,
            "consolidation_count": self.consolidation_count,
            "by_type": {
                mt.value: len(mids) 
                for mt, mids in self._by_type.items()
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize memory system."""
        return {
            "agent_id": self.agent_id,
            "statistics": self.get_statistics(),
            "memories": [m.to_dict() for m in self.memories.values()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LongTermMemory':
        """Deserialize memory system."""
        memory = cls(agent_id=data["agent_id"])
        
        for mem_data in data.get("memories", []):
            memory.store(
                content=mem_data["content"],
                memory_type=MemoryType(mem_data.get("type", "episodic")),
                context=mem_data.get("context", ""),
                importance=mem_data.get("importance", 0.5),
                keywords=mem_data.get("keywords", []),
                emotional_tags=mem_data.get("emotional_tags", []),
                emotional_valence=mem_data.get("emotional_valence", 0.0),
                emotional_arousal=mem_data.get("emotional_arousal", 0.5),
                tick=mem_data.get("created_at", 0)
            )
        
        return memory


# Convenience function for storing event memories
async def store_event_memory(
    memory_system: LongTermMemory,
    event: str,
    context: str = "",
    importance: float = 0.5,
    emotional_tags: List[str] = None,
    tick: int = 0
) -> str:
    """
    Helper to store an episodic memory of an event.
    
    Args:
        memory_system: The memory system to store in
        event: What happened
        context: Circumstances
        importance: How important
        emotional_tags: Emotions felt
        tick: Current tick
    
    Returns:
        Memory ID
    """
    # Extract keywords from event
    words = event.lower().split()
    keywords = [w for w in words if len(w) > 3][:5]
    
    return memory_system.store(
        content=event,
        memory_type=MemoryType.EPISODIC,
        context=context,
        importance=importance,
        keywords=keywords,
        emotional_tags=emotional_tags or [],
        tick=tick
    )


__all__ = [
    "MemoryType",
    "MemoryImportance", 
    "Memory",
    "LongTermMemory",
    "store_event_memory"
]
