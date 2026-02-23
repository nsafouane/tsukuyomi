"""
Belief System - Unified Module
==============================

Re-exports all belief system components for backward compatibility.
This module is split into focused submodules:
- belief_system.py: Core BeliefSystem class
- existential.py: Existential challenge processing
- structures.py: Data classes and types
"""

from .belief_system import BeliefSystem
from .structures import (
    Belief, Evidence, BeliefUpdate, BeliefType,
    ENTRENCHED_THRESHOLD, MIN_CONFIDENCE, MAX_CONFIDENCE,
    SATURATION_DECAY, DecayConfig
)

__all__ = [
    'BeliefSystem',
    'Belief',
    'Evidence',
    'BeliefUpdate',
    'BeliefType',
    'ENTRENCHED_THRESHOLD',
    'MIN_CONFIDENCE',
    'MAX_CONFIDENCE',
    'SATURATION_DECAY',
    'DecayConfig',
]
