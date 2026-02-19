"""
Behavioral Diversity System
===========================

Defines agent behavioral traits and decision-making for social interactions.
This is a GENERAL system applicable to any social simulation.

Location: tsukuyomi/agent/behavior.py
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import random
import logging

logger = logging.getLogger("BehavioralTraits")


@dataclass
class BehavioralTraits:
    """
    Defines how an agent behaves in social situations.
    
    These are stable traits that affect decision-making.
    Applicable to ANY simulation with social interactions:
    - Jury: How active in deliberation, leadership style
    - Marketplace: Negotiation style, responsiveness
    - Politics: Coalition building, debate style
    - Social: Conversation patterns, relationship building
    """
    
    # Social behavior (Big Five derived)
    introversion: float = 0.5  # 0=extrovert (talks a lot), 1=introvert (quiet)
    dominance: float = 0.5  # 0=follower, 1=leader
    agreeableness: float = 0.5  # 0=challenging, 1=accommodating
    
    # Conversation behavior
    speak_probability: float = 0.3  # Base chance to speak per turn
    interrupt_probability: float = 0.1  # Chance to interrupt
    topic_initiation_prob: float = 0.2  # Chance to start new topic
    
    # Responsiveness
    response_latency: float = 0.5  # 0=instant, 1=delayed (not currently used)
    reply_probability: float = 0.7  # Chance to respond when directly addressed
    
    # Attention
    attention_span: float = 0.5  # How long to focus on one topic (0-1)
    distractibility: float = 0.3  # Chance to shift attention spontaneously
    
    # Persistence
    stubbornness: float = 0.5  # How hard to change their mind (0-1)
    persuasibility: float = 0.5  # How easily persuaded by others (0-1)
    
    def should_speak(self, tick: int, addressing_me: bool = False) -> bool:
        """
        Determine if agent should speak in this turn.
        
        Args:
            tick: Current simulation tick
            addressing_me: Whether someone directly addressed this agent
        
        Returns:
            True if agent should generate a response
        """
        # If directly addressed, high chance to respond
        if addressing_me:
            return random.random() < self.reply_probability
        
        # Otherwise, use base speak probability modulated by introversion
        # Introverts speak less (higher introversion = lower probability)
        effective_prob = self.speak_probability * (1.5 - self.introversion)
        
        return random.random() < effective_prob
    
    def should_initiate_topic(
        self,
        current_topic_age: int,
        boredom_threshold: int = 50
    ) -> bool:
        """
        Determine if agent should change the subject.
        
        Args:
            current_topic_age: How long current topic has been discussed
            boredom_threshold: Ticks before agent gets bored
        
        Returns:
            True if agent should start a new topic
        """
        # If topic is fresh, rarely change
        if current_topic_age < boredom_threshold * self.attention_span:
            return False
        
        # Check distractibility - more distractible = more likely to change topic
        effective_prob = self.topic_initiation_prob * (1 + self.distractibility)
        
        return random.random() < effective_prob
    
    def should_interrupt(self, speaker_dominance: float) -> bool:
        """
        Determine if agent should interrupt the current speaker.
        
        Args:
            speaker_dominance: Dominance of current speaker (0-1)
        
        Returns:
            True if agent should interrupt
        """
        # Higher dominance agents interrupt more
        # But less likely to interrupt higher-dominance speakers
        dominance_advantage = self.dominance - speaker_dominance
        
        if dominance_advantage < -0.3:  # Speaker is much more dominant
            return False
        
        effective_prob = self.interrupt_probability * (1 + dominance_advantage)
        return random.random() < max(0, effective_prob)
    
    def get_leadership_style(self) -> str:
        """
        Get categorical leadership style based on traits.
        
        Returns:
            "leader", "follower", or "peer"
        """
        if self.dominance > 0.7:
            return "leader"
        elif self.dominance < 0.3:
            return "follower"
        else:
            return "peer"
    
    def get_conversation_role(self) -> str:
        """
        Get the agent's typical role in conversation.
        
        Returns:
            One of: "initiator", "responder", "listener", "mediator"
        """
        if self.topic_initiation_prob > 0.4:
            return "initiator"
        elif self.reply_probability > 0.8:
            return "responder"
        elif self.speak_probability < 0.2:
            return "listener"
        elif self.agreeableness > 0.7:
            return "mediator"
        else:
            return "responder"
    
    def to_dict(self) -> Dict:
        return {
            "introversion": self.introversion,
            "dominance": self.dominance,
            "agreeableness": self.agreeableness,
            "speak_probability": self.speak_probability,
            "interrupt_probability": self.interrupt_probability,
            "topic_initiation_prob": self.topic_initiation_prob,
            "reply_probability": self.reply_probability,
            "attention_span": self.attention_span,
            "distractibility": self.distractibility,
            "stubbornness": self.stubbornness,
            "persuasibility": self.persuasibility
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BehavioralTraits':
        return cls(**data)


class BehavioralDecider:
    """
    Decides agent actions based on behavioral traits and context.
    
    This is a GENERAL system that determines what actions an agent
    takes in any social simulation.
    """
    
    def __init__(self, traits: BehavioralTraits):
        self.traits = traits
        self.current_topic_age = 0
        self.silence_counter = 0
        self.last_speaker: Optional[str] = None
    
    def decide_action(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Decide what the agent should do.
        
        Args:
            context: Dict with:
                - addressing_me: bool
                - last_speaker: str or None
                - topic_age: int
                - group_size: int
                - agents_present: List[str]
        
        Returns:
            Dict with 'action' and parameters:
            - "silent": {}
            - "respond": {"to": agent_id, "interrupt": bool}
            - "new_topic": {"topic": str or None}
        """
        addressing_me = context.get("addressing_me", False)
        topic_age = context.get("topic_age", 0)
        
        # Update topic age tracking
        if self.last_speaker != context.get("last_speaker"):
            self.current_topic_age = 0
        else:
            self.current_topic_age += 1
        
        # Check if should speak
        if not self.traits.should_speak(context.get("tick", 0), addressing_me):
            self.silence_counter += 1
            return {"action": "silent", "reason": "trait_probability"}
        
        self.silence_counter = 0
        
        # Check for topic change
        if self.traits.should_initiate_topic(topic_age, context.get("boredom_threshold", 50)):
            return {"action": "new_topic", "reason": "boredom"}
        
        # Default: respond to last speaker or group
        return {
            "action": "respond",
            "to": context.get("last_speaker"),
            "interrupt": self._check_interrupt(context)
        }
    
    def _check_interrupt(self, context: Dict[str, Any]) -> bool:
        """Check if should interrupt current speaker."""
        last_speaker = context.get("last_speaker")
        if not last_speaker:
            return False
        
        # Would need speaker's dominance from context
        speaker_dominance = context.get("speaker_dominance", 0.5)
        
        return self.traits.should_interrupt(speaker_dominance)
    
    def select_respond_target(
        self,
        agents_present: List[str],
        recent_interactions: Dict[str, int]
    ) -> Optional[str]:
        """
        Choose who to respond to.
        
        Args:
            agents_present: IDs of agents in the conversation
            recent_interactions: agent_id -> tick of last interaction
        
        Returns:
            Agent ID to respond to, or None for group
        """
        if not agents_present:
            return None
        
        # High-dominance agents prefer to respond to lower-dominance ones
        # This creates natural leader-follower dynamics
        
        # Simple heuristic: respond to most recent speaker or random
        if random.random() < 0.7 and recent_interactions:
            # Respond to most recent
            last = max(recent_interactions.items(), key=lambda x: x[1])
            return last[0]
        
        # Otherwise pick random (weighted by presence)
        return random.choice(agents_present) if agents_present else None
    
    def get_influence_weight(
        self,
        speaker_traits: BehavioralTraits,
        relationship_trust: float = 0.5
    ) -> float:
        """
        Calculate how much this agent is influenced by another speaker.
        
        This creates ASYMMETRIC influence - A→B ≠ B→A
        
        Args:
            speaker_traits: Traits of the speaker
            relationship_trust: Trust level with speaker (0-1)
        
        Returns:
            Influence weight (0-1)
        """
        # Base influence from persuasibility
        base = self.traits.persuasibility
        
        # Trust modifier
        trust_mod = 0.5 + relationship_trust * 0.5
        
        # Dominance: higher dominance speakers influence more
        dominance_mod = 0.7 + speaker_traits.dominance * 0.3
        
        # Agreeableness: agreeable agents are more easily influenced
        agree_mod = 0.7 + self.traits.agreeableness * 0.3
        
        # Stubbornness reduces influence
        stubborn_mod = 1.0 - self.traits.stubbornness * 0.5
        
        return base * trust_mod * dominance_mod * agree_mod * stubborn_mod
    
    def reset_topic_age(self):
        """Reset topic age counter (call when topic changes)."""
        self.current_topic_age = 0


