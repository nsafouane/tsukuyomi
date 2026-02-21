"""
Tests for Tsukuyomi Brain State Manager Module

Run with: python -m pytest tests/test_state_manager.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.core.emotion.unified import (
    StateManager, PersonalityBaseline, EmotionalState
)


class TestPersonalityBaseline:
    def test_create_baseline(self):
        """Test creating personality baseline."""
        baseline = PersonalityBaseline(
            valence_baseline=0.0,
            arousal_baseline=0.5,
            dominance_baseline=0.0,
            regression_rate=0.015
        )
        assert baseline.valence_baseline == 0.0
        assert baseline.arousal_baseline == 0.5


class TestEmotionalState:
    def test_create_state(self):
        """Test creating emotional state."""
        state = EmotionalState(
            valence=0.5,
            arousal=0.5,
            dominance=0.5
        )
        assert state.valence == 0.5


class TestStateManager:
    @pytest.fixture
    def manager(self):
        """Create a state manager for testing."""
        baseline = PersonalityBaseline(
            valence_baseline=0.0,
            arousal_baseline=0.5,
            dominance_baseline=0.0
        )
        return StateManager(baseline)

    def test_create_manager(self, manager):
        """Test creating a state manager."""
        assert manager is not None

    def test_get_emotional_context(self, manager):
        """Test getting emotional context."""
        context = manager.get_emotional_context()
        assert context is not None

    def test_get_state_dict(self, manager):
        """Test getting state as dict."""
        state = manager.get_state_dict()
        assert isinstance(state, dict)

    def test_reset_to_baseline(self, manager):
        """Test resetting to baseline."""
        manager.reset_to_baseline()
        state = manager.get_state_dict()
        assert state is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])