"""
Tsukuyomi Agent System

This package contains the unified agent architecture that supports both
standalone and simulation modes through shared cognitive components.

Subpackages:
- core: Base classes and identity
- cognitive: Memory, perception, deliberation
- internal: Emotion, beliefs, needs, personality
- social: Relationships, conversation, influence
- runtime: Standalone and simulation agent implementations
- prompts: LLM prompt templates and context builders

Usage:
    from tsukuyomi.agents.core import BaseAgent
    from tsukuyomi.agents.runtime.standalone_agent import UniversalAgent, AgentState
    from tsukuyomi.agents.internal.emotion import StateManager, PersonalityBaseline
    from tsukuyomi.agents.internal.beliefs import BeliefManager
    from tsukuyomi.agents.cognitive.memory.memory_system import LongTermMemory
"""

__version__ = "0.1.0"
