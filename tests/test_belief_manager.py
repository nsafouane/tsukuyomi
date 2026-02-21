"""
Tests for Tsukuyomi Brain Belief Manager Module

Run with: python -m pytest tests/test_belief_manager.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.core.belief import BeliefManager, PersonalityBias


class TestPersonalityBias:
    def test_create_bias(self):
        """Test creating personality bias."""
        bias = PersonalityBias(
            confirmation_bias=1.0,
            disconfirmation_resistance=1.0,
            social_pressure_immunity=1.0
        )
        assert bias.confirmation_bias == 1.0


class TestBeliefManager:
    @pytest.fixture
    def manager(self):
        """Create a belief manager for testing."""
        bias = PersonalityBias(
            confirmation_bias=1.0,
            disconfirmation_resistance=0.5,
            social_pressure_immunity=0.5
        )
        return BeliefManager("test-agent", bias)

    def test_create_manager(self, manager):
        """Test creating a belief manager."""
        assert manager is not None

    def test_add_evidence(self, manager):
        """Test adding evidence."""
        manager.add_evidence(
            topic="trust_marcus",
            position="negative",
            weight=0.8,
            source_type="witness",
            description="Marcus lied",
            tick_added=100
        )

    def test_get_evidence_summary(self, manager):
        """Test getting evidence summary."""
        manager.add_evidence("topic1", "negative", 0.5, "test", "desc", 1)
        summary = manager.get_evidence_summary("topic1")
        assert summary is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])