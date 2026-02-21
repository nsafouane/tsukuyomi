import uuid
"""
Persuasion Dynamics Engine
==========================

Models how agents persuade and are persuaded by others.

Key Features:
- Persuasion strategies (logic, emotion, authority, social proof)
- Resistance based on personality and belief strength
- Argument tracking and effectiveness
- Multi-agent persuasion networks
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Set, Tuple
from datetime import datetime
import json
import math
import random

# Saturation constants (synced with belief_system)
ENTRENCHED_THRESHOLD = 0.85
MAX_CONFIDENCE = 0.95


class PersuasionStrategy(Enum):
    """Types of persuasion strategies."""
    LOGIC = "logic"                # Facts, evidence, reasoning
    EMOTION = "emotion"            # Appeal to feelings
    AUTHORITY = "authority"        # Appeal to expertise
    SOCIAL_PROOF = "social_proof"  # Everyone else believes X
    RECIPROCITY = "reciprocity"    # I helped you, now help me
    SCARCITY = "scarcity"         # Limited time/opportunity
    COMMITMENT = "commitment"      # You said X before
    LIKING = "liking"             # I like you, so trust me


class ArgumentStrength(Enum):
    """Strength categories for arguments."""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class Argument:
    """
    A persuasive argument made by an agent.
    """
    id: str = field(default_factory=lambda: f"arg_{str(uuid.uuid4())}")
    claim: str = ""                          # What's being argued
    strategy: PersuasionStrategy = PersuasionStrategy.LOGIC
    evidence_ids: List[str] = field(default_factory=list)  # Linked evidence
    target_belief_id: Optional[str] = None   # Belief trying to change
    speaker_id: str = ""
    tick: int = 0
    
    # Effectiveness metrics
    strength_score: float = 0.5              # How strong is the argument
    confidence: float = 0.5                  # Speaker's confidence
    
    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "claim": self.claim,
            "strategy": self.strategy.value,
            "evidence_ids": self.evidence_ids,
            "target_belief_id": self.target_belief_id,
            "speaker_id": self.speaker_id,
            "tick": self.tick,
            "strength_score": self.strength_score,
            "confidence": self.confidence,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Argument":
        return cls(
            id=data["id"],
            claim=data["claim"],
            strategy=PersuasionStrategy(data["strategy"]),
            evidence_ids=data.get("evidence_ids", []),
            target_belief_id=data.get("target_belief_id"),
            speaker_id=data["speaker_id"],
            tick=data["tick"],
            strength_score=data.get("strength_score", 0.5),
            confidence=data.get("confidence", 0.5),
            context=data.get("context", {})
        )


@dataclass
class PersuasionAttempt:
    """
    Record of a persuasion attempt between agents.
    """
    id: str = field(default_factory=lambda: f"pa_{str(uuid.uuid4())}")
    arg_id: str = ""
    speaker_id: str = ""
    listener_id: str = ""
    tick: int = 0
    
    # Before/After state
    initial_confidence: float = 0.5
    final_confidence: float = 0.5
    change: float = 0.0
    
    # Why it worked/didn't
    resistance_factors: List[str] = field(default_factory=list)
    effectiveness_factors: List[str] = field(default_factory=list)
    
    @property
    def was_effective(self) -> bool:
        return abs(self.change) > 0.05
    
    @property
    def direction(self) -> str:
        if self.change > 0.01:
            return "strengthened"
        elif self.change < -0.01:
            return "weakened"
        return "unchanged"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "arg_id": self.arg_id,
            "speaker_id": self.speaker_id,
            "listener_id": self.listener_id,
            "tick": self.tick,
            "initial_confidence": self.initial_confidence,
            "final_confidence": self.final_confidence,
            "change": self.change,
            "resistance_factors": self.resistance_factors,
            "effectiveness_factors": self.effectiveness_factors
        }


@dataclass
class PersuasionProfile:
    """
    An agent's persuasion tendencies and resistances.
    """
    agent_id: str = ""
    
    # Persuasion tendencies (how they persuade)
    strategy_preferences: Dict[PersuasionStrategy, float] = field(default_factory=lambda: {
        PersuasionStrategy.LOGIC: 0.5,
        PersuasionStrategy.EMOTION: 0.5,
        PersuasionStrategy.AUTHORITY: 0.5,
        PersuasionStrategy.SOCIAL_PROOF: 0.5,
        PersuasionStrategy.RECIPROCITY: 0.5,
        PersuasionStrategy.SCARCITY: 0.5,
        PersuasionStrategy.COMMITMENT: 0.5,
        PersuasionStrategy.LIKING: 0.5,
    })
    
    # Resistance (how hard to persuade)
    base_resistance: float = 0.5             # General stubbornness
    strategy_resistance: Dict[PersuasionStrategy, float] = field(default_factory=lambda: {
        PersuasionStrategy.LOGIC: 0.5,
        PersuasionStrategy.EMOTION: 0.5,
        PersuasionStrategy.AUTHORITY: 0.5,
        PersuasionStrategy.SOCIAL_PROOF: 0.5,
        PersuasionStrategy.RECIPROCITY: 0.5,
        PersuasionStrategy.SCARCITY: 0.5,
        PersuasionStrategy.COMMITMENT: 0.5,
        PersuasionStrategy.LIKING: 0.5,
    })
    
    # History
    arguments_made: List[str] = field(default_factory=list)
    arguments_heard: List[str] = field(default_factory=list)
    successful_persuasions: int = 0
    failed_persuasions: int = 0
    times_persuaded: int = 0
    times_resisted: int = 0
    
    @property
    def persuasion_success_rate(self) -> float:
        total = self.successful_persuasions + self.failed_persuasions
        if total == 0:
            return 0.5
        return self.successful_persuasions / total
    
    @property
    def resistance_rate(self) -> float:
        total = self.times_persuaded + self.times_resisted
        if total == 0:
            return 0.5
        return self.times_resisted / total
    
    def get_preferred_strategy(self) -> PersuasionStrategy:
        """Get most preferred strategy."""
        return max(self.strategy_preferences.items(), key=lambda x: x[1])[0]
    
    def get_weakest_resistance(self) -> PersuasionStrategy:
        """Get strategy with lowest resistance."""
        return min(self.strategy_resistance.items(), key=lambda x: x[1])[0]
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "strategy_preferences": {k.value: v for k, v in self.strategy_preferences.items()},
            "base_resistance": self.base_resistance,
            "strategy_resistance": {k.value: v for k, v in self.strategy_resistance.items()},
            "arguments_made": self.arguments_made,
            "arguments_heard": self.arguments_heard,
            "successful_persuasions": self.successful_persuasions,
            "failed_persuasions": self.failed_persuasions,
            "times_persuaded": self.times_persuaded,
            "times_resisted": self.times_resisted
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PersuasionProfile":
        profile = cls(agent_id=data["agent_id"])
        profile.strategy_preferences = {
            PersuasionStrategy(k): v for k, v in data.get("strategy_preferences", {}).items()
        }
        profile.base_resistance = data.get("base_resistance", 0.5)
        profile.strategy_resistance = {
            PersuasionStrategy(k): v for k, v in data.get("strategy_resistance", {}).items()
        }
        profile.arguments_made = data.get("arguments_made", [])
        profile.arguments_heard = data.get("arguments_heard", [])
        profile.successful_persuasions = data.get("successful_persuasions", 0)
        profile.failed_persuasions = data.get("failed_persuasions", 0)
        profile.times_persuaded = data.get("times_persuaded", 0)
        profile.times_resisted = data.get("times_resisted", 0)
        return profile


class PersuasionEngine:
    """
    Main persuasion engine for modeling persuasive dynamics.
    """
    
    def __init__(
        self,
        agent_id: str,
        profile: Optional[PersuasionProfile] = None,
        personality: Optional[Dict[str, float]] = None
    ):
        self.agent_id = agent_id
        self.profile = profile or PersuasionProfile(agent_id=agent_id)
        self.personality = personality or {}
        
        # Argument tracking
        self.arguments: Dict[str, Argument] = {}
        self.attempts: Dict[str, PersuasionAttempt] = []
        
        # Relationship modifiers (trust, liking, respect)
        self.relationship_modifiers: Dict[str, float] = {}
        
        # Configuration
        self.min_change = 0.01
        self.max_change = 0.3
        
        # Apply personality to profile if provided
        if self.personality:
            apply_personality_to_persuasion_engine(self, self.personality)
    
    # ==================== ARGUMENT CREATION ====================
    
    def create_argument(
        self,
        claim: str,
        strategy: PersuasionStrategy,
        target_belief_id: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        strength_score: Optional[float] = None,
        confidence: float = 0.5,
        tick: int = 0,
        context: Optional[Dict] = None
    ) -> Argument:
        """
        Create a persuasive argument.
        """
        # Auto-calculate strength if not provided
        if strength_score is None:
            strength_score = self._calculate_arg_strength(
                strategy=strategy,
                evidence_ids=evidence_ids or [],
                confidence=confidence
            )
        
        arg = Argument(
            claim=claim,
            strategy=strategy,
            target_belief_id=target_belief_id,
            evidence_ids=evidence_ids or [],
            speaker_id=self.agent_id,
            tick=tick,
            strength_score=strength_score,
            confidence=confidence,
            context=context or {}
        )
        
        self.arguments[arg.id] = arg
        self.profile.arguments_made.append(arg.id)
        
        return arg
    
    def _calculate_arg_strength(
        self,
        strategy: PersuasionStrategy,
        evidence_ids: List[str],
        confidence: float
    ) -> float:
        """Calculate argument strength from components."""
        # Base from strategy preference
        strategy_bonus = self.profile.strategy_preferences.get(strategy, 0.5)
        
        # Evidence count bonus
        evidence_bonus = min(0.2, len(evidence_ids) * 0.05)
        
        # Combine
        strength = (confidence * 0.5 + strategy_bonus * 0.3 + evidence_bonus + 0.2)
        
        return min(1.0, max(0.0, strength))
    
    # ==================== PERSUASION CALCULATION ====================
    
    def calculate_persuasion_effect(
        self,
        argument: Argument,
        listener_id: str,
        belief_confidence: float,
        belief_is_core: bool = False,
        existing_evidence_count: int = 0,
        tick: int = 0
    ) -> Tuple[float, PersuasionAttempt]:
        """
        Calculate how much an argument persuades.
        
        Returns (new_confidence, attempt_record)
        """
        attempt = PersuasionAttempt(
            arg_id=argument.id,
            speaker_id=argument.speaker_id,
            listener_id=listener_id,
            tick=tick,
            initial_confidence=belief_confidence
        )
        
        # Track that we heard this
        self.profile.arguments_heard.append(argument.id)
        
        # Calculate resistance
        resistance = self._calculate_resistance(
            strategy=argument.strategy,
            belief_confidence=belief_confidence,
            belief_is_core=belief_is_core,
            existing_evidence_count=existing_evidence_count,
            speaker_id=argument.speaker_id
        )
        
        attempt.resistance_factors = self._get_resistance_factors(
            belief_is_core=belief_is_core,
            belief_confidence=belief_confidence,
            strategy=argument.strategy
        )
        
        # Calculate effectiveness
        effectiveness = self._calculate_effectiveness(
            argument=argument,
            resistance=resistance,
            relationship=self.relationship_modifiers.get(argument.speaker_id, 0.5)
        )
        
        attempt.effectiveness_factors = self._get_effectiveness_factors(
            arg_strength=argument.strength_score,
            strategy=argument.strategy,
            relationship=self.relationship_modifiers.get(argument.speaker_id, 0.5)
        )
        
        # Calculate change
        potential_change = effectiveness * self.max_change
        actual_change = potential_change * (1 - resistance)
        
        # Apply minimum threshold
        if abs(actual_change) < self.min_change:
            actual_change = 0.0
        
        # Calculate new confidence
        new_confidence = belief_confidence + actual_change
        new_confidence = max(0.0, min(1.0, new_confidence))
        
        # Record result
        attempt.final_confidence = new_confidence
        attempt.change = new_confidence - belief_confidence
        
        self.attempts.append(attempt)
        
        # Update profile
        if attempt.was_effective:
            self.profile.times_persuaded += 1
        else:
            self.profile.times_resisted += 1
        
        return new_confidence, attempt
    
    def _calculate_resistance(
        self,
        strategy: PersuasionStrategy,
        belief_confidence: float,
        belief_is_core: bool,
        existing_evidence_count: int,
        speaker_id: str
    ) -> float:
        """
        Calculate resistance to persuasion.
        
        Higher = harder to persuade.
        """
        # Base resistance
        base = self.profile.base_resistance
        
        # Strategy-specific resistance
        strategy_res = self.profile.strategy_resistance.get(strategy, 0.5)
        
        # Belief strength resistance
        strength_res = abs(belief_confidence - 0.5) * 0.4  # Max 0.2
        
        # SATURATION RESISTANCE: Much harder to change entrenched beliefs
        if belief_confidence > ENTRENCHED_THRESHOLD:
            # Exponential resistance growth as confidence approaches max
            saturation = (belief_confidence - ENTRENCHED_THRESHOLD) / (MAX_CONFIDENCE - ENTRENCHED_THRESHOLD)
            saturation_res = saturation * 0.6  # Up to 0.6 extra resistance
        else:
            saturation_res = 0.0
        
        # Core value resistance
        core_res = 0.3 if belief_is_core else 0.0
        
        # Evidence count resistance (more evidence = harder to sway)
        evidence_res = min(0.2, existing_evidence_count * 0.02)
        
        # Combine - strategy resistance from personality has SIGNIFICANT weight
        # This ensures personality has a strong impact on persuasion outcomes
        total_resistance = (
            base * 0.15 +
            strategy_res * 0.5 +  # Increased from 0.25 - personality matters!
            strength_res +
            saturation_res +  # NEW: Saturation resistance
            core_res +
            evidence_res
        )
        
        return min(1.0, max(0.0, total_resistance))
    
    def _calculate_effectiveness(
        self,
        argument: Argument,
        resistance: float,
        relationship: float
    ) -> float:
        """
        Calculate persuasion effectiveness.
        
        Higher = more persuasive.
        """
        # Argument strength
        arg_strength = argument.strength_score
        
        # Speaker confidence
        confidence = argument.confidence
        
        # Relationship bonus
        rel_bonus = (relationship - 0.5) * 0.3  # -0.15 to +0.15
        
        # Phase 4: Personality Susceptibility
        personality_susceptibility = 1.0
        if self.personality:
            personality_susceptibility = calculate_persuasion_effectiveness_by_personality(
                self.personality, argument.strategy
            )
        
        # Combine
        effectiveness = (
            arg_strength * 0.3 +
            confidence * 0.2 +
            personality_susceptibility * 0.3 +
            0.2 +
            rel_bonus
        )
        
        # Apply resistance
        effectiveness *= (1 - resistance * 0.5)
        
        return min(1.0, max(0.0, effectiveness))
    
    def _get_resistance_factors(
        self,
        belief_is_core: bool,
        belief_confidence: float,
        strategy: PersuasionStrategy
    ) -> List[str]:
        """Get list of resistance factors."""
        factors = []
        
        if belief_is_core:
            factors.append("core_value")
        if belief_confidence > ENTRENCHED_THRESHOLD:
            factors.append("entrenched_belief")  # NEW: Saturation indicator
        if belief_confidence > 0.8:
            factors.append("strong_belief")
        if belief_confidence < 0.2:
            factors.append("weak_belief")  # Hard to push lower
        
        strategy_res = self.profile.strategy_resistance.get(strategy, 0.5)
        if strategy_res > 0.7:
            factors.append(f"resists_{strategy.value}")
        
        if self.profile.base_resistance > 0.7:
            factors.append("stubborn_personality")
        
        return factors
    
    def _get_effectiveness_factors(
        self,
        arg_strength: float,
        strategy: PersuasionStrategy,
        relationship: float
    ) -> List[str]:
        """Get list of effectiveness factors."""
        factors = []
        
        if arg_strength > 0.7:
            factors.append("strong_argument")
        if arg_strength < 0.3:
            factors.append("weak_argument")
        
        pref = self.profile.strategy_preferences.get(strategy, 0.5)
        if pref > 0.7:
            factors.append(f"prefers_{strategy.value}")
        
        if relationship > 0.7:
            factors.append("high_trust_speaker")
        if relationship < 0.3:
            factors.append("low_trust_speaker")
        
        return factors
    
    # ==================== STRATEGY SELECTION ====================

    def select_best_strategy(
        self,
        listener_id: str,
        belief_confidence: float,
        available_evidence: int = 0,
        relationship: float = 0.5
    ) -> PersuasionStrategy:
        """
        Select the best persuasion strategy for this situation.
        """
        scores = {}
        
        for strategy in PersuasionStrategy:
            # Preference score
            pref = self.profile.strategy_preferences.get(strategy, 0.5)
            
            # Effectiveness prediction
            resistance = self.profile.strategy_resistance.get(strategy, 0.5)
            
            # Context bonus
            context_bonus = 0.0
            if strategy == PersuasionStrategy.LOGIC and available_evidence > 2:
                context_bonus = 0.2
            if strategy == PersuasionStrategy.SOCIAL_PROOF and relationship < 0.3:
                context_bonus = 0.1
            if strategy == PersuasionStrategy.EMOTION and belief_confidence > 0.7:
                context_bonus = 0.1
            if strategy == PersuasionStrategy.AUTHORITY and relationship > 0.7:
                context_bonus = 0.15
            
            scores[strategy] = pref * (1 - resistance) + context_bonus
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    # ==================== RELATIONSHIP MANAGEMENT ====================
    
    def update_relationship(self, other_id: str, delta: float):
        """Update relationship modifier with another agent."""
        current = self.relationship_modifiers.get(other_id, 0.5)
        new_value = max(-1.0, min(1.0, current + delta))
        self.relationship_modifiers[other_id] = new_value
    
    def get_relationship(self, other_id: str) -> float:
        """Get relationship score with another agent."""
        return self.relationship_modifiers.get(other_id, 0.5)
    
    # ==================== STATISTICS ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get persuasion statistics."""
        return {
            "agent_id": self.agent_id,
            "arguments_made": len(self.profile.arguments_made),
            "arguments_heard": len(self.profile.arguments_heard),
            "persuasion_success_rate": self.profile.persuasion_success_rate,
            "resistance_rate": self.profile.resistance_rate,
            "preferred_strategy": self.profile.get_preferred_strategy().value,
            "weakest_resistance": self.profile.get_weakest_resistance().value,
            "base_resistance": self.profile.base_resistance,
            "total_attempts": len(self.attempts),
            "effective_attempts": sum(1 for a in self.attempts if a.was_effective)
        }
    
    def get_argument_effectiveness_report(self) -> str:
        """Generate a report on argument effectiveness."""
        lines = [
            f"PERSUASION REPORT: {self.agent_id}",
            "=" * 40,
            "",
            f"Arguments Made: {len(self.profile.arguments_made)}",
            f"Arguments Heard: {len(self.profile.arguments_heard)}",
            f"Success Rate: {self.profile.persuasion_success_rate:.0%}",
            f"Resistance Rate: {self.profile.resistance_rate:.0%}",
            "",
            "STRATEGY PREFERENCES:",
        ]
        
        for strategy, pref in sorted(
            self.profile.strategy_preferences.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            lines.append(f"  {strategy.value}: {pref:.0%}")
        
        lines.extend([
            "",
            "STRATEGY RESISTANCES:",
        ])
        
        for strategy, res in sorted(
            self.profile.strategy_resistance.items(),
            key=lambda x: x[1]
        ):
            lines.append(f"  {strategy.value}: {res:.0%}")
        
        return "\n".join(lines)
    
    # ==================== SERIALIZATION ====================
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "profile": self.profile.to_dict(),
            "arguments": {aid: arg.to_dict() for aid, arg in self.arguments.items()},
            "attempts": [a.to_dict() for a in self.attempts],
            "relationship_modifiers": self.relationship_modifiers
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PersuasionEngine":
        engine = cls(
            agent_id=data["agent_id"],
            profile=PersuasionProfile.from_dict(data["profile"])
        )
        engine.arguments = {
            aid: Argument.from_dict(arg) for aid, arg in data.get("arguments", {}).items()
        }
        engine.attempts = [
            PersuasionAttempt(**a) for a in data.get("attempts", [])
        ]
        engine.relationship_modifiers = data.get("relationship_modifiers", {})
        return engine


# ==================== HELPER FUNCTIONS ====================

def create_persuasion_profile_from_personality(
    personality_traits: Dict[str, float]
) -> PersuasionProfile:
    """
    Create a persuasion profile from personality traits.
    
    Args:
        personality_traits: Dict with keys like "agreeableness", "conscientiousness", etc.
    
    Returns:
        PersuasionProfile configured based on personality
    """
    profile = PersuasionProfile()
    
    # Base resistance from emotional stability
    neuroticism = personality_traits.get("neuroticism", 0.5)
    agreeableness = personality_traits.get("agreeableness", 0.5)
    conscientiousness = personality_traits.get("conscientiousness", 0.5)
    
    # High neuroticism = more resistant (defensive)
    # High agreeableness = less resistant (cooperative)
    profile.base_resistance = 0.3 + neuroticism * 0.3 - agreeableness * 0.2
    
    # Strategy preferences from personality
    openness = personality_traits.get("openness", 0.5)
    
    profile.strategy_preferences[PersuasionStrategy.LOGIC] = 0.3 + conscientiousness * 0.4
    profile.strategy_preferences[PersuasionStrategy.EMOTION] = 0.3 + neuroticism * 0.3
    profile.strategy_preferences[PersuasionStrategy.AUTHORITY] = 0.3 + (1 - openness) * 0.3
    profile.strategy_preferences[PersuasionStrategy.SOCIAL_PROOF] = 0.3 + agreeableness * 0.3
    
    # Strategy resistances
    profile.strategy_resistance[PersuasionStrategy.EMOTION] = 0.3 + conscientiousness * 0.3
    profile.strategy_resistance[PersuasionStrategy.LOGIC] = 0.3 + (1 - openness) * 0.2
    
    return profile


def argument_strength_category(strength: float) -> ArgumentStrength:
    """Categorize argument strength."""
    if strength >= 0.8:
        return ArgumentStrength.VERY_STRONG
    elif strength >= 0.6:
        return ArgumentStrength.STRONG
    elif strength >= 0.4:
        return ArgumentStrength.MODERATE
    elif strength >= 0.2:
        return ArgumentStrength.WEAK
    else:
        return ArgumentStrength.VERY_WEAK


# ==================== PERSONALITY-WEIGHTED PERSUASION ====================
# Phase 4: Personality-Weighted Argument Effectiveness
# This makes argument effectiveness vary by agent personality

# Mapping of which personality traits affect which argument types
ARGUMENT_EFFECTIVENESS_BY_PERSONALITY = {
    "logic": {
        "openness": 0.8,       # Open agents value logic more
        "conscientiousness": 0.6,
    },
    "emotion": {
        "neuroticism": 0.9,    # Neurotic agents more emotional
        "agreeableness": 0.5,
    },
    "authority": {
        "conscientiousness": 0.8,
        "openness": 0.3,       # Low openness = more deferential to authority
    },
    "social_proof": {
        "extraversion": 0.7,
        "agreeableness": 0.6,
    },
    "scarcity": {
        "conscientiousness": 0.5,
        "neuroticism": 0.7,
    },
    "liking": {
        "agreeableness": 0.8,
        "extraversion": 0.5,
    },
    "reciprocity": {
        "agreeableness": 0.7,
        "extraversion": 0.4,
    },
    "commitment": {
        "conscientiousness": 0.6,
        "openness": 0.4,
    },
}


def calculate_persuasion_effectiveness_by_personality(
    agent_personality: Dict[str, float],
    argument_strategy: PersuasionStrategy
) -> float:
    """
    Calculate how effective a specific argument type is for an agent,
    based on their personality.
    
    This is the key function that makes persuasion personality-dependent.
    
    Args:
        agent_personality: Dict with Big Five traits (0-1 scale)
        argument_strategy: The type of persuasion being used
    
    Returns:
        Effectiveness score (0-1), where higher = more susceptible
    """
    strategy_name = argument_strategy.value
    
    # Get trait weights for this strategy
    trait_weights = ARGUMENT_EFFECTIVENESS_BY_PERSONALITY.get(strategy_name, {})
    
    if not trait_weights:
        # Unknown strategy, return neutral
        return 0.5
    
    effectiveness = 0.0
    total_weight = 0.0
    
    for trait, weight in trait_weights.items():
        # Get the trait value (default to 0.5 if not present)
        trait_value = agent_personality.get(trait, 0.5)
        
        # Add weighted contribution
        effectiveness += trait_value * weight
        total_weight += weight
    
    # Normalize
    if total_weight > 0:
        effectiveness = effectiveness / total_weight
    
    # Scale to meaningful range (0.2 to 0.8 instead of 0 to 1)
    effectiveness = 0.2 + (effectiveness * 0.6)
    
    return effectiveness


def calculate_persuasion_resistance_by_personality(
    agent_personality: Dict[str, float],
    argument_strategy: PersuasionStrategy
) -> float:
    """
    Calculate how resistant an agent is to a specific argument type,
    based on their personality.
    
    This is the inverse of effectiveness - high resistance means
    the argument won't work well regardless of other factors.
    
    Args:
        agent_personality: Dict with Big Five traits (0-1 scale)
        argument_strategy: The type of persuasion being used
    
    Returns:
        Resistance score (0-1), where higher = more resistant
    """
    strategy_name = argument_strategy.value
    
    # Some traits naturally resist certain argument types
    resistance_factors = {
        "logic": {
            "openness": -0.8,   # High openness = much less resistant to logic
            "neuroticism": 0.4,  # Neurotic = more skeptical
        },
        "emotion": {
            "conscientiousness": 0.6,  # Conscientious = more logical, less emotional
            "neuroticism": -0.5,       # Neurotic = more emotional, less resistant
        },
        "authority": {
            "openness": 0.7,     # High openness = questioning, less deferential
            "extraversion": -0.4,  # Extraverted = more dominant, less submissive
        },
        "social_proof": {
            "agreeableness": -0.6,  # Agreeable = follows group
            "stubbornness": 0.8,     # Stubborn = resists peer pressure
        },
        "scarcity": {
            "conscientiousness": -0.4,  # Conscientious = plans ahead, fears missing out
            "cynicism": 0.6,            # Cynical = skeptical of scarcity claims
        },
    }
    
    factors = resistance_factors.get(strategy_name, {})
    
    # Base resistance modified by general stubbornness if present
    base_res = agent_personality.get("stubbornness", 0.5) * 0.4
    resistance = 0.2 + base_res
    
    for trait, modifier in factors.items():
        # Use 0.5 as neutral point: (trait - 0.5) * 2 gives -1 to 1
        trait_value = agent_personality.get(trait, 0.5)
        impact = (trait_value - 0.5) * modifier * 2
        resistance += impact
    
    # Normalize and clamp
    resistance = max(0.05, min(0.95, resistance))
    
    return resistance


def get_personality_persuasion_summary(
    agent_personality: Dict[str, float]
) -> Dict[str, Dict[str, float]]:
    """
    Get a summary of how an agent responds to all argument types.
    
    Useful for debugging and analysis.
    
    Args:
        agent_personality: Dict with personality traits
    
    Returns:
        Dict mapping strategy names to effectiveness/resistance scores
    """
    summary = {}
    
    for strategy in PersuasionStrategy:
        effectiveness = calculate_persuasion_effectiveness_by_personality(
            agent_personality, strategy
        )
        resistance = calculate_persuasion_resistance_by_personality(
            agent_personality, strategy
        )
        
        summary[strategy.value] = {
            "effectiveness": effectiveness,
            "resistance": resistance,
            "net_impact": effectiveness - resistance
        }
    
    return summary


# ==================== HELPER TO INTEGRATE WITH PERSUASION ENGINE ====================

def apply_personality_to_persuasion_engine(
    engine: PersuasionEngine,
    agent_personality: Dict[str, float]
) -> None:
    """
    Apply personality weights to an existing PersuasionEngine.
    
    This modifies the engine's strategy resistances to reflect
    the agent's personality.
    
    Args:
        engine: PersuasionEngine to modify
        agent_personality: Dict with personality traits
    """
    # Update engine personality reference
    engine.personality = agent_personality
    
    for strategy in PersuasionStrategy:
        # Get personality-based resistance
        personality_resistance = calculate_persuasion_resistance_by_personality(
            agent_personality, strategy
        )
        
        # Blend with existing profile resistance
        existing_resistance = engine.profile.strategy_resistance.get(strategy, 0.5)
        
        # Weight: 60% personality, 40% original profile
        new_resistance = (personality_resistance * 0.6) + (existing_resistance * 0.4)
        
        engine.profile.strategy_resistance[strategy] = new_resistance
