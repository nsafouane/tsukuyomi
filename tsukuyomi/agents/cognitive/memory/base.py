from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional

class MemoryType(Enum):
    """Types of memories stored in the system (Unified Enum)."""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"
    EMOTIONAL = "emotional"
    SOCIAL = "social"

class ImportanceLevel(Enum):
    """Importance levels for memory consolidation."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TRIVIAL = 1

class BaseMemorySystem(ABC):
    """
    Unified tiered memory architecture.
    """
    
    @abstractmethod
    def add_memory(self, *args, **kwargs) -> str:
        """Add a memory to the system."""
        pass
        
    @abstractmethod
    def retrieve_memories(self, *args, **kwargs) -> List[Any]:
        """Retrieve relevant memories."""
        pass
