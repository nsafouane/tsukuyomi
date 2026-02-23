"""
Reasoning Validator - Phase 17: Reasoning Transparency

This module implements consistency checks for agent reasoning.
"""

import logging
import re
from typing import Dict, List, Optional, Any

from .validation_types import (
    ViolationType,
    ViolationSeverity,
    ReasoningViolation,
    ValidationResult,
    PersonalitySnapshot,
    BeliefSnapshot,
    NeedsSnapshot,
)


logger = logging.getLogger(__name__)


class TraitChecker:
    """Check if decisions align with personality traits."""

    def __init__(self, personality: PersonalitySnapshot):
        self.personality = personality

    def check_trait_consistency(
        self,
        action: str,
        params: Dict[str, Any],
        emotional_state: str,
        reasoning: str,
        heat_level: float = 0.0
    ) -> List[ReasoningViolation]:
        """Check if action aligns with personality traits."""
        violations = []

        violations.extend(self._check_extraversion(action, params, reasoning))
        violations.extend(self._check_agreeableness(action, params, reasoning))
        violations.extend(self._check_neuroticism(emotional_state, heat_level, reasoning))
        violations.extend(self._check_conscientiousness(action, params, reasoning))
        violations.extend(self._check_vocabulary(reasoning))

        return violations

    def _check_extraversion(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str
    ) -> List[ReasoningViolation]:
        """Check extraversion-related consistency."""
        violations = []

        if self.personality.extraversion < -0.3:
            if action == "EMOTE" and params.get("type") in ["shout", "announce"]:
                violations.append(ReasoningViolation(
                    violation_type=ViolationType.TRAIT_INCONSISTENCY,
                    description="Introvert choosing to shout/announce to crowd",
                    severity=ViolationSeverity.MEDIUM.value,
                    trait="extraversion",
                    expected="avoid_crowd_attention",
                    actual="shout_to_all",
                    suggestion="Consider quieter forms of communication"
                ))

            if action == "SPEAK" and not params.get("response_to"):
                if "approach" not in reasoning.lower() and "greet" not in reasoning.lower():
                    violations.append(ReasoningViolation(
                        violation_type=ViolationType.TRAIT_INCONSISTENCY,
                        description="Introvert initiating conversation without clear reason",
                        severity=ViolationSeverity.LOW.value,
                        trait="extraversion",
                        expected="wait_to_be_addressed",
                        actual="initiate_conversation",
                        suggestion="Add clear motivation for initiating"
                    ))

        if self.personality.extraversion > 0.5:
            if action == "IDLE" and "social" in str(params).lower():
                violations.append(ReasoningViolation(
                    violation_type=ViolationType.TRAIT_INCONSISTENCY,
                    description="Extravert avoiding social interaction",
                    severity=ViolationSeverity.LOW.value,
                    trait="extraversion",
                    expected="engage_socially",
                    actual="idle_avoid_social",
                    suggestion="Extraverts typically seek social engagement"
                ))

        return violations

    def _check_agreeableness(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str
    ) -> List[ReasoningViolation]:
        """Check agreeableness-related consistency."""
        violations = []

        if self.personality.agreeableness > 0.5:
            reasoning_lower = reasoning.lower()

            if any(word in reasoning_lower for word in ["confront", "challenge", "argue", "disagree"]):
                if "despite" not in reasoning_lower and "although" not in reasoning_lower:
                    violations.append(ReasoningViolation(
                        violation_type=ViolationType.TRAIT_INCONSISTENCY,
                        description="Highly agreeable person being confrontational without justification",
                        severity=ViolationSeverity.MEDIUM.value,
                        trait="agreeableness",
                        expected="cooperative_approach",
                        actual="confrontational",
                        suggestion="Add internal conflict about being confrontational"
                    ))

        if self.personality.agreeableness < -0.5:
            reasoning_lower = reasoning.lower()

            if any(word in reasoning_lower for word in ["agree", "cooperate", "accept"]):
                if "reluctantly" not in reasoning_lower and "grudgingly" not in reasoning_lower:
                    violations.append(ReasoningViolation(
                        violation_type=ViolationType.TRAIT_INCONSISTENCY,
                        description="Competitive person being overly agreeable",
                        severity=ViolationSeverity.LOW.value,
                        trait="agreeableness",
                        expected="competitive_challenge",
                        actual="cooperative_agree",
                        suggestion="Show reluctance or skepticism in agreement"
                    ))

        return violations

    def _check_neuroticism(
        self,
        emotional_state: str,
        heat_level: float,
        reasoning: str
    ) -> List[ReasoningViolation]:
        """Check neuroticism-related consistency."""
        violations = []

        if self.personality.neuroticism > 0.5 and heat_level > 0.5:
            calm_words = ["calm", "relaxed", "unbothered", "unconcerned"]
            reasoning_lower = reasoning.lower()

            if any(word in reasoning_lower for word in calm_words):
                violations.append(ReasoningViolation(
                    violation_type=ViolationType.TRAIT_INCONSISTENCY,
                    description="High neuroticism agent remaining calm under pressure",
                    severity=ViolationSeverity.MEDIUM.value,
                    trait="neuroticism",
                    expected="emotional_reactivity",
                    actual="calm_under_pressure",
                    suggestion="Show emotional response to tension"
                ))

            if emotional_state in ["calm", "relaxed", "serene"]:
                violations.append(ReasoningViolation(
                    violation_type=ViolationType.EMOTIONAL_INCOHERENCE,
                    description="High neuroticism agent has calm emotional state under tension",
                    severity=ViolationSeverity.HIGH.value,
                    trait="neuroticism",
                    expected="anxious_agitated",
                    actual=emotional_state,
                    suggestion="Adjust emotional state to reflect personality"
                ))

        if self.personality.neuroticism < -0.3:
            if emotional_state in ["anxious", "fearful", "panicked"]:
                violations.append(ReasoningViolation(
                    violation_type=ViolationType.EMOTIONAL_INCOHERENCE,
                    description="Emotionally stable agent showing high anxiety",
                    severity=ViolationSeverity.MEDIUM.value,
                    trait="neuroticism",
                    expected="stable_calm",
                    actual=emotional_state,
                    suggestion="Reduce emotional reactivity for stable personality"
                ))

        return violations

    def _check_conscientiousness(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str
    ) -> List[ReasoningViolation]:
        """Check conscientiousness-related consistency."""
        violations = []

        if self.personality.conscientiousness > 0.5:
            reasoning_lower = reasoning.lower()

            if any(phrase in reasoning_lower for phrase in ["spontaneous", "impulse", "why not"]):
                violations.append(ReasoningViolation(
                    violation_type=ViolationType.TRAIT_INCONSISTENCY,
                    description="Conscientious agent acting on impulse",
                    severity=ViolationSeverity.LOW.value,
                    trait="conscientiousness",
                    expected="planned_deliberate",
                    actual="spontaneous_impulsive",
                    suggestion="Add deliberation before spontaneous action"
                ))

        if self.personality.conscientiousness < -0.3:
            reasoning_lower = reasoning.lower()

            if any(phrase in reasoning_lower for phrase in ["plan", "carefully", "deliberately"]):
                violations.append(ReasoningViolation(
                    violation_type=ViolationType.TRAIT_INCONSISTENCY,
                    description="Spontaneous agent acting too deliberately",
                    severity=ViolationSeverity.LOW.value,
                    trait="conscientiousness",
                    expected="spontaneous_flexible",
                    actual="planned_deliberate",
                    suggestion="Allow more flexibility in reasoning"
                ))

        return violations

    def _check_vocabulary(self, reasoning: str) -> List[ReasoningViolation]:
        """Check vocabulary level consistency."""
        violations = []

        if self.personality.vocabulary_level == "simple":
            complex_patterns = [
                r"\b\w{12,}\b",
                r"\bnevertheless\b",
                r"\bconsequently\b",
                r"\bfurthermore\b",
                r"\bnotwithstanding\b",
                r"\bheretofore\b"
            ]

            complex_count = sum(
                len(re.findall(pattern, reasoning, re.IGNORECASE))
                for pattern in complex_patterns
            )

            if complex_count > 2:
                violations.append(ReasoningViolation(
                    violation_type=ViolationType.TRAIT_INCONSISTENCY,
                    description=f"Simple vocabulary profile using complex words ({complex_count} found)",
                    severity=ViolationSeverity.LOW.value,
                    trait="vocabulary_level",
                    expected="simple_direct_language",
                    actual="complex_vocabulary",
                    suggestion="Use simpler, more direct language"
                ))

        return violations


