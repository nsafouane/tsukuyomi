"""
BeliefManager - Evidence-based belief stance calculation.

This module provides the BeliefManager class for managing evidence-based
beliefs and calculating stances on topics.

Extracted from logic.py for ARCHITECTURE_SPEC 3.1 compliance.
"""

import logging
from typing import List, Dict, Optional

from .structures import EvidenceItem, StanceResult, PersonalityBias

logger = logging.getLogger("BeliefManager")


class BeliefManager:
    """
    Manages evidence-based beliefs and calculates stances.

    Usage:
        bm = BeliefManager(agent_id, PersonalityBias())
        bm.add_evidence("defendant_guilt", {"position": "against", "weight": 0.8, ...})
        stance = bm.calculate_stance("defendant_guilt")
    """

    def __init__(self, agent_id: str, bias: PersonalityBias):
        self.agent_id = agent_id
        self.bias = bias

        self.evidence_ledger: Dict[str, List[EvidenceItem]] = {}
        self._evidence_counter = 0

        logger.info(f"BeliefManager initialized for {agent_id}")

    def add_evidence(
        self,
        topic: str,
        position: str,
        weight: float,
        source_type: str,
        description: str,
        tick_added: int,
        confidence: float = 1.0,
    ) -> str:
        """
        Add evidence for a topic.

        Args:
            topic: The belief topic (e.g., "defendant_guilt")
            position: "for" or "against"
            weight: Base weight of evidence (0.0 to 1.0)
            source_type: "observation", "reasoning", "social_pressure", "hearsay"
            description: Human-readable description
            tick_added: Tick when evidence was added
            confidence: Confidence in evidence quality (0.0 to 1.0)
        """
        self._evidence_counter += 1
        evidence_id = f"ev_{self._evidence_counter}"

        if topic not in self.evidence_ledger:
            self.evidence_ledger[topic] = []

        evidence = EvidenceItem(
            evidence_id=evidence_id,
            topic=topic,
            position=position.lower(),
            weight=weight,
            source_type=source_type,
            description=description,
            tick_added=tick_added,
            confidence=confidence,
        )

        self.evidence_ledger[topic].append(evidence)
        logger.debug(
            f"Added evidence {evidence_id} for topic {topic}: {position} (weight={weight:.2f})"
        )

        return evidence_id

    def calculate_stance(self, topic: str) -> Optional[StanceResult]:
        """
        Calculate stance for a topic based on weighted evidence.

        Returns:
            StanceResult with position ("for", "against", "neutral")
        """
        if topic not in self.evidence_ledger:
            return None

        evidence_list = self.evidence_ledger[topic]
        if not evidence_list:
            return StanceResult(
                topic=topic,
                position="neutral",
                confidence=0.0,
                for_score=0.0,
                against_score=0.0,
                total_evidence_count=0,
            )

        for_score = 0.0
        against_score = 0.0

        # Calculate current stance first to avoid infinite recursion
        # We use a simple initial pass without bias to get a baseline stance
        baseline_for_score = sum(ev.weight * ev.confidence for ev in evidence_list if ev.position == "for")
        baseline_against_score = sum(ev.weight * ev.confidence for ev in evidence_list if ev.position == "against")
        baseline_total = baseline_for_score + baseline_against_score

        current_stance = None
        if baseline_total > 0:
            baseline_for_ratio = baseline_for_score / baseline_total
            baseline_against_ratio = baseline_against_score / baseline_total
            if baseline_for_ratio > 0.6:
                current_stance = StanceResult(
                    topic=topic,
                    position="for",
                    confidence=baseline_for_ratio,
                    for_score=baseline_for_score,
                    against_score=baseline_against_score,
                    total_evidence_count=len(evidence_list),
                )
            elif baseline_against_ratio > 0.6:
                current_stance = StanceResult(
                    topic=topic,
                    position="against",
                    confidence=baseline_against_ratio,
                    for_score=baseline_for_score,
                    against_score=baseline_against_score,
                    total_evidence_count=len(evidence_list),
                )

        for ev in evidence_list:
            effective_weight = ev.weight * ev.confidence

            if ev.position == "for":
                weighted = self._apply_confirmation_bias(
                    effective_weight, position="for", current_stance=current_stance
                )
                for_score += weighted
            elif ev.position == "against":
                weighted = self._apply_confirmation_bias(
                    effective_weight, position="against", current_stance=current_stance
                )
                against_score += weighted

        total_score = for_score + against_score
        if total_score == 0:
            position = "neutral"
            confidence = 0.0
        else:
            for_ratio = for_score / total_score
            against_ratio = against_score / total_score

            if for_ratio > 0.6:
                position = "for"
                confidence = for_ratio
            elif against_ratio > 0.6:
                position = "against"
                confidence = against_ratio
            else:
                position = "neutral"
                confidence = max(for_ratio, against_ratio) * 0.5

        return StanceResult(
            topic=topic,
            position=position,
            confidence=confidence,
            for_score=for_score,
            against_score=against_score,
            total_evidence_count=len(evidence_list),
        )

    def format_beliefs(self, topics: Optional[List[str]] = None) -> str:
        """
        Format beliefs for LLM prompt context.

        Args:
            topics: Specific topics to format. If None, formats all.
        """
        if not topics:
            topics = list(self.evidence_ledger.keys())

        if not topics:
            return "CURRENT BELIEFS: No topics under consideration."

        parts = ["CURRENT BELIEFS:"]
        for topic in topics:
            stance = self.calculate_stance(topic)
            if stance:
                parts.append(
                    f"  - {topic}: {stance.position.upper()} (confidence: {stance.confidence:.2f})"
                )
                parts.append(
                    f"    Evidence: {stance.total_evidence_count} pieces (for: {stance.for_score:.2f}, against: {stance.against_score:.2f})"
                )
            else:
                parts.append(f"  - {topic}: neutral (no evidence)")

        return "\n".join(parts)

    def get_evidence_summary(self, topic: str, limit: int = 5) -> str:
        """Get a summary of recent evidence for a topic."""
        if topic not in self.evidence_ledger:
            return f"No evidence for topic: {topic}"

        evidence_list = sorted(
            self.evidence_ledger[topic], key=lambda e: e.tick_added, reverse=True
        )[:limit]

        parts = [f"EVIDENCE FOR '{topic}':" for ev in evidence_list]
        for ev in evidence_list:
            parts.append(
                f"  - [{ev.position.upper()}] {ev.description} (weight: {ev.weight:.2f}, source: {ev.source_type})"
            )

        return "\n".join(parts)

    def prune_evidence(self, tick_threshold: int, max_per_side: int = 20):
        """
        Remove old and low-weight evidence to prevent ledger bloat.

        Args:
            tick_threshold: Remove evidence older than this tick
            max_per_side: Keep only top N evidence per side per topic
        """
        for topic in list(self.evidence_ledger.keys()):
            evidence_list = self.evidence_ledger[topic]

            evidence_list = [e for e in evidence_list if e.tick_added >= tick_threshold]

            for_evidence = [e for e in evidence_list if e.position == "for"]
            against_evidence = [e for e in evidence_list if e.position == "against"]

            for_evidence.sort(key=lambda e: e.weight * e.confidence, reverse=True)
            against_evidence.sort(key=lambda e: e.weight * e.confidence, reverse=True)

            self.evidence_ledger[topic] = (
                for_evidence[:max_per_side] + against_evidence[:max_per_side]
            )

        logger.debug(f"Pruned evidence ledger for {self.agent_id}")

    def _apply_confirmation_bias(self, weight: float, position: str, current_stance: Optional[StanceResult] = None) -> float:
        """
        Apply personality bias to evidence weighting.

        High confirmation_bias amplifies evidence that supports current stance.
        High social_pressure_immunity reduces impact of social_pressure source.

        Args:
            weight: Base evidence weight
            position: Evidence position ("for" or "against")
            current_stance: Optional pre-computed stance (to avoid infinite recursion)
        """
        # Accept current_stance as parameter to avoid infinite recursion
        # If not provided, fall back to "neutral" (no bias)
        if current_stance is None:
            return max(0.01, min(1.0, weight))

        if current_stance.position != "neutral":
            if current_stance.position == position:
                weight *= self.bias.confirmation_bias
            else:
                weight /= self.bias.disconfirmation_resistance

        return max(0.01, min(1.0, weight))


__all__ = ["BeliefManager"]