# ========================
# Behavioral Presets
# ========================

def create_behavior_from_traits(big_five: Dict[str, float], role: Optional[str] = None) -> BehavioralTraits:
    """
    Create behavioral traits from Big Five personality.
    
    Args:
        big_five: Dict with openness, conscientiousness, extraversion,
                  agreeableness, neuroticism (0.0-1.0)
        role: Optional role hint
    
    Returns:
        BehavioralTraits configured for the personality
    """
    traits = BehavioralTraits()
    
    # Map Big Five to behavioral traits
    extraversion = big_five.get("extraversion", 0.5)
    traits.introversion = 1.0 - extraversion
    traits.speak_probability = 0.2 + extraversion * 0.4
    traits.reply_probability = 0.5 + extraversion * 0.4
    
    agreeableness = big_five.get("agreeableness", 0.5)
    traits.agreeableness = agreeableness
    traits.persuasibility = 0.3 + agreeableness * 0.4
    
    conscientiousness = big_five.get("conscientiousness", 0.5)
    traits.stubbornness = 0.3 + conscientiousness * 0.4
    traits.attention_span = 0.3 + conscientiousness * 0.4
    
    neuroticism = big_five.get("neuroticism", 0.5)
    traits.distractibility = 0.2 + neuroticism * 0.4
    
    # Role modifications
    if role:
        if role == "leader":
            traits.dominance = 0.8
            traits.speak_probability = 0.6
            traits.topic_initiation_prob = 0.5
        elif role == "skeptic":
            traits.persuasibility = 0.3
            traits.stubbornness = 0.8
            traits.agreeableness = 0.4
        elif role == "diplomat":
            traits.agreeableness = 0.8
            traits.persuasibility = 0.6
        elif role == "listener":
            traits.speak_probability = 0.15
            traits.reply_probability = 0.8
        elif role == "agitator":
            traits.dominance = 0.7
            traits.interrupt_probability = 0.3
            traits.topic_initiation_prob = 0.4
    
    return traits


