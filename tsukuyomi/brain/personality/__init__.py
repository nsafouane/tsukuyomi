"""
personality - Personality Integrity System for Tsukuyomi Agents

This module implements Phase 14 of the Tsukuyomi V2 Agent Quality Implementation:
Personality Integrity System. It ensures agents have stable, consistent personalities
that persist across the entire simulation.

Key Components:
- PersonalityProfile: Complete personality definition with Big Five traits
- PersonalityConstraintSampler: Pre-generation validation with forbidden patterns
- PersonalityDriftMonitor: Post-generation drift detection with EMA

Usage:
    from tsukuyomi.brain.personality import (
        PersonalityProfile,
        PersonalityConstraintSampler,
        PersonalityDriftMonitor,
        build_personality_context,
    )
    
    # Create a profile
    profile = PersonalityProfile(
        name="Arthur Miller",
        age=52,
        role="Juror #3",
        openness=-0.2,
        conscientiousness=0.3,
        extraversion=0.6,
        agreeableness=-0.5,
        neuroticism=0.7,
        # ... additional fields
    )
    
    # Generate personality context for LLM
    context = build_personality_context(profile)
    
    # Create constraint sampler for pre-generation validation
    sampler = PersonalityConstraintSampler(profile)
    constraints = sampler.build_generation_constraints()
    forbidden = sampler.build_forbidden_patterns()
    
    # Create drift monitor for post-generation monitoring
    monitor = PersonalityDriftMonitor(profile)
    report = monitor.analyze_response(response, context, tick)

Phase 14 Success Criteria:
- Agent responses match personality traits 90%+ of the time
- Drift monitor flags inconsistencies with 80%+ accuracy
- Prevention layer blocks 70%+ of personality violations before generation
- Each agent has a distinct, recognizable voice (4/5 human recognition)
"""

# Profile module
from .profile import (
    PersonalityProfile,
    VocabularyLevel,
    build_personality_context,
    ANGRY_MAN_PROFILE,
    ANALYTICAL_JUROR_PROFILE,
    STOCKBROKER_PROFILE,
    BANK_TELLER_PROFILE,
    ELDERLY_MAN_PROFILE,
    SAMPLE_PROFILES,
    get_sample_profile,
)

# Constraint sampler module
from .constraint_sampler import (
    GenerationConstraints,
    ActionValidationResult,
    PersonalityConstraintSampler,
    ActionFilterChain,
)

# Drift monitor module
from .drift_monitor import (
    BehaviorSnapshot,
    DriftReport,
    PersonalityEvolutionEvent,
    PersonalityDriftMonitor,
    PersonalityEvolutionManager,
)

# Module metadata
__all__ = [
    # Profile
    'PersonalityProfile',
    'VocabularyLevel',
    'build_personality_context',
    'ANGRY_MAN_PROFILE',
    'ANALYTICAL_JUROR_PROFILE',
    'STOCKBROKER_PROFILE',
    'BANK_TELLER_PROFILE',
    'ELDERLY_MAN_PROFILE',
    'SAMPLE_PROFILES',
    'get_sample_profile',
    
    # Constraint Sampler
    'GenerationConstraints',
    'ActionValidationResult',
    'PersonalityConstraintSampler',
    'ActionFilterChain',
    
    # Drift Monitor
    'BehaviorSnapshot',
    'DriftReport',
    'PersonalityEvolutionEvent',
    'PersonalityDriftMonitor',
    'PersonalityEvolutionManager',
]

__version__ = '14.0.0'
__author__ = 'Tsukuyomi Development Team'
__phase__ = 'Phase 14: Personality Integrity System'
