"""
Tests for Tsukuyomi Brain Relationship Manager Module

Run with: python -m pytest tests/test_relationship_manager.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.agents.social.relationship_manager import RelationshipManager


class TestRelationshipManager:
    @pytest.fixture
    def manager(self):
        """Create a relationship manager for testing."""
        return RelationshipManager("test-agent")

    def test_create_manager(self, manager):
        """Test creating a relationship manager."""
        assert manager is not None

    def test_get_affinity(self, manager):
        """Test getting affinity with another agent."""
        affinity = manager.get_affinity("other-agent")
        assert affinity is not None

    def test_record_event(self, manager):
        """Test recording a social event."""
        manager.record_event("other-agent", "positive", 0.5, 0.8, "Test event")

    def test_to_llm_context(self, manager):
        """Test converting to LLM context."""
        context = manager.to_llm_context()
        assert isinstance(context, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])