class BeliefChecker:
    """Check if actions align with stated beliefs."""

    def __init__(self, beliefs: BeliefSnapshot):
        self.beliefs = beliefs

    def check_belief_consistency(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str,
        personality_drivers: List[str]
    ) -> List[ReasoningViolation]:
        """Check if action aligns with stated beliefs."""
        violations = []

        violations.extend(self._check_belief_action_consistency(action, params, reasoning))
        violations.extend(self._check_stance_reversal(reasoning, personality_drivers))

        return violations

    def _check_belief_action_consistency(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str
    ) -> List[ReasoningViolation]:
        """Check if actions contradict stated beliefs."""
        violations = []

        for topic, (stance, confidence) in self.beliefs.stances.items():
            if self._action_relates_to_topic(action, params, topic):
                if self._reasoning_contradicts_stance(reasoning, stance, topic):
                    violations.append(ReasoningViolation(
                        violation_type=ViolationType.BELIEF_CONTRADICTION,
                        description=f"Action contradicts belief on {topic} (stance: {stance})",
                        severity=ViolationSeverity.HIGH.value,
                        expected=f"action_consistent_with_{stance}",
                        actual="contradictory_action",
                        context=f"Belief confidence: {confidence:.0%}",
                        suggestion=f"Add reasoning for stance change or adjust action"
                    ))

        return violations

    def _check_stance_reversal(
        self,
        reasoning: str,
        personality_drivers: List[str]
    ) -> List[ReasoningViolation]:
        """Check for sudden stance reversals without justification."""
        violations = []

        for driver in personality_drivers:
            if driver.startswith("belief:"):
                parts = driver.split(":", 2)
                if len(parts) >= 3:
                    topic_part = parts[1].strip()
                    for topic, (stance, confidence) in self.beliefs.stances.items():
                        if topic in topic_part.lower():
                            if stance == "for" and "against" in reasoning.lower():
                                if "changed" not in reasoning.lower() and "reconsider" not in reasoning.lower():
                                    violations.append(ReasoningViolation(
                                        violation_type=ViolationType.BELIEF_CONTRADICTION,
                                        description=f"Sudden stance reversal on {topic} without justification",
                                        severity=ViolationSeverity.MEDIUM.value,
                                        expected=f"consistent_{stance}_stance",
                                        actual="sudden_reversal",
                                        suggestion="Add reasoning for stance change"
                                    ))

        return violations

    def _action_relates_to_topic(self, action: str, params: Dict[str, Any], topic: str) -> bool:
        """Check if an action relates to a belief topic."""
        topic_keywords = {
            "defendant_guilt": ["vote", "verdict", "guilty", "innocent", "evidence"],
            "trust_marcus": ["marcus", "trust", "believe"],
            "justice": ["justice", "fair", "punishment", "law"]
        }

        keywords = topic_keywords.get(topic.lower(), [topic.lower()])

        if any(kw in action.lower() for kw in keywords):
            return True

        params_str = str(params).lower()
        if any(kw in params_str for kw in keywords):
            return True

        return False

    def _reasoning_contradicts_stance(self, reasoning: str, stance: str, topic: str) -> bool:
        """Check if reasoning contradicts the current stance."""
        reasoning_lower = reasoning.lower()

        if stance == "for":
            if f"against {topic}" in reasoning_lower or f"not {topic}" in reasoning_lower:
                return True
        elif stance == "against":
            if f"for {topic}" in reasoning_lower or f"support {topic}" in reasoning_lower:
                return True

        return False


