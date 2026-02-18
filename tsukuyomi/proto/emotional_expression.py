"""
Emotional Expression Layer
==========================

Transforms PAD (Pleasure-Arousal-Dominance) emotional state into
concrete dialogue modifiers that shape how agents express themselves.

Key Features:
- PAD state to tone modifiers mapping
- Sentence length adjustments based on arousal
- Justification/incertainty based on pleasure
- Punctuation and emphasis based on emotional intensity
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger("EmotionalExpression")


class EmotionalTone(Enum):
    """Categorical emotional tones derived from PAD."""
    NEUTRAL = "neutral"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SAD = "sad"
    HAPPY = "happy"
    EXCITED = "excited"
    CALM = "calm"
    FRUSTRATED = "frustrated"
    DEFENSIVE = "defensive"
    RECEPTIVE = "receptive"


@dataclass
class ToneModifiers:
    """
    Dialogue modifiers derived from emotional state.
    
    These should be applied to LLM prompts and/or output post-processing.
    """
    # Sentence structure
    sentence_length: str = "medium"  # short, medium, long
    sentence_complexity: str = "medium"  # simple, medium, complex
    
    # Emphasis
    emphasis: str = "normal"  # low, normal, high
    punctuation_style: str = "normal"  # normal, emphatic, questioning
    
    # Tone indicators
    tone_adjectives: List[str] = None  # e.g., ["skeptical", "defensive"]
    tone_verbs: List[str] = None  # e.g., ["argue", "question"]
    
    # Justification (how much to explain/defend)
    justification_level: str = "normal"  # minimal, normal, high
    certainty_level: str = "normal"  # uncertain, normal, confident
    
    # Additional context
    speaking_pace: str = "normal"  # slow, normal, fast
    emotional_intensity: float = 0.5  # 0-1 scale
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentence_length": self.sentence_length,
            "sentence_complexity": self.sentence_complexity,
            "emphasis": self.emphasis,
            "punctuation_style": self.punctuation_style,
            "tone_adjectives": self.tone_adjectives or [],
            "tone_verbs": self.tone_verbs or [],
            "justification_level": self.justification_level,
            "certainty_level": self.certainty_level,
            "speaking_pace": self.speaking_pace,
            "emotional_intensity": self.emotional_intensity
        }
    
    def get_prompt_additions(self) -> str:
        """Get prompt text to inject emotional state."""
        parts = []
        
        # Sentence length guidance
        if self.sentence_length == "short":
            parts.append("Keep responses brief and direct.")
        elif self.sentence_length == "long":
            parts.append("Elaborate on your points with detail.")
        
        # Emphasis guidance
        if self.emphasis == "high":
            parts.append("Speak with strong emphasis and conviction.")
        elif self.emphasis == "low":
            parts.append("Speak quietly and hesitantly.")
        
        # Certainty
        if self.certainty_level == "confident":
            parts.append("Be confident in your statements.")
        elif self.certainty_level == "uncertain":
            parts.append("Express doubt and uncertainty.")
        
        # Justification
        if self.justification_level == "high":
            parts.append("Be prepared to defend your position with reasoning.")
        
        # Tone adjectives
        if self.tone_adjectives:
            tone_str = ", ".join(self.tone_adjectives[:3])
            parts.append(f"Your tone should be: {tone_str}.")
        
        return " ".join(parts)


class EmotionalExpression:
    """
    Converts PAD emotional state into dialogue modifiers.
    
    Usage:
        expr = EmotionalExpression(pad_state={"valence": -0.3, "arousal": 0.7, "dominance": 0.5})
        modifiers = expr.get_tone_modifiers()
        
        prompt_addition = expr.get_prompt_additions()
    """
    
    def __init__(
        self,
        pad_state: Dict[str, float] = None,
        personality: Dict[str, float] = None
    ):
        """
        Initialize with PAD state.
        
        Args:
            pad_state: Dict with keys 'valence', 'arousal', 'dominance' (all -1 to 1)
            personality: Dict with personality traits for modulation
        """
        self.pad_state = pad_state or {
            "valence": 0.0,
            "arousal": 0.5,
            "dominance": 0.0
        }
        self.personality = personality or {}
        
        # Cache the computed tone
        self._cached_tone: Optional[EmotionalTone] = None
        self._cached_modifiers: Optional[ToneModifiers] = None
        
        logger.debug(f"EmotionalExpression initialized: PAD={self.pad_state}")
    
    def update_pad(self, pad_state: Dict[str, float]) -> None:
        """Update PAD state and invalidate cache."""
        self.pad_state = pad_state
        self._cached_tone = None
        self._cached_modifiers = None
    
    def get_tone(self) -> EmotionalTone:
        """
        Derive categorical tone from PAD state.
        
        Uses dimensional mapping:
        - High arousal + negative valence = Angry/Frustrated
        - High arousal + positive valence = Excited/Happy
        - Low arousal + negative valence = Sad/Defensive
        - Low arousal + positive valence = Calm/Content
        """
        if self._cached_tone:
            return self._cached_tone
        
        valence = self.pad_state.get("valence", 0.0)
        arousal = self.pad_state.get("arousal", 0.5)
        dominance = self.pad_state.get("dominance", 0.0)
        
        # Determine primary tone
        if arousal > 0.6:
            if valence > 0.2:
                tone = EmotionalTone.EXCITED
            elif valence < -0.2:
                tone = EmotionalTone.ANGRY
            else:
                tone = EmotionalTone.EXCITED  # High arousal, neutral valence
        elif arousal < 0.4:
            if valence > 0.2:
                tone = EmotionalTone.CALM
            elif valence < -0.2:
                tone = EmotionalTone.SAD
            else:
                tone = EmotionalTone.NEUTRAL
        else:  # Medium arousal
            if valence > 0.2:
                tone = EmotionalTone.HAPPY
            elif valence < -0.2:
                tone = EmotionalTone.FRUSTRATED
            else:
                tone = EmotionalTone.NEUTRAL
        
        # Override based on dominance for defensive/receptive states
        if dominance < -0.3:
            tone = EmotionalTone.DEFENSIVE
        elif dominance > 0.3 and valence > 0.2:
            tone = EmotionalTone.RECEPTIVE
        
        self._cached_tone = tone
        return tone
    
    def get_tone_modifiers(self) -> ToneModifiers:
        """
        Get full set of tone modifiers from PAD state.
        
        This is the main method to call for prompt injection.
        """
        if self._cached_modifiers:
            return self._cached_modifiers
        
        valence = self.pad_state.get("valence", 0.0)
        arousal = self.pad_state.get("arousal", 0.5)
        dominance = self.pad_state.get("dominance", 0.0)
        
        tone = self.get_tone()
        
        # === SENTENCE LENGTH ===
        # High arousal = shorter, more emphatic sentences
        if arousal > 0.7:
            sentence_length = "short"
        elif arousal < 0.3:
            sentence_length = "long"
        else:
            sentence_length = "medium"
        
        # === EMPHASIS ===
        if arousal > 0.7:
            emphasis = "high"
        elif arousal < 0.3:
            emphasis = "low"
        else:
            emphasis = "normal"
        
        # === PUNCTUATION ===
        if arousal > 0.7 and valence < 0:
            punctuation_style = "emphatic"  # Exclamation marks
        elif arousal < 0.3:
            punctuation_style = "questioning"  # More questions
        else:
            punctuation_style = "normal"
        
        # === JUSTIFICATION ===
        # Low pleasure (negative valence) = more defensive/justifying
        if valence < -0.3:
            justification_level = "high"
        elif valence > 0.3:
            justification_level = "minimal"
        else:
            justification_level = "normal"
        
        # === CERTAINTY ===
        # High dominance = more certain
        if dominance > 0.3:
            certainty_level = "confident"
        elif dominance < -0.3:
            certainty_level = "uncertain"
        else:
            certainty_level = "normal"
        
        # === TONE ADJECTIVES & VERBS ===
        tone_adjectives, tone_verbs = self._get_tone_words(tone)
        
        # === SPEAKING PACE ===
        if arousal > 0.7:
            speaking_pace = "fast"
        elif arousal < 0.3:
            speaking_pace = "slow"
        else:
            speaking_pace = "normal"
        
        # === EMOTIONAL INTENSITY ===
        emotional_intensity = abs(valence) * 0.5 + arousal * 0.5
        
        modifiers = ToneModifiers(
            sentence_length=sentence_length,
            emphasis=emphasis,
            punctuation_style=punctuation_style,
            justification_level=justification_level,
            certainty_level=certainty_level,
            tone_adjectives=tone_adjectives,
            tone_verbs=tone_verbs,
            speaking_pace=speaking_pace,
            emotional_intensity=emotional_intensity
        )
        
        self._cached_modifiers = modifiers
        return modifiers
    
    def _get_tone_words(self, tone: EmotionalTone) -> tuple:
        """Get tone-specific adjectives and verbs."""
        
        tone_words = {
            EmotionalTone.ANGRY: {
                "adjectives": ["angry", "frustrated", "indignant"],
                "verbs": ["demand", "protest", "object"]
            },
            EmotionalTone.FRUSTRATED: {
                "adjectives": ["frustrated", "impatient", "irritated"],
                "verbs": ["push back", "question", "challenge"]
            },
            EmotionalTone.FEARFUL: {
                "adjectives": ["worried", "anxious", "concerned"],
                "verbs": ["hesitate", "question", "doubt"]
            },
            EmotionalTone.SAD: {
                "adjectives": ["somber", "sorrowful", "regretful"],
                "verbs": ["mourn", "lament", "reflect"]
            },
            EmotionalTone.HAPPY: {
                "adjectives": ["pleased", "satisfied", "content"],
                "verbs": ["agree", "support", "approve"]
            },
            EmotionalTone.EXCITED: {
                "adjectives": ["enthusiastic", "eager", "energetic"],
                "verbs": ["urge", "encourage", "push"]
            },
            EmotionalTone.CALM: {
                "adjectives": ["calm", "measured", "rational"],
                "verbs": ["consider", "reason", "explain"]
            },
            EmotionalTone.DEFENSIVE: {
                "adjectives": ["defensive", "guarded", "skeptical"],
                "verbs": ["justify", "explain", "defend"]
            },
            EmotionalTone.RECEPTIVE: {
                "adjectives": ["open", "curious", "attentive"],
                "verbs": ["listen", "consider", "weigh"]
            },
            EmotionalTone.NEUTRAL: {
                "adjectives": [],
                "verbs": []
            }
        }
        
        words = tone_words.get(tone, {"adjectives": [], "verbs": []})
        return words.get("adjectives", []), words.get("verbs", [])
    
    def get_prompt_injection(self) -> str:
        """
        Get full prompt text to inject emotional context.
        
        This should be added to the LLM system/user prompt.
        """
        modifiers = self.get_tone_modifiers()
        tone = self.get_tone()
        
        parts = [
            f"CURRENT EMOTIONAL STATE: {tone.value.upper()}",
            f"(Valence: {self.pad_state.get('valence', 0):.2f}, "
            f"Arousal: {self.pad_state.get('arousal', 0.5):.2f}, "
            f"Dominance: {self.pad_state.get('dominance', 0):.2f})",
            "",
            modifiers.get_prompt_additions()
        ]
        
        return "\n".join([p for p in parts if p])
    
    def apply_to_response(self, response: str) -> str:
        """
        Apply tone modifiers to a generated response (post-processing).
        
        This is optional - the primary method is prompt injection.
        """
        modifiers = self.get_tone_modifiers()
        
        # This would be more sophisticated in production
        # For now, just a placeholder for potential post-processing
        
        return response
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize emotional expression state."""
        return {
            "pad_state": self.pad_state,
            "tone": self.get_tone().value,
            "modifiers": self.get_tone_modifiers().to_dict()
        }


