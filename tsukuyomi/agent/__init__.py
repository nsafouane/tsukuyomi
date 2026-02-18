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
    "tally_votes"
]