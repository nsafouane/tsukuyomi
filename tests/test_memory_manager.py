"""
Tests for Tsukuyomi Brain Memory Manager Module

Run with: python -m pytest tests/test_memory_manager.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.brain.MemoryManager import MemoryManager


class TestMemoryManager:
    @pytest.fixture
    def manager(self):
        """Create a memory manager for testing."""
        return MemoryManager("test-agent")

    def test_create_manager(self, manager):
        """Test creating a memory manager."""
        assert manager is not None

    def test_add_fact(self, manager):
        """Test adding a fact to memory."""
        manager.add_fact("Marcus", "is_a", "trader", confidence=0.9)

    def test_query_recent(self, manager):
        """Test querying recent memories."""
        manager.add_fact("Test", "is", "fact")
        results = manager.query_recent(limit=10)
        assert isinstance(results, list)

    def test_query_long_term(self, manager):
        """Test querying long-term memories."""
        results = manager.query_long_term("trader")
        assert isinstance(results, list)

    def test_get_semantic_summary(self, manager):
        """Test getting semantic summary."""
        summary = manager.get_semantic_summary()
        assert summary is not None

    def test_tick_decay(self, manager):
        """Test tick decay."""
        manager.tick_decay(current_tick=100)

    def test_get_relations(self, manager):
        """Test getting relations."""
        manager.add_fact("Marcus", "knows", "Julia")
        relations = manager.get_relations("Marcus")
        assert isinstance(relations, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])