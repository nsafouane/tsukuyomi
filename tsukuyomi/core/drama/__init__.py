"""
Drama Module - Narrative direction and event injection.

Provides context-aware drama direction for driving narrative
progression and maintaining engagement.

Author: Tanit (OpenClaw Agent)
Date: February 17, 2026
"""

from .event_library import (
    EventCategory,
    Event,
    CharacterTrigger,
    EventLibrary,
)
from .branch_manager import (
    BranchState,
    ConditionEvaluator,
    BranchManager,
)
from .context_aware_director import (
    TensionSnapshot,
    ContextAwareDramaDirector,
)

__all__ = [
    # Event Library
    "EventCategory",
    "Event",
    "CharacterTrigger",
    "EventLibrary",
    # Branch Manager
    "BranchState",
    "ConditionEvaluator",
    "BranchManager",
    # Director
    "TensionSnapshot",
    "ContextAwareDramaDirector",
]