# ========================
# HELPER FUNCTIONS
# ========================

def create_emotional_expression(
    pad_state: Dict[str, float] = None,
    personality: Dict[str, float] = None
) -> EmotionalExpression:
    """
    Factory function to create an emotional expression handler.
    
    Args:
        pad_state: PAD values (valence, arousal, dominance) -1 to 1
        personality: Optional personality traits
    
    Returns:
        Configured EmotionalExpression
    """
    return EmotionalExpression(
        pad_state=pad_state or {"valence": 0.0, "arousal": 0.5, "dominance": 0.0},
        personality=personality or {}
    )


def pad_from_baseline(
    baseline: str,
    arousal_modifier: float = 0.0
) -> Dict[str, float]:
    """
    Get PAD state from baseline description.
    
    Args:
        baseline: "positive", "negative", "neutral"
        arousal_modifier: -1 to 1 adjustment
    
    Returns:
        PAD state dict
    """
    baseline_states = {
        "positive": {"valence": 0.5, "arousal": 0.5, "dominance": 0.0},
        "negative": {"valence": -0.5, "arousal": 0.5, "dominance": -0.3},
        "neutral": {"valence": 0.0, "arousal": 0.5, "dominance": 0.0}
    }
    
    state = baseline_states.get(baseline, baseline_states["neutral"]).copy()
    state["arousal"] = max(0, min(1, state["arousal"] + arousal_modifier))
    
    return state


