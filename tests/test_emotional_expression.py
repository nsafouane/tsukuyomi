"""
Unit Tests for Emotional Expression
===================================
"""

import pytest
from tsukuyomi.proto.emotional_expression import (
    EmotionalExpression,
    ToneModifiers,
    EmotionalTone,
    create_emotional_expression,
    pad_from_baseline
)


class TestEmotionalExpression:
    """Tests for EmotionalExpression."""
    
    def test_initialization(self):
        """Test initialization with default values."""
        expr = EmotionalExpression()
        
        assert expr.pad_state == {"valence": 0.0, "arousal": 0.5, "dominance": 0.0}
        assert expr._cached_tone is None
        assert expr._cached_modifiers is None
    
    def test_initialization_with_values(self):
        """Test initialization with custom PAD values."""
        expr = EmotionalExpression(
            pad_state={"valence": 0.5, "arousal": 0.8, "dominance": 0.3},
            personality={"extraversion": 0.7}
        )
        
        assert expr.pad_state["valence"] == 0.5
        assert expr.pad_state["arousal"] == 0.8
        assert expr.personality["extraversion"] == 0.7
    
    def test_update_pad(self):
        """Test updating PAD state."""
        expr = EmotionalExpression()
        
        new_state = {"valence": -0.5, "arousal": 0.9, "dominance": 0.1}
        expr.update_pad(new_state)
        
        assert expr.pad_state == new_state
        assert expr._cached_tone is None  # Cache should be cleared
        assert expr._cached_modifiers is None
    
    # === Tone Detection Tests ===
    
    def test_tone_angry(self):
        """Test angry tone detection."""
        expr = EmotionalExpression({"valence": -0.5, "arousal": 0.8, "dominance": 0.2})
        assert expr.get_tone() == EmotionalTone.ANGRY
    
    def test_tone_excited(self):
        """Test excited tone detection."""
        expr = EmotionalExpression({"valence": 0.5, "arousal": 0.8, "dominance": 0.3})
        assert expr.get_tone() == EmotionalTone.EXCITED
    
    def test_tone_calm(self):
        """Test calm tone detection."""
        expr = EmotionalExpression({"valence": 0.5, "arousal": 0.2, "dominance": 0.3})
        assert expr.get_tone() == EmotionalTone.CALM
    
    def test_tone_sad(self):
        """Test sad tone detection."""
        expr = EmotionalExpression({"valence": -0.5, "arousal": 0.2, "dominance": -0.3})
        assert expr.get_tone() == EmotionalTone.SAD
    
    def test_tone_defensive(self):
        """Test defensive tone detection."""
        expr = EmotionalExpression({"valence": 0.0, "arousal": 0.5, "dominance": -0.5})
        assert expr.get_tone() == EmotionalTone.DEFENSIVE
    
    def test_tone_receptive(self):
        """Test receptive tone detection."""
        expr = EmotionalExpression({"valence": 0.5, "arousal": 0.5, "dominance": 0.5})
        assert expr.get_tone() == EmotionalTone.RECEPTIVE
    
    def test_tone_neutral(self):
        """Test neutral tone detection."""
        expr = EmotionalExpression({"valence": 0.0, "arousal": 0.5, "dominance": 0.0})
        assert expr.get_tone() == EmotionalTone.NEUTRAL
    
    # === Tone Modifiers Tests ===
    
    def test_modifiers_high_arousal_short_sentences(self):
        """Test high arousal produces short sentences."""
        expr = EmotionalExpression({"valence": 0.0, "arousal": 0.8, "dominance": 0.0})
        modifiers = expr.get_tone_modifiers()
        
        assert modifiers.sentence_length == "short"
        assert modifiers.emphasis == "high"
    
    def test_modifiers_low_arousal_long_sentences(self):
        """Test low arousal produces long sentences."""
        expr = EmotionalExpression({"valence": 0.0, "arousal": 0.2, "dominance": 0.0})
        modifiers = expr.get_tone_modifiers()
        
        assert modifiers.sentence_length == "long"
    
    def test_modifiers_negative_valence_justification(self):
        """Test negative valence increases justification."""
        expr = EmotionalExpression({"valence": -0.5, "arousal": 0.5, "dominance": 0.0})
        modifiers = expr.get_tone_modifiers()
        
        assert modifiers.justification_level == "high"
    
    def test_modifiers_high_dominance_confident(self):
        """Test high dominance produces confident tone."""
        expr = EmotionalExpression({"valence": 0.0, "arousal": 0.5, "dominance": 0.5})
        modifiers = expr.get_tone_modifiers()
        
        assert modifiers.certainty_level == "confident"
    
    def test_modifiers_low_dominance_uncertain(self):
        """Test low dominance produces uncertain tone."""
        expr = EmotionalExpression({"valence": 0.0, "arousal": 0.5, "dominance": -0.5})
        modifiers = expr.get_tone_modifiers()
        
        assert modifiers.certainty_level == "uncertain"
    
    def test_modifiers_tone_words(self):
        """Test tone-specific adjectives and verbs."""
        expr = EmotionalExpression({"valence": -0.5, "arousal": 0.8, "dominance": 0.0})
        modifiers = expr.get_tone_modifiers()
        
        # Should have angry tone words
        assert len(modifiers.tone_adjectives) > 0
        assert modifiers.tone_adjectives[0] in ["angry", "frustrated", "indignant"]
    
    def test_modifiers_emotional_intensity(self):
        """Test emotional intensity calculation."""
        expr = EmotionalExpression({"valence": -0.8, "arousal": 0.9, "dominance": 0.0})
        modifiers = expr.get_tone_modifiers()
        
        # High valence + high arousal = high intensity
        assert modifiers.emotional_intensity > 0.7
    
    # === Prompt Injection Tests ===
    
    def test_prompt_injection_contains_state(self):
        """Test prompt injection contains emotional state."""
        expr = EmotionalExpression({"valence": -0.5, "arousal": 0.8, "dominance": 0.0})
        prompt = expr.get_prompt_injection()
        
        assert "EMOTIONAL STATE" in prompt
        assert "ANGRY" in prompt
    
    def test_prompt_injection_contains_modifiers(self):
        """Test prompt injection contains modifiers."""
        expr = EmotionalExpression({"valence": -0.5, "arousal": 0.8, "dominance": 0.0})
        prompt = expr.get_prompt_injection()
        
        # Should contain guidance
        assert "short" in prompt.lower() or "brief" in prompt.lower()
    
    # === ToneModifiers Tests ===
    
    def test_tone_modifiers_to_dict(self):
        """Test ToneModifiers serialization."""
        modifiers = ToneModifiers(
            sentence_length="short",
            emphasis="high",
            justification_level="high",
            certainty_level="confident"
        )
        
        data = modifiers.to_dict()
        
        assert data["sentence_length"] == "short"
        assert data["emphasis"] == "high"
    
    def test_tone_modifiers_get_prompt_additions(self):
        """Test prompt additions generation."""
        modifiers = ToneModifiers(
            sentence_length="short",
            emphasis="high",
            certainty_level="confident"
        )
        
        prompt = modifiers.get_prompt_additions()
        
        assert "brief" in prompt.lower() or "short" in prompt.lower()
        assert "confident" in prompt.lower()
    
    # === Caching Tests ===
    
    def test_caching(self):
        """Test that results are cached."""
        expr = EmotionalExpression({"valence": 0.5, "arousal": 0.5, "dominance": 0.0})
        
        # First call
        tone1 = expr.get_tone()
        
        # Should be cached
        assert expr._cached_tone is not None
        
        # Second call should return cached
        tone2 = expr.get_tone()
        assert tone1 == tone2
    
    def test_cache_invalidated_on_update(self):
        """Test cache is invalidated on PAD update."""
        expr = EmotionalExpression({"valence": 0.5, "arousal": 0.5, "dominance": 0.0})
        
        # Generate and cache
        _ = expr.get_tone()
        assert expr._cached_tone is not None
        
        # Update PAD
        expr.update_pad({"valence": -0.5, "arousal": 0.5, "dominance": 0.0})
        
        # Cache should be cleared
        assert expr._cached_tone is None
    
    # === Serialization Tests ===
    
    def test_to_dict(self):
        """Test serialization to dict."""
        expr = EmotionalExpression(
            pad_state={"valence": 0.3, "arousal": 0.7, "dominance": 0.2}
        )
        
        data = expr.to_dict()
        
        assert "pad_state" in data
        assert "tone" in data
        assert "modifiers" in data
        assert data["tone"] == "excited"


