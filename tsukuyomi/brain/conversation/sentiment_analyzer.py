"""
Sentiment Analyzer Module - Tsukuyomi V2

This module implements rule-based sentiment analysis for speech content.
It identifies hostile, friendly, and neutral patterns in dialogue to
support relationship impact calculation and conversation heat tracking.

Key Features:
- Pattern-based sentiment classification
- Emotion label detection
- Confidence scoring
- Extensible pattern system
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

from .conversation_state import SentimentSnapshot, IntentType

logger = logging.getLogger(__name__)


class EmotionCategory(Enum):
    """Categories of emotions for sentiment analysis."""
    HOSTILE = "hostile"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"


@dataclass
class SentimentPattern:
    """
    A pattern for detecting sentiment in speech.
    
    Attributes:
        pattern: Regex pattern to match
        category: Emotion category this pattern indicates
        weight: How strongly this pattern indicates the category
        emotion_labels: Emotion labels associated with this pattern
    """
    pattern: str
    category: EmotionCategory
    weight: float = 1.0
    emotion_labels: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Compile the regex pattern."""
        self._compiled = re.compile(self.pattern, re.IGNORECASE)
    
    def matches(self, text: str) -> int:
        """Count matches of this pattern in text."""
        return len(self._compiled.findall(text))


@dataclass
class SentimentConfig:
    """
    Configuration for sentiment analysis.
    
    Allows customization of patterns and thresholds.
    """
    # Hostile patterns
    hostile_patterns: List[SentimentPattern] = field(default_factory=lambda: [
        # Strong hostility
        SentimentPattern(r"\b(stupid|idiot|fool|moron|imbecile)\b", EmotionCategory.HOSTILE, 0.8, ["anger", "contempt"]),
        SentimentPattern(r"\b(liar|lying|lie[sd]?)\b", EmotionCategory.HOSTILE, 0.7, ["anger", "distrust"]),
        SentimentPattern(r"\b(wrong|incorrect|mistaken)\b", EmotionCategory.HOSTILE, 0.4, ["disagreement"]),
        SentimentPattern(r"\b(shut up|be quiet|stop talking)\b", EmotionCategory.HOSTILE, 0.9, ["anger", "hostility"]),
        SentimentPattern(r"\b(hate|loathe|despise)\b", EmotionCategory.HOSTILE, 0.85, ["hatred", "anger"]),
        SentimentPattern(r"\b(ridiculous|absurd|nonsense)\b", EmotionCategory.HOSTILE, 0.5, ["contempt", "frustration"]),
        SentimentPattern(r"\b(never|impossible|won't work)\b", EmotionCategory.HOSTILE, 0.3, ["dismissiveness"]),
        SentimentPattern(r"!{2,}", EmotionCategory.HOSTILE, 0.6, ["intensity", "frustration"]),  # Multiple exclamation marks
        SentimentPattern(r"\b(don't be|stop being)\s+(stupid|ridiculous|foolish)\b", EmotionCategory.HOSTILE, 0.75, ["contempt", "frustration"]),
        
        # Moderate hostility
        SentimentPattern(r"\b(what are you talking about|that makes no sense)\b", EmotionCategory.HOSTILE, 0.5, ["frustration", "confusion"]),
        SentimentPattern(r"\b(I can't believe you|how could you)\b", EmotionCategory.HOSTILE, 0.55, ["frustration", "disappointment"]),
        SentimentPattern(r"\b(this is (a )?waste|wasting time)\b", EmotionCategory.HOSTILE, 0.5, ["frustration", "impatience"]),
        
        # Challenge patterns (moderate)
        SentimentPattern(r"\bbut\b", EmotionCategory.HOSTILE, 0.2, ["disagreement"]),
        SentimentPattern(r"\bhowever\b", EmotionCategory.HOSTILE, 0.2, ["disagreement"]),
        SentimentPattern(r"\bwhat about\b", EmotionCategory.HOSTILE, 0.25, ["questioning"]),
    ])
    
    # Friendly patterns
    friendly_patterns: List[SentimentPattern] = field(default_factory=lambda: [
        # Strong friendliness
        SentimentPattern(r"\b(please|thank you|thanks)\b", EmotionCategory.FRIENDLY, 0.7, ["politeness", "gratitude"]),
        SentimentPattern(r"\b(sorry|apologize|apology)\b", EmotionCategory.FRIENDLY, 0.6, ["remorse", "cooperation"]),
        SentimentPattern(r"\b(I agree|you're right|exactly|precisely)\b", EmotionCategory.FRIENDLY, 0.75, ["agreement", "validation"]),
        SentimentPattern(r"\b(good point|fair enough|well said)\b", EmotionCategory.FRIENDLY, 0.7, ["respect", "agreement"]),
        SentimentPattern(r"\b(I understand|I see|that makes sense)\b", EmotionCategory.FRIENDLY, 0.6, ["understanding", "empathy"]),
        SentimentPattern(r"\b(excellent|wonderful|great|amazing)\b", EmotionCategory.FRIENDLY, 0.65, ["enthusiasm", "approval"]),
        SentimentPattern(r"\b(love|adore|appreciate)\b", EmotionCategory.FRIENDLY, 0.8, ["warmth", "affection"]),
        
        # Moderate friendliness
        SentimentPattern(r"\b(perhaps|maybe|possibly)\b", EmotionCategory.FRIENDLY, 0.3, ["openness"]),
        SentimentPattern(r"\b(let's|we could|how about)\b", EmotionCategory.FRIENDLY, 0.4, ["cooperation", "collaboration"]),
        SentimentPattern(r"\b(I think|I believe|in my opinion)\b", EmotionCategory.FRIENDLY, 0.25, ["openness", "sharing"]),
        SentimentPattern(r"\byes\b", EmotionCategory.FRIENDLY, 0.3, ["agreement"]),
        SentimentPattern(r"\bright\b", EmotionCategory.FRIENDLY, 0.25, ["agreement"]),
    ])
    
    # Emotion label mappings
    emotion_to_intensity: Dict[str, float] = field(default_factory=lambda: {
        # High intensity emotions
        "anger": 0.9,
        "hatred": 0.95,
        "hostility": 0.85,
        "contempt": 0.75,
        "hatred": 0.9,
        
        # Medium intensity emotions
        "frustration": 0.6,
        "disappointment": 0.5,
        "distrust": 0.55,
        "disagreement": 0.4,
        "dismissiveness": 0.45,
        "impatience": 0.5,
        
        # Positive emotions
        "gratitude": 0.7,
        "agreement": 0.5,
        "validation": 0.55,
        "respect": 0.6,
        "empathy": 0.55,
        "enthusiasm": 0.7,
        "warmth": 0.65,
        "affection": 0.75,
        "cooperation": 0.5,
        "collaboration": 0.45,
        
        # Neutral/mild emotions
        "politeness": 0.3,
        "remorse": 0.4,
        "understanding": 0.35,
        "openness": 0.3,
        "sharing": 0.25,
        "questioning": 0.2,
        "confusion": 0.25,
        "intensity": 0.5,
    })


