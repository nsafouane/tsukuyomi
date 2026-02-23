"""
Emotional System - Unified Module
=================================

Re-exports all emotional components for backward compatibility.
This module is split into focused submodules:
- types.py: Data classes and enums
- personality.py: PersonalityBaseline and presets
- impact_rules.py: Event-to-impact mapping
- state_manager.py: StateManager class
- contagion.py: ContagionEmotionalState and group dynamics
"""

from .types import (
    MoodLabel,
    EmotionalTone,
    EmotionalState,
    EmotionalEpisode,
    EmotionalImpact,
    EmotionalEvent,
)

from .personality import (
    PersonalityBaseline,
    ANGRY_MAN,
    BANK_TELLER,
    STOCKBROKER,
    ANALYTICAL_JUROR,
    EMPATHETIC_JUROR,
    PRESET_PROFILES,
)

from .impact_rules import (
    EmotionalImpactRules,
    EVENT_IMPACTS,
    get_impact,
    create_emotional_impact,
)

from .state_manager import (
    StateManager,
    create_state_manager_from_big_five,
)

from .contagion import (
    ContagionEmotionalState,
    apply_group_contagion,
    calculate_group_mood,
)

__all__ = [
    'MoodLabel',
    'EmotionalTone',
    'EmotionalState',
    'EmotionalEpisode',
    'EmotionalImpact',
    'EmotionalEvent',
    'PersonalityBaseline',
    'ANGRY_MAN',
    'BANK_TELLER',
    'STOCKBROKER',
    'ANALYTICAL_JUROR',
    'EMPATHETIC_JUROR',
    'PRESET_PROFILES',
    'EmotionalImpactRules',
    'EVENT_IMPACTS',
    'get_impact',
    'create_emotional_impact',
    'StateManager',
    'create_state_manager_from_big_five',
    'ContagionEmotionalState',
    'apply_group_contagion',
    'calculate_group_mood',
]
