"""
Memory Retrieval System for Tsukuyomi V2 Agent Quality Implementation.

This module implements context-aware memory retrieval for the Deep Memory Architecture
(Phase 15 of the Agent Quality Specification).

The retrieval system supports:
- Semantic similarity search (via embeddings)
- Participant matching (memories involving relevant people)
- Emotional similarity (memories with similar emotional content)
- Decay-adjusted ranking (accounting for memory age and importance)
- Context-aware retrieval (considering current situation)

Author: Tanit (AI Co-founder) + Safouane
Date: 2026-02-17
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Set, Tuple, Callable
from enum import Enum
import logging
import math
import re
from collections import defaultdict

from .memory_types import Memory, MemoryType, MemoryContext, MemoryImportance
from .decay_calculator import MemoryDecayCalculator, DecayConfig

logger = logging.getLogger("MemoryRetrieval")


class RetrievalMode(Enum):
    """
    Different modes for memory retrieval.
    
    RELEVANCE: Balance of semantic, participant, and decay factors
    RECENT: Prioritize recent memories
    IMPORTANT: Prioritize high importance memories
    EMOTIONAL: Prioritize emotional memories
    SOCIAL: Prioritize social/relational memories
    HYBRID: Combine multiple factors with configurable weights
    """
    
    RELEVANCE = "relevance"
    RECENT = "recent"
    IMPORTANT = "important"
    EMOTIONAL = "emotional"
    SOCIAL = "social"
    HYBRID = "hybrid"


@dataclass
class RetrievalContext:
    """
    Context for memory retrieval operation.
    
    Provides all the information needed to retrieve memories
    that are relevant to the current situation.
    """
    
    # Current situation description
    situation: str = ""
    
    # Current participants (people present)
    participants: List[str] = field(default_factory=list)
    
    # Current location
    location: str = ""
    
    # Current tick
    current_tick: int = 0
    
    # Emotional state (for emotional similarity matching)
    emotional_state: Optional[Dict[str, float]] = None  # e.g., {"valence": 0.5, "arousal": 0.3}
    
    # Active goals (for goal relevance)
    active_goals: List[str] = field(default_factory=list)
    
    # Keywords extracted from situation
    keywords: List[str] = field(default_factory=list)
    
    # Memory types to prioritize
    priority_types: List[MemoryType] = field(default_factory=list)
    
    # Minimum importance threshold
    min_importance: float = 0.0
    
    # Maximum memories to return
    limit: int = 5


@dataclass
class RetrievalWeights:
    """
    Weights for different factors in hybrid retrieval mode.
    
    All weights should sum to 1.0 for proper normalization.
    """
    
    semantic_similarity: float = 0.35    # Vector/text similarity
    participant_match: float = 0.25      # Involves current participants
    decay_adjusted_importance: float = 0.20  # Importance with decay
    emotional_similarity: float = 0.10   # Similar emotional content
    recency: float = 0.10               # How recent the memory is
    
    def validate(self) -> bool:
        """Check if weights sum to approximately 1.0."""
        total = (
            self.semantic_similarity +
            self.participant_match +
            self.decay_adjusted_importance +
            self.emotional_similarity +
            self.recency
        )
        return abs(total - 1.0) < 0.01


@dataclass
class ScoredMemory:
    """
    A memory with its retrieval score breakdown.
    
    Useful for debugging and understanding why certain
    memories were retrieved.
    """
    
    memory: Memory
    total_score: float
    
    # Score breakdown
    semantic_score: float = 0.0
    participant_score: float = 0.0
    importance_score: float = 0.0
    emotional_score: float = 0.0
    recency_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "memory_id": self.memory.memory_id,
            "summary": self.memory.summary,
            "total_score": self.total_score,
            "breakdown": {
                "semantic": self.semantic_score,
                "participant": self.participant_score,
                "importance": self.importance_score,
                "emotional": self.emotional_score,
                "recency": self.recency_score,
            }
        }


class MemoryRetrieval:
    """
    Context-aware memory retrieval system.
    
    This class implements the memory retrieval algorithm that combines
    multiple factors to find the most relevant memories for a situation.
    
    Retrieval Process:
    1. **Candidate Generation**: Find potential memories via semantic search,
       participant matching, and emotional similarity
    2. **Scoring**: Score each candidate using weighted factors
    3. **Ranking**: Sort by combined score
    4. **Access Update**: Update access counts for retrieved memories
    
    Usage:
        retrieval = MemoryRetrieval(memory_store, decay_calculator)
        
        context = RetrievalContext(
            situation="discussing trade with Marcus",
            participants=["Marcus"],
            current_tick=150
        )
        
        memories = retrieval.retrieve(context)
    """
    
    def __init__(
        self,
        decay_calculator: Optional[MemoryDecayCalculator] = None,
        weights: Optional[RetrievalWeights] = None,
        embedding_func: Optional[Callable[[str], List[float]]] = None
    ):
        """
        Initialize the memory retrieval system.
        
        Args:
            decay_calculator: Calculator for memory decay (uses default if None)
            weights: Retrieval factor weights (uses default if None)
            embedding_func: Function to compute embeddings for semantic search
        """
        self.decay_calculator = decay_calculator or MemoryDecayCalculator()
        self.weights = weights or RetrievalWeights()
        self.embedding_func = embedding_func
        
        # Cache for embeddings
        self._embedding_cache: Dict[str, List[float]] = {}
    
    def retrieve(
        self,
        memories: List[Memory],
        context: RetrievalContext
    ) -> List[Memory]:
        """
        Retrieve the most relevant memories for the given context.
        
        Args:
            memories: All available memories
            context: Retrieval context with situation, participants, etc.
            
        Returns:
            List[Memory]: Top memories sorted by relevance
        """
        if not memories:
            return []
        
        # Step 1: Filter by minimum criteria
        candidates = self._filter_candidates(memories, context)
        
        if not candidates:
            return []
        
        # Step 2: Score candidates
        scored = self._score_candidates(candidates, context)
        
        # Step 3: Rank and select top
        scored.sort(key=lambda x: x.total_score, reverse=True)
        top_memories = [s.memory for s in scored[:context.limit]]
        
        # Step 4: Update access stats
        for memory in top_memories:
            memory.record_access(context.current_tick)
        
        return top_memories
    
    def retrieve_with_scores(
        self,
        memories: List[Memory],
        context: RetrievalContext
    ) -> List[ScoredMemory]:
        """
        Retrieve memories with detailed score breakdown.
        
        Useful for debugging and understanding retrieval decisions.
        
        Args:
            memories: All available memories
            context: Retrieval context
            
        Returns:
            List[ScoredMemory]: Scored memories sorted by relevance
        """
        if not memories:
            return []
        
        candidates = self._filter_candidates(memories, context)
        scored = self._score_candidates(candidates, context)
        scored.sort(key=lambda x: x.total_score, reverse=True)
        
        return scored[:context.limit]
    
    def _filter_candidates(
        self,
        memories: List[Memory],
        context: RetrievalContext
    ) -> List[Memory]:
        """
        Filter memories by minimum criteria.
        
        Applies quick filters before detailed scoring:
        - Minimum importance threshold
        - Memory type priorities
        - Pruned memories (below decay threshold)
        
        Args:
            memories: All memories
            context: Retrieval context
            
        Returns:
            List[Memory]: Filtered candidates
        """
        candidates = []
        
        for memory in memories:
            # Skip pruned memories
            if self.decay_calculator.should_prune(memory, context.current_tick):
                continue
            
            # Check minimum importance
            effective_importance = self.decay_calculator.effective_importance(
                memory, context.current_tick
            )
            if effective_importance < context.min_importance:
                continue
            
            # Check memory type priority
            if context.priority_types:
                if memory.memory_type not in context.priority_types:
                    continue
            
            candidates.append(memory)
        
        return candidates
    
    def _score_candidates(
        self,
        memories: List[Memory],
        context: RetrievalContext
    ) -> List[ScoredMemory]:
        """
        Score each memory candidate using weighted factors.
        
        Args:
            memories: Candidate memories
            context: Retrieval context
            
        Returns:
            List[ScoredMemory]: Scored memories
        """
        scored = []
        
        for memory in memories:
            # Calculate individual scores
            semantic_score = self._semantic_similarity(memory, context)
            participant_score = self._participant_match(memory, context)
            importance_score = self._decay_adjusted_importance(memory, context)
            emotional_score = self._emotional_similarity(memory, context)
            recency_score = self._recency_score(memory, context)
            
            # Combine with weights
            total_score = (
                semantic_score * self.weights.semantic_similarity +
                participant_score * self.weights.participant_match +
                importance_score * self.weights.decay_adjusted_importance +
                emotional_score * self.weights.emotional_similarity +
                recency_score * self.weights.recency
            )
            
            scored.append(ScoredMemory(
                memory=memory,
                total_score=total_score,
                semantic_score=semantic_score,
                participant_score=participant_score,
                importance_score=importance_score,
                emotional_score=emotional_score,
                recency_score=recency_score
            ))
        
        return scored
    
    def _semantic_similarity(self, memory: Memory, context: RetrievalContext) -> float:
        """
        Calculate semantic similarity between memory and context.
        
        Uses embeddings if available, otherwise falls back to keyword matching.
        
        Args:
            memory: Memory to score
            context: Retrieval context
            
        Returns:
            float: Similarity score (0.0 to 1.0)
        """
        # If embeddings available, use cosine similarity
        if self.embedding_func and memory.embedding:
            try:
                # Get or compute embedding for situation
                if context.situation not in self._embedding_cache:
                    self._embedding_cache[context.situation] = self.embedding_func(context.situation)
                
                situation_embedding = self._embedding_cache[context.situation]
                return self._cosine_similarity(memory.embedding, situation_embedding)
            except Exception as e:
                logger.debug(f"Embedding similarity failed: {e}")
        
        # Fallback to keyword matching
        if not context.keywords and context.situation:
            context.keywords = self._extract_keywords(context.situation)
        
        if not context.keywords:
            return 0.0
        
        # Check for keyword matches
        memory_keywords = set(memory.keywords) | set(k.lower() for k in memory.tags)
        context_keywords = set(k.lower() for k in context.keywords)
        
        if not memory_keywords or not context_keywords:
            return 0.0
        
        # Jaccard similarity
        intersection = len(memory_keywords & context_keywords)
        union = len(memory_keywords | context_keywords)
        
        return intersection / union if union > 0 else 0.0
    
    def _participant_match(self, memory: Memory, context: RetrievalContext) -> float:
        """
        Calculate participant match score.
        
        Memories involving current participants are more relevant.
        
        Args:
            memory: Memory to score
            context: Retrieval context
            
        Returns:
            float: Participant match score (0.0 to 1.0)
        """
        if not context.participants or not memory.context.participants:
            return 0.0
        
        memory_participants = set(p.lower() for p in memory.context.participants)
        context_participants = set(p.lower() for p in context.participants)
        
        intersection = memory_participants & context_participants
        
        if not intersection:
            return 0.0
        
        # Full match = 1.0, partial match = proportion
        return len(intersection) / len(context_participants)
    
    def _decay_adjusted_importance(
        self, 
        memory: Memory, 
        context: RetrievalContext
    ) -> float:
        """
        Calculate decay-adjusted importance score.
        
        Args:
            memory: Memory to score
            context: Retrieval context
            
        Returns:
            float: Importance score (0.0 to 1.0)
        """
        effective = self.decay_calculator.effective_importance(
            memory, context.current_tick
        )
        return min(1.0, effective)
    
    def _emotional_similarity(
        self, 
        memory: Memory, 
        context: RetrievalContext
    ) -> float:
        """
        Calculate emotional similarity score.
        
        Memories with similar emotional content are more relevant
        when in similar emotional states.
        
        Args:
            memory: Memory to score
            context: Retrieval context
            
        Returns:
            float: Emotional similarity score (0.0 to 1.0)
        """
        if not context.emotional_state:
            # If no emotional state provided, use emotional weight as relevance
            return memory.importance.emotional_weight
        
        # Compare emotional valence
        context_valence = context.emotional_state.get("valence", 0.0)
        memory_valence = memory.importance.emotional_valence
        
        # Similar valence = higher score
        valence_similarity = 1.0 - abs(context_valence - memory_valence) / 2.0
        
        # Weight by emotional intensity
        return valence_similarity * memory.importance.emotional_weight
    
    def _recency_score(self, memory: Memory, context: RetrievalContext) -> float:
        """
        Calculate recency score.
        
        More recent memories score higher, but with diminishing returns.
        
        Args:
            memory: Memory to score
            context: Retrieval context
            
        Returns:
            float: Recency score (0.0 to 1.0)
        """
        if context.current_tick <= 0:
            return 0.5  # Default if no tick info
        
        age = context.current_tick - memory.access.creation_tick
        
        if age <= 0:
            return 1.0
        
        # Exponential decay of recency (recent = high, old = low)
        # Adjusted so ~100 ticks = 0.5 score, ~500 ticks = 0.1 score
        return math.exp(-age / 200.0)
    
    def _cosine_similarity(
        self, 
        vec1: List[float], 
        vec2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            float: Cosine similarity (0.0 to 1.0)
        """
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Cosine similarity ranges from -1 to 1, normalize to 0 to 1
        similarity = dot_product / (norm1 * norm2)
        return (similarity + 1.0) / 2.0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text for keyword matching.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List[str]: Extracted keywords
        """
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'was', 'at', 'on', 'in', 'to', 'for',
            'of', 'and', 'or', 'but', 'with', 'by', 'from', 'that', 'this',
            'it', 'he', 'she', 'they', 'we', 'i', 'you', 'be', 'been',
        }
        
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return list(set(keywords))  # Unique keywords only


class MemoryStore:
    """
    In-memory storage for memories with indexing for fast retrieval.
    
    This provides efficient lookup by:
    - Memory ID
    - Participant
    - Memory type
    - Location
    - Tags/keywords
    """
    
    def __init__(self):
        """Initialize the memory store."""
        # Primary storage
        self.memories: Dict[str, Memory] = {}
        
        # Indexes for fast lookup
        self._participant_index: Dict[str, Set[str]] = defaultdict(set)
        self._type_index: Dict[MemoryType, Set[str]] = defaultdict(set)
        self._location_index: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
    
    def store(self, memory: Memory) -> None:
        """
        Store a memory and update indexes.
        
        Args:
            memory: Memory to store
        """
        # Store in primary storage
        self.memories[memory.memory_id] = memory
        
        # Update indexes
        for participant in memory.context.participants:
            self._participant_index[participant.lower()].add(memory.memory_id)
        
        self._type_index[memory.memory_type].add(memory.memory_id)
        
        if memory.context.location:
            self._location_index[memory.context.location.lower()].add(memory.memory_id)
        
        for tag in memory.tags:
            self._tag_index[tag.lower()].add(memory.memory_id)
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Optional[Memory]: Memory if found
        """
        return self.memories.get(memory_id)
    
    def get_by_participant(self, participant: str) -> List[Memory]:
        """
        Get all memories involving a participant.
        
        Args:
            participant: Participant name/ID
            
        Returns:
            List[Memory]: Memories involving participant
        """
        memory_ids = self._participant_index.get(participant.lower(), set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """
        Get all memories of a specific type.
        
        Args:
            memory_type: Memory type to filter by
            
        Returns:
            List[Memory]: Memories of that type
        """
        memory_ids = self._type_index.get(memory_type, set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_by_location(self, location: str) -> List[Memory]:
        """
        Get all memories at a specific location.
        
        Args:
            location: Location name
            
        Returns:
            List[Memory]: Memories at that location
        """
        memory_ids = self._location_index.get(location.lower(), set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_by_tag(self, tag: str) -> List[Memory]:
        """
        Get all memories with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List[Memory]: Memories with that tag
        """
        memory_ids = self._tag_index.get(tag.lower(), set())
        return [self.memories[mid] for mid in memory_ids if mid in self.memories]
    
    def get_all(self) -> List[Memory]:
        """
        Get all memories.
        
        Returns:
            List[Memory]: All stored memories
        """
        return list(self.memories.values())
    
    def remove(self, memory_id: str) -> bool:
        """
        Remove a memory from the store.
        
        Args:
            memory_id: Memory ID to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        memory = self.memories.get(memory_id)
        if not memory:
            return False
        
        # Remove from indexes
        for participant in memory.context.participants:
            self._participant_index[participant.lower()].discard(memory_id)
        
        self._type_index[memory.memory_type].discard(memory_id)
        
        if memory.context.location:
            self._location_index[memory.context.location.lower()].discard(memory_id)
        
        for tag in memory.tags:
            self._tag_index[tag.lower()].discard(memory_id)
        
        # Remove from primary storage
        del self.memories[memory_id]
        
        return True
    
    def count(self) -> int:
        """Get total memory count."""
        return len(self.memories)
    
    def clear(self) -> None:
        """Clear all memories and indexes."""
        self.memories.clear()
        self._participant_index.clear()
        self._type_index.clear()
        self._location_index.clear()
        self._tag_index.clear()


def build_memory_context_for_llm(
    memories: List[Memory],
    current_situation: str = ""
) -> str:
    """
    Format memories for LLM prompt context.
    
    Creates a human-readable context section showing relevant
    memories and why they're relevant.
    
    Args:
        memories: Memories to format
        current_situation: Current situation description
        
    Returns:
        str: Formatted memory context for LLM
    """
    if not memories:
        return "RELEVANT MEMORIES: None"
    
    parts = ["RELEVANT MEMORIES (influencing your thinking):"]
    
    for i, memory in enumerate(memories, 1):
        # Memory type indicator
        type_indicator = {
            MemoryType.EPISODIC: "📝",
            MemoryType.SEMANTIC: "📚",
            MemoryType.EMOTIONAL: "❤️",
            MemoryType.SOCIAL: "👥",
            MemoryType.PROCEDURAL: "🔧",
        }.get(memory.memory_type, "💭")
        
        # Memory line
        parts.append(f"\n{i}. {type_indicator} [{memory.memory_type.value}] {memory.summary}")
        
        # Relevance info
        if memory.tags:
            parts.append(f"   Tags: {', '.join(memory.tags[:5])}")
        
        if memory.context.participants:
            parts.append(f"   Involves: {', '.join(memory.context.participants)}")
        
        # Emotional weight if significant
        if memory.importance.emotional_weight > 0.5:
            valence = "positive" if memory.importance.emotional_valence > 0 else "negative"
            parts.append(f"   (This memory has strong {valence} emotional weight)")
    
    return "\n".join(parts)
