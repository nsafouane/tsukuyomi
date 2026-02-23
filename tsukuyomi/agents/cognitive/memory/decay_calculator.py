"""
Memory Decay Calculator for Tsukuyomi V2 Agent Quality Implementation.

This module implements the memory decay system for the Deep Memory Architecture
(Phase 15 of the Agent Quality Specification).

The decay system ensures:
- Important memories persist longer
- Emotional memories are resistant to decay
- Frequently accessed memories are reinforced
- Trivial memories fade over time
- Memory storage remains bounded

Decay Formula:
    effective_importance = base_importance * decay_factor * emotional_factor * access_boost

Where:
    decay_factor = exp(-age * BASE_DECAY_RATE)
    emotional_factor = 1.0 - (emotional_weight * EMOTIONAL_RESISTANCE)
    access_boost = 1.0 + (access_count * ACCESS_REINFORCEMENT * 0.1)

Author: Tanit (AI Co-founder) + Safouane
Date: 2026-02-17
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable
from enum import Enum
import logging

from .memory_types import Memory, MemoryType, MemoryPriority

logger = logging.getLogger("MemoryDecayCalculator")


class DecayStrategy(Enum):
    """
    Different strategies for memory decay.
    
    EXPONENTIAL: Standard exponential decay (default)
    LINEAR: Simple linear decay
    LOGARITHMIC: Slow initial decay, accelerates later
    STEP: Discrete steps (sudden drops at thresholds)
    """
    
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    STEP = "step"


@dataclass
class DecayConfig:
    """
    Configuration parameters for memory decay calculation.
    
    These can be tuned to adjust how quickly memories fade.
    """
    
    # Base decay rate (per-tick decay factor)
    base_decay_rate: float = 0.001  # Higher = faster decay
    
    # Emotional resistance (how much emotions protect memories)
    emotional_resistance: float = 0.5  # Higher = more protection
    
    # Access reinforcement (how much each access strengthens memory)
    access_reinforcement: float = 0.1  # Higher = stronger reinforcement
    
    # Minimum importance threshold (memories below this are pruned)
    min_importance_threshold: float = 0.05
    
    # Maximum access boost cap (prevent unbounded reinforcement)
    max_access_boost: float = 2.0
    
    # Strategy for decay calculation
    strategy: DecayStrategy = DecayStrategy.EXPONENTIAL
    
    # Type-specific decay multipliers
    type_decay_multipliers: dict = field(default_factory=lambda: {
        MemoryType.EPISODIC: 1.0,      # Standard decay
        MemoryType.SEMANTIC: 0.5,      # Facts decay slower
        MemoryType.EMOTIONAL: 0.3,     # Emotional memories decay slowest
        MemoryType.SOCIAL: 0.7,        # Social memories moderately slow
        MemoryType.PROCEDURAL: 0.4,    # Skills persist well
    })
    
    # Priority-based decay modifiers
    priority_decay_modifiers: dict = field(default_factory=lambda: {
        MemoryPriority.CRITICAL: 0.1,   # Critical memories decay very slowly
        MemoryPriority.HIGH: 0.3,       # High priority memories decay slowly
        MemoryPriority.MEDIUM: 1.0,     # Standard decay
        MemoryPriority.LOW: 2.0,        # Low priority memories decay faster
        MemoryPriority.ARCHIVED: 3.0,   # Archived memories decay fastest
    })


class MemoryDecayCalculator:
    """
    Calculate effective importance of memories over time.
    
    The decay system implements a multi-factor decay model:
    
    1. **Base Decay**: Memories naturally fade over time (exponential by default)
    2. **Emotional Resistance**: High emotional weight memories decay slower
    3. **Access Reinforcement**: Frequently accessed memories are reinforced
    4. **Type Modifier**: Different memory types decay at different rates
    5. **Priority Modifier**: Priority levels affect decay rate
    
    Usage:
        calculator = MemoryDecayCalculator()
        
        # Check if a memory should be pruned
        if calculator.should_prune(memory, current_tick):
            # Remove memory
            
        # Get effective importance for ranking
        effective = calculator.effective_importance(memory, current_tick)
    """
    
    def __init__(self, config: Optional[DecayConfig] = None):
        """
        Initialize the decay calculator.
        
        Args:
            config: Optional decay configuration. Uses defaults if not provided.
        """
        self.config = config or DecayConfig()
    
    def effective_importance(self, memory: Memory, current_tick: int) -> float:
        """
        Calculate current effective importance with decay applied.
        
        This is the main entry point for decay calculation, combining
        all decay factors into a single importance score.
        
        Args:
            memory: The memory to calculate importance for
            current_tick: Current simulation tick
            
        Returns:
            float: Effective importance (0.0 to 1.0+, typically < 2.0)
        """
        # Get base importance from computed value
        base_importance = memory.compute_importance()
        
        # Calculate age (ticks since creation)
        age = max(0, current_tick - memory.access.creation_tick)
        
        # 1. Base decay factor (exponential by default)
        decay_factor = self._calculate_decay_factor(age)
        
        # 2. Emotional resistance factor
        emotional_factor = self._calculate_emotional_factor(memory)
        
        # 3. Access reinforcement factor
        access_boost = self._calculate_access_boost(memory)
        
        # 4. Memory type modifier
        type_multiplier = self._get_type_multiplier(memory.memory_type)
        
        # 5. Priority modifier
        priority_modifier = self._get_priority_modifier(memory.priority)
        
        # Combine all factors
        effective = (
            base_importance 
            * decay_factor 
            * emotional_factor 
            * access_boost
            * type_multiplier
            * priority_modifier
        )
        
        return effective
    
    def _calculate_decay_factor(self, age: int) -> float:
        """
        Calculate the base decay factor based on memory age.
        
        Uses the configured decay strategy.
        
        Args:
            age: Ticks since memory creation
            
        Returns:
            float: Decay factor (0.0 to 1.0)
        """
        if age <= 0:
            return 1.0
        
        strategy = self.config.strategy
        
        if strategy == DecayStrategy.EXPONENTIAL:
            # Standard exponential decay
            return math.exp(-age * self.config.base_decay_rate)
        
        elif strategy == DecayStrategy.LINEAR:
            # Linear decay (bounded at 0)
            return max(0.0, 1.0 - (age * self.config.base_decay_rate))
        
        elif strategy == DecayStrategy.LOGARITHMIC:
            # Slow initial decay, accelerates later
            if age <= 1:
                return 1.0
            return 1.0 / (1.0 + math.log(age) * self.config.base_decay_rate * 10)
        
        elif strategy == DecayStrategy.STEP:
            # Discrete steps at threshold ages
            if age < 100:
                return 1.0
            elif age < 500:
                return 0.8
            elif age < 1000:
                return 0.5
            elif age < 2000:
                return 0.3
            else:
                return 0.1
        
        return 1.0  # Fallback
    
    def _calculate_emotional_factor(self, memory: Memory) -> float:
        """
        Calculate emotional resistance factor.
        
        Emotional memories are more resistant to decay because
        they have stronger neural encoding.
        
        Args:
            memory: The memory to calculate for
            
        Returns:
            float: Emotional resistance factor (0.5 to 1.0)
        """
        # Emotional resistance: high emotional weight = slower decay
        # Factor ranges from 0.5 (no emotion) to 1.0 (max emotion)
        emotional_weight = memory.importance.emotional_weight
        
        # Higher emotional weight means higher resistance (closer to 1.0)
        resistance = 1.0 - (emotional_weight * self.config.emotional_resistance)
        
        # Ensure minimum of 0.5 (emotional memories decay at half rate at max)
        return max(0.5, resistance)
    
    def _calculate_access_boost(self, memory: Memory) -> float:
        """
        Calculate access reinforcement boost.
        
        Frequently accessed memories are "rehearsed" and strengthened.
        This mimics how repeated recall strengthens real memories.
        
        Args:
            memory: The memory to calculate for
            
        Returns:
            float: Access boost factor (1.0 to max_access_boost)
        """
        # Each access adds reinforcement
        access_count = memory.access.access_count
        
        # Calculate boost with diminishing returns
        boost = 1.0 + (access_count * self.config.access_reinforcement * 0.1)
        
        # Cap at maximum
        return min(self.config.max_access_boost, boost)
    
    def _get_type_multiplier(self, memory_type: MemoryType) -> float:
        """
        Get decay multiplier for memory type.
        
        Different memory types decay at different rates:
        - Semantic and procedural memories persist longer
        - Emotional memories are most resistant
        - Episodic memories decay at standard rate
        
        Args:
            memory_type: The type of memory
            
        Returns:
            float: Type-specific multiplier
        """
        return self.config.type_decay_multipliers.get(memory_type, 1.0)
    
    def _get_priority_modifier(self, priority: MemoryPriority) -> float:
        """
        Get decay modifier for priority level.
        
        Higher priority memories decay slower.
        
        Args:
            priority: The priority level
            
        Returns:
            float: Priority-based modifier
        """
        return self.config.priority_decay_modifiers.get(priority, 1.0)
    
    def should_prune(self, memory: Memory, current_tick: int) -> bool:
        """
        Determine if a memory should be pruned (removed).
        
        Memories are pruned when their effective importance falls
        below the minimum threshold.
        
        Args:
            memory: The memory to check
            current_tick: Current simulation tick
            
        Returns:
            bool: True if memory should be pruned
        """
        effective = self.effective_importance(memory, current_tick)
        return effective < self.config.min_importance_threshold
    
    def get_memories_to_prune(
        self, 
        memories: List[Memory], 
        current_tick: int
    ) -> List[Memory]:
        """
        Get all memories that should be pruned.
        
        Args:
            memories: List of all memories
            current_tick: Current simulation tick
            
        Returns:
            List[Memory]: Memories to prune
        """
        return [m for m in memories if self.should_prune(m, current_tick)]
    
    def get_decay_report(
        self, 
        memory: Memory, 
        current_tick: int
    ) -> dict:
        """
        Get a detailed breakdown of decay factors for a memory.
        
        Useful for debugging and visualization.
        
        Args:
            memory: The memory to analyze
            current_tick: Current simulation tick
            
        Returns:
            dict: Detailed decay breakdown
        """
        age = max(0, current_tick - memory.access.creation_tick)
        
        return {
            "memory_id": memory.memory_id,
            "memory_type": memory.memory_type.value,
            "priority": memory.priority.value,
            "age_ticks": age,
            "base_importance": memory.compute_importance(),
            "decay_factor": self._calculate_decay_factor(age),
            "emotional_factor": self._calculate_emotional_factor(memory),
            "access_boost": self._calculate_access_boost(memory),
            "type_multiplier": self._get_type_multiplier(memory.memory_type),
            "priority_modifier": self._get_priority_modifier(memory.priority),
            "effective_importance": self.effective_importance(memory, current_tick),
            "should_prune": self.should_prune(memory, current_tick),
        }
    
    def rank_by_importance(
        self, 
        memories: List[Memory], 
        current_tick: int,
        limit: Optional[int] = None
    ) -> List[Tuple[Memory, float]]:
        """
        Rank memories by effective importance.
        
        Args:
            memories: Memories to rank
            current_tick: Current simulation tick
            limit: Maximum number to return (optional)
            
        Returns:
            List[Tuple[Memory, float]]: Memories with importance scores, sorted descending
        """
        scored = [
            (memory, self.effective_importance(memory, current_tick))
            for memory in memories
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        if limit is not None:
            scored = scored[:limit]
        
        return scored


class MemoryImportanceCalculator:
    """
    Calculate initial importance for new memories.
    
    This determines how important a memory should be when first created,
    based on emotional intensity, social relevance, novelty, and goal impact.
    """
    
    def __init__(
        self,
        emotional_weight: float = 0.3,
        social_weight: float = 0.2,
        novelty_weight: float = 0.2,
        goal_weight: float = 0.2,
        base_weight: float = 0.1
    ):
        """
        Initialize the importance calculator with weights.
        
        Args:
            emotional_weight: Weight for emotional intensity
            social_weight: Weight for social relevance
            novelty_weight: Weight for novelty factor
            goal_weight: Weight for goal relevance
            base_weight: Base weight for minimum importance
        """
        self.emotional_weight = emotional_weight
        self.social_weight = social_weight
        self.novelty_weight = novelty_weight
        self.goal_weight = goal_weight
        self.base_weight = base_weight
    
    def calculate_importance(
        self,
        emotional_intensity: float = 0.0,
        social_relevance: float = 0.0,
        novelty: float = 0.0,
        goal_relevance: float = 0.0,
        base_importance: float = 0.3
    ) -> float:
        """
        Calculate initial importance for a new memory.
        
        Args:
            emotional_intensity: Emotional intensity (0.0 to 1.0)
            social_relevance: Social relevance (0.0 to 1.0)
            novelty: Novelty factor (0.0 to 1.0)
            goal_relevance: Goal relevance (0.0 to 1.0)
            base_importance: Base importance (default 0.3)
            
        Returns:
            float: Importance score (0.0 to 1.0)
        """
        score = (
            base_importance * self.base_weight +
            emotional_intensity * self.emotional_weight +
            social_relevance * self.social_weight +
            novelty * self.novelty_weight +
            goal_relevance * self.goal_weight
        )
        
        return min(1.0, max(0.0, score))
    
    def calculate_from_state(
        self,
        arousal: float,
        participants: List[str],
        relationship_affinities: dict,
        is_novel: bool,
        affects_goals: bool
    ) -> float:
        """
        Calculate importance from agent state.
        
        Args:
            arousal: Agent's arousal level (0.0 to 1.0)
            participants: List of participants in event
            relationship_affinities: Dict of participant_id -> affinity
            is_novel: Whether this is a novel experience
            affects_goals: Whether this affects agent's goals
            
        Returns:
            float: Importance score (0.0 to 1.0)
        """
        # Emotional intensity from arousal
        emotional_intensity = arousal
        
        # Social relevance from relationship strengths
        if participants and relationship_affinities:
            affinities = [
                abs(relationship_affinities.get(p, 0.5))
                for p in participants
            ]
            social_relevance = sum(affinities) / len(affinities)
        else:
            social_relevance = 0.0
        
        # Novelty
        novelty = 1.0 if is_novel else 0.0
        
        # Goal relevance
        goal_relevance = 1.0 if affects_goals else 0.0
        
        return self.calculate_importance(
            emotional_intensity=emotional_intensity,
            social_relevance=social_relevance,
            novelty=novelty,
            goal_relevance=goal_relevance
        )


def apply_decay_batch(
    memories: List[Memory],
    current_tick: int,
    config: Optional[DecayConfig] = None
) -> Tuple[List[Memory], List[Memory]]:
    """
    Apply decay to a batch of memories.
    
    This is a convenience function for processing all memories at once.
    
    Args:
        memories: List of memories to process
        current_tick: Current simulation tick
        config: Optional decay configuration
        
    Returns:
        Tuple[List[Memory], List[Memory]]: (kept memories, pruned memories)
    """
    calculator = MemoryDecayCalculator(config)
    
    kept = []
    pruned = []
    
    for memory in memories:
        if calculator.should_prune(memory, current_tick):
            pruned.append(memory)
        else:
            kept.append(memory)
    
    return kept, pruned
