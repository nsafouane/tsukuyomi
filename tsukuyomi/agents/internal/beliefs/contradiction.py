"""
Belief Contradiction Detection and Resolution.

This module provides contradiction detection and resolution for the belief system.

Extracted from logic.py for ARCHITECTURE_SPEC 3.1 compliance.
"""

import logging
import random
from typing import List, Dict, Optional, Any, Tuple

from .structures import (
    Belief, BeliefUpdate, BeliefType,
    MIN_CONFIDENCE
)

logger = logging.getLogger("BeliefContradiction")


class ContradictionDetector:
    """
    Detects and resolves contradictions between beliefs.
    """
    
    @staticmethod
    def find_contradictions(beliefs: Dict[str, Belief]) -> List[Tuple[Belief, Belief]]:
        """
        Find pairs of contradictory beliefs.
        
        Returns:
            List of (belief1, belief2) pairs that contradict each other
        """
        contradictions = []
        beliefs_list = list(beliefs.values())
        
        for i, b1 in enumerate(beliefs_list):
            for b2 in beliefs_list[i+1:]:
                if ContradictionDetector._are_contradictory(b1, b2):
                    contradictions.append((b1, b2))
        
        return contradictions
    
    @staticmethod
    def _are_contradictory(b1: Belief, b2: Belief) -> bool:
        """Check if two beliefs contradict each other."""
        # Same type, high confidence, opposite positions
        if b1.belief_type != b2.belief_type:
            return False
        
        if not (b1.is_certain and b2.is_certain):
            return False
        
        # Simple keyword contradiction check
        negation_words = {"not", "never", "no", "isn't", "doesn't", "won't", "can't"}
        
        s1_words = set(b1.statement.lower().split())
        s2_words = set(b2.statement.lower().split())
        
        # Check if one has negation and other doesn't
        s1_negations = s1_words & negation_words
        s2_negations = s2_words & negation_words
        
        if bool(s1_negations) != bool(s2_negations):
            # One has negation, check if content is similar
            s1_content = s1_words - negation_words
            s2_content = s2_words - negation_words
            overlap = len(s1_content & s2_content)
            if overlap >= 2:  # At least 2 words overlap
                return True
        
        return False
    
    @staticmethod
    def resolve_contradiction(
        b1: Belief,
        b2: Belief,
        tick: int = 0
    ) -> Optional[str]:
        """
        Attempt to resolve a contradiction between two beliefs.
        
        Strategy:
        1. Keep belief with more evidence
        2. Reduce confidence in the other
        3. If equal, reduce both slightly
        
        Returns:
            ID of the belief that was weakened, or None
        """
        if b1.evidence_count > b2.evidence_count:
            # Weaken b2
            b2.confidence *= 0.7
            b2.last_updated = tick
            logger.info(f"Resolved contradiction: weakened '{b2.statement[:30]}...'")
            return b2.id
        elif b2.evidence_count > b1.evidence_count:
            # Weaken b1
            b1.confidence *= 0.7
            b1.last_updated = tick
            logger.info(f"Resolved contradiction: weakened '{b1.statement[:30]}...'")
            return b1.id
        else:
            # Equal evidence - weaken both
            b1.confidence *= 0.85
            b2.confidence *= 0.85
            b1.last_updated = tick
            b2.last_updated = tick
            logger.info("Resolved contradiction: weakened both equally")
            return None
    
    @staticmethod
    def detect_contradictions_detailed(beliefs: Dict[str, Belief]) -> List[Dict[str, Any]]:
        """
        Detect pairs of beliefs that contradict each other.
        
        Uses keyword analysis to find contradictory statements.
        
        Returns:
            List of contradiction dicts with severity scores
        """
        contradictions = []
        beliefs_list = list(beliefs.values())
        
        for i, b1 in enumerate(beliefs_list):
            for b2 in beliefs_list[i+1:]:
                if ContradictionDetector._are_contradictory(b1, b2):
                    severity = (b1.confidence + b2.confidence) / 2
                    contradictions.append({
                        "belief_1": b1.id,
                        "belief_2": b2.id,
                        "statement_1": b1.statement,
                        "statement_2": b2.statement,
                        "severity": severity
                    })
        
        return contradictions
    
    @staticmethod
    def resolve_contradiction_advanced(
        beliefs: Dict[str, Belief],
        contradiction: Dict[str, Any],
        resolution: str = "reduce_both"
    ) -> Dict[str, float]:
        """
        Resolve a detected contradiction with specified strategy.
        
        Args:
            beliefs: Dict of belief_id -> Belief
            contradiction: Dict from detect_contradictions_detailed()
            resolution: "reduce_both", "keep_stronger", or "random"
        
        Returns:
            Dict of belief_id -> new_confidence
        """
        b1 = beliefs.get(contradiction["belief_1"])
        b2 = beliefs.get(contradiction["belief_2"])
        
        if not b1 or not b2:
            return {}
        
        changes = {}
        severity = contradiction.get("severity", 0.5)
        
        if resolution == "reduce_both":
            reduction = severity * 0.2
            b1.confidence = max(MIN_CONFIDENCE, b1.confidence - reduction)
            b2.confidence = max(MIN_CONFIDENCE, b2.confidence - reduction)
            changes[b1.id] = b1.confidence
            changes[b2.id] = b2.confidence
            
        elif resolution == "keep_stronger":
            weaker = b1 if b1.confidence < b2.confidence else b2
            stronger = b2 if weaker == b1 else b1
            weaker.confidence = max(MIN_CONFIDENCE, weaker.confidence - 0.3)
            changes[weaker.id] = weaker.confidence
            logger.info(f"Contradiction resolved: kept '{stronger.statement[:30]}...'")
            
        elif resolution == "random":
            target = random.choice([b1, b2])
            target.confidence = max(MIN_CONFIDENCE, target.confidence - 0.25)
            changes[target.id] = target.confidence
        
        return changes


__all__ = ["ContradictionDetector"]
