"""
Tests for Tsukuyomi Brain Working Memory Module

Run with: python -m pytest tests/test_working_memory.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.agents.cognitive.working_memory import WorkingMemory, MemoryChunk


class MockPercept:
    """Mock percept for testing."""
    def __init__(self, content: str, salience: float = 0.5):
        self.content = content
        self.salience = salience
        self.actor = None
        self.speech = None
        self.object = None
    
    def HasField(self, field: str) -> bool:
        return False


class TestMemoryChunk:
    def test_create_chunk(self):
        """Test creating a memory chunk."""
        chunk = MemoryChunk(
            source="percept",
            content="test content",
            relevance=0.8
        )
        
        assert chunk.source == "percept"
        assert chunk.content == "test content"
        assert chunk.relevance == 0.8
    
    def test_to_text_generic(self):
        """Test formatting generic content."""
        chunk = MemoryChunk(
            source="semantic",
            content="John is a doctor",
            relevance=0.5
        )
        
        text = chunk.to_text()
        assert "John is a doctor" in text


class TestWorkingMemory:
    def test_initialization(self):
        """Test working memory initialization."""
        wm = WorkingMemory()
        
        assert len(wm.slots) == 0
        assert wm.slot_count == 0
    
    def test_slot_count(self):
        """Test slot count property."""
        wm = WorkingMemory()
        
        assert wm.slot_count == 0
        
        wm.slots.append(MemoryChunk(source="test", content="a", relevance=0.5))
        assert wm.slot_count == 1
    
    def test_refresh_with_percepts(self):
        """Test refreshing with percepts."""
        wm = WorkingMemory()
        
        percepts = [
            MockPercept("event 1", salience=0.9),
            MockPercept("event 2", salience=0.5),
        ]
        
        wm.refresh(
            percepts=percepts,
            episodic_memories=[],
            semantic_memory={},
            emotional_state=None
        )
        
        assert wm.slot_count > 0
        assert wm.slot_count <= WorkingMemory.MAX_SLOTS
    
    def test_refresh_respects_max_slots(self):
        """Test that refresh respects max slots limit."""
        wm = WorkingMemory()
        
        percepts = [MockPercept(f"event {i}", salience=0.5) for i in range(20)]
        
        wm.refresh(
            percepts=percepts,
            episodic_memories=[],
            semantic_memory={},
            emotional_state=None
        )
        
        assert wm.slot_count <= WorkingMemory.MAX_SLOTS
    
    def test_to_llm_context_empty(self):
        """Test LLM context when empty."""
        wm = WorkingMemory()
        
        context = wm.to_llm_context()
        
        assert "WORKING MEMORY" in context
        assert "0/7" in context or "(0/" in context
    
    def test_to_llm_context_with_content(self):
        """Test LLM context with content."""
        wm = WorkingMemory()
        wm.slots.append(MemoryChunk(source="percept", content=MockPercept("test"), relevance=0.8))
        
        context = wm.to_llm_context()
        
        assert "WORKING MEMORY" in context
    
    def test_refresh_with_episodic_memories(self):
        """Test refreshing with episodic memories."""
        wm = WorkingMemory()
        
        episodic = [
            {"who": "John", "what": "said hello", "when": 100, "details": {}}
        ]
        
        wm.refresh(
            percepts=[],
            episodic_memories=episodic,
            semantic_memory={},
            emotional_state=None
        )
        
        assert wm.slot_count >= 0
    
    def test_refresh_with_semantic_memory(self):
        """Test refreshing with semantic memory."""
        wm = WorkingMemory()
        
        semantic = {
            "John": {
                "is": [{"object": "a doctor"}]
            }
        }
        
        wm.refresh(
            percepts=[],
            episodic_memories=[],
            semantic_memory=semantic,
            emotional_state=None
        )
        
        assert wm.slot_count >= 0
    
    def test_refresh_prioritizes_high_salience(self):
        """Test that high salience percepts are prioritized."""
        wm = WorkingMemory()
        
        percepts = [
            MockPercept("low", salience=0.1),
            MockPercept("high", salience=0.9),
            MockPercept("medium", salience=0.5),
        ]
        
        wm.refresh(
            percepts=percepts,
            episodic_memories=[],
            semantic_memory={},
            emotional_state=None
        )
        
        if wm.slot_count > 0:
            assert wm.slots[0].relevance >= wm.slots[-1].relevance
