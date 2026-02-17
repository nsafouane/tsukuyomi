"""
Tests for Tsukuyomi Brain Memory Decay Calculator (Phase 15)

Run with: python -m pytest tests/test_memory_decay.py -v
"""

import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tsukuyomi.brain.memory.decay_calculator import (
    MemoryDecayCalculator, DecayConfig, DecayStrategy
)
from tsukuyomi.brain.memory.memory_types import (
    Memory, MemoryType, MemoryPriority, MemoryContext, MemoryImportance
)


class TestDecayConfig:
    def test_create_config(self):
        """Test creating decay configuration."""
        config = DecayConfig()
        assert config.base_decay_rate == 0.001
        assert config.emotional_resistance == 0.5

    def test_custom_config(self):
        """Test custom decay configuration."""
        config = DecayConfig(
            base_decay_rate=0.01,
            emotional_resistance=0.8,
            strategy=DecayStrategy.LINEAR
        )
        assert config.base_decay_rate == 0.01
        assert config.strategy == DecayStrategy.LINEAR

    def test_type_multipliers(self):
        """Test type-specific decay multipliers."""
        config = DecayConfig()
        assert config.type_decay_multipliers[MemoryType.SEMANTIC] == 0.5
        assert config.type_decay_multipliers[MemoryType.EMOTIONAL] == 0.3


class TestDecayStrategy:
    def test_all_strategies_exist(self):
        """Test all decay strategies are defined."""
        assert DecayStrategy.EXPONENTIAL.value == "exponential"
        assert DecayStrategy.LINEAR.value == "linear"
        assert DecayStrategy.LOGARITHMIC.value == "logarithmic"
        assert DecayStrategy.STEP.value == "step"


class TestMemoryDecayCalculator:
    @pytest.fixture
    def calculator(self):
        """Create a decay calculator for testing."""
        return MemoryDecayCalculator()

    @pytest.fixture
    def sample_memory(self):
        """Create a sample memory for testing."""
        return Memory(
            memory_id="test-decay-001",
            memory_type=MemoryType.EPISODIC,
            priority=MemoryPriority.MEDIUM,
            content="Test memory for decay",
            context=MemoryContext(tick=1),
            importance=MemoryImportance(base_importance=0.5)
        )

    def test_create_calculator(self, calculator):
        """Test creating a decay calculator."""
        assert calculator is not None
        assert calculator.config is not None

    def test_calculate_effective_importance(self, calculator, sample_memory):
        """Test calculating effective importance."""
        # Memory at tick 1, current tick 10 (age = 9)
        effective = calculator.effective_importance(sample_memory, current_tick=10)
        assert 0.0 <= effective <= 1.0

    def test_decay_over_time(self, calculator, sample_memory):
        """Test that memories decay over time."""
        early_tick = calculator.effective_importance(sample_memory, current_tick=10)
        late_tick = calculator.effective_importance(sample_memory, current_tick=1000)
        # Later tick should have lower effective importance
        assert late_tick < early_tick

    def test_should_prune(self, calculator, sample_memory):
        """Test pruning decision."""
        # New memory shouldn't be pruned
        assert not calculator.should_prune(sample_memory, current_tick=1)

    def test_rank_by_importance(self, calculator):
        """Test ranking memories by importance."""
        memories = [
            Memory(
                memory_id=f"mem-{i}",
                memory_type=MemoryType.EPISODIC,
                priority=MemoryPriority.MEDIUM,
                content=f"Memory {i}",
                context=MemoryContext(tick=i * 10),
                importance=MemoryImportance(base_importance=0.3 + i * 0.1)
            )
            for i in range(5)
        ]
        
        ranked = calculator.rank_by_importance(memories, current_tick=100)
        assert len(ranked) == 5
        # rank_by_importance returns list of tuples (memory, score)
        # Check structure
        assert isinstance(ranked[0], tuple)

    def test_get_memories_to_prune(self, calculator):
        """Test getting memories to prune."""
        memories = [
            Memory(
                memory_id="keep-me",
                memory_type=MemoryType.SEMANTIC,
                priority=MemoryPriority.HIGH,
                content="Important fact",
                context=MemoryContext(tick=1),
                importance=MemoryImportance(base_importance=0.9)
            ),
            Memory(
                memory_id="prune-me",
                memory_type=MemoryType.EPISODIC,
                priority=MemoryPriority.LOW,
                content="Trivial detail",
                context=MemoryContext(tick=1),
                importance=MemoryImportance(base_importance=0.05)
            )
        ]
        
        to_prune = calculator.get_memories_to_prune(memories, current_tick=10000)
        assert isinstance(to_prune, list)

    def test_get_decay_report(self, calculator, sample_memory):
        """Test getting decay report."""
        report = calculator.get_decay_report(sample_memory, current_tick=100)
        assert report is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])