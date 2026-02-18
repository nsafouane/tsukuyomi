"""
Asymmetric Influence System
===========================

Models how influence between agents is NOT symmetric.
Different agents have different amounts of influence based on:
- Speaker credibility (expertise, history)
- Listener openness (Big Five personality)
- Relationship trust (history between agents)
- Argument quality (strength of reasoning)
- Personality compatibility (similar traits)

This is a GENERAL system that applies to ANY multi-agent scenario.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import math


@dataclass
class InfluenceFactors:
    """
    Individual factors that determine influence weight.
    
    Each factor is 0.0-1.0, where:
    - 0.0 = minimum
    - 0.5 = neutral/average
    - 1.0 = maximum
    """
    speaker_credibility: float = 0.5      # Expertise, track record
    listener_openness: float = 0.5        # Big Five openness trait
    relationship_trust: float = 0.5       # History between agents
    argument_quality: float = 0.5         # Strength of the argument
    personality_compatibility: float = 0.5  # Similar personality traits
    
    @property
    def total_weight(self) -> float:
        """
        Calculate composite influence weight.
        
        Weights are designed so:
        - All factors contribute
        - No single factor dominates
        - Range is naturally 0.0-1.0
        """
        return (
            self.speaker_credibility * 0.25 +      # Credibility matters
            self.listener_openness * 0.25 +        # Openness matters equally
            self.relationship_trust * 0.20 +       # Trust is important
            self.argument_quality * 0.15 +         # Argument strength
            self.personality_compatibility * 0.15  # Compatibility
        )
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "speaker_credibility": self.speaker_credibility,
            "listener_openness": self.listener_openness,
            "relationship_trust": self.relationship_trust,
            "argument_quality": self.argument_quality,
            "personality_compatibility": self.personality_compatibility,
            "total_weight": self.total_weight
        }


class InfluenceWeightCalculator:
    """
    Calculates asymmetric influence weights between agents.
    
    Key principle: A→B influence ≠ B→A influence
    
    Usage:
        calc = InfluenceWeightCalculator()
        
        # Calculate how much Speaker influences Listener
        weight = calc.calculate(
            speaker_personality={"openness": 0.8, "conscientiousness": 0.7},
            listener_personality={"openness": 0.3, "agreeableness": 0.6},
            speaker_credibility=0.8,
            relationship_trust=0.6,
            argument_strength=0.7
        )
        # weight ≈ 0.45 (moderate influence despite low listener openness)
    """
    
    def __init__(
        self,
        credibility_weight: float = 0.25,
        openness_weight: float = 0.25,
        trust_weight: float = 0.20,
        argument_weight: float = 0.15,
        compatibility_weight: float = 0.15
    ):
        """
        Initialize with custom weights for each factor.
        
        Default weights sum to 1.0.
        """
        self.weights = {
            "credibility": credibility_weight,
            "openness": openness_weight,
            "trust": trust_weight,
            "argument": argument_weight,
            "compatibility": compatibility_weight
        }
        
        # Normalize to ensure they sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in self.weights.items()}
    
    def calculate(
        self,
        speaker_personality: Dict[str, float],
        listener_personality: Dict[str, float],
        speaker_credibility: float = 0.5,
        relationship_trust: float = 0.5,
        argument_strength: float = 0.5
    ) -> Tuple[float, InfluenceFactors]:
        """
        Calculate influence weight from speaker to listener.
        
        Args:
            speaker_personality: Big Five traits of speaker
            listener_personality: Big Five traits of listener
            speaker_credibility: How credible/trustworthy the speaker is (0-1)
            relationship_trust: Trust level between speaker and listener (0-1)
            argument_strength: Quality of the argument being made (0-1)
        
        Returns:
            (weight, factors) - Weight is 0-1, factors shows breakdown
        """
        # Listener's openness to new ideas
        listener_openness = listener_personality.get("openness", 0.5)
        
        # Speaker's credibility (can be boosted by conscientiousness)
        speaker_consc = speaker_personality.get("conscientiousness", 0.5)
        adjusted_credibility = (speaker_credibility * 0.7 + speaker_consc * 0.3)
        
        # Personality compatibility
        compatibility = self._calculate_compatibility(
            speaker_personality, listener_personality
        )
        
        factors = InfluenceFactors(
            speaker_credibility=adjusted_credibility,
            listener_openness=listener_openness,
            relationship_trust=relationship_trust,
            argument_quality=argument_strength,
            personality_compatibility=compatibility
        )
        
        return factors.total_weight, factors
    
    def _calculate_compatibility(
        self,
        p1: Dict[str, float],
        p2: Dict[str, float]
    ) -> float:
        """
        Calculate personality compatibility between two agents.
        
        Similar personalities tend to influence each other more.
        Uses cosine similarity-like calculation.
        
        Returns 0.0-1.0 where:
        - 1.0 = identical personalities
        - 0.5 = neutral/average
        - 0.0 = opposite personalities
        """
        # Get common traits
        common_traits = set(p1.keys()) & set(p2.keys())
        
        if not common_traits:
            return 0.5  # No data, assume neutral
        
        # Calculate similarity
        dot_product = sum(p1[t] * p2[t] for t in common_traits)
        mag1 = math.sqrt(sum(p1[t]**2 for t in common_traits))
        mag2 = math.sqrt(sum(p2[t]**2 for t in common_traits))
        
        if mag1 == 0 or mag2 == 0:
            return 0.5
        
        # Cosine similarity (range -1 to 1)
        cosine = dot_product / (mag1 * mag2)
        
        # Convert to 0-1 range
        compatibility = (cosine + 1) / 2
        
        return compatibility
    
    def calculate_credibility_from_history(
        self,
        successful_persuasions: int,
        total_attempts: int,
        base_credibility: float = 0.5
    ) -> float:
        """
        Calculate speaker credibility from persuasion history.
        
        Agents with successful track records are more credible.
        """
        if total_attempts == 0:
            return base_credibility
        
        success_rate = successful_persuasions / total_attempts
        
        # Blend base credibility with success rate
        # Weight towards base for new agents, towards history for experienced
        history_weight = min(0.7, total_attempts / 20)  # Max 70% from history
        
        credibility = (
            base_credibility * (1 - history_weight) +
            success_rate * history_weight
        )
        
        return min(1.0, max(0.1, credibility))


def calculate_influence_weight(
    speaker_id: str,
    listener_id: str,
    speaker_personality: Dict[str, float],
    listener_personality: Dict[str, float],
    speaker_credibility: float = 0.5,
    relationship_trust: float = 0.5,
    argument_strength: float = 0.5
) -> float:
    """
    Convenience function to calculate influence weight.
    
    Returns just the weight (0-1) without detailed factors.
    """
    calc = InfluenceWeightCalculator()
    weight, _ = calc.calculate(
        speaker_personality=speaker_personality,
        listener_personality=listener_personality,
        speaker_credibility=speaker_credibility,
        relationship_trust=relationship_trust,
        argument_strength=argument_strength
    )
    return weight


def demonstrate_asymmetry():
    """
    Demonstrate that influence is NOT symmetric.
    
    Shows how different personalities create different influence patterns.
    """
    calc = InfluenceWeightCalculator()
    
    # Agent A: High openness, low credibility
    agent_a = {"openness": 0.9, "conscientiousness": 0.3, "agreeableness": 0.6}
    
    # Agent B: Low openness, high credibility
    agent_b = {"openness": 0.2, "conscientiousness": 0.9, "agreeableness": 0.4}
    
    # A -> B (high openness speaker to low openness listener)
    weight_ab, factors_ab = calc.calculate(
        speaker_personality=agent_a,
        listener_personality=agent_b,
        speaker_credibility=0.3,  # Low credibility
        relationship_trust=0.5,
        argument_strength=0.6
    )
    
    # B -> A (high credibility speaker to high openness listener)
    weight_ba, factors_ba = calc.calculate(
        speaker_personality=agent_b,
        listener_personality=agent_a,
        speaker_credibility=0.9,  # High credibility
        relationship_trust=0.5,
        argument_strength=0.6
    )
    
    return {
        "A_to_B": {"weight": weight_ab, "factors": factors_ab.to_dict()},
        "B_to_A": {"weight": weight_ba, "factors": factors_ba.to_dict()},
        "asymmetric": weight_ab != weight_ba,
        "ratio": weight_ab / weight_ba if weight_ba > 0 else 0
    }


# ========================
# Integration with BeliefSystem
# ========================

def get_influence_weight_for_belief_update(
    listener_belief_system: Any,
    speaker_id: str,
    speaker_personality: Dict[str, float],
    speaker_credibility: float = 0.5,
    relationship_trust: float = 0.5,
    argument_strength: float = 0.5
) -> float:
    """
    Get influence weight for a belief system update.
    
    This is the main integration point between the influence system
    and the belief system.
    
    Args:
        listener_belief_system: The BeliefSystem of the listener
        speaker_id: ID of the speaker
        speaker_personality: Speaker's Big Five traits
        speaker_credibility: Speaker's credibility (0-1)
        relationship_trust: Trust between speaker and listener (0-1)
        argument_strength: Strength of the argument (0-1)
    
    Returns:
        Influence weight (0-1)
    """
    calc = InfluenceWeightCalculator()
    
    # Get listener's personality from belief system
    listener_openness = getattr(listener_belief_system, 'openness', 0.5)
    listener_personality = {
        "openness": listener_openness,
        # Get other traits if available
        "conscientiousness": getattr(listener_belief_system, 'conscientiousness', 0.5),
        "agreeableness": getattr(listener_belief_system, 'agreeableness', 0.5),
        "neuroticism": getattr(listener_belief_system, 'neuroticism', 0.5),
        "extraversion": getattr(listener_belief_system, 'extraversion', 0.5)
    }
    
    weight, _ = calc.calculate(
        speaker_personality=speaker_personality,
        listener_personality=listener_personality,
        speaker_credibility=speaker_credibility,
        relationship_trust=relationship_trust,
        argument_strength=argument_strength
    )
    
    return weight