class TestCreateEmotionalExpression:
    """Tests for factory function."""
    
    def test_create_with_defaults(self):
        """Test factory with defaults."""
        expr = create_emotional_expression()
        
        assert expr.pad_state == {"valence": 0.0, "arousal": 0.5, "dominance": 0.0}
    
    def test_create_with_custom(self):
        """Test factory with custom values."""
        expr = create_emotional_expression(
            pad_state={"valence": -0.5, "arousal": 0.9, "dominance": 0.1},
            personality={"extraversion": 0.8}
        )
        
        assert expr.pad_state["valence"] == -0.5
        assert expr.personality["extraversion"] == 0.8


class TestPadFromBaseline:
    """Tests for pad_from_baseline helper."""
    
    def test_positive_baseline(self):
        """Test positive baseline."""
        state = pad_from_baseline("positive")
        
        assert state["valence"] == 0.5
        assert state["arousal"] == 0.5
    
    def test_negative_baseline(self):
        """Test negative baseline."""
        state = pad_from_baseline("negative")
        
        assert state["valence"] == -0.5
    
    def test_arousal_modifier(self):
        """Test arousal modifier."""
        state = pad_from_baseline("neutral", arousal_modifier=0.3)
        
        assert state["arousal"] == 0.8  # 0.5 + 0.3
    
    def test_arousal_clamp(self):
        """Test arousal is clamped to valid range."""
        state = pad_from_baseline("neutral", arousal_modifier=1.0)
        
        assert state["arousal"] == 1.0  # Clamped to max


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