class SentimentAnalyzer:
    """
    Rule-based sentiment analyzer for speech content.
    
    Uses pattern matching to identify hostile, friendly, and neutral
    sentiment in speech, providing emotion labels and confidence scores.
    
    Example:
        >>> analyzer = SentimentAnalyzer()
        >>> sentiment = analyzer.analyze("That's a stupid idea!", "speaker_1", tick=100)
        >>> print(sentiment.sentiment_score)  # Will be negative (hostile)
        >>> print(sentiment.emotion_labels)   # ["anger", "contempt"]
    """
    
    def __init__(self, config: Optional[SentimentConfig] = None):
        """
        Initialize the sentiment analyzer.
        
        Args:
            config: Optional custom configuration
        """
        self.config = config or SentimentConfig()
    
    def analyze(self, speech: str, speaker: str, tick: int) -> SentimentSnapshot:
        """
        Analyze sentiment of speech.
        
        Args:
            speech: The speech text to analyze
            speaker: ID of the speaking agent
            tick: Current simulation tick
        
        Returns:
            SentimentSnapshot with analysis results
        """
        speech_lower = speech.lower()
        
        # Count pattern matches
        hostile_score = 0.0
        friendly_score = 0.0
        all_emotions: List[str] = []
        
        # Analyze hostile patterns
        for pattern in self.config.hostile_patterns:
            matches = pattern.matches(speech_lower)
            if matches > 0:
                hostile_score += matches * pattern.weight
                all_emotions.extend(pattern.emotion_labels * matches)
        
        # Analyze friendly patterns
        for pattern in self.config.friendly_patterns:
            matches = pattern.matches(speech_lower)
            if matches > 0:
                friendly_score += matches * pattern.weight
                all_emotions.extend(pattern.emotion_labels * matches)
        
        # Calculate sentiment score
        total = hostile_score + friendly_score
        if total == 0:
            sentiment_score = 0.0  # Neutral
        else:
            # Normalize to -1 to 1 range
            sentiment_score = (friendly_score - hostile_score) / max(total, 1.0)
            # Clamp to valid range
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Determine emotion labels (unique, preserve order)
        seen = set()
        emotion_labels = []
        for emotion in all_emotions:
            if emotion not in seen:
                seen.add(emotion)
                emotion_labels.append(emotion)
        
        # Limit to top 3 most intense emotions
        if emotion_labels:
            emotion_labels = sorted(
                emotion_labels,
                key=lambda e: self.config.emotion_to_intensity.get(e, 0.3),
                reverse=True
            )[:3]
        
        # Calculate confidence
        # More patterns matched = higher confidence
        pattern_count = len([e for e in all_emotions])
        confidence = min(1.0, pattern_count / 3.0)  # Cap at 3 patterns for full confidence
        
        return SentimentSnapshot(
            tick=tick,
            speaker=speaker,
            sentiment_score=sentiment_score,
            emotion_labels=emotion_labels,
            confidence=confidence
        )
    
    def classify_intent(self, speech: str, sentiment: SentimentSnapshot) -> IntentType:
        """
        Classify the intent of speech based on content and sentiment.
        
        Args:
            speech: The speech text
            sentiment: Pre-computed sentiment analysis
        
        Returns:
            Classified IntentType
        """
        speech_lower = speech.lower()
        
        # Strong sentiment-based classification
        if sentiment.sentiment_score < -0.5:
            # Strong hostility often indicates challenge or disagreement
            if "?" in speech:
                return IntentType.CHALLENGE
            return IntentType.DISAGREE
        
        if sentiment.sentiment_score > 0.5:
            # Strong friendliness often indicates agreement
            return IntentType.AGREE
        
        # Keyword-based classification
        # Apologies
        if any(kw in speech_lower for kw in ["sorry", "apologize", "my fault", "i was wrong"]):
            return IntentType.APOLOGIZE
        
        # Questions
        if "?" in speech_lower or any(kw in speech_lower for kw in ["what", "why", "how", "when", "where", "who"]):
            return IntentType.QUESTION
        
        # Commands
        if any(kw in speech_lower for kw in ["you must", "you should", "do this", "let's", "we need to"]):
            return IntentType.COMMAND if sentiment.sentiment_score < 0 else IntentType.PERSUADE
        
        # Agreement
        if any(kw in speech_lower for kw in ["yes", "right", "agree", "exactly", "correct", "true"]):
            return IntentType.AGREE
        
        # Disagreement
        if any(kw in speech_lower for kw in ["no", "wrong", "disagree", "incorrect", "false"]):
            return IntentType.DISAGREE
        
        # Challenge
        if any(kw in speech_lower for kw in ["but", "however", "what about", "on the other hand"]):
            return IntentType.CHALLENGE
        
        # Defense
        if any(kw in speech_lower for kw in ["i didn't", "that's not", "i would never", "you're mistaken"]):
            return IntentType.DEFEND
        
        # Persuasion
        if any(kw in speech_lower for kw in ["i think", "i believe", "in my opinion", "trust me", "believe me"]):
            return IntentType.PERSUADE
        
        # Default to inform
        return IntentType.INFORM
    
    def get_emotional_intensity(self, emotion_labels: List[str]) -> float:
        """
        Calculate overall emotional intensity from emotion labels.
        
        Args:
            emotion_labels: List of detected emotion labels
        
        Returns:
            Intensity score (0.0 to 1.0)
        """
        if not emotion_labels:
            return 0.0
        
        intensities = [
            self.config.emotion_to_intensity.get(label, 0.3)
            for label in emotion_labels
        ]
        
        # Return max intensity
        return max(intensities) if intensities else 0.0
    
    def suggest_heat_change(self, sentiment: SentimentSnapshot, intent: IntentType) -> float:
        """
        Suggest how much the conversation heat should change.
        
        Args:
            sentiment: Sentiment analysis of the turn
            intent: Classified intent of the turn
        
        Returns:
            Suggested heat change (-0.2 to +0.2)
        """
        base_change = 0.0
        
        # Sentiment-based heat change
        if sentiment.is_hostile():
            # More hostile = more heat
            base_change += abs(sentiment.sentiment_score) * 0.15
        elif sentiment.is_friendly():
            # More friendly = less heat
            base_change -= sentiment.sentiment_score * 0.05
        
        # Intent-based heat change
        intent_heat_map = {
            IntentType.CHALLENGE: 0.1,
            IntentType.DISAGREE: 0.08,
            IntentType.DEFEND: 0.05,
            IntentType.COMMAND: 0.03,
            IntentType.AGREE: -0.08,
            IntentType.APOLOGIZE: -0.1,
            IntentType.PERSUADE: -0.02,  # Persuasion can go either way
            IntentType.QUESTION: 0.0,
            IntentType.INFORM: 0.0,
        }
        
        base_change += intent_heat_map.get(intent, 0.0)
        
        # Factor in confidence
        if sentiment.confidence > 0.5:
            base_change *= (0.8 + sentiment.confidence * 0.4)  # Amplify confident signals
        
        # Clamp to reasonable range
        return max(-0.2, min(0.2, base_change))


