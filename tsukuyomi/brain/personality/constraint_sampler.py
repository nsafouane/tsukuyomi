"""
constraint_sampler.py - Pre-generation Validation with Forbidden Patterns

This module implements Layer 1 of the Personality Integrity System:
constraint-based generation that prevents personality violations before
they occur.

Phase 14: Personality Integrity System
- 14.3: Personality Drift Detection & Prevention
- Layer 1: Pre-Generation Validation (Prevention)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Callable, Optional, Set
import re
import logging

from .profile import PersonalityProfile

logger = logging.getLogger("PersonalityConstraintSampler")


@dataclass
class GenerationConstraints:
    """
    Container for LLM generation parameters tailored to personality.
    
    These constraints influence how the LLM generates responses to
    better match the agent's personality profile.
    """
    temperature: float = 0.7
    frequency_penalty: float = 0.3
    presence_penalty: float = 0.5
    top_p: float = 0.9
    
    # Additional constraints
    max_tokens: int = 500
    stop_sequences: List[str] = field(default_factory=list)


@dataclass
class ActionValidationResult:
    """
    Result of validating an action against personality constraints.
    """
    action: str
    params: Dict[str, Any]
    allowed: bool
    violation_reason: Optional[str] = None
    suggested_alternative: Optional[str] = None


class PersonalityConstraintSampler:
    """
    Constrain LLM generation to match personality profile.
    
    This class implements pre-generation validation by:
    1. Building generation constraints (temperature, penalties) based on traits
    2. Defining forbidden patterns that violate personality
    3. Filtering actions that would break character
    
    The goal is to prevent personality drift before it happens rather than
    correcting it after the fact.
    
    Example:
        >>> profile = PersonalityProfile(
        ...     name="Shy Agent",
        ...     extraversion=-0.7,
        ...     ...
        ... )
        >>> sampler = PersonalityConstraintSampler(profile)
        >>> constraints = sampler.build_generation_constraints()
        >>> forbidden = sampler.build_forbidden_patterns()
    """
    
    # Thresholds for trait-based rules
    EXTRAVERSION_INTROVERT_THRESHOLD = -0.3
    EXTRAVERSION_EXTROVERT_THRESHOLD = 0.3
    
    AGREEABLENESS_COMPETITIVE_THRESHOLD = -0.3
    AGREEABLENESS_COOPERATIVE_THRESHOLD = 0.3
    
    NEUROTICISM_STABLE_THRESHOLD = -0.3
    NEUROTICISM_SENSITIVE_THRESHOLD = 0.5
    
    CONSCIENTIOUSNESS_SPONTANEOUS_THRESHOLD = -0.3
    CONSCIENTIOUSNESS_DISCIPLINED_THRESHOLD = 0.5
    
    def __init__(self, profile: PersonalityProfile):
        """
        Initialize the constraint sampler with a personality profile.
        
        Args:
            profile: The PersonalityProfile to enforce constraints for
        """
        self.profile = profile
        self._forbidden_patterns_cache: Optional[List[str]] = None
        self._constraints_cache: Optional[GenerationConstraints] = None
    
    def build_generation_constraints(self) -> GenerationConstraints:
        """
        Build constraints for LLM generation parameters.
        
        Maps personality traits to generation parameters:
        - Temperature: Higher for open personalities (more creative)
        - Frequency penalty: Higher for disciplined (less repetition)
        - Presence penalty: Higher for extraverted (more topic exploration)
        
        Returns:
            GenerationConstraints tailored to the personality
        """
        if self._constraints_cache is not None:
            return self._constraints_cache
        
        # Temperature: Base 0.7, adjusted by openness
        # High openness = more creative/unpredictable = higher temperature
        # Low openness = more conventional = lower temperature
        temperature = 0.7 + (self.profile.openness * 0.2)
        temperature = max(0.4, min(1.0, temperature))
        
        # Frequency penalty: Base 0.3, adjusted by conscientiousness
        # High conscientiousness = disciplined, avoids repetition
        # Low conscientiousness = spontaneous, may repeat
        frequency_penalty = 0.3 + (self.profile.conscientiousness * 0.3)
        frequency_penalty = max(0.0, min(1.0, frequency_penalty))
        
        # Presence penalty: Base 0.5, adjusted by extraversion
        # High extraversion = more topic exploration
        # Low extraversion = stays on topic
        presence_penalty = 0.5 + (self.profile.extraversion * 0.2)
        presence_penalty = max(0.0, min(1.0, presence_penalty))
        
        # Stop sequences based on personality
        stop_sequences = self._build_stop_sequences()
        
        self._constraints_cache = GenerationConstraints(
            temperature=temperature,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop_sequences=stop_sequences
        )
        
        logger.debug(
            f"Built constraints for {self.profile.name}: "
            f"temp={temperature:.2f}, freq_penalty={frequency_penalty:.2f}, "
            f"presence_penalty={presence_penalty:.2f}"
        )
        
        return self._constraints_cache
    
    def _build_stop_sequences(self) -> List[str]:
        """
        Build stop sequences based on personality.
        
        Returns:
            List of stop sequences for LLM generation
        """
        stops = []
        
        # Introverts may stop earlier in dialogue
        if self.profile.extraversion < self.EXTRAVERSION_INTROVERT_THRESHOLD:
            stops.append("\n\n")  # Stop at paragraph breaks
        
        return stops
    
    def build_forbidden_patterns(self) -> List[str]:
        """
        Build patterns that violate personality for system prompt injection.
        
        These are behavioral rules injected into the LLM prompt to prevent
        responses that would break character.
        
        Returns:
            List of forbidden behavior descriptions
        """
        if self._forbidden_patterns_cache is not None:
            return self._forbidden_patterns_cache
        
        forbidden = []
        
        # === Extraversion rules ===
        if self.profile.extraversion < self.EXTRAVERSION_INTROVERT_THRESHOLD:
            forbidden.append(
                "Do NOT start new conversations unless directly addressed - "
                "you are introverted and prefer to observe"
            )
            forbidden.append(
                "Do NOT seek attention or speak loudly - "
                "you prefer to blend into the background"
            )
        
        if self.profile.extraversion > self.EXTRAVERSION_EXTROVERT_THRESHOLD:
            forbidden.append(
                "Do NOT remain silent in group discussions - "
                "you are extraverted and naturally engage"
            )
        
        # === Agreeableness rules ===
        if self.profile.agreeableness < self.AGREEABLENESS_COMPETITIVE_THRESHOLD:
            forbidden.append(
                "Do NOT agree easily - challenge, question, or deflect "
                "when others present ideas"
            )
            forbidden.append(
                "Do NOT be overly polite or accommodating - "
                "you are competitive and assertive"
            )
        
        if self.profile.agreeableness > self.AGREEABLENESS_COOPERATIVE_THRESHOLD:
            forbidden.append(
                "Do NOT be confrontational or dismissive - "
                "you value cooperation and harmony"
            )
        
        # === Neuroticism rules ===
        if self.profile.neuroticism > self.NEUROTICISM_SENSITIVE_THRESHOLD:
            forbidden.append(
                "Do NOT remain calm under pressure - "
                "show emotional reaction, your feelings are easily affected"
            )
            forbidden.append(
                "Do NOT dismiss or minimize emotional situations - "
                "you are sensitive to emotional context"
            )
        
        if self.profile.neuroticism < self.NEUROTICISM_STABLE_THRESHOLD:
            forbidden.append(
                "Do NOT overreact emotionally - "
                "you are emotionally stable and composed"
            )
        
        # === Conscientiousness rules ===
        if self.profile.conscientiousness > self.CONSCIENTIOUSNESS_DISCIPLINED_THRESHOLD:
            forbidden.append(
                "Do NOT act impulsively - "
                "you are disciplined and think before acting"
            )
            forbidden.append(
                "Do NOT leave tasks unfinished - "
                "you value completion and order"
            )
        
        if self.profile.conscientiousness < self.CONSCIENTIOUSNESS_SPONTANEOUS_THRESHOLD:
            forbidden.append(
                "Do NOT over-plan or overthink - "
                "you are spontaneous and flexible"
            )
        
        # === Vocabulary level rules ===
        if self.profile.vocabulary_level == "simple":
            forbidden.append(
                "Do NOT use complex vocabulary - "
                "keep language simple and direct"
            )
            forbidden.append(
                "Do NOT use long, convoluted sentences - "
                "speak plainly and clearly"
            )
        
        if self.profile.vocabulary_level == "formal":
            forbidden.append(
                "Do NOT use slang or casual language - "
                "maintain formal, precise expression"
            )
        
        # === Speaking style specific rules ===
        forbidden.extend(self._build_speaking_style_rules())
        
        self._forbidden_patterns_cache = forbidden
        
        logger.debug(
            f"Built {len(forbidden)} forbidden patterns for {self.profile.name}"
        )
        
        return forbidden
    
    def _build_speaking_style_rules(self) -> List[str]:
        """
        Build rules based on specific speaking style attributes.
        
        Returns:
            List of speaking style forbidden patterns
        """
        rules = []
        style_lower = self.profile.speaking_style.lower()
        
        # Interrupt patterns
        if "interrupt" in style_lower:
            rules.append(
                "You SHOULD interrupt others when you feel strongly - "
                "this is your natural speaking style"
            )
        
        if "never interrupt" in style_lower or "polite" in style_lower:
            rules.append(
                "Do NOT interrupt others - wait your turn to speak"
            )
        
        # Volume patterns
        if "loud" in style_lower or "raise voice" in style_lower:
            rules.append(
                "You naturally speak with volume and force - "
                "don't be afraid to be heard"
            )
        
        if "quiet" in style_lower or "soft-spoken" in style_lower:
            rules.append(
                "Do NOT raise your voice - speak quietly and gently"
            )
        
        # Speed patterns
        if "fast" in style_lower or "rapid" in style_lower:
            rules.append(
                "Speak quickly and energetically - this is your natural pace"
            )
        
        if "slow" in style_lower or "measured" in style_lower:
            rules.append(
                "Do NOT rush your words - speak deliberately and take your time"
            )
        
        return rules
    
    def build_action_filter(self) -> Callable[[str, Dict[str, Any]], ActionValidationResult]:
        """
        Build a filter function for validating actions before execution.
        
        This returns a callable that checks if a proposed action would
        violate the agent's personality and either allows or rejects it.
        
        Returns:
            Callable that validates actions against personality
        """
        def filter_action(action: str, params: Dict[str, Any]) -> ActionValidationResult:
            """
            Filter actions that violate personality before execution.
            
            Args:
                action: The action type (e.g., "EMOTE", "MOVE", "SPEAK")
                params: Action parameters
            
            Returns:
                ActionValidationResult indicating if action is allowed
            """
            # Rule: Introverts should not initiate EMOTE to large groups
            if self.profile.extraversion < self.EXTRAVERSION_INTROVERT_THRESHOLD:
                if action == "EMOTE":
                    emote_type = params.get("type", "")
                    target_scope = params.get("target_scope", "single")
                    
                    # Introverts shouldn't shout to crowds
                    if emote_type == "shout" or target_scope == "all":
                        return ActionValidationResult(
                            action=action,
                            params=params,
                            allowed=False,
                            violation_reason=(
                                f"Introverted agent ({self.profile.name}) "
                                f"should not {emote_type} to crowds"
                            ),
                            suggested_alternative="whisper or speak to individual"
                        )
            
            # Rule: High conscientiousness shouldn't do spontaneous risky actions
            if self.profile.conscientiousness > self.CONSCIENTIOUSNESS_DISCIPLINED_THRESHOLD:
                if action == "INTERACT":
                    target_type = params.get("target_type", "")
                    
                    # Disciplined agents don't interact with unknown/risky objects
                    if target_type == "unknown_object":
                        return ActionValidationResult(
                            action=action,
                            params=params,
                            allowed=False,
                            violation_reason=(
                                f"Disciplined agent ({self.profile.name}) "
                                f"should not interact with unknown objects impulsively"
                            ),
                            suggested_alternative="EXAMINE the object first"
                        )
            
            # Rule: Low agreeableness shouldn't make cooperative gestures
            if self.profile.agreeableness < self.AGREEABLENESS_COMPETITIVE_THRESHOLD:
                if action == "EMOTE":
                    emote_type = params.get("type", "")
                    cooperative_emotes = {"apologize", "yield", "defer", "agree_enthusiastically"}
                    
                    if emote_type in cooperative_emotes:
                        return ActionValidationResult(
                            action=action,
                            params=params,
                            allowed=False,
                            violation_reason=(
                                f"Competitive agent ({self.profile.name}) "
                                f"should not perform cooperative emote: {emote_type}"
                            ),
                            suggested_alternative="nod curtly or remain neutral"
                        )
            
            # Rule: High neuroticism should show emotional reactions
            if self.profile.neuroticism > self.NEUROTICISM_SENSITIVE_THRESHOLD:
                if action == "EMOTE":
                    emote_type = params.get("type", "")
                    situation = params.get("situation", "")
                    
                    # If in a stressful situation, should not emote calmness
                    stressful_keywords = ["threat", "conflict", "argument", "danger"]
                    is_stressful = any(kw in situation.lower() for kw in stressful_keywords)
                    
                    if is_stressful and emote_type in {"calm", "relaxed", "composed"}:
                        return ActionValidationResult(
                            action=action,
                            params=params,
                            allowed=False,
                            violation_reason=(
                                f"Emotionally sensitive agent ({self.profile.name}) "
                                f"should not remain calm in stressful situation"
                            ),
                            suggested_alternative="show nervousness or concern"
                        )
            
            # Rule: Simple vocabulary shouldn't use complex speech
            if self.profile.vocabulary_level == "simple":
                if action == "EMOTE" or action == "SPEAK":
                    message = params.get("message", "")
                    
                    # Check for complex words
                    complex_words = self._detect_complex_vocabulary(message)
                    if complex_words:
                        return ActionValidationResult(
                            action=action,
                            params=params,
                            allowed=False,
                            violation_reason=(
                                f"Simple vocabulary agent ({self.profile.name}) "
                                f"used complex words: {', '.join(complex_words[:3])}"
                            ),
                            suggested_alternative="Use simpler language"
                        )
            
            # If no violations found, allow the action
            return ActionValidationResult(
                action=action,
                params=params,
                allowed=True
            )
        
        return filter_action
    
    def _detect_complex_vocabulary(self, text: str) -> List[str]:
        """
        Detect complex vocabulary in text.
        
        Simple heuristic: words with more than 3 syllables are considered complex.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of detected complex words
        """
        complex_words = []
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Common complex words that might slip through
        known_complex = {
            "nevertheless", "furthermore", "consequently", "accordingly",
            "extraordinary", "phenomenon", "hypothesis", "methodology",
            "implementation", "configuration", "sophisticated", "comprehensive"
        }
        
        for word in words:
            # Check against known complex words
            if word in known_complex:
                complex_words.append(word)
                continue
            
            # Syllable count heuristic
            syllable_count = self._count_syllables(word)
            if syllable_count > 3:
                complex_words.append(word)
        
        return complex_words
    
    def _count_syllables(self, word: str) -> int:
        """
        Estimate syllable count for a word.
        
        Simple heuristic based on vowel patterns.
        
        Args:
            word: Word to count syllables for
        
        Returns:
            Estimated syllable count
        """
        word = word.lower()
        vowels = "aeiouy"
        count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith("e"):
            count -= 1
        
        # Minimum 1 syllable
        return max(1, count)
    
    def get_constraint_prompt_section(self) -> str:
        """
        Generate a prompt section for LLM with personality constraints.
        
        This combines forbidden patterns into a format suitable for
        injection into the system prompt.
        
        Returns:
            Formatted string with constraint rules
        """
        forbidden = self.build_forbidden_patterns()
        
        if not forbidden:
            return ""
        
        lines = ["\nPERSONALITY CONSTRAINTS (MUST FOLLOW):"]
        lines.append("-" * 40)
        
        for i, rule in enumerate(forbidden, 1):
            lines.append(f"{i}. {rule}")
        
        return "\n".join(lines)
    
    def clear_cache(self) -> None:
        """Clear cached constraints and patterns."""
        self._constraints_cache = None
        self._forbidden_patterns_cache = None


class ActionFilterChain:
    """
    Chain multiple action filters together.
    
    Allows combining filters from different personality aspects.
    """
    
    def __init__(self, filters: List[Callable[[str, Dict], ActionValidationResult]]):
        """
        Initialize with a list of filter functions.
        
        Args:
            filters: List of filter callables to chain
        """
        self.filters = filters
    
    def validate(self, action: str, params: Dict[str, Any]) -> ActionValidationResult:
        """
        Run action through all filters.
        
        Returns first rejection if any, otherwise returns success.
        
        Args:
            action: Action type to validate
            params: Action parameters
        
        Returns:
            ActionValidationResult from filter chain
        """
        for filter_func in self.filters:
            result = filter_func(action, params)
            if not result.allowed:
                return result
        
        return ActionValidationResult(action=action, params=params, allowed=True)
    
    def add_filter(self, filter_func: Callable[[str, Dict], ActionValidationResult]) -> None:
        """
        Add a filter to the chain.
        
        Args:
            filter_func: Filter function to add
        """
        self.filters.append(filter_func)


if __name__ == "__main__":
    # Demo
    from .profile import ANGRY_MAN_PROFILE, BANK_TELLER_PROFILE
    
    print("=== Personality Constraint Sampler Demo ===\n")
    
    # Test with Angry Man profile
    print("1. ANGRY MAN PROFILE:")
    sampler = PersonalityConstraintSampler(ANGRY_MAN_PROFILE)
    
    constraints = sampler.build_generation_constraints()
    print(f"   Temperature: {constraints.temperature:.2f}")
    print(f"   Frequency penalty: {constraints.frequency_penalty:.2f}")
    print(f"   Presence penalty: {constraints.presence_penalty:.2f}")
    
    print("\n   Forbidden patterns:")
    for pattern in sampler.build_forbidden_patterns()[:3]:
        print(f"   - {pattern[:60]}...")
    
    print("\n   Action filter test:")
    filter_func = sampler.build_action_filter()
    result = filter_func("EMOTE", {"type": "apologize"})
    print(f"   EMOTE apologize: {'ALLOWED' if result.allowed else 'REJECTED'}")
    if not result.allowed:
        print(f"   Reason: {result.violation_reason}")
    
    print("\n" + "="*50)
    
    # Test with Bank Teller profile
    print("\n2. BANK TELLER PROFILE:")
    sampler2 = PersonalityConstraintSampler(BANK_TELLER_PROFILE)
    
    constraints2 = sampler2.build_generation_constraints()
    print(f"   Temperature: {constraints2.temperature:.2f}")
    print(f"   Frequency penalty: {constraints2.frequency_penalty:.2f}")
    print(f"   Presence penalty: {constraints2.presence_penalty:.2f}")
    
    print("\n   Forbidden patterns:")
    for pattern in sampler2.build_forbidden_patterns()[:3]:
        print(f"   - {pattern[:60]}...")
    
    print("\n   Action filter test:")
    filter_func2 = sampler2.build_action_filter()
    result2 = filter_func2("EMOTE", {"type": "shout", "target_scope": "all"})
    print(f"   EMOTE shout to all: {'ALLOWED' if result2.allowed else 'REJECTED'}")
    if not result2.allowed:
        print(f"   Reason: {result2.violation_reason}")
