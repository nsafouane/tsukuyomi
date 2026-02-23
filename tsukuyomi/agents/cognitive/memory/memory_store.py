"""
Memory Store
============

In-memory storage for memories with indexing for fast retrieval.
"""

from collections import defaultdict
from typing import List, Dict, Optional, Set

from .memory_types import Memory, MemoryType


class MemoryStore:
    """In-memory storage for memories with indexing for fast retrieval."""
    
    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self._participant_index: Dict[str, Set[str]] = defaultdict(set)
        self._type_index: Dict[MemoryType, Set[str]] = defaultdict(set)
        self._location_index: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
    
    def store(self, memory: Memory) -> None:
        """Store a memory and update indexes."""
        self.memories[memory.memory_id] = memory
        
        for participant in memory.context.participants:
            self._participant_index[participant.lower()].add(memory.memory_id)
        
        self._type_index[memory.memory_type].add(memory.memory_id)
        
        if memory.context.location:
            self._location_index[memory.context.location.lower()].add(memory.memory_id)
        
        for tag in memory.tags:
            self._tag_index[tag.lower()].add(memory.memory_id)
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID."""
        return self.memories.get(memory_id)
    
    def get_by_participant(self, participant: str) -> List[Memory]:
        """Get all memories involving a participant."""
        memory_ids = self._participant_index.get(participant.lower(), set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """Get all memories of a specific type."""
        memory_ids = self._type_index.get(memory_type, set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_by_location(self, location: str) -> List[Memory]:
        """Get all memories at a specific location."""
        memory_ids = self._location_index.get(location.lower(), set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_by_tag(self, tag: str) -> List[Memory]:
        """Get all memories with a specific tag."""
        memory_ids = self._tag_index.get(tag.lower(), set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_all(self) -> List[Memory]:
        """Get all memories."""
        return list(self.memories.values())
    
    def remove(self, memory_id: str) -> bool:
        """Remove a memory from the store."""
        memory = self.memories.get(memory_id)
        if not memory:
            return False
        
        for participant in memory.context.participants:
            self._participant_index[participant.lower()].discard(memory_id)
        
        self._type_index[memory.memory_type].discard(memory_id)
        
        if memory.context.location:
            self._location_index[memory.context.location.lower()].discard(memory_id)
        
        for tag in memory.tags:
            self._tag_index[tag.lower()].discard(memory_id)
        
        del self.memories[memory_id]
        
        return True
    
    def count(self) -> int:
        """Get total memory count."""
        return len(self.memories)
    
    def clear(self) -> None:
        """Clear all memories and indexes."""
        self.memories.clear()
        self._participant_index.clear()
        self._type_index.clear()
        self._location_index.clear()
        self._tag_index.clear()


def build_memory_context_for_llm(
    memories: List[Memory],
    current_situation: str = ""
) -> str:
    """Format memories for LLM prompt context."""
    if not memories:
        return "RELEVANT MEMORIES: None"
    
    parts = ["RELEVANT MEMORIES (influencing your thinking):"]
    
    for i, memory in enumerate(memories, 1):
        type_indicator = {
            MemoryType.EPISODIC: "[EPISODE]",
            MemoryType.SEMANTIC: "[FACT]",
            MemoryType.EMOTIONAL: "[FEELING]",
            MemoryType.SOCIAL: "[SOCIAL]",
            MemoryType.PROCEDURAL: "[SKILL]",
        }.get(memory.memory_type, "[MEMORY]")
        
        parts.append(f"\n{i}. {type_indicator} {memory.summary}")
        
        if memory.tags:
            parts.append(f"   Tags: {', '.join(memory.tags[:5])}")
        
        if memory.context.participants:
            parts.append(f"   Involves: {', '.join(memory.context.participants)}")
        
        if memory.importance.emotional_weight > 0.5:
            valence = "positive" if memory.importance.emotional_valence > 0 else "negative"
            parts.append(f"   (Strong {valence} emotional weight)")
    
    return "\n".join(parts)