class NeedsChecker:
    """Check if decisions address critical needs."""

    def __init__(self, needs: NeedsSnapshot):
        self.needs = needs

    def check_needs_consistency(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str
    ) -> List[ReasoningViolation]:
        """Check if action addresses critical needs."""
        violations = []

        critical_needs = self.needs.get_critical_needs()

        if not critical_needs:
            return violations

        need_action_map = {
            "hunger": ["COLLECT", "INTERACT", "MOVE"],
            "fatigue": ["IDLE", "REFLECT", "SLEEP"],
            "boredom": ["MOVE", "INTERACT", "EMOTE", "EXPLORE"],
            "social": ["EMOTE", "INTERACT", "SPEAK"]
        }

        for need in critical_needs:
            addressing_actions = need_action_map.get(need, [])

            if action not in addressing_actions:
                if need.lower() not in reasoning.lower():
                    violations.append(ReasoningViolation(
                        violation_type=ViolationType.NEEDS_IGNORED,
                        description=f"Critical {need} need ignored in decision",
                        severity=ViolationSeverity.HIGH.value,
                        expected=f"address_{need}",
                        actual=action,
                        suggestion=f"Consider addressing {need} need or explain why deferred"
                    ))
                else:
                    violations.append(ReasoningViolation(
                        violation_type=ViolationType.NEEDS_IGNORED,
                        description=f"Critical {need} need acknowledged but not addressed",
                        severity=ViolationSeverity.MEDIUM.value,
                        expected=f"address_{need}",
                        actual=action,
                        context="Need mentioned in reasoning but not prioritized"
                    ))

        return violations


