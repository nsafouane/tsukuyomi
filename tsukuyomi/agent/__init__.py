"""
Tsukuyomi Agent System
=====================

Complete agent architecture for simulation and roleplay.

Key Components:
- Identity: Who an agent is (values, memories, personality)
- Memory: What they remember (episodic, semantic, emotional)
- Prompts: How they express themselves (immersive prompts)
- Runtime: Complete runnable agent

Usage:
    from tsukuyomi.agent import create_agent
    
    agent = create_agent(
        name="Arthur Miller",
        age=58,
        occupation="Retired Factory Worker",
        origin_story="Worked 30 years in the steel mill...",
        core_values=[{"value": "Personal responsibility", "source": "Life", "intensity": 1.0}],
        defining_memories=[...],
        personality={"big_five": {"neuroticism": 0.5}, "specific_traits": {"stubbornness": 0.9}},
        scenario_name="jury"
    )
    
    # Set LLM
    async def my_llm(prompt, **kwargs):
        return "Response"
    
    agent.set_llm(my_llm)
    
    # Get response
    response = await agent.respond("What do you think?")
"""

# Identity
from .identity import (
    MemoryType as IdentityMemoryType,
    CoreValue,
    DefiningMemory,
    PersonalityTraits,
    AgentIdentity,
    create_identity
)

# Memory
from .memory_system import (
    MemoryType,
    MemoryImportance,
    Memory,
    LongTermMemory,
    store_event_memory
)

# Prompts
from .immersive_prompt import (
    PromptContext,
    ImmersivePromptBuilder,
    create_prompt_context
)

# Runtime
from .universal_agent import (
    AgentState,
    AgentConfig,
    UniversalAgent,
    create_agent
)

# Beliefs
from .belief_system import (
    BeliefType,
    EvidenceStrength,
    Evidence,
    Belief,
    BeliefUpdate,
    BeliefSystem,
    create_belief_from_core_value,
    belief_strength_category
)

# Persuasion
from .persuasion import (
    PersuasionStrategy,
    ArgumentStrength,
    Argument,
    PersuasionAttempt,
    PersuasionProfile,
    PersuasionEngine,
    create_persuasion_profile_from_personality,
    apply_personality_to_persuasion_engine,
    calculate_persuasion_effectiveness_by_personality,
    calculate_persuasion_resistance_by_personality,
    argument_strength_category as persuasion_strength_category
)

# Decision
from .decision_engine import (
    DecisionType,
    DecisionPriority,
    DecisionOutcome,
    DecisionFactor,
    ReasoningStep,
    Decision,
    DecisionEngine,
    create_verdict_decision,
    create_action_decision
)

# Context
from .context_manager import (
    ContextType,
    Utterance,
    KeyPoint,
    Turn,
    ContextManager,
    extract_keywords,
    extract_topics
)

# Proposal
from .proposal_handler import (
    ProposalType,
    ProposalStatus,
    Proposal,
    ProposalHandler,
    create_verdict_proposal,
    tally_votes
)

# V3 Architecture Components
from .emotional_state import (
    EmotionalTone,
    EmotionalState,
    EmotionalEvent,
    apply_group_contagion,
    calculate_group_mood
)

from .conversation import (
    ResponseRecord,
    ResponseHistory,
    generate_variety_prompt_modifier,
    check_response_quality
)

from .personality import (
    CommunicationStyle,
    inject_style_into_prompt,
    create_style_from_traits,
    get_style_preset
)

from .memory import (
    Utterance,
    ConversationMemory
)

from .behavior import (
    BehavioralTraits,
    BehavioralDecider,
    create_behavior_from_traits,
    get_behavior_preset
)

from .belief_system import (
    DecayConfig
)

# V3 Integration
from .v3_integration import (
    enhance_agent,
    enhance_prompt,
    record_response,
    update_emotional_state,
    decide_action,
    apply_belief_plasticity,
    check_response_variety,
    apply_group_emotional_dynamics,
    V3AgentMixin
)

__all__ = [
    # Identity
    "CoreValue",
    "DefiningMemory",
    "PersonalityTraits",
    "AgentIdentity",
    "create_identity",
    
    # Memory
    "MemoryType",
    "MemoryImportance",
    "Memory",
    "LongTermMemory",
    "store_event_memory",
    
    # Prompts
    "PromptContext",
    "ImmersivePromptBuilder",
    "create_prompt_context",
    
    # Runtime
    "AgentState",
    "AgentConfig",
    "UniversalAgent",
    "create_agent",
    
    # Beliefs
    "BeliefType",
    "EvidenceStrength",
    "Evidence",
    "Belief",
    "BeliefUpdate",
    "BeliefSystem",
    "create_belief_from_core_value",
    "belief_strength_category",
    
    # Persuasion
    "PersuasionStrategy",
    "ArgumentStrength",
    "Argument",
    "PersuasionAttempt",
    "PersuasionProfile",
    "PersuasionEngine",
    "create_persuasion_profile_from_personality",
    "apply_personality_to_persuasion_engine",
    "calculate_persuasion_effectiveness_by_personality",
    "calculate_persuasion_resistance_by_personality",
    
    # Decision
    "DecisionType",
    "DecisionPriority",
    "DecisionOutcome",
    "DecisionFactor",
    "ReasoningStep",
    "Decision",
    "DecisionEngine",
    "create_verdict_decision",
    "create_action_decision",
    
    # Context
    "ContextType",
    "Utterance",
    "KeyPoint",
    "Turn",
    "ContextManager",
    "extract_keywords",
    "extract_topics",
    
    # Proposal
    "ProposalType",
    "ProposalStatus",
    "Proposal",
    "ProposalHandler",
    "create_verdict_proposal",
    "tally_votes",
    
    # V3 Architecture
    "EmotionalTone",
    "EmotionalState",
    "EmotionalEvent",
    "apply_group_contagion",
    "calculate_group_mood",
    
    "ResponseRecord",
    "ResponseHistory",
    "generate_variety_prompt_modifier",
    "check_response_quality",
    
    "CommunicationStyle",
    "inject_style_into_prompt",
    "create_style_from_traits",
    "get_style_preset",
    
    "Utterance",
    "ConversationMemory",
    
    "BehavioralTraits",
    "BehavioralDecider",
    "create_behavior_from_traits",
    "get_behavior_preset",
    
    "DecayConfig",
    
    # V3 Integration
    "enhance_agent",
    "enhance_prompt",
    "record_response",
    "update_emotional_state",
    "decide_action",
    "apply_belief_plasticity",
    "check_response_variety",
    "apply_group_emotional_dynamics",
    "V3AgentMixin"
]