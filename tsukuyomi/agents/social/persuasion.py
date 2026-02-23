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

from typing import List, Dict, Optional, Any, Tuple

from tsukuyomi.agents.social.persuasion_types import (
    PersuasionStrategy,
    ArgumentStrength,
    Argument,
    PersuasionAttempt,
    PersuasionProfile,
    ENTRENCHED_THRESHOLD,
    MAX_CONFIDENCE,
)


class PersuasionEngine:
    """Main persuasion engine for modeling persuasive dynamics."""
    
    def __init__(
        self,
        agent_id: str,
        profile: Optional[PersuasionProfile] = None,
        personality: Optional[Dict[str, float]] = None
    ):
        self.agent_id = agent_id
        self.profile = profile or PersuasionProfile(agent_id=agent_id)
        self.personality = personality or {}
        
        self.arguments: Dict[str, Argument] = {}
        self.attempts: List[PersuasionAttempt] = []
        self.relationship_modifiers: Dict[str, float] = {}
        
        self.min_change = 0.01
        self.max_change = 0.3
        
        if self.personality:
            apply_personality_to_persuasion_engine(self, self.personality)
    
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
        """Create a persuasive argument."""
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
        strategy_bonus = self.profile.strategy_preferences.get(strategy, 0.5)
        evidence_bonus = min(0.2, len(evidence_ids) * 0.05)
        strength = (confidence * 0.5 + strategy_bonus * 0.3 + evidence_bonus + 0.2)
        return min(1.0, max(0.0, strength))
    
    def calculate_persuasion_effect(
        self,
        argument: Argument,
        listener_id: str,
        belief_confidence: float,
        belief_is_core: bool = False,
        existing_evidence_count: int = 0,
        tick: int = 0
    ) -> Tuple[float, PersuasionAttempt]:
        """Calculate how much an argument persuades."""
        attempt = PersuasionAttempt(
            arg_id=argument.id,
            speaker_id=argument.speaker_id,
            listener_id=listener_id,
            tick=tick,
            initial_confidence=belief_confidence
        )
        
        self.profile.arguments_heard.append(argument.id)
        
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
        
        potential_change = effectiveness * self.max_change
        actual_change = potential_change * (1 - resistance)
        
        if abs(actual_change) < self.min_change:
            actual_change = 0.0
        
        new_confidence = belief_confidence + actual_change
        new_confidence = max(0.0, min(1.0, new_confidence))
        
        attempt.final_confidence = new_confidence
        attempt.change = new_confidence - belief_confidence
        
        self.attempts.append(attempt)
        
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
        """Calculate resistance to persuasion."""
        base = self.profile.base_resistance
        strategy_res = self.profile.strategy_resistance.get(strategy, 0.5)
        strength_res = abs(belief_confidence - 0.5) * 0.4
        
        if belief_confidence > ENTRENCHED_THRESHOLD:
            saturation = (belief_confidence - ENTRENCHED_THRESHOLD) / (MAX_CONFIDENCE - ENTRENCHED_THRESHOLD)
            saturation_res = saturation * 0.6
        else:
            saturation_res = 0.0
        
        core_res = 0.3 if belief_is_core else 0.0
        evidence_res = min(0.2, existing_evidence_count * 0.02)
        
        total_resistance = (
            base * 0.15 +
            strategy_res * 0.5 +
            strength_res +
            saturation_res +
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
        """Calculate persuasion effectiveness."""
        arg_strength = argument.strength_score
        confidence = argument.confidence
        rel_bonus = (relationship - 0.5) * 0.3
        
        personality_susceptibility = 1.0
        if self.personality:
            personality_susceptibility = calculate_persuasion_effectiveness_by_personality(
                self.personality, argument.strategy
            )
        
        effectiveness = (
            arg_strength * 0.3 +
            confidence * 0.2 +
            personality_susceptibility * 0.3 +
            0.2 +
            rel_bonus
        )
        
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
            factors.append("entrenched_belief")
        if belief_confidence > 0.8:
            factors.append("strong_belief")
        if belief_confidence < 0.2:
            factors.append("weak_belief")
        
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
    
    def select_best_strategy(
        self,
        listener_id: str,
        belief_confidence: float,
        available_evidence: int = 0,
        relationship: float = 0.5
    ) -> PersuasionStrategy:
        """Select the best persuasion strategy for this situation."""
        scores = {}
        
        for strategy in PersuasionStrategy:
            pref = self.profile.strategy_preferences.get(strategy, 0.5)
            resistance = self.profile.strategy_resistance.get(strategy, 0.5)
            
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
    
    def update_relationship(self, other_id: str, delta: float):
        """Update relationship modifier with another agent."""
        current = self.relationship_modifiers.get(other_id, 0.5)
        new_value = max(-1.0, min(1.0, current + delta))
        self.relationship_modifiers[other_id] = new_value
    
    def get_relationship(self, other_id: str) -> float:
        """Get relationship score with another agent."""
        return self.relationship_modifiers.get(other_id, 0.5)
    
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


def create_persuasion_profile_from_personality(
    personality_traits: Dict[str, float]
) -> PersuasionProfile:
    """Create a persuasion profile from personality traits."""
    profile = PersuasionProfile()
    
    neuroticism = personality_traits.get("neuroticism", 0.5)
    agreeableness = personality_traits.get("agreeableness", 0.5)
    conscientiousness = personality_traits.get("conscientiousness", 0.5)
    
    profile.base_resistance = 0.3 + neuroticism * 0.3 - agreeableness * 0.2
    
    openness = personality_traits.get("openness", 0.5)
    
    profile.strategy_preferences[PersuasionStrategy.LOGIC] = 0.3 + conscientiousness * 0.4
    profile.strategy_preferences[PersuasionStrategy.EMOTION] = 0.3 + neuroticism * 0.3
    profile.strategy_preferences[PersuasionStrategy.AUTHORITY] = 0.3 + (1 - openness) * 0.3
    profile.strategy_preferences[PersuasionStrategy.SOCIAL_PROOF] = 0.3 + agreeableness * 0.3
    
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


ARGUMENT_EFFECTIVENESS_BY_PERSONALITY = {
    "logic": {
        "openness": 0.8,
        "conscientiousness": 0.6,
    },
    "emotion": {
        "neuroticism": 0.9,
        "agreeableness": 0.5,
    },
    "authority": {
        "conscientiousness": 0.8,
        "openness": 0.3,
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
    """Calculate how effective a specific argument type is for an agent."""
    strategy_name = argument_strategy.value
    trait_weights = ARGUMENT_EFFECTIVENESS_BY_PERSONALITY.get(strategy_name, {})
    
    if not trait_weights:
        return 0.5
    
    effectiveness = 0.0
    total_weight = 0.0
    
    for trait, weight in trait_weights.items():
        trait_value = agent_personality.get(trait, 0.5)
        effectiveness += trait_value * weight
        total_weight += weight
    
    if total_weight > 0:
        effectiveness = effectiveness / total_weight
    
    effectiveness = 0.2 + (effectiveness * 0.6)
    
    return effectiveness


def calculate_persuasion_resistance_by_personality(
    agent_personality: Dict[str, float],
    argument_strategy: PersuasionStrategy
) -> float:
    """Calculate how resistant an agent is to a specific argument type."""
    strategy_name = argument_strategy.value
    
    resistance_factors = {
        "logic": {
            "openness": -0.8,
            "neuroticism": 0.4,
        },
        "emotion": {
            "conscientiousness": 0.6,
            "neuroticism": -0.5,
        },
        "authority": {
            "openness": 0.7,
            "extraversion": -0.4,
        },
        "social_proof": {
            "agreeableness": -0.6,
            "stubbornness": 0.8,
        },
        "scarcity": {
            "conscientiousness": -0.4,
            "cynicism": 0.6,
        },
    }
    
    factors = resistance_factors.get(strategy_name, {})
    
    base_res = agent_personality.get("stubbornness", 0.5) * 0.4
    resistance = 0.2 + base_res
    
    for trait, modifier in factors.items():
        trait_value = agent_personality.get(trait, 0.5)
        impact = (trait_value - 0.5) * modifier * 2
        resistance += impact
    
    resistance = max(0.05, min(0.95, resistance))
    
    return resistance


def get_personality_persuasion_summary(
    agent_personality: Dict[str, float]
) -> Dict[str, Dict[str, float]]:
    """Get a summary of how an agent responds to all argument types."""
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


def apply_personality_to_persuasion_engine(
    engine: PersuasionEngine,
    agent_personality: Dict[str, float]
) -> None:
    """Apply personality weights to an existing PersuasionEngine."""
    engine.personality = agent_personality
    
    for strategy in PersuasionStrategy:
        personality_resistance = calculate_persuasion_resistance_by_personality(
            agent_personality, strategy
        )
        
        existing_resistance = engine.profile.strategy_resistance.get(strategy, 0.5)
        new_resistance = (personality_resistance * 0.6) + (existing_resistance * 0.4)
        
        engine.profile.strategy_resistance[strategy] = new_resistance
