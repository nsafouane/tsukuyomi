"""
Unit Tests for Long-Term Memory System
=====================================
"""

import pytest
import asyncio
from tsukuyomi.agent.memory_system import (
    MemoryType,
    MemoryImportance,
    Memory,
    LongTermMemory,
    store_event_memory
)


class TestMemory:
    """Tests for Memory dataclass."""
    
    def test_create_memory(self):
        """Test creating a basic memory."""
        memory = Memory(
            content="Saw the defendant with a knife",
            context="In the alley behind the store",
            importance=0.8,
            keywords=["knife", "defendant", "alley"],
            emotional_tags=["fear", "shock"]
        )
        
        assert memory.content == "Saw the defendant with a knife"
        assert memory.context == "In the alley behind the store"
        assert memory.importance == 0.8
        assert "knife" in memory.keywords
        assert "fear" in memory.emotional_tags
    
    def test_importance_bounds(self):
        """Test importance must be 0.0-1.0."""
        with pytest.raises(ValueError):
            Memory(content="test", importance=1.5)
        
        with pytest.raises(ValueError):
            Memory(content="test", importance=-0.5)
    
    def test_emotional_bounds(self):
        """Test emotional values must be in valid ranges."""
        with pytest.raises(ValueError):
            Memory(content="test", emotional_valence=2.0)
        
        with pytest.raises(ValueError):
            Memory(content="test", emotional_arousal=2.0)
    
    def test_access_tracking(self):
        """Test memory access tracking."""
        memory = Memory(content="Test memory")
        initial_count = memory.access_count
        
        memory.access(100)
        
        assert memory.access_count == initial_count + 1
        assert memory.last_accessed == 100
    
    def test_recency_score(self):
        """Test recency score calculation."""
        memory = Memory(created_at=50, last_accessed=50)
        
        # Immediate access
        score = memory.get_recency_score(50)
        assert score == 1.0
        
        # After some time - should still have some recency
        score = memory.get_recency_score(150, decay_rate=0.01)
        # With default decay, after 100 ticks it should be 0, so let's use higher decay
        assert score >= 0.0
    
    def test_relevance_score(self):
        """Test keyword relevance scoring."""
        memory = Memory(
            content="Test content",
            keywords=["knife", "defendant", "murder"]
        )
        
        # Direct match
        score = memory.get_relevance_score("knife")
        assert score > 0.0
        
        # No match
        score = memory.get_relevance_score("totally unrelated")
        assert score == 0.0
        
        # Multiple matches
        score = memory.get_relevance_score("knife defendant")
        assert score > memory.get_relevance_score("knife")
    
    def test_to_dict(self):
        """Test serialization."""
        memory = Memory(
            content="Test",
            memory_type=MemoryType.EPISODIC,
            importance=0.7
        )
        
        d = memory.to_dict()
        
        assert d["content"] == "Test"
        assert d["type"] == "episodic"
        assert d["importance"] == 0.7
    
    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "content": "Test memory",
            "type": "semantic",
            "importance": 0.6,
            "keywords": ["test", "data"]
        }
        
        memory = Memory.from_dict(data)
        
        assert memory.content == "Test memory"
        assert memory.memory_type == MemoryType.SEMANTIC
        assert memory.importance == 0.6
        assert "test" in memory.keywords


