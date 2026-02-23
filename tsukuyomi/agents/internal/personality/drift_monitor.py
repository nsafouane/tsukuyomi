"""
drift_monitor.py - Post-generation Drift Detection with EMA

This module implements Layer 2 of the Personality Integrity System:
post-generation drift detection that monitors agent behavior for
inconsistencies with their personality profile.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from .profile import PersonalityProfile
from .drift_types import BehaviorSnapshot, DriftReport


logger = logging.getLogger("PersonalityDriftMonitor")


class PersonalityDriftMonitor:
    """
    Detect when agent behavior drifts from personality profile.
    
    This class implements post-generation monitoring by analyzing
    responses and actions for personality violations. It uses
    Exponential Moving Average (EMA) to track drift trends over time.
    """
    
    DEFAULT_EMA_ALPHA: float = 0.3
    DRIFT_THRESHOLD: float = 0.1
    MAX_HISTORY_SIZE: int = 100
    
    COMPLEX_WORD_PATTERNS = [
        r'\b\w{12,}\b',
        r'\b(nevertheless|furthermore|consequently|accordingly)\b',
        r'\b(extraordinary|phenomenon|hypothesis|methodology)\b',
        r'\b(implementation|configuration|sophisticated)\b',
    ]
    
    AGREEABLE_PHRASES = [
        r'\b(you\'?re right|I agree|exactly|absolutely|of course)\b',
        r'\b(that makes sense|good point|fair enough)\b',
        r'\b(I understand|you\'?re correct|I see your point)\b',
    ]
    
    DISAGREEABLE_PHRASES = [
        r'\b(that\'?s wrong|I disagree|you\'?re mistaken|no way)\b',
        r'\b(rubbish|nonsense|bullshit|ridiculous)\b',
        r'\b(I don\'?t think so|I can\'?t accept that)\b',
    ]
    
    EMOTIONAL_INDICATORS = [
        r'!{2,}',
        r'\?{2,}',
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
        self.profile = profile
        self.ema_alpha = ema_alpha
        
        self.behavior_history: List[BehaviorSnapshot] = []
        self.drift_reports: List[DriftReport] = []
        
        self.drift_score_ema: float = 0.0
        
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
        """Check if response matches expected personality."""
        snapshot = BehaviorSnapshot(
            tick=tick,
            response=response,
            context=context,
            action=action,
            action_params=action_params
        )
        self.behavior_history.append(snapshot)
        self._trim_history()
        
        drifts = []
        component_scores = {}
        
        vocab_drift, vocab_score = self._check_vocabulary(response)
        drifts.extend(vocab_drift)
        component_scores['vocabulary'] = vocab_score
        self._update_component_ema('vocabulary', vocab_score)
        
        agree_drift, agree_score = self._check_agreeableness(response)
        drifts.extend(agree_drift)
        component_scores['agreeableness'] = agree_score
        self._update_component_ema('agreeableness', agree_score)
        
        extra_drift, extra_score = self._check_extraversion(response, context)
        drifts.extend(extra_drift)
        component_scores['extraversion'] = extra_score
        self._update_component_ema('extraversion', extra_score)
        
        neuro_drift, neuro_score = self._check_neuroticism(response)
        drifts.extend(neuro_drift)
        component_scores['neuroticism'] = neuro_score
        self._update_component_ema('neuroticism', neuro_score)
        
        style_drift, style_score = self._check_speaking_style(response)
        drifts.extend(style_drift)
        component_scores['style'] = style_score
        self._update_component_ema('style', style_score)
        
        drift_score = sum(component_scores.values()) / len(component_scores)
        
        self.drift_score_ema = (
            self.ema_alpha * drift_score +
            (1 - self.ema_alpha) * self.drift_score_ema
        )
        
        report = DriftReport(
            agent_name=self.profile.name,
            tick=tick,
            drifts=drifts,
            severity=drift_score,
            ema_severity=self.drift_score_ema
        )
        
        self.drift_reports.append(report)
        
        if drift_score > self.DRIFT_THRESHOLD:
            logger.warning(
                f"Personality drift detected for {self.profile.name}: "
                f"severity={drift_score:.2f}, EMA={self.drift_score_ema:.2f}"
            )
        
        return report
    
    def _check_vocabulary(self, response: str) -> Tuple[List[str], float]:
        """Check if vocabulary matches the profile's vocabulary level."""
        drifts = []
        score = 0.0
        
        if self.profile.vocabulary_level == "simple":
            complex_words = self._count_complex_words(response)
            if complex_words > 3:
                drifts.append(
                    f"Vocabulary too complex for 'simple' profile "
                    f"(found {complex_words} complex words)"
                )
                score = min(1.0, complex_words * 0.05)
        
        elif self.profile.vocabulary_level == "formal":
            casual_indicators = self._detect_casual_language(response)
            if casual_indicators > 2:
                drifts.append(
                    f"Language too casual for 'formal' profile "
                    f"(found {casual_indicators} casual elements)"
                )
                score = min(1.0, casual_indicators * 0.05)
        
        return drifts, score
    
    def _check_agreeableness(self, response: str) -> Tuple[List[str], float]:
        """Check if agreeableness patterns match the profile."""
        drifts = []
        score = 0.0
        response_lower = response.lower()
        
        if self.profile.agreeableness < -0.3:
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
        """Check if extraversion patterns match the profile."""
        drifts = []
        score = 0.0
        
        if self.profile.extraversion < -0.3:
            if self._is_initiating_conversation(response, context):
                drifts.append(
                    "Introvert initiating conversation unexpectedly"
                )
                score = 0.25
            
            exclamation_count = response.count('!')
            if exclamation_count > 3:
                drifts.append(
                    f"Too enthusiastic for introverted personality "
                    f"({exclamation_count} exclamation marks)"
                )
                score += min(0.2, exclamation_count * 0.02)
        
        elif self.profile.extraversion > 0.3:
            if self._is_overly_passive(response):
                drifts.append(
                    "Extravert being too passive in conversation"
                )
                score = 0.15
        
        return drifts, score
    
    def _check_neuroticism(self, response: str) -> Tuple[List[str], float]:
        """Check if emotional expression matches neuroticism level."""
        drifts = []
        score = 0.0
        response_lower = response.lower()
        
        if self.profile.neuroticism > 0.5:
            emotional_count = self._count_pattern_matches(
                response_lower, self.EMOTIONAL_INDICATORS
            )
            calm_count = self._count_pattern_matches(
                response_lower, self.CALM_INDICATORS
            )
            
            if calm_count > 2 and emotional_count == 0:
                drifts.append(
                    "Emotionally sensitive personality appearing too calm"
                )
                score = 0.2
        
        elif self.profile.neuroticism < -0.3:
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
        """Check if speaking style matches the profile."""
        drifts = []
        score = 0.0
        style_lower = self.profile.speaking_style.lower()
        
        if "interrupt" in style_lower:
            if response.endswith("?") and "excuse me" in response.lower():
                drifts.append(
                    "Agent with interrupting style being too polite"
                )
                score = 0.15
        
        if "quiet" in style_lower or "soft" in style_lower:
            if response.isupper() or response.count('!') > 2:
                drifts.append(
                    "Soft-spoken agent speaking loudly (caps/exclamation)"
                )
                score = 0.2
        
        if "aggressive" in style_lower or "loud" in style_lower:
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
            r'\'s\s',
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
        """Determine if response is initiating a new conversation."""
        if self.profile.name.lower() in context.lower():
            return False
        
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
        """Determine if response is overly passive."""
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
        """Return personality consistency score (0.0 to 1.0)."""
        return 1.0 - min(1.0, self.drift_score_ema)
    
    def get_component_scores(self) -> Dict[str, float]:
        """Get consistency scores by component."""
        return {
            'vocabulary': 1.0 - min(1.0, self.vocabulary_drift_ema),
            'agreeableness': 1.0 - min(1.0, self.agreeableness_drift_ema),
            'extraversion': 1.0 - min(1.0, self.extraversion_drift_ema),
            'neuroticism': 1.0 - min(1.0, self.neuroticism_drift_ema),
            'style': 1.0 - min(1.0, self.style_drift_ema),
        }
    
    def get_drift_trend(self) -> str:
        """Analyze drift trend over recent history."""
        if len(self.drift_reports) < 3:
            return "insufficient_data"
        
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
        """Generate a summary report of drift monitoring."""
        return {
            'agent_name': self.profile.name,
            'overall_consistency': self.get_consistency_score(),
            'component_consistency': self.get_component_scores(),
            'drift_trend': self.get_drift_trend(),
            'total_checks': len(self.drift_reports),
            'drifts_detected': sum(1 for r in self.drift_reports if r.has_drift),
            'current_ema': self.drift_score_ema,
        }
