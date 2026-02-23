"""
Tests for Tsukuyomi Brain Memory Types Module (Phase 15)

Run with: python -m pytest tests/test_memory_types.py -v
"""

import pytest
import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.agents.cognitive.memory.memory_types import (
    MemoryType, MemoryPriority, MemoryContext, MemoryImportance,
    Memory, MemoryAccess,
    create_episodic_memory, create_semantic_memory, create_emotional_memory,
    create_social_memory, create_procedural_memory
)


class TestMemoryType:
    def test_all_types_exist(self):
        """Test that all memory types are defined."""
        assert MemoryType.EPISODIC.value == "episodic"
        assert MemoryType.SEMANTIC.value == "semantic"
        assert MemoryType.EMOTIONAL.value == "emotional"
        assert MemoryType.SOCIAL.value == "social"
        assert MemoryType.PROCEDURAL.value == "procedural"

    def test_type_count(self):
        """Test we have exactly 5 memory types."""
        assert len(MemoryType) == 5


class TestMemoryPriority:
    def test_all_priorities_exist(self):
        """Test that all priority levels are defined."""
        assert MemoryPriority.CRITICAL.value == "critical"
        assert MemoryPriority.HIGH.value == "high"
        assert MemoryPriority.MEDIUM.value == "medium"
        assert MemoryPriority.LOW.value == "low"
        assert MemoryPriority.ARCHIVED.value == "archived"

    def test_priority_order(self):
        """Test priority ordering."""
        priorities = list(MemoryPriority)
        assert priorities[0] == MemoryPriority.CRITICAL
        assert priorities[-1] == MemoryPriority.ARCHIVED


class TestMemoryContext:
    def test_create_context(self):
        """Test creating a memory context."""
        context = MemoryContext(tick=100)
        assert context.tick == 100
        assert context.timestamp is not None

    def test_context_with_all_fields(self):
        """Test context with all fields populated."""
        context = MemoryContext(
            tick=100,
            location="market",
            location_type="commercial",
            participants=["Marcus", "Julia"],
            witnesses=["spectator1"],
            situation="trade negotiation",
            trigger="price dispute"
        )
        assert context.location == "market"
        assert len(context.participants) == 2
        assert context.situation == "trade negotiation"

    def test_context_auto_timestamp(self):
        """Test that timestamp is auto-set."""
        before = time.time()
        context = MemoryContext(tick=1)
        after = time.time()
        assert before <= context.timestamp <= after


class TestMemoryImportance:
    def test_create_importance(self):
        """Test creating importance metrics."""
        importance = MemoryImportance(
            base_importance=0.5,
            emotional_weight=0.8,
            emotional_valence=0.3,
            social_weight=0.6,
            goal_relevance=0.7,
            novelty=0.4
        )
        assert importance.base_importance == 0.5
        assert importance.emotional_weight == 0.8

    def test_importance_defaults(self):
        """Test default importance values."""
        importance = MemoryImportance(base_importance=0.5)
        assert importance.emotional_weight == 0.0
        assert importance.goal_relevance == 0.0


class TestMemoryAccess:
    def test_create_access(self):
        """Test creating memory access tracking."""
        access = MemoryAccess()
        assert access is not None


class TestMemory:
    def test_create_memory(self):
        """Test creating a basic memory."""
        memory = Memory(
            memory_id="test-001",
            memory_type=MemoryType.EPISODIC,
            priority=MemoryPriority.MEDIUM,
            content="Test content",
            context=MemoryContext(tick=1),
            importance=MemoryImportance(base_importance=0.5)
        )
        assert memory.memory_id == "test-001"
        assert memory.memory_type == MemoryType.EPISODIC

    def test_memory_with_all_fields(self):
        """Test memory with all optional fields."""
        memory = Memory(
            memory_id="test-002",
            memory_type=MemoryType.SOCIAL,
            priority=MemoryPriority.HIGH,
            content="Marcus is dishonest",
            summary="Trust issue with Marcus",
            context=MemoryContext(tick=10, location="market"),
            importance=MemoryImportance(base_importance=0.8, social_weight=0.9),
            tags=["trust", "trade", "Marcus"],
            keywords=["dishonest", "trade"],
            confidence=0.85
        )
        assert memory.summary == "Trust issue with Marcus"
        assert len(memory.tags) == 3
        assert memory.confidence == 0.85


class TestMemoryFactoryFunctions:
    def test_create_episodic_memory(self):
        """Test episodic memory factory."""
        memory = create_episodic_memory(
            content="Test event",
            tick=100,
            location="market"
        )
        assert memory.memory_type == MemoryType.EPISODIC
        assert memory.content == "Test event"

    def test_create_semantic_memory(self):
        """Test semantic memory factory."""
        memory = create_semantic_memory(
            content="Apples are fruit",
            tick=1
        )
        assert memory.memory_type == MemoryType.SEMANTIC

    def test_create_emotional_memory(self):
        """Test emotional memory factory."""
        memory = create_emotional_memory(
            content="Fear of spiders",
            tick=1,
            emotional_weight=0.9
        )
        assert memory.memory_type == MemoryType.EMOTIONAL

    def test_create_social_memory(self):
        """Test social memory factory."""
        memory = create_social_memory(
            content="Marcus is a trader",
            tick=1,
            participants=["Marcus"]
        )
        assert memory.memory_type == MemoryType.SOCIAL

    def test_create_procedural_memory(self):
        """Test procedural memory factory."""
        memory = create_procedural_memory(
            content="How to barter",
            tick=1
        )
        assert memory.memory_type == MemoryType.PROCEDURAL


if __name__ == "__main__":
    pytest.main([__file__, "-v"])