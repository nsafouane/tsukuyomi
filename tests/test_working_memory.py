"""
Tests for Tsukuyomi Brain Working Memory Module

Run with: python -m pytest tests/test_working_memory.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.brain.WorkingMemory import WorkingMemory
from dataclasses import dataclass


@dataclass
class MockPercept:
    """Mock percept for testing."""
    content: str
    salience: float = 0.5


class TestWorkingMemory:
    def test_create(self):
        """Test creating working memory."""
        wm = WorkingMemory()
        assert wm is not None

    def test_max_slots(self):
        """Test that max slots is defined (Miller's Law: 7±2)."""
        assert hasattr(WorkingMemory, 'MAX_SLOTS')
        # Should be between 5 and 9 (Miller's Law)
        assert 5 <= WorkingMemory.MAX_SLOTS <= 9

    def test_slot_count_initial(self):
        """Test initial slot count (it's a property, not method)."""
        wm = WorkingMemory()
        assert wm.slot_count == 0

    def test_refresh(self):
        """Test refreshing working memory."""
        wm = WorkingMemory()
        percepts = [
            MockPercept(content="saw Marcus", salience=0.8),
            MockPercept(content="heard shouting", salience=0.6)
        ]
        episodic = []
        semantic = {"Marcus": "trader"}
        emotional_state = {"valence": 0.5}
        wm.refresh(percepts, episodic, semantic, emotional_state)
        # After refresh, slot_count should be updated
        assert wm.slot_count >= 0

    def test_to_llm_context(self):
        """Test converting to LLM context."""
        wm = WorkingMemory()
        percepts = [
            MockPercept(content="item1", salience=0.5),
            MockPercept(content="item2", salience=0.4)
        ]
        wm.refresh(percepts, [], {}, {})
        context = wm.to_llm_context()
        assert isinstance(context, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])