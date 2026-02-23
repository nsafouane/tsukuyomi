"""
Core Belief Module.

This module provides a unified belief system for agents, including:
- Belief tracking with confidence levels
- Evidence-based belief updates
- Contradiction detection and resolution
- Belief decay and saturation management
- Existential challenge processing

Module Structure (refactored for ARCHITECTURE_SPEC 3.1 compliance):
- structures.py: Core data structures (Belief, Evidence, BeliefUpdate, etc.)
- manager.py: BeliefManager class for evidence-based stance calculation
- system.py: BeliefSystem class for full belief lifecycle management
- contradiction.py: ContradictionDetector for detecting and resolving conflicts
- decay.py: BeliefDecayManager for belief decay and saturation
- existential.py: ExistentialChallengeProcessor for metaphysical challenges
- logic.py: Re-exports all classes for backward compatibility
"""

# Core structures
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

# Helper functions
from .logic import create_belief_from_core_value, belief_strength_category

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
