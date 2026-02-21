"""
Belief Logic Module - Re-exports for backward compatibility.

This module provides a unified import point for all belief-related classes.
The implementations have been split into focused sub-modules for
ARCHITECTURE_SPEC 3.1 compliance (700-line file limit).

Sub-modules:
- structures.py: Core data structures (Belief, Evidence, BeliefUpdate, etc.)
- manager.py: BeliefManager class for evidence-based belief stance calculation
- system.py: BeliefSystem class for full belief lifecycle management
- contradiction.py: ContradictionDetector for detecting and resolving conflicts
- decay.py: BeliefDecayManager for belief decay and saturation
- existential.py: ExistentialChallengeProcessor for metaphysical challenges
"""

# Core structures - imported from structures.py
from .structures import (
    # Enums
    BeliefType,
    EvidenceStrength,
    
    # Data classes
    Belief,
    Evidence,
    BeliefUpdate,
    EvidenceItem,
    StanceResult,
    PersonalityBias,
    DecayConfig,
    
    # Constants
    ENTRENCHED_THRESHOLD,
    MIN_CONFIDENCE,
    MAX_CONFIDENCE,
    SATURATION_DECAY,
)

# BeliefManager - evidence-based stance calculation
from .manager import BeliefManager

# BeliefSystem - full belief lifecycle management
from .system import BeliefSystem

# Contradiction detection and resolution
from .contradiction import ContradictionDetector

# Belief decay and saturation management
from .decay import BeliefDecayManager

# Existential challenge processing
from .existential import ExistentialChallengeProcessor

# Integration helpers
def create_belief_from_core_value(
    value: str,
    source: str,
    intensity: float
) -> Belief:
    """
    Create a belief from an agent's core value.
    
    Core values become immutable, high-confidence beliefs.
    """
    return Belief(
        statement=value,
        belief_type=BeliefType.VALUE,
        confidence=min(1.0, intensity + 0.3),  # Boost confidence for core values
        source=f"Core value: {source}",
        mutable=False,
        is_core_value=True,
        tags=["core_value"]
    )


def belief_strength_category(confidence: float) -> str:
    """Categorize belief strength for display."""
    if confidence >= 0.9:
        return "ABSOLUTE"
    elif confidence >= 0.7:
        return "STRONG"
    elif confidence >= 0.5:
        return "MODERATE"
    elif confidence >= 0.3:
        return "WEAK"
    else:
        return "DOUBTFUL"


__all__ = [
    # Structures
    "BeliefType",
    "EvidenceStrength",
    "Belief",
    "Evidence",
    "BeliefUpdate",
    "EvidenceItem",
    "StanceResult",
    "PersonalityBias",
    "DecayConfig",
    
    # Constants
    "ENTRENCHED_THRESHOLD",
    "MIN_CONFIDENCE",
    "MAX_CONFIDENCE",
    "SATURATION_DECAY",
    
    # Classes
    "BeliefManager",
    "BeliefSystem",
    "ContradictionDetector",
    "BeliefDecayManager",
    "ExistentialChallengeProcessor",
    
    # Helper functions
    "create_belief_from_core_value",
    "belief_strength_category",
]