class ReasoningValidator:
    """Main validation orchestrator for agent reasoning."""

    def __init__(
        self,
        personality: Optional[PersonalitySnapshot] = None,
        beliefs: Optional[BeliefSnapshot] = None,
        needs: Optional[NeedsSnapshot] = None
    ):
        self.personality = personality or PersonalitySnapshot()
        self.beliefs = beliefs or BeliefSnapshot()
        self.needs = needs or NeedsSnapshot()

        self.trait_checker = TraitChecker(self.personality)
        self.belief_checker = BeliefChecker(self.beliefs)
        self.needs_checker = NeedsChecker(self.needs)

        logger.debug("ReasoningValidator initialized")

    def update_profiles(
        self,
        personality: Optional[PersonalitySnapshot] = None,
        beliefs: Optional[BeliefSnapshot] = None,
        needs: Optional[NeedsSnapshot] = None
    ) -> None:
        """Update the profiles used for validation."""
        if personality:
            self.personality = personality
            self.trait_checker = TraitChecker(personality)

        if beliefs:
            self.beliefs = beliefs
            self.belief_checker = BeliefChecker(beliefs)

        if needs:
            self.needs = needs
            self.needs_checker = NeedsChecker(needs)

    def validate(
        self,
        action: str,
        params: Dict[str, Any],
        reasoning: str,
        emotional_state: str = "neutral",
        heat_level: float = 0.0,
        personality_drivers: Optional[List[str]] = None
    ) -> ValidationResult:
        """Validate the reasoning for consistency."""
        result = ValidationResult(valid=True)
        personality_drivers = personality_drivers or []

        trait_violations = self.trait_checker.check_trait_consistency(
            action=action,
            params=params,
            emotional_state=emotional_state,
            reasoning=reasoning,
            heat_level=heat_level
        )

        for violation in trait_violations:
            result.add_violation(violation)

        belief_violations = self.belief_checker.check_belief_consistency(
            action=action,
            params=params,
            reasoning=reasoning,
            personality_drivers=personality_drivers
        )

        for violation in belief_violations:
            result.add_violation(violation)

        needs_violations = self.needs_checker.check_needs_consistency(
            action=action,
            params=params,
            reasoning=reasoning
        )

        for violation in needs_violations:
            result.add_violation(violation)

        result.recommendations = self._generate_recommendations(result)

        logger.debug(
            f"Validation complete: valid={result.valid}, "
            f"violations={result.violation_count}, severity={result.severity:.2f}"
        )

        return result

    def _generate_recommendations(self, result: ValidationResult) -> List[str]:
        """Generate recommendations based on violations."""
        recommendations = []

        if result.trait_violations > 0:
            recommendations.append(
                "Review personality trait alignment - some actions may not match character profile"
            )

        if result.belief_violations > 0:
            recommendations.append(
                "Check for belief-action consistency - beliefs should inform decisions"
            )

        if result.needs_violations > 0:
            recommendations.append(
                "Address critical needs - ignoring them may cause unrealistic behavior"
            )

        if result.severity > 0.5:
            recommendations.append(
                "HIGH severity issues detected - consider revising decision"
            )

        return recommendations

    def validate_decision_record(self, record: 'DecisionRecord') -> ValidationResult:
        """Validate a complete DecisionRecord."""
        return self.validate(
            action=record.final_action,
            params=record.action_params,
            reasoning=record.get_reasoning_summary(),
            emotional_state=record.context.emotional_state,
            heat_level=record.context.conversation_heat,
            personality_drivers=record.personality_drivers
        )
