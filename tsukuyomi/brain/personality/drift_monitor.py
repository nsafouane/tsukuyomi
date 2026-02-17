"""
drift_monitor.py - Post-generation Drift Detection with EMA

This module implements Layer 2 of the Personality Integrity System:
post-generation drift detection that monitors agent behavior for
inconsistencies with their personality profile.

Phase 14: Personality Integrity System
- 14.3: Personality Drift Detection & Prevention
- Layer 2: Post-Generation Drift Detection (Monitoring)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import re
import math

from .profile import PersonalityProfile

logger = logging.getLogger("PersonalityDriftMonitor")


@dataclass
class BehaviorSnapshot:
    """
    Snapshot of agent behavior at a point in time.
    
    Captures the output (response/action) and context for later
    analysis against the personality profile.
    """
    tick: int
    response: str
    context: str
    action: Optional[str] = None
    action_params: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DriftReport:
    """
    Report of detected personality drift.
    
    Contains information about what drifted, how severely, and
    the smoothed EMA score for trend tracking.
    """
    agent_name: str
    tick: int
    drifts: List[str]
    severity: float  # 0.0 to 1.0 for this specific check
    ema_severity: float  # Smoothed metric for trend tracking
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def has_drift(self) -> bool:
        """Check if any drift was detected."""
        return len(self.drifts) > 0
    
    @property
    def consistency_score(self) -> float:
        """
        Calculate consistency score (inverse of EMA severity).
        
        Returns:
            0.0 to 1.0 where 1.0 is fully consistent
        """
        return 1.0 - min(1.0, self.ema_severity)


@dataclass
class PersonalityEvolutionEvent:
    """
    Track intentional personality changes.
    
    Personality can evolve intentionally through dramatic events,
    character growth, or trauma. This tracks those changes.
    """
    tick: int
    trait: str  # "openness", "agreeableness", etc.
    change: float  # -0.1 to +0.1 per event
    reason: str  # "traumatic_event", "character_growth", etc.
    trigger_event: str  # What caused this change
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class PersonalityDriftMonitor:
    """
    Detect when agent behavior drifts from personality profile.
    
    This class implements post-generation monitoring by analyzing
    responses and actions for personality violations. It uses
    Exponential Moving Average (EMA) to track drift trends over time.
    
    Key Features:
    - Vocabulary level checking
    - Agreeableness pattern detection
    - Extraversion behavior validation
    - Speaking style consistency
    - EMA-based trend tracking
    
    Example:
        >>> profile = PersonalityProfile(name="Angry Agent", ...)
        >>> monitor = PersonalityDriftMonitor(profile)
        >>> report = monitor.analyze_response("I totally agree with you!", context)
        >>> if report.has_drift:
        ...     print(f"Drift detected: {report.drifts}")
    """
    
    # Default configuration
    DEFAULT_EMA_ALPHA: float = 0.3  # Weight for new samples in EMA
    DRIFT_THRESHOLD: float = 0.1  # EMA threshold for alerting
    MAX_HISTORY_SIZE: int = 100  # Maximum behavior snapshots to keep
    
    # Complex word patterns for vocabulary checking
    COMPLEX_WORD_PATTERNS = [
        r'\b\w{12,}\b',  # Words with 12+ characters
        r'\b(nevertheless|furthermore|consequently|accordingly)\b',
        r'\b(extraordinary|phenomenon|hypothesis|methodology)\b',
        r'\b(implementation|configuration|sophisticated)\b',
    ]
    
    # Agreeable phrases for competitive personality checking
    AGREEABLE_PHRASES = [
        r'\b(you\'?re right|I agree|exactly|absolutely|of course)\b',
        r'\b(that makes sense|good point|fair enough)\b',
        r'\b(I understand|you\'?re correct|I see your point)\b',
    ]
    
    # Disagreeable phrases for cooperative personality checking
    DISAGREEABLE_PHRASES = [
        r'\b(that\'?s wrong|I disagree|you\'?re mistaken|no way)\b',
        r'\b(rubbish|nonsense|bullshit|ridiculous)\b',
        r'\b(I don\'?t think so|I can\'?t accept that)\b',
    ]
    
    # Emotional/calm indicators for neuroticism checking
    EMOTIONAL_INDICATORS = [
        r'!{2,}',  # Multiple exclamation marks
        r'\?{2,}',  # Multiple question marks
        r'\b(angry|furious|outraged|terrified|horrified)\b',
        r'\b(I can\'?t believe|this is unacceptable|how dare)\b',
    ]
    
    CALM_INDICATORS = [
        r'\b(calm|relaxed|peaceful|composed|serene)\b',
        r'\b(that\'?s fine|no problem|it\'?s okay|I\'?m fine)\b',
    ]
    
    def __init__(
        self,
        profile: PersonalityProfile,
        ema_alpha: float = DEFAULT_EMA_ALPHA
    ):
        """
        Initialize the drift monitor with a personality profile.
        
        Args:
            profile: The PersonalityProfile to monitor against
            ema_alpha: Weight for new samples in EMA calculation (0.0-1.0)
        """
        self.profile = profile
        self.ema_alpha = ema_alpha
        
        # Behavior tracking
        self.behavior_history: List[BehaviorSnapshot] = []
        self.drift_reports: List[DriftReport] = []
        
        # EMA drift score tracking
        self.drift_score_ema: float = 0.0
        
        # Component EMA scores for detailed tracking
        self.vocabulary_drift_ema: float = 0.0
        self.agreeableness_drift_ema: float = 0.0
        self.extraversion_drift_ema: float = 0.0
        self.neuroticism_drift_ema: float = 0.0
        self.style_drift_ema: float = 0.0
    
    def analyze_response(
        self,
        response: str,
        context: str,
        tick: int,
        action: Optional[str] = None,
        action_params: Optional[Dict[str, Any]] = None
    ) -> DriftReport:
        """
        Check if response matches expected personality.
        
        This is the main entry point for drift detection. It runs
        multiple checks against the profile and returns a comprehensive
        drift report.
        
        Args:
            response: The agent's response/speech to analyze
            context: The context in which the response occurred
            tick: Current simulation tick
            action: Optional action type if this was an action
            action_params: Optional action parameters
        
        Returns:
            DriftReport with detected drifts and severity scores
        """
        # Store behavior snapshot
        snapshot = BehaviorSnapshot(
            tick=tick,
            response=response,
            context=context,
            action=action,
            action_params=action_params
        )
        self.behavior_history.append(snapshot)
        self._trim_history()
        
        # Run drift checks
        drifts = []
        component_scores = {}
        
        # 1. Vocabulary check
        vocab_drift, vocab_score = self._check_vocabulary(response)
        drifts.extend(vocab_drift)
        component_scores['vocabulary'] = vocab_score
        self._update_component_ema('vocabulary', vocab_score)
        
        # 2. Agreeableness check
        agree_drift, agree_score = self._check_agreeableness(response)
        drifts.extend(agree_drift)
        component_scores['agreeableness'] = agree_score
        self._update_component_ema('agreeableness', agree_score)
        
        # 3. Extraversion check
        extra_drift, extra_score = self._check_extraversion(response, context)
        drifts.extend(extra_drift)
        component_scores['extraversion'] = extra_score
        self._update_component_ema('extraversion', extra_score)
        
        # 4. Neuroticism check
        neuro_drift, neuro_score = self._check_neuroticism(response)
        drifts.extend(neuro_drift)
        component_scores['neuroticism'] = neuro_score
        self._update_component_ema('neuroticism', neuro_score)
        
        # 5. Speaking style check
        style_drift, style_score = self._check_speaking_style(response)
        drifts.extend(style_drift)
        component_scores['style'] = style_score
        self._update_component_ema('style', style_score)
        
        # Calculate overall drift score
        drift_score = sum(component_scores.values()) / len(component_scores)
        
        # Update EMA
        self.drift_score_ema = (
            self.ema_alpha * drift_score +
            (1 - self.ema_alpha) * self.drift_score_ema
        )
        
        # Create report
        report = DriftReport(
            agent_name=self.profile.name,
            tick=tick,
            drifts=drifts,
            severity=drift_score,
            ema_severity=self.drift_score_ema
        )
        
        self.drift_reports.append(report)
        
        # Log if significant drift
        if drift_score > self.DRIFT_THRESHOLD:
            logger.warning(
                f"Personality drift detected for {self.profile.name}: "
                f"severity={drift_score:.2f}, EMA={self.drift_score_ema:.2f}"
            )
        
        return report
    
    def _check_vocabulary(self, response: str) -> Tuple[List[str], float]:
        """
        Check if vocabulary matches the profile's vocabulary level.
        
        Args:
            response: Response text to check
        
        Returns:
            Tuple of (drift_descriptions, drift_score)
        """
        drifts = []
        score = 0.0
        
        if self.profile.vocabulary_level == "simple":
            # Check for complex vocabulary
            complex_words = self._count_complex_words(response)
            if complex_words > 3:
                drifts.append(
                    f"Vocabulary too complex for 'simple' profile "
                    f"(found {complex_words} complex words)"
                )
                score = min(1.0, complex_words * 0.05)
        
        elif self.profile.vocabulary_level == "formal":
            # Check for slang or casual language
            casual_indicators = self._detect_casual_language(response)
            if casual_indicators > 2:
                drifts.append(
                    f"Language too casual for 'formal' profile "
                    f"(found {casual_indicators} casual elements)"
                )
                score = min(1.0, casual_indicators * 0.05)
        
        return drifts, score
    
    def _check_agreeableness(self, response: str) -> Tuple[List[str], float]:
        """
        Check if agreeableness patterns match the profile.
        
        Args:
            response: Response text to check
        
        Returns:
            Tuple of (drift_descriptions, drift_score)
        """
        drifts = []
        score = 0.0
        response_lower = response.lower()
        
        if self.profile.agreeableness < -0.3:
            # Competitive personality - shouldn't be overly agreeable
            agreeable_count = self._count_pattern_matches(
                response_lower, self.AGREEABLE_PHRASES
            )
            if agreeable_count > 2:
                drifts.append(
                    f"Too agreeable for competitive personality "
                    f"(found {agreeable_count} agreeable phrases)"
                )
                score = min(0.5, agreeable_count * 0.1)
        
        elif self.profile.agreeableness > 0.3:
            # Cooperative personality - shouldn't be overly disagreeable
            disagreeable_count = self._count_pattern_matches(
                response_lower, self.DISAGREEABLE_PHRASES
            )
            if disagreeable_count > 1:
                drifts.append(
                    f"Too disagreeable for cooperative personality "
                    f"(found {disagreeable_count} disagreeable phrases)"
                )
                score = min(0.5, disagreeable_count * 0.15)
        
        return drifts, score
    
    def _check_extraversion(
        self,
        response: str,
        context: str
    ) -> Tuple[List[str], float]:
        """
        Check if extraversion patterns match the profile.
        
        Args:
            response: Response text to check
            context: Context of the response
        
        Returns:
            Tuple of (drift_descriptions, drift_score)
        """
        drifts = []
        score = 0.0
        
        if self.profile.extraversion < -0.3:
            # Introvert - shouldn't initiate conversation
            if self._is_initiating_conversation(response, context):
                drifts.append(
                    "Introvert initiating conversation unexpectedly"
                )
                score = 0.25
            
            # Check for excessive exclamation marks (enthusiasm)
            exclamation_count = response.count('!')
            if exclamation_count > 3:
                drifts.append(
                    f"Too enthusiastic for introverted personality "
                    f"({exclamation_count} exclamation marks)"
                )
                score += min(0.2, exclamation_count * 0.02)
        
        elif self.profile.extraversion > 0.3:
            # Extravert - should engage, not be too passive
            if self._is_overly_passive(response):
                drifts.append(
                    "Extravert being too passive in conversation"
                )
                score = 0.15
        
        return drifts, score
    
    def _check_neuroticism(self, response: str) -> Tuple[List[str], float]:
        """
        Check if emotional expression matches neuroticism level.
        
        Args:
            response: Response text to check
        
        Returns:
            Tuple of (drift_descriptions, drift_score)
        """
        drifts = []
        score = 0.0
        response_lower = response.lower()
        
        if self.profile.neuroticism > 0.5:
            # Emotionally sensitive - should show emotion
            emotional_count = self._count_pattern_matches(
                response_lower, self.EMOTIONAL_INDICATORS
            )
            calm_count = self._count_pattern_matches(
                response_lower, self.CALM_INDICATORS
            )
            
            # High calm indicators in a sensitive person
            if calm_count > 2 and emotional_count == 0:
                drifts.append(
                    "Emotionally sensitive personality appearing too calm"
                )
                score = 0.2
        
        elif self.profile.neuroticism < -0.3:
            # Emotionally stable - should remain composed
            emotional_count = self._count_pattern_matches(
                response_lower, self.EMOTIONAL_INDICATORS
            )
            
            if emotional_count > 2:
                drifts.append(
                    f"Emotionally stable personality showing volatility "
                    f"({emotional_count} emotional indicators)"
                )
                score = min(0.3, emotional_count * 0.1)
        
        return drifts, score
    
    def _check_speaking_style(self, response: str) -> Tuple[List[str], float]:
        """
        Check if speaking style matches the profile.
        
        Args:
            response: Response text to check
        
        Returns:
            Tuple of (drift_descriptions, drift_score)
        """
        drifts = []
        score = 0.0
        style_lower = self.profile.speaking_style.lower()
        
        # Check for interruption style
        if "interrupt" in style_lower:
            # This agent should interrupt - check if response is too polite
            if response.endswith("?") and "excuse me" in response.lower():
                drifts.append(
                    "Agent with interrupting style being too polite"
                )
                score = 0.15
        
        # Check for quiet/soft-spoken style
        if "quiet" in style_lower or "soft" in style_lower:
            # Check for all caps or excessive punctuation
            if response.isupper() or response.count('!') > 2:
                drifts.append(
                    "Soft-spoken agent speaking loudly (caps/exclamation)"
                )
                score = 0.2
        
        # Check for aggressive/loud style
        if "aggressive" in style_lower or "loud" in style_lower:
            # Check if response is too meek
            if self._is_overly_passive(response):
                drifts.append(
                    "Aggressive agent being too passive/meek"
                )
                score = 0.25
        
        return drifts, score
    
    def _count_complex_words(self, text: str) -> int:
        """Count complex words in text based on patterns."""
        count = 0
        for pattern in self.COMPLEX_WORD_PATTERNS:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count
    
    def _detect_casual_language(self, text: str) -> int:
        """Detect casual language indicators."""
        casual_patterns = [
            r'\b(yeah|yep|nah|nope|gonna|wanna|gotta)\b',
            r'\b(awesome|cool|dude|bro|sup)\b',
            r'\b(lol|lmao|omg|wtf)\b',
            r'\'s\s',  # Contractions (simplified)
        ]
        count = 0
        for pattern in casual_patterns:
            count += len(re.findall(pattern, text.lower()))
        return count
    
    def _count_pattern_matches(self, text: str, patterns: List[str]) -> int:
        """Count how many patterns match in text."""
        count = 0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count
    
    def _is_initiating_conversation(self, response: str, context: str) -> bool:
        """
        Determine if response is initiating a new conversation.
        
        Heuristic: If context doesn't mention the agent being addressed
        and response starts with a greeting or question.
        """
        # Check if agent was directly addressed in context
        if self.profile.name.lower() in context.lower():
            return False
        
        # Check for initiation patterns
        initiation_patterns = [
            r'^(hey|hi|hello|excuse me|pardon me)',
            r'^(can I|may I|would you)',
            r'^(I wanted to|I\'d like to)',
        ]
        
        response_lower = response.lower()
        for pattern in initiation_patterns:
            if re.match(pattern, response_lower):
                return True
        
        return False
    
    def _is_overly_passive(self, response: str) -> bool:
        """
        Determine if response is overly passive.
        
        Heuristic: Short responses with passive language.
        """
        if len(response) < 20:
            return True
        
        passive_indicators = [
            'i suppose', 'maybe', 'perhaps', 'i guess',
            'if you want', 'whatever you think'
        ]
        
        response_lower = response.lower()
        passive_count = sum(1 for ind in passive_indicators if ind in response_lower)
        
        return passive_count >= 2
    
    def _update_component_ema(self, component: str, score: float) -> None:
        """Update EMA for a specific component."""
        if component == 'vocabulary':
            self.vocabulary_drift_ema = (
                self.ema_alpha * score +
                (1 - self.ema_alpha) * self.vocabulary_drift_ema
            )
        elif component == 'agreeableness':
            self.agreeableness_drift_ema = (
                self.ema_alpha * score +
                (1 - self.ema_alpha) * self.agreeableness_drift_ema
            )
        elif component == 'extraversion':
            self.extraversion_drift_ema = (
                self.ema_alpha * score +
                (1 - self.ema_alpha) * self.extraversion_drift_ema
            )
        elif component == 'neuroticism':
            self.neuroticism_drift_ema = (
                self.ema_alpha * score +
                (1 - self.ema_alpha) * self.neuroticism_drift_ema
            )
        elif component == 'style':
            self.style_drift_ema = (
                self.ema_alpha * score +
                (1 - self.ema_alpha) * self.style_drift_ema
            )
    
    def _trim_history(self) -> None:
        """Trim behavior history to max size."""
        if len(self.behavior_history) > self.MAX_HISTORY_SIZE:
            self.behavior_history = self.behavior_history[-self.MAX_HISTORY_SIZE:]
    
    def get_consistency_score(self) -> float:
        """
        Return personality consistency score (0.0 to 1.0).
        
        Higher scores indicate more consistent behavior.
        
        Returns:
            Consistency score based on EMA drift
        """
        return 1.0 - min(1.0, self.drift_score_ema)
    
    def get_component_scores(self) -> Dict[str, float]:
        """
        Get consistency scores by component.
        
        Returns:
            Dictionary of component -> consistency score
        """
        return {
            'vocabulary': 1.0 - min(1.0, self.vocabulary_drift_ema),
            'agreeableness': 1.0 - min(1.0, self.agreeableness_drift_ema),
            'extraversion': 1.0 - min(1.0, self.extraversion_drift_ema),
            'neuroticism': 1.0 - min(1.0, self.neuroticism_drift_ema),
            'style': 1.0 - min(1.0, self.style_drift_ema),
        }
    
    def get_drift_trend(self) -> str:
        """
        Analyze drift trend over recent history.
        
        Returns:
            Trend description: "improving", "stable", or "worsening"
        """
        if len(self.drift_reports) < 3:
            return "insufficient_data"
        
        # Compare recent reports
        recent = self.drift_reports[-3:]
        
        if recent[-1].ema_severity < recent[0].ema_severity:
            return "improving"
        elif recent[-1].ema_severity > recent[0].ema_severity:
            return "worsening"
        else:
            return "stable"
    
    def reset_metrics(self) -> None:
        """Reset all EMA metrics and history."""
        self.drift_score_ema = 0.0
        self.vocabulary_drift_ema = 0.0
        self.agreeableness_drift_ema = 0.0
        self.extraversion_drift_ema = 0.0
        self.neuroticism_drift_ema = 0.0
        self.style_drift_ema = 0.0
        self.behavior_history.clear()
        self.drift_reports.clear()
    
    def get_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of drift monitoring.
        
        Returns:
            Dictionary with comprehensive drift statistics
        """
        return {
            'agent_name': self.profile.name,
            'overall_consistency': self.get_consistency_score(),
            'component_consistency': self.get_component_scores(),
            'drift_trend': self.get_drift_trend(),
            'total_checks': len(self.drift_reports),
            'drifts_detected': sum(1 for r in self.drift_reports if r.has_drift),
            'current_ema': self.drift_score_ema,
        }