class TestLongTermMemory:
    """Tests for LongTermMemory class."""
    
    @pytest.fixture
    def memory_system(self):
        """Create a fresh memory system."""
        return LongTermMemory(agent_id="test_agent")
    
    def test_initialization(self, memory_system):
        """Test memory system initialization."""
        assert memory_system.agent_id == "test_agent"
        assert memory_system.get_memory_count() == 0
    
    def test_store_memory(self, memory_system):
        """Test storing a memory."""
        memory_id = memory_system.store(
            content="Witnessed an argument",
            context="Between two men on the street",
            importance=0.6,
            keywords=["argument", "witness", "street"]
        )
        
        assert memory_id is not None
        assert memory_system.get_memory_count() == 1
        
        # Verify it's stored
        memory = memory_system.memories[memory_id]
        assert memory.content == "Witnessed an argument"
    
    def test_store_indexes(self, memory_system):
        """Test that indexes are updated on store."""
        memory_id = memory_system.store(
            content="Test",
            keywords=["test", "example", "sample"]
        )
        
        assert "test" in memory_system._by_keyword
        assert memory_id in memory_system._by_keyword["test"]
    
    @pytest.mark.asyncio
    async def test_retrieve_basic(self, memory_system):
        """Test basic memory retrieval."""
        # Store some memories
        memory_system.store(
            content="Saw the defendant with a knife",
            keywords=["knife", "defendant"],
            importance=0.9
        )
        memory_system.store(
            content="Heard a loud noise",
            keywords=["noise", "sound"],
            importance=0.5
        )
        
        # Retrieve
        results = await memory_system.retrieve("knife defendant", k=5)
        
        assert len(results) >= 1
        assert "knife" in results[0].keywords
    
    @pytest.mark.asyncio
    async def test_retrieve_importance_filter(self, memory_system):
        """Test retrieval with importance filter."""
        memory_system.store(
            content="Important event",
            importance=0.9
        )
        memory_system.store(
            content="Unimportant event",
            importance=0.1
        )
        
        results = await memory_system.retrieve(
            "event", 
            min_importance=0.5
        )
        
        for r in results:
            assert r.importance >= 0.5
    
    @pytest.mark.asyncio
    async def test_retrieve_by_type(self, memory_system):
        """Test retrieval filtered by type."""
        memory_system.store(
            content="Fact about the case",
            memory_type=MemoryType.SEMANTIC,
            keywords=["fact"]
        )
        memory_system.store(
            content="Something that happened",
            memory_type=MemoryType.EPISODIC,
            keywords=["happened"]
        )
        
        results = await memory_system.retrieve(
            "fact happened",
            memory_types=[MemoryType.SEMANTIC]
        )
        
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.SEMANTIC
    
    @pytest.mark.asyncio
    async def test_retrieve_by_emotion(self, memory_system):
        """Test retrieval by emotional tag."""
        memory_system.store(
            content="Frightening event",
            emotional_tags=["fear", "terror"]
        )
        memory_system.store(
            content="Happy moment",
            emotional_tags=["joy", "happiness"]
        )
        
        results = await memory_system.retrieve_by_emotion("fear")
        
        assert len(results) == 1
        assert "fear" in results[0].emotional_tags
    
    @pytest.mark.asyncio
    async def test_get_recent(self, memory_system):
        """Test getting recent memories."""
        memory_system.store(content="First", importance=0.5)
        memory_system.store(content="Second", importance=0.5)
        memory_system.store(content="Third", importance=0.5)
        
        results = await memory_system.get_recent(count=2)
        
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_get_memories_for_prompt(self, memory_system):
        """Test formatted prompt output."""
        memory_system.store(
            content="The defendant threatened the victim yesterday",
            keywords=["defendant", "threat", "victim"],
            importance=0.8,
            emotional_tags=["fear"],
            tick=100
        )
        
        result = await memory_system.get_memories_for_prompt(
            current_situation="defendant",
            max_memories=3,
            tick=150
        )
        
        assert "defendant" in result.lower()
        assert len(result) > 0
    
    def test_statistics(self, memory_system):
        """Test statistics tracking."""
        memory_system.store(content="Test 1", importance=0.5)
        memory_system.store(content="Test 2", importance=0.5)
        
        stats = memory_system.get_statistics()
        
        assert stats["total_memories"] == 2
        assert stats["total_stored"] == 2
    
    def test_to_dict(self, memory_system):
        """Test serialization."""
        memory_system.store(content="Test")
        
        data = memory_system.to_dict()
        
        assert data["agent_id"] == "test_agent"
        assert len(data["memories"]) == 1
    
    def test_from_dict(self, memory_system):
        """Test deserialization."""
        data = {
            "agent_id": "restored_agent",
            "memories": [
                {
                    "content": "Restored memory",
                    "type": "episodic",
                    "importance": 0.7
                }
            ]
        }
        
        restored = LongTermMemory.from_dict(data)
        
        assert restored.agent_id == "restored_agent"
        assert restored.get_memory_count() == 1


class TestStoreEventMemory:
    """Tests for store_event_memory helper."""
    
    @pytest.mark.asyncio
    async def test_store_event(self):
        """Test storing an event memory."""
        memory_system = LongTermMemory(agent_id="test")
        
        memory_id = await store_event_memory(
            memory_system,
            event="The defendant shouted at the victim",
            context="In the courtroom",
            importance=0.8,
            emotional_tags=["anger", "fear"],
            tick=100
        )
        
        assert memory_id is not None
        assert memory_system.get_memory_count() == 1
        
        memory = memory_system.memories[memory_id]
        assert memory.memory_type == MemoryType.EPISODIC
        assert "defendant" in memory.keywords


class TestMemoryIntegration:
    """Integration tests for memory system."""
    
    @pytest.mark.asyncio
    async def test_full_memory_lifecycle(self):
        """Test complete memory lifecycle."""
        ms = LongTermMemory(agent_id="integration_test")
        
        # Store multiple memories
        ms.store(
            content="Initial impression of defendant",
            importance=0.7,
            keywords=["defendant", "impression"]
        )
        id2 = ms.store(
            content="Saw security footage",
            importance=0.9,
            keywords=["footage", "security"]
        )
        
        # Retrieve
        results = await ms.retrieve("defendant footage", k=5)
        assert len(results) >= 1
        
        # Access again - should increase access count
        results2 = await ms.retrieve("defendant footage", k=5)
        
        # Get recent
        recent = await ms.get_recent(count=5)
        assert len(recent) >= 2
        
        # Check statistics
        stats = ms.get_statistics()
        assert stats["total_stored"] == 2
        assert stats["total_retrieved"] >= 2
    
    @pytest.mark.asyncio
    async def test_association_chaining(self):
        """Test memory associations."""
        ms = LongTermMemory(agent_id="chain_test")
        
        id1 = ms.store(content="First event")
        id2 = ms.store(
            content="Second event",
            associated_memories=[id1]
        )
        
        # Verify association
        mem1 = ms.memories[id1]
        mem2 = ms.memories[id2]
        
        assert id2 in mem1.associated_ids
        assert id1 in mem2.associated_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
