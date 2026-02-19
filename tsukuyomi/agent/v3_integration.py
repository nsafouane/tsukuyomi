"""
V3 Architecture Integration
===========================

Integration helpers for using V3 architecture components with existing
experiment code. This module provides drop-in enhancements for the
run_oracle_experiment.py without requiring major refactoring.

Usage:
    from tsukuyomi.agent.v3_integration import enhance_agent
    
    # Enhance an existing agent with V3 capabilities
    enhance_agent(agent, profile)
    
    # The agent will now have:
    # - emotional_state: EmotionalState
    # - response_history: ResponseHistory
    # - conversation_memory: ConversationMemory
    # - behavioral_traits: BehavioralTraits
    # - communication_style: CommunicationStyle
"""

from typing import Dict, Any, Optional
from .emotional_state import EmotionalState, EmotionalTone, apply_group_contagion
from .conversation import ResponseHistory, ResponseRecord, check_response_quality
from .personality import CommunicationStyle, inject_style_into_prompt, create_style_from_traits
from .memory import ConversationMemory, Utterance
from .behavior import BehavioralTraits, BehavioralDecider, create_behavior_from_traits
from .belief_system import BeliefSystem, DecayConfig
import logging

logger = logging.getLogger("V3Integration")


def enhance_agent(agent: Any, profile: Dict) -> Dict[str, Any]:
    """
    Enhance an agent with V3 architecture components.
    
    This function creates and attaches V3 components to an agent
    based on their profile. It returns a dict of components that
    can be attached to the agent.
    
    Args:
        agent: The agent object to enhance
        profile: Agent profile dict with personality, traits, etc.
    
    Returns:
        Dict of V3 components to attach to agent
    """
    components = {}
    
    # Extract personality traits
    big_five = profile.get("personality", {}).get("big_five", {})
    traits = profile.get("personality", {}).get("traits", {})
    role = profile.get("role", "juror")
    
    # Create emotional state
    neuroticism = big_five.get("neuroticism", 0.5)
    extraversion = big_five.get("extraversion", 0.5)
    
    components["emotional_state"] = EmotionalState(
        pleasure=0.0,  # Start neutral
        arousal=extraversion * 0.3 - 0.15,  # Slight arousal based on extraversion
        dominance=big_five.get("agreeableness", 0.5) * -0.2 + 0.1,  # Lower for agreeable
        susceptibility=0.3 + neuroticism * 0.3,  # Neurotic = more susceptible
        expressiveness=0.3 + extraversion * 0.4  # Extraverted = more expressive
    )
    
    # Create response history
    components["response_history"] = ResponseHistory(
        max_history=10,
        repetition_threshold=3
    )
    
    # Create conversation memory
    components["conversation_memory"] = ConversationMemory(
        max_utterances=50
    )
    
    # Create behavioral traits
    components["behavioral_traits"] = create_behavior_from_traits(big_five, role)
    
    # Create communication style
    components["communication_style"] = create_style_from_traits(big_five, role)
    
    # Create behavioral decider
    components["behavioral_decider"] = BehavioralDecider(components["behavioral_traits"])
    
    logger.info(f"Enhanced agent with V3 components: {list(components.keys())}")
    
    return components


def enhance_prompt(
    base_prompt: str,
    base_system_prompt: str,
    emotional_state: Optional[EmotionalState] = None,
    response_history: Optional[ResponseHistory] = None,
    communication_style: Optional[CommunicationStyle] = None,
    conversation_memory: Optional[ConversationMemory] = None
) -> tuple:
    """
    Enhance prompts with V3 architecture context.
    
    This function takes base prompts and enhances them with:
    - Emotional state context
    - Response variety warnings
    - Communication style guidelines
    - Personal narrative context
    
    Args:
        base_prompt: The user prompt
        base_system_prompt: The system prompt
        emotional_state: Optional emotional state
        response_history: Optional response history
        communication_style: Optional communication style
        conversation_memory: Optional conversation memory
    
    Returns:
        Tuple of (enhanced_prompt, enhanced_system_prompt)
    """
    enhanced_prompt = base_prompt
    enhanced_system = base_system_prompt
    
    # Apply emotional state to prompt
    if emotional_state:
        enhanced_system = emotional_state.apply_to_prompt(enhanced_system)
    
    # Apply communication style
    if communication_style:
        enhanced_system = inject_style_into_prompt(
            enhanced_system,
            communication_style,
            response_history
        )
    
    # Add conversation memory context
    if conversation_memory and len(conversation_memory.utterances) > 0:
        narrative = conversation_memory.get_personal_narrative()
        enhanced_prompt = f"{narrative}\n\n{enhanced_prompt}"
    
    return enhanced_prompt, enhanced_system


def record_response(
    agent: Any,
    tick: int,
    content: str,
    prompt_type: str,
    tone: str = "neutral"
):
    """
    Record a response in the agent's V3 tracking systems.
    
    Args:
        agent: Agent with V3 components
        tick: Current tick
        content: Response content
        prompt_type: Type of prompt used
        tone: Emotional tone of response
    """
    # Record in response history
    if hasattr(agent, 'response_history') and agent.response_history:
        record = ResponseRecord(
            tick=tick,
            content=content,
            prompt_type=prompt_type,
            tone=tone,
            word_count=len(content.split())
        )
        agent.response_history.add(record)
    
    # Record in conversation memory
    if hasattr(agent, 'conversation_memory') and agent.conversation_memory:
        utterance = Utterance(
            tick=tick,
            content=content,
            tone=tone
        )
        agent.conversation_memory.add(utterance)


def update_emotional_state(
    agent: Any,
    event_type: str,
    intensity: float = 0.1,
    tick: int = 0,
    source_agent: Optional[Any] = None
):
    """
    Update agent's emotional state based on event.
    
    Args:
        agent: Agent with V3 components
        event_type: Type of emotional event
        intensity: Event intensity (0-1)
        tick: Current tick
        source_agent: Optional source agent for contagion
    """
    if not hasattr(agent, 'emotional_state') or not agent.emotional_state:
        return
    
    source_emotion = None
    if source_agent and hasattr(source_agent, 'emotional_state'):
        source_emotion = source_agent.emotional_state
    
    agent.emotional_state.update(
        event_type=event_type,
        intensity=intensity,
        tick=tick,
        source_emotion=source_emotion
    )


def decide_action(
    agent: Any,
    context: Dict
) -> Dict:
    """
    Decide what action an agent should take.
    
    Args:
        agent: Agent with V3 components
        context: Decision context dict
    
    Returns:
        Action decision dict
    """
    if not hasattr(agent, 'behavioral_decider') or not agent.behavioral_decider:
        return {"action": "respond"}  # Default
    
    return agent.behavioral_decider.decide_action(context)


def apply_belief_plasticity(
    belief_system: BeliefSystem,
    tick: int,
    context: Optional[Dict] = None
) -> Dict[str, float]:
    """
    Apply V3 belief plasticity features.
    
    This applies:
    - Exponential decay
    - Perturbation of saturated beliefs
    
    Args:
        belief_system: The belief system to update
        tick: Current tick
        context: Optional context for plasticity calculation
    
    Returns:
        Dict of belief_id -> new_confidence for changed beliefs
    """
    config = DecayConfig()
    changes = {}
    
    # Apply exponential decay
    decay_changes = belief_system.decay_beliefs(tick, config)
    changes.update(decay_changes)
    
    # Apply perturbation
    perturb_changes = belief_system.perturb_saturated_beliefs(tick, config)
    changes.update(perturb_changes)
    
    return changes


def check_response_variety(
    agent: Any,
    proposed_content: str
) -> Dict:
    """
    Check if a proposed response meets variety standards.
    
    Args:
        agent: Agent with response history
        proposed_content: Proposed response content
    
    Returns:
        Quality check result dict
    """
    if not hasattr(agent, 'response_history') or not agent.response_history:
        return {"is_valid": True, "issues": []}
    
    return check_response_quality(proposed_content, agent.response_history)


# ========================
# Batch Operations
# ========================

def apply_group_emotional_dynamics(
    agents: list,
    tick: int,
    proximity_matrix: Optional[Dict] = None
):
    """
    Apply emotional dynamics across a group of agents.
    
    This applies emotional contagion and updates group mood.
    
    Args:
        agents: List of agents with emotional_state
        tick: Current tick
        proximity_matrix: Optional proximity matrix for contagion
    
    Returns:
        Group mood dict
    """
    from .emotional_state import calculate_group_mood
    
    # Apply decay to all agents
    for agent in agents:
        if hasattr(agent, 'emotional_state') and agent.emotional_state:
            agent.emotional_state.decay(tick)
    
    # Apply contagion if proximity matrix provided
    if proximity_matrix:
        # Build agent list for contagion
        agent_list = [
            {
                "id": getattr(agent, 'agent_id', str(id(agent))),
                "emotional_state": getattr(agent, 'emotional_state', None)
            }
            for agent in agents
            if hasattr(agent, 'emotional_state')
        ]
        
        apply_group_contagion(agent_list, proximity_matrix, tick)
    
    # Calculate group mood
    agent_list = [
        {
            "id": getattr(agent, 'agent_id', str(id(agent))),
            "emotional_state": getattr(agent, 'emotional_state', None)
        }
        for agent in agents
        if hasattr(agent, 'emotional_state')
    ]
    
    return calculate_group_mood(agent_list)


# ========================
# Integration Class
# ========================

class V3AgentMixin:
    """
    Mixin class for adding V3 capabilities to agents.
    
    Usage:
        class EnhancedAgent(V3AgentMixin, OriginalAgent):
            pass
    """
    
    def init_v3(self, profile: Dict):
        """Initialize V3 components."""
        components = enhance_agent(self, profile)
        
        self.emotional_state = components["emotional_state"]
        self.response_history = components["response_history"]
        self.conversation_memory = components["conversation_memory"]
        self.behavioral_traits = components["behavioral_traits"]
        self.communication_style = components["communication_style"]
        self.behavioral_decider = components["behavioral_decider"]
    
    def enhance_prompt_v3(self, prompt: str, system_prompt: str) -> tuple:
        """Enhance prompts with V3 context."""
        return enhance_prompt(
            prompt,
            system_prompt,
            self.emotional_state if hasattr(self, 'emotional_state') else None,
            self.response_history if hasattr(self, 'response_history') else None,
            self.communication_style if hasattr(self, 'communication_style') else None,
            self.conversation_memory if hasattr(self, 'conversation_memory') else None
        )
    
    def record_response_v3(self, tick: int, content: str, prompt_type: str, tone: str = "neutral"):
        """Record response in V3 systems."""
        record_response(self, tick, content, prompt_type, tone)
    
    def update_emotion_v3(self, event_type: str, intensity: float = 0.1, tick: int = 0, source=None):
        """Update emotional state."""
        update_emotional_state(self, event_type, intensity, tick, source)
    
    def decide_action_v3(self, context: Dict) -> Dict:
        """Decide action using V3 behavioral system."""
        return decide_action(self, context)
