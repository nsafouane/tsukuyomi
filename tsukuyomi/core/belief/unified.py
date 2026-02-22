"""
Backward-compatibility shim.

The belief module was refactored into separate submodules:
  - structures.py, manager.py, system.py, contradiction.py, decay.py, etc.

This file re-exports every public symbol so that existing
``from tsukuyomi.core.belief.unified import X`` statements
continue to work without modification.

TODO: Migrate all callers to import directly from
      ``tsukuyomi.core.belief`` and delete this shim.
"""

from tsukuyomi.core.belief import (           # noqa: F401
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

    # Classes
    BeliefManager,
    BeliefSystem,
    ContradictionDetector,
    BeliefDecayManager,
    ExistentialChallengeProcessor,

    # Helper functions
    create_belief_from_core_value,
    belief_strength_category,
)