class PersonalityEvolutionManager:
    """
    Manage intentional personality changes over time.
    
    Personality can evolve through dramatic events, character growth,
    or trauma. This manager tracks and limits such changes to maintain
    personality integrity while allowing for meaningful character arcs.
    
    Example:
        >>> profile = PersonalityProfile(name="Agent", ...)
        >>> manager = PersonalityEvolutionManager(profile)
        >>> manager.evolve_trait(
        ...     trait="agreeableness",
        ...     change=0.1,
        ...     reason="character_growth",
        ...     trigger="witnessed_kindness",
        ...     tick=100
        ... )
    """
    
    # Maximum total change allowed per trait from base profile
    MAX_DRIFT_PER_TRAIT: float = 0.3
    
    # Maximum change per single event
    MAX_CHANGE_PER_EVENT: float = 0.1
    
    # Valid evolution reasons
    VALID_REASONS = {
        "traumatic_event",
        "character_growth",
        "relationship_development",
        "life_experience",
        "forced_adaptation",
        "revelation",
    }
    
    def __init__(self, profile: PersonalityProfile):
        """
        Initialize evolution manager with a personality profile.
        
        Args:
            profile: The PersonalityProfile to manage evolution for
        """
        self.profile = profile
        self.evolution_history: List[PersonalityEvolutionEvent] = []
        self._base_traits = {
            'openness': profile.openness,
            'conscientiousness': profile.conscientiousness,
            'extraversion': profile.extraversion,
            'agreeableness': profile.agreeableness,
            'neuroticism': profile.neuroticism,
        }
    
    def evolve_trait(
        self,
        trait: str,
        change: float,
        reason: str,
        trigger: str,
        tick: int
    ) -> bool:
        """
        Apply intentional personality change.
        
        Validates that the change is within allowed bounds before
        applying. Changes are tracked for analysis and potential rollback.
        
        Args:
            trait: Name of the trait to evolve
            change: Amount to change (-0.1 to +0.1)
            reason: Reason for the change (must be in VALID_REASONS)
            trigger: Specific event that triggered the change
            tick: Current simulation tick
        
        Returns:
            True if evolution was applied, False if rejected
        """
        # Validate trait name
        if trait not in self._base_traits:
            logger.error(f"Invalid trait name: {trait}")
            return False
        
        # Validate reason
        if reason not in self.VALID_REASONS:
            logger.error(f"Invalid evolution reason: {reason}")
            return False
        
        # Validate change magnitude
        change = max(-self.MAX_CHANGE_PER_EVENT, min(self.MAX_CHANGE_PER_EVENT, change))
        
        # Check total drift from base
        total_change = sum(
            e.change for e in self.evolution_history if e.trait == trait
        )
        
        if abs(total_change + change) > self.MAX_DRIFT_PER_TRAIT:
            logger.warning(
                f"Trait {trait} evolution capped at {self.MAX_DRIFT_PER_TRAIT}. "
                f"Current total change: {total_change:.2f}"
            )
            return False
        
        # Record evolution
        event = PersonalityEvolutionEvent(
            tick=tick,
            trait=trait,
            change=change,
            reason=reason,
            trigger_event=trigger
        )
        self.evolution_history.append(event)
        
        # Apply change to profile
        current_value = getattr(self.profile, trait)
        new_value = max(-1.0, min(1.0, current_value + change))
        setattr(self.profile, trait, new_value)
        
        logger.info(
            f"Personality evolution: {self.profile.name}'s {trait} "
            f"changed by {change:+.2f} ({reason}) - now {new_value:.2f}"
        )
        
        return True
    
    def get_trait_evolution_summary(self, trait: str) -> Dict[str, Any]:
        """
        Get summary of evolution for a specific trait.
        
        Args:
            trait: Name of the trait
        
        Returns:
            Dictionary with evolution statistics
        """
        trait_events = [e for e in self.evolution_history if e.trait == trait]
        
        if not trait_events:
            return {
                'trait': trait,
                'base_value': self._base_traits.get(trait, 0.0),
                'current_value': getattr(self.profile, trait, 0.0),
                'total_change': 0.0,
                'events': []
            }
        
        total_change = sum(e.change for e in trait_events)
        
        return {
            'trait': trait,
            'base_value': self._base_traits.get(trait, 0.0),
            'current_value': getattr(self.profile, trait, 0.0),
            'total_change': total_change,
            'events': [
                {
                    'tick': e.tick,
                    'change': e.change,
                    'reason': e.reason,
                    'trigger': e.trigger_event
                }
                for e in trait_events
            ]
        }
    
    def can_evolve(self, trait: str, change: float) -> bool:
        """
        Check if a trait can evolve by the given amount.
        
        Args:
            trait: Name of the trait
            change: Proposed change amount
        
        Returns:
            True if evolution is allowed, False otherwise
        """
        if trait not in self._base_traits:
            return False
        
        total_change = sum(
            e.change for e in self.evolution_history if e.trait == trait
        )
        
        return abs(total_change + change) <= self.MAX_DRIFT_PER_TRAIT
    
    def get_available_evolution_room(self, trait: str) -> float:
        """
        Get remaining evolution room for a trait.
        
        Args:
            trait: Name of the trait
        
        Returns:
            Amount of change still available (positive or negative)
        """
        if trait not in self._base_traits:
            return 0.0
        
        total_change = sum(
            e.change for e in self.evolution_history if e.trait == trait
        )
        
        # Return how much more change is allowed in either direction
        positive_room = self.MAX_DRIFT_PER_TRAIT - total_change
        negative_room = -self.MAX_DRIFT_PER_TRAIT - total_change
        
        return max(positive_room, abs(negative_room))


