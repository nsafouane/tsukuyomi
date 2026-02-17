"""
Memory Module for Tsukuyomi V2 Agent Quality Implementation.

This module implements Phase 15: Deep Memory Architecture from the
Agent Quality Specification (2026-02-16).

The memory system provides:
- Structured memory types (Episodic, Semantic, Emotional, Social, Procedural)
- Memory decay with emotional resistance
- Context-aware retrieval with participant matching
- Memory consolidation for repeated experiences

Components:
    memory_types: Core memory data structures and types
    decay_calculator: Memory decay and importance calculation
    retrieval: Context-aware memory retrieval system

Usage:
    from tsukuyomi.brain.memory import (
        Memory,
        MemoryType,
        MemoryRetrieval,
        MemoryDecayCalculator,
        create_episodic_memory,
    )
    
    # Create a memory
    memory = create_episodic_memory(
        content="Marcus sold me a rotten apple",
        tick=100,
        location="market",
        participants=["Marcus"],
        emotional_weight=0.7,
        tags=["trade", "betrayal"]
    )
    
    # Calculate decay
    calculator = MemoryDecayCalculator()
    importance = calculator.effective_importance(memory, current_tick=500)
    
    # Retrieve relevant memories
    retrieval = MemoryRetrieval(calculator)
    context = RetrievalContext(
        situation="buying apples from Marcus",
        participants=["Marcus"],
        current_tick=600
    )
    relevant = retrieval.retrieve(memories, context)

Author: Tanit (AI Co-founder) + Safouane
Date: 2026-02-17
"""

# Core memory types
from .memory_types import (
    Memory,
    MemoryType,
    MemoryPriority,
    MemoryContext,
    MemoryImportance,
    MemoryAccess,
    MemoryList,
    MemoryDict,
)

# Factory functions for creating memories
from .memory_types import (
    create_episodic_memory,
    create_semantic_memory,
    create_emotional_memory,
    create_social_memory,
    create_procedural_memory,
)

# Decay system
from .decay_calculator import (
    MemoryDecayCalculator,
    MemoryImportanceCalculator,
    DecayConfig,
    DecayStrategy,
    apply_decay_batch,
)

# Retrieval system
from .retrieval import (
    MemoryRetrieval,
    MemoryStore,
    RetrievalContext,
    RetrievalMode,
    RetrievalWeights,
    ScoredMemory,
    build_memory_context_for_llm,
)


__all__ = [
    # Memory types
    "Memory",
    "MemoryType",
    "MemoryPriority",
    "MemoryContext",
    "MemoryImportance",
    "MemoryAccess",
    "MemoryList",
    "MemoryDict",
    
    # Factory functions
    "create_episodic_memory",
    "create_semantic_memory",
    "create_emotional_memory",
    "create_social_memory",
    "create_procedural_memory",
    
    # Decay system
    "MemoryDecayCalculator",
    "MemoryImportanceCalculator",
    "DecayConfig",
    "DecayStrategy",
    "apply_decay_batch",
    
    # Retrieval system
    "MemoryRetrieval",
    "MemoryStore",
    "RetrievalContext",
    "RetrievalMode",
    "RetrievalWeights",
    "ScoredMemory",
    "build_memory_context_for_llm",
]

# Module version
__version__ = "1.0.0"