# ========================
# UNIT TESTS
# ========================

def test_emotional_expression():
    """Test basic emotional expression functionality."""
    
    # Test 1: High arousal, negative valence = Angry
    expr = EmotionalExpression({"valence": -0.5, "arousal": 0.8, "dominance": 0.2})
    assert expr.get_tone() == EmotionalTone.ANGRY
    modifiers = expr.get_tone_modifiers()
    assert modifiers.sentence_length == "short"
    assert modifiers.emphasis == "high"
    print("✅ Test 1: Angry state correct")
    
    # Test 2: Low arousal, positive valence = Calm
    expr = EmotionalExpression({"valence": 0.5, "arousal": 0.2, "dominance": 0.3})
    assert expr.get_tone() == EmotionalTone.CALM
    modifiers = expr.get_tone_modifiers()
    assert modifiers.sentence_length == "long"
    print("✅ Test 2: Calm state correct")
    
    # Test 3: Negative valence, low dominance = Defensive
    expr = EmotionalExpression({"valence": -0.3, "arousal": 0.5, "dominance": -0.5})
    assert expr.get_tone() == EmotionalTone.DEFENSIVE
    print("✅ Test 3: Defensive state correct")
    
    # Test 4: Prompt injection
    expr = EmotionalExpression({"valence": -0.4, "arousal": 0.7, "dominance": 0.0})
    prompt = expr.get_prompt_injection()
    assert "EMOTIONAL STATE" in prompt
    assert "short" in prompt.lower()
    print("✅ Test 4: Prompt injection works")
    
    print("\n✅ All emotional expression tests passed!")


if __name__ == "__main__":
    test_emotional_expression()
