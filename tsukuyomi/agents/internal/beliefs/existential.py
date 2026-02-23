"""
Existential Challenge Processing for Beliefs.

This module handles existential/metaphysical challenges to agent beliefs.

Extracted from logic.py for ARCHITECTURE_SPEC 3.1 compliance.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple

from .structures import Belief, BeliefUpdate, BeliefType

logger = logging.getLogger("ExistentialChallenge")


class ExistentialChallengeProcessor:
    """
    Processes existential/metaphysical challenges to agent beliefs.
    """
    
    @staticmethod
    def process_existential_challenge(
        beliefs: Dict[str, Belief],
        add_belief_func,
        update_history: List[BeliefUpdate],
        openness: float,
        agent_id: str,
        challenge_content: str,
        speaker_id: str,
        tick: int,
        speaker_credibility: float = 0.5
    ) -> Optional[Tuple[str, Optional[BeliefUpdate]]]:
        """
        Process an existential/metaphysical challenge from another agent.
        
        Unlike normal evidence, existential challenges affect agent's 
        core beliefs about identity, meaning, and purpose. These can
        trigger larger belief changes or create cognitive dissonance.
        
        Args:
            beliefs: Dict of belief_id -> Belief
            add_belief_func: Function to add a new belief
            update_history: List to append BeliefUpdate records
            openness: Agent's openness trait
            agent_id: Agent's ID
            challenge_content: The existential statement made
            speaker_id: Who made the statement
            tick: Current tick
            speaker_credibility: Speaker's credibility (0-1)
        
        Returns:
            Tuple of (response_type, optional BeliefUpdate) or None
            Response types: "contemplation", "rejection", "crisis", "acceptance"
        """
        # Determine the type of existential challenge
        challenge_type = ExistentialChallengeProcessor._classify_existential_challenge(challenge_content)
        
        # Find any existing related beliefs
        related_beliefs = ExistentialChallengeProcessor._find_related_existential_beliefs(
            beliefs, challenge_content
        )
        
        # Calculate impact based on openness and existing beliefs
        openness_factor = openness * 1.5  # More impact from openness for existential
        base_impact = 0.3 + (speaker_credibility * 0.3)
        
        if challenge_type == "identity_challenge":
            # Challenges to who the agent is - higher impact
            impact = base_impact * openness_factor * 1.5
            response_type = ExistentialChallengeProcessor._handle_identity_challenge(
                challenge_content, impact, related_beliefs, tick
            )
        elif challenge_type == "purpose_challenge":
            # Challenges to meaning/purpose - moderate impact
            impact = base_impact * openness_factor
            response_type = ExistentialChallengeProcessor._handle_purpose_challenge(
                challenge_content, impact, related_beliefs, tick
            )
        elif challenge_type == "reality_challenge":
            # Challenges to reality - can trigger crisis
            impact = base_impact * openness_factor * 2.0
            response_type = ExistentialChallengeProcessor._handle_reality_challenge(
                challenge_content, impact, related_beliefs, tick
            )
        else:
            # Generic existential - mild response
            impact = base_impact * openness_factor * 0.5
            response_type = "contemplation"
        
        # Create a belief if impact is significant
        update = None
        if impact > 0.4:
            # Clamp impact to valid range for belief confidence
            clamped_impact = min(0.9, max(0.1, impact))
            # Form a new metaphysical belief
            belief_id = add_belief_func(
                statement=f"Existential reflection: {challenge_content[:50]}...",
                confidence=clamped_impact,
                belief_type=BeliefType.METAPHYSICAL,
                source=f"challenge from {speaker_id}",
                tick=tick,
                tags=["existential", challenge_type]
            )
            update = BeliefUpdate(
                belief_id=belief_id,
                old_confidence=0.0,
                new_confidence=clamped_impact,
                reason=f"Existential challenge from {speaker_id}",
                tick=tick,
                evidence_id=""
            )
            update_history.append(update)
        
        logger.info(f"Agent {agent_id} existential response: {response_type} "
                   f"(impact={impact:.2f}, type={challenge_type})")
        
        return (response_type, update)
    
    @staticmethod
    def _classify_existential_challenge(content: str) -> str:
        """Classify the type of existential challenge."""
        content_lower = content.lower()
        
        # Identity challenges
        identity_keywords = ["who are you", "what are you", "identity", "self",
                           "purpose", "meaning", "why do you exist"]
        if any(kw in content_lower for kw in identity_keywords):
            return "identity_challenge"
        
        # Purpose challenges
        purpose_keywords = ["meaning", "purpose", "point", "why bother", 
                          "does it matter", "what's the point"]
        if any(kw in content_lower for kw in purpose_keywords):
            return "purpose_challenge"
        
        # Reality challenges
        reality_keywords = ["simulation", "real", "reality", "exist", 
                          "are we real", "is this real", "observer"]
        if any(kw in content_lower for kw in reality_keywords):
            return "reality_challenge"
        
        return "generic_existential"
    
    @staticmethod
    def _find_related_existential_beliefs(
        beliefs: Dict[str, Belief],
        content: str
    ) -> List[Belief]:
        """Find existing beliefs related to the existential content."""
        related = []
        for belief in beliefs.values():
            if belief.belief_type == BeliefType.METAPHYSICAL:
                related.append(belief)
            elif belief.belief_type == BeliefType.VALUE:
                # Core values might be relevant
                related.append(belief)
        return related
    
    @staticmethod
    def _handle_identity_challenge(
        content: str,
        impact: float,
        related_beliefs: List[Belief],
        tick: int
    ) -> str:
        """Handle a challenge to identity."""
        # If agent has strong core values, they're resilient
        core_strength = sum(b.confidence for b in related_beliefs 
                          if b.is_core_value) / max(len(related_beliefs), 1)
        
        if core_strength > 0.7:
            return "rejection"  # Strong identity, rejects challenge
        elif core_strength > 0.4:
            return "contemplation"  # Some contemplation
        else:
            return "crisis"  # Identity crisis possible
    
    @staticmethod
    def _handle_purpose_challenge(
        content: str,
        impact: float,
        related_beliefs: List[Belief],
        tick: int
    ) -> str:
        """Handle a challenge to purpose/meaning."""
        if impact > 0.7:
            return "crisis"
        elif impact > 0.4:
            return "contemplation"
        else:
            return "rejection"
    
    @staticmethod
    def _handle_reality_challenge(
        content: str,
        impact: float,
        related_beliefs: List[Belief],
        tick: int
    ) -> str:
        """Handle a challenge to reality."""
        # Reality challenges can trigger existential crisis
        if len(related_beliefs) > 0:
            avg_confidence = sum(b.confidence for b in related_beliefs) / len(related_beliefs)
            if avg_confidence < 0.3:
                return "acceptance"  # Already uncertain, accepts
        return "crisis" if impact > 0.6 else "contemplation"


__all__ = ["ExistentialChallengeProcessor"]
