"""
Tsukuyomi Narrative System

Provides narrative control, event injection, and story flow management
for the Tsukuyomi Engine.

Modules:
- core: Core narrative components (DramaDirector, CatalystSystem)
- events: Event library and selection
- flow: Branching and narrative flow control
- context: Context-aware narrative management
"""

from tsukuyomi.narrative.core.director import DramaDirector, TensionVector
from tsukuyomi.narrative.core.catalyst import CatalystSystem, CatalystTemplate
from tsukuyomi.narrative.events.library import (
    EventLibrary,
    Event,
    EventCategory,
    CharacterTrigger,
)
from tsukuyomi.narrative.flow.branching import (
    BranchManager,
    BranchState,
    ConditionEvaluator,
)
from tsukuyomi.narrative.context.context_aware import (
    ContextAwareDramaDirector,
    TensionSnapshot,
    NarrativeBeat,
)

__all__ = [
    # Core
    "DramaDirector",
    "TensionVector",
    "CatalystSystem",
    "CatalystTemplate",
    # Events
    "EventLibrary",
    "Event",
    "EventCategory",
    "CharacterTrigger",
    # Flow
    "BranchManager",
    "BranchState",
    "ConditionEvaluator",
    # Context
    "ContextAwareDramaDirector",
    "TensionSnapshot",
    "NarrativeBeat",
]
