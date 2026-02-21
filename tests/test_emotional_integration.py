"""
Tests for Emotional State System
================================

Tests the PAD emotional model, tone detection, and prompt injection.

Run with: python -m pytest tsukuyomi/agent/tests/test_emotional_integration.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


from tsukuyomi.core.emotion.unified import (
    EmotionalState, EmotionalTone, apply_group_contagion
)


class TestEmotionalTone:
    """Tests for PAD to tone mapping."""
    
    def test_angry_tone(self):
        """High arousal + negative pleasure = angry."""
        state = EmotionalState(pleasure=-0.6, arousal=0.6, dominance=0.0)
        assert state.tone == EmotionalTone.ANGRY
    
    def test_anxious_tone(self):
        """High arousal + mild negative pleasure = anxious."""
        state = EmotionalState(pleasure=-0.3, arousal=0.6, dominance=0.0)
        assert state.tone == EmotionalTone.ANXIOUS
    
    def test_excited_tone(self):
        """High arousal + positive pleasure = excited."""
        state = EmotionalState(pleasure=0.6, arousal=0.6, dominance=0.0)
        assert state.tone == EmotionalTone.EXCITED
    
    def test_calm_tone(self):
        """Low arousal + positive pleasure = calm."""
        state = EmotionalState(pleasure=0.5, arousal=-0.6, dominance=0.0)
        assert state.tone == EmotionalTone.CALM
    
    def test_confident_tone(self):
        """High dominance = confident."""
        state = EmotionalState(pleasure=0.0, arousal=0.0, dominance=0.7)
        assert state.tone == EmotionalTone.CONFIDENT
    
    def test_neutral_tone(self):
        """Balanced PAD = neutral."""
        state = EmotionalState(pleasure=0.0, arousal=0.0, dominance=0.0)
        assert state.tone == EmotionalTone.NEUTRAL


class TestEmotionalUpdate:
    """Tests for emotional event updates."""
    
    def test_contradiction_decreases_pleasure(self):
        """Contradiction events decrease pleasure."""
        state = EmotionalState(pleasure=0.5, arousal=0.2)
        state.update("contradicted", intensity=0.5, tick=100)
        
        assert state.pleasure < 0.5
    
    def test_contradiction_increases_arousal(self):
        """Contradiction events increase arousal."""
        state = EmotionalState(pleasure=0.5, arousal=0.2)
        state.update("contradicted", intensity=0.5, tick=100)
        
        assert state.arousal > 0.2
    
    def test_agreement_increases_pleasure(self):
        """Agreement events increase pleasure."""
        state = EmotionalState(pleasure=0.2, arousal=0.2)
        state.update("agreed_with", intensity=0.5, tick=100)
        
        assert state.pleasure > 0.2
    
    def test_success_increases_dominance(self):
        """Success events increase dominance."""
        state = EmotionalState(pleasure=0.0, arousal=0.0, dominance=0.0)
        state.update("success", intensity=0.5, tick=100)
        
        assert state.dominance > 0
    
    def test_event_clamping(self):
        """Values stay within bounds."""
        state = EmotionalState(pleasure=0.9, arousal=0.9)
        state.update("threatened", intensity=1.0, tick=100)
        
        assert -1.0 <= state.pleasure <= 1.0
        assert -1.0 <= state.arousal <= 1.0


class TestEmotionalContagion:
    """Tests for emotional contagion between agents."""
    
    def test_contagion_affects_pleasure(self):
        """Agents catch emotions from nearby agents."""
        agents = [
            {"id": "a1", "emotional_state": EmotionalState(pleasure=0.8, susceptibility=0.5)},
            {"id": "a2", "emotional_state": EmotionalState(pleasure=0.0, susceptibility=0.5)}
        ]
        proximity = {
            "a1": {"a2": 1.0},
            "a2": {"a1": 1.0}
        }
        
        apply_group_contagion(agents, proximity, 100)
        
        # a2 should become more positive
        assert agents[1]["emotional_state"].pleasure > 0.0
    
    def test_susceptibility_affects_contagion(self):
        """Low susceptibility agents resist contagion."""
        high_suscept = EmotionalState(pleasure=0.8, susceptibility=0.9)
        low_suscept = EmotionalState(pleasure=0.0, susceptibility=0.1)
        
        agents = [
            {"id": "a1", "emotional_state": high_suscept},
            {"id": "a2", "emotional_state": low_suscept}
        ]
        proximity = {
            "a1": {"a2": 1.0},
            "a2": {"a1": 1.0}
        }
        
        apply_group_contagion(agents, proximity, 100)
        
        # Low susceptibility agent should change less
        assert agents[1]["emotional_state"].pleasure < 0.4


class TestPromptInjection:
    """Tests for prompt injection."""
    
    def test_prompt_includes_tone(self):
        """Emotional state adds tone to prompt."""
        state = EmotionalState(pleasure=-0.6, arousal=0.6)
        prompt = state.apply_to_prompt("Say something")
        
        assert "angry" in prompt.lower() or "ANXIOUS" in prompt
    
    def test_prompt_includes_arousal_guidance(self):
        """High arousal adds guidance."""
        state = EmotionalState(pleasure=0.0, arousal=0.8)
        prompt = state.apply_to_prompt("Say something")
        
        assert "activated" in prompt.lower() or "tense" in prompt.lower()
    
    def test_prompt_includes_dominance_guidance(self):
        """Dominance affects prompt."""
        state = EmotionalState(pleasure=0.0, arousal=0.0, dominance=0.8)
        prompt = state.apply_to_prompt("Say something")
        
        assert "assertive" in prompt.lower() or "control" in prompt.lower()


class TestSerialization:
    """Tests for emotional state serialization."""
    
    def test_to_dict(self):
        """Can serialize emotional state."""
        state = EmotionalState(pleasure=0.5, arousal=0.3, dominance=0.2)
        data = state.to_dict()
        
        assert data["pleasure"] == 0.5
        assert data["arousal"] == 0.3
        assert data["dominance"] == 0.2
    
    def test_from_dict(self):
        """Can deserialize emotional state."""
        data = {"pleasure": 0.5, "arousal": 0.3, "dominance": 0.2}
        state = EmotionalState.from_dict(data)
        
        assert state.pleasure == 0.5
        assert state.arousal == 0.3
        assert state.dominance == 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