# Preset trait configurations
BEHAVIOR_PRESETS = {
    "leader": BehavioralTraits(
        dominance=0.8,
        speak_probability=0.6,
        topic_initiation_prob=0.5,
        interrupt_probability=0.2,
        persuasibility=0.4,
        stubbornness=0.5
    ),
    "follower": BehavioralTraits(
        dominance=0.2,
        speak_probability=0.3,
        reply_probability=0.8,
        persuasibility=0.7,
        stubbornness=0.3
    ),
    "skeptic": BehavioralTraits(
        dominance=0.5,
        speak_probability=0.4,
        persuasibility=0.2,
        stubbornness=0.8,
        interrupt_probability=0.2
    ),
    "listener": BehavioralTraits(
        introversion=0.8,
        speak_probability=0.15,
        reply_probability=0.6,
        distractibility=0.2
    ),
    "agitator": BehavioralTraits(
        dominance=0.7,
        speak_probability=0.5,
        interrupt_probability=0.3,
        topic_initiation_prob=0.4,
        persuasibility=0.5
    ),
    "mediator": BehavioralTraits(
        agreeableness=0.8,
        dominance=0.4,
        speak_probability=0.35,
        reply_probability=0.8,
        persuasibility=0.6
    )
}


def get_behavior_preset(name: str) -> Optional[BehavioralTraits]:
    """Get a predefined behavioral preset by name."""
    return BEHAVIOR_PRESETS.get(name.lower())
