"""
Personality system for agents.
"""

from .profile import PersonalityProfile, VocabularyLevel, build_personality_context, get_sample_profile
from .constraint_sampler import PersonalityConstraintSampler
from .drift_monitor import PersonalityDriftMonitor
from .drift_types import BehaviorSnapshot, DriftReport, PersonalityEvolutionEvent
from .evolution_manager import PersonalityEvolutionManager
from .communication import CommunicationStyle, inject_style_into_prompt, create_style_from_traits, get_style_preset

__all__ = [
    'PersonalityProfile',
    'VocabularyLevel',
    'build_personality_context',
    'get_sample_profile',
    'PersonalityConstraintSampler',
    'PersonalityDriftMonitor',
    'BehaviorSnapshot',
    'DriftReport',
    'PersonalityEvolutionEvent',
    'PersonalityEvolutionManager',
    'CommunicationStyle',
    'inject_style_into_prompt',
    'create_style_from_traits',
    'get_style_preset',
]