def analyze_speech(speech: str, speaker: str, tick: int) -> SentimentSnapshot:
    """
    Convenience function to analyze speech sentiment.
    
    Args:
        speech: The speech text to analyze
        speaker: ID of the speaking agent
        tick: Current simulation tick
    
    Returns:
        SentimentSnapshot with analysis results
    """
    analyzer = SentimentAnalyzer()
    return analyzer.analyze(speech, speaker, tick)


# Example usage and testing

if __name__ == "__main__":
    print("=== Sentiment Analyzer Demo ===\n")
    
    analyzer = SentimentAnalyzer()
    
    # Test cases
    test_speeches = [
        ("That's a stupid idea! You're an idiot if you believe that.", "hostile_high"),
        ("I completely agree with you. That's an excellent point.", "friendly_high"),
        ("The weather seems nice today.", "neutral"),
        ("But have you considered the alternative? What about the evidence?", "challenge"),
        ("I'm sorry, I was wrong about that.", "apologetic"),
        ("Let's work together to solve this problem.", "cooperative"),
        ("This is ridiculous! We're wasting time here!", "frustrated"),
    ]
    
    for speech, label in test_speeches:
        sentiment = analyzer.analyze(speech, "speaker_1", tick=100)
        intent = analyzer.classify_intent(speech, sentiment)
        
        print(f"Label: {label}")
        print(f"Speech: '{speech}'")
        print(f"Sentiment Score: {sentiment.sentiment_score:.3f}")
        print(f"Emotions: {sentiment.emotion_labels}")
        print(f"Confidence: {sentiment.confidence:.2f}")
        print(f"Intent: {intent.value}")
        print(f"Heat Change Suggestion: {analyzer.suggest_heat_change(sentiment, intent):+.3f}")
        print("-" * 60)
