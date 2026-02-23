"""
Emotional Expression Module
==========================

Provides emotional expression generation and tone modifiers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from .emotion.types import EmotionalTone


class ToneModifiers(Enum):
    """Modifiers for emotional tones."""
    INTENSIFY = "intensify"
    SOFTEN = "soften"
    NEUTRAL = "neutral"
    DRAMATIC = "dramatic"


@dataclass
class ToneModifierResult:
    """Result from tone modifier calculation."""
    modifiers: List[str] = field(default_factory=list)
    
    def get_prompt_additions(self) -> str:
        """Get prompt additions from modifiers."""
        if not self.modifiers:
            return ""
        return f"[Tone: {', '.join(self.modifiers)}]"


@dataclass
class EmotionalExpression:
    """
    Manages emotional expression and tone generation.
    """
    pad_state: Dict[str, float] = field(default_factory=lambda: {"valence": 0.0, "arousal": 0.5, "dominance": 0.0})
    personality: Dict[str, Any] = field(default_factory=dict)
    _cached_tone: Optional[EmotionalTone] = None
    _cached_modifiers: Optional[List[str]] = None
    
    def get_tone(self) -> EmotionalTone:
        """Get the current emotional tone."""
        if self._cached_tone is None:
            self._cached_tone = self._calculate_tone()
        return self._cached_tone
    
    def _calculate_tone(self) -> EmotionalTone:
        """Calculate tone from PAD state."""
        v = self.pad_state.get("valence", 0.0)
        a = self.pad_state.get("arousal", 0.5)
        d = self.pad_state.get("dominance", 0.0)
        
        if a > 0.7:
            if v > 0.3:
                return EmotionalTone.EXCITED
            elif v < -0.3:
                return EmotionalTone.ANGRY
            return EmotionalTone.ANXIOUS
        elif a < 0.3:
            if v > 0.3:
                return EmotionalTone.CALM
            elif v < -0.3:
                return EmotionalTone.SAD
            return EmotionalTone.NEUTRAL
        
        if v > 0.5:
            return EmotionalTone.HAPPY
        elif v < -0.5:
            return EmotionalTone.FEARFUL
        
        if d > 0.3:
            return EmotionalTone.CONFIDENT
        elif d < -0.3:
            return EmotionalTone.UNCERTAIN
        
        return EmotionalTone.NEUTRAL
    
    def get_modifiers(self) -> List[str]:
        """Get tone modifiers for expression."""
        if self._cached_modifiers is None:
            self._cached_modifiers = self._calculate_modifiers()
        return self._cached_modifiers
    
    def get_tone_modifiers(self) -> ToneModifierResult:
        """Get tone modifiers as a result object."""
        return ToneModifierResult(modifiers=self.get_modifiers())
    
    def _calculate_modifiers(self) -> List[str]:
        """Calculate expression modifiers."""
        modifiers = []
        tone = self.get_tone()
        
        if tone == EmotionalTone.ANGRY:
            modifiers = ["intense", "direct", "forceful"]
        elif tone == EmotionalTone.HAPPY:
            modifiers = ["warm", "enthusiastic", "positive"]
        elif tone == EmotionalTone.SAD:
            modifiers = ["subdued", "quiet", "melancholic"]
        elif tone == EmotionalTone.ANXIOUS:
            modifiers = ["hesitant", "uncertain", "nervous"]
        elif tone == EmotionalTone.EXCITED:
            modifiers = ["energetic", "animated", "enthusiastic"]
        elif tone == EmotionalTone.CALM:
            modifiers = ["measured", "peaceful", "relaxed"]
        elif tone == EmotionalTone.CONFIDENT:
            modifiers = ["assertive", "decisive", "bold"]
        elif tone == EmotionalTone.UNCERTAIN:
            modifiers = ["tentative", "cautious", "doubtful"]
        else:
            modifiers = ["neutral", "balanced"]
        
        return modifiers
    
    def apply_to_text(self, text: str) -> str:
        """Apply emotional tone to text."""
        modifiers = self.get_modifiers()
        if modifiers:
            return f"[{modifiers[0]}] {text}"
        return text
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "pad_state": self.pad_state,
            "personality": self.personality,
            "tone": self.get_tone().value if self._cached_tone else None,
            "modifiers": self._cached_modifiers
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "EmotionalExpression":
        """Deserialize from dictionary."""
        expr = cls(
            pad_state=data.get("pad_state", {"valence": 0.0, "arousal": 0.5, "dominance": 0.0}),
            personality=data.get("personality", {})
        )
        return expr


def create_emotional_expression(
    valence: float = 0.0,
    arousal: float = 0.5,
    dominance: float = 0.0,
    personality: Optional[Dict] = None
) -> EmotionalExpression:
    """Factory function to create an emotional expression."""
    return EmotionalExpression(
        pad_state={"valence": valence, "arousal": arousal, "dominance": dominance},
        personality=personality or {}
    )


def pad_from_baseline(baseline: Dict) -> Dict[str, float]:
    """Create PAD state from personality baseline."""
    return {
        "valence": baseline.get("valence_baseline", 0.0),
        "arousal": baseline.get("arousal_baseline", 0.5),
        "dominance": baseline.get("dominance_baseline", 0.0)
    }


__all__ = [
    "EmotionalExpression",
    "ToneModifiers",
    "EmotionalTone",
    "create_emotional_expression",
    "pad_from_baseline"
]
