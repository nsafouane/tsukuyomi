"""
Belief Decay and Saturation Management.

This module provides decay and saturation management for beliefs.

Extracted from logic.py for ARCHITECTURE_SPEC 3.1 compliance.
"""

import logging
import random
import math
from typing import Dict, List, Optional, Any

from .structures import (
    Belief, BeliefUpdate, BeliefType,
    ENTRENCHED_THRESHOLD, MIN_CONFIDENCE, MAX_CONFIDENCE,
    SATURATION_DECAY, DecayConfig
)

logger = logging.getLogger("BeliefDecay")


class BeliefDecayManager:
    """
    Manages belief decay, saturation, and social pressure.
    """
    
    @staticmethod
    def apply_saturation_decay(
        beliefs: Dict[str, Belief],
        tick: int = 0
    ) -> List[str]:
        """
        Apply decay to saturated beliefs (above ENTRENCHED_THRESHOLD).
        
        This prevents beliefs from staying at maximum confidence indefinitely.
        Beliefs near the cap slowly drift towards the threshold.
        
        Returns:
            List of belief IDs that were decayed
        """
        decayed = []
        
        for belief in beliefs.values():
            if belief.confidence > ENTRENCHED_THRESHOLD and belief.mutable:
                # Decay towards threshold
                decay_amount = SATURATION_DECAY * (belief.confidence - ENTRENCHED_THRESHOLD)
                belief.confidence -= decay_amount
                belief.last_updated = tick
                decayed.append(belief.id)
                logger.debug(f"Decayed belief {belief.id[:8]}: {belief.confidence:.3f}")
        
        return decayed
    
    @staticmethod
    def is_belief_saturated(belief: Optional[Belief]) -> bool:
        """Check if a belief is at or near saturation."""
        if not belief:
            return False
        return belief.confidence >= ENTRENCHED_THRESHOLD
    
    @staticmethod
    def get_saturation_level(belief: Optional[Belief]) -> float:
        """Get how saturated a belief is (0.0 = not saturated, 1.0 = max saturated)."""
        if not belief:
            return 0.0
        if belief.confidence <= ENTRENCHED_THRESHOLD:
            return 0.0
        return (belief.confidence - ENTRENCHED_THRESHOLD) / (MAX_CONFIDENCE - ENTRENCHED_THRESHOLD)
    
    @staticmethod
    def apply_memory_decay(
        beliefs: Dict[str, Belief],
        tick: int = 0,
        decay_rate: float = 0.0005,
        min_confidence: float = 0.3
    ) -> List[str]:
        """
        Apply general memory decay to all mutable beliefs.
        
        Beliefs that aren't reinforced gradually decay towards a minimum.
        This simulates how memories fade without reinforcement.
        
        Returns:
            List of belief IDs that were decayed
        """
        decayed = []
        
        for belief in beliefs.values():
            if not belief.mutable:
                continue
            
            # Skip recently updated beliefs (within last 100 ticks)
            if tick - belief.last_updated < 100:
                continue
            
            # Apply decay
            if belief.confidence > min_confidence:
                old_conf = belief.confidence
                belief.confidence = max(min_confidence, belief.confidence - decay_rate)
                
                if belief.confidence < old_conf:
                    decayed.append(belief.id)
                    logger.debug(
                        f"Memory decay on {belief.id[:8]}: "
                        f"{old_conf:.3f} -> {belief.confidence:.3f}"
                    )
        
        return decayed
    
    @staticmethod
    def apply_social_pressure(
        beliefs: Dict[str, Belief],
        my_stance: str,
        vote_distribution: Dict[str, int],
        tick: int = 0,
        pressure_strength: float = 0.02
    ) -> List[str]:
        """
        Apply social pressure to beliefs when agent is in minority.
        
        Being in the minority should increase doubt in held beliefs.
        
        Args:
            beliefs: Dict of belief_id -> Belief
            my_stance: Agent's current stance ("guilty" or "not_guilty")
            vote_distribution: Dict like {"guilty": 3, "not_guilty": 2}
            tick: Current tick
            pressure_strength: Base pressure per tick
        
        Returns:
            List of belief IDs affected
        """
        affected = []
        
        my_count = vote_distribution.get(my_stance, 0)
        total = sum(vote_distribution.values())
        
        if total == 0:
            return affected
        
        minority_ratio = my_count / total
        
        # Only apply pressure if in significant minority (< 40%)
        if minority_ratio >= 0.4:
            return affected
        
        # Calculate pressure (stronger minority = more pressure)
        pressure = pressure_strength * (0.4 - minority_ratio)
        
        for belief in beliefs.values():
            if not belief.mutable:
                continue
            
            # Only affect beliefs related to the case
            if "verdict" in belief.tags or "case" in belief.tags:
                old_conf = belief.confidence
                belief.confidence = max(0.2, belief.confidence - pressure)
                belief.last_updated = tick
                
                if belief.confidence < old_conf:
                    affected.append(belief.id)
                    logger.debug(
                        f"Social pressure on {belief.id[:8]}: "
                        f"{old_conf:.3f} -> {belief.confidence:.3f} "
                        f"(minority ratio: {minority_ratio:.1%})"
                    )
        
        return affected
    
    @staticmethod
    def decay_beliefs(
        beliefs: Dict[str, Belief],
        tick: int,
        config: Optional[DecayConfig] = None
    ) -> Dict[str, float]:
        """
        Apply exponential decay to all beliefs.
        
        Uses formula: confidence *= e^(-rate * age)
        Older beliefs decay faster than newer ones.
        
        Returns:
            Dict of belief_id -> new_confidence for beliefs that changed
        """
        config = config or DecayConfig()
        changes = {}
        
        for belief_id, belief in beliefs.items():
            if belief.confidence <= config.min_confidence:
                continue
            
            # Calculate age in ticks
            age = tick - belief.last_updated
            if age <= 0:
                continue
            
            # Exponential decay: faster decay for older beliefs
            decay_factor = math.exp(-config.base_rate * age * config.time_factor)
            old_confidence = belief.confidence
            belief.confidence = max(config.min_confidence, belief.confidence * decay_factor)
            
            if abs(old_confidence - belief.confidence) > 0.001:
                changes[belief_id] = belief.confidence
        
        return changes
    
    @staticmethod
    def perturb_saturated_beliefs(
        beliefs: Dict[str, Belief],
        tick: int,
        neuroticism: float = 0.5,
        config: Optional[DecayConfig] = None
    ) -> Dict[str, float]:
        """
        Randomly perturb beliefs that are stuck at high confidence.
        
        Simulates "moments of doubt" where agents question certainties.
        Higher neuroticism = more perturbation events.
        
        Returns:
            Dict of belief_id -> new_confidence for perturbed beliefs
        """
        config = config or DecayConfig()
        changes = {}
        
        for belief_id, belief in beliefs.items():
            # Only perturb high-confidence mutable beliefs
            if belief.confidence < config.saturation_threshold or not belief.mutable:
                continue
            
            # Base chance + neuroticism modifier
            perturb_chance = config.perturbation_chance * (1 + neuroticism)
            
            if random.random() < perturb_chance:
                old_confidence = belief.confidence
                reduction = config.perturbation_strength * random.uniform(0.5, 1.5)
                belief.confidence = max(
                    config.min_confidence,
                    belief.confidence - reduction
                )
                belief.last_updated = tick
                
                changes[belief_id] = belief.confidence
                logger.info(
                    f"Belief perturbed: {belief_id[:20]}... "
                    f"{old_confidence:.2f} -> {belief.confidence:.2f}"
                )
        
        return changes
    
    @staticmethod
    def get_plasticity(
        openness: float,
        neuroticism: float,
        context: Dict[str, float]
    ) -> float:
        """
        Calculate current belief plasticity based on context.
        
        High stress = more malleable
        High arousal = more malleable
        Recent failures = more malleable
        
        Args:
            openness: Agent's openness trait
            neuroticism: Agent's neuroticism trait
            context: Dict with 'stress', 'arousal', 'recent_contradictions'
        
        Returns:
            Plasticity multiplier (0.5-2.0)
        """
        base_plasticity = 1.0
        
        # Stress modifier (high stress = more open to change)
        stress = context.get("stress", 0.5)
        stress_mod = 1.0 + (stress - 0.5) * 0.5
        
        # Arousal modifier
        arousal = context.get("arousal", 0.5)
        arousal_mod = 1.0 + (arousal - 0.5) * 0.3
        
        # Recent contradiction modifier
        contradictions = context.get("recent_contradictions", 0)
        contr_mod = min(1.5, 1.0 + contradictions * 0.1)
        
        # Neuroticism affects plasticity
        neuro_mod = 0.8 + neuroticism * 0.4
        
        return base_plasticity * stress_mod * arousal_mod * contr_mod * neuro_mod


__all__ = ["BeliefDecayManager"]