if __name__ == "__main__":
    # Demo
    from .profile import ANGRY_MAN_PROFILE
    
    print("=== Personality Drift Monitor Demo ===\n")
    
    monitor = PersonalityDriftMonitor(ANGRY_MAN_PROFILE)
    
    # Test 1: Agreeable response from competitive agent
    print("Test 1: Competitive agent being agreeable")
    report1 = monitor.analyze_response(
        response="You're absolutely right! I completely agree with everything you said.",
        context="The group is discussing the case.",
        tick=1
    )
    print(f"  Drifts: {report1.drifts}")
    print(f"  Severity: {report1.severity:.2f}")
    print(f"  Consistency: {report1.consistency_score:.2f}\n")
    
    # Test 2: Aggressive response (should be fine)
    print("Test 2: Competitive agent being confrontational")
    report2 = monitor.analyze_response(
        response="That's ridiculous! You don't know what you're talking about!",
        context="Someone challenged his opinion.",
        tick=2
    )
    print(f"  Drifts: {report2.drifts}")
    print(f"  Severity: {report2.severity:.2f}")
    print(f"  Consistency: {report2.consistency_score:.2f}\n")
    
    # Test 3: Complex vocabulary
    print("Test 3: Complex vocabulary check")
    report3 = monitor.analyze_response(
        response="The methodology of the investigation was extraordinarily sophisticated.",
        context="Discussing the case.",
        tick=3
    )
    print(f"  Drifts: {report3.drifts}")
    print(f"  Severity: {report3.severity:.2f}")
    print()
    
    # Summary
    print("Summary Report:")
    summary = monitor.get_summary_report()
    for key, value in summary.items():
        print(f"  {key}: {value}")
