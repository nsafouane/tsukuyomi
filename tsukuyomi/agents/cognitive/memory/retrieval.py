"""
Memory Retrieval System

Context-aware memory retrieval for the Deep Memory Architecture.
"""

import logging
import math
import re
from typing import List, Dict, Optional, Callable

from .memory_types import Memory
from .decay_calculator import MemoryDecayCalculator, DecayConfig
from .retrieval_types import (
    RetrievalMode,
    RetrievalContext,
    RetrievalWeights,
    ScoredMemory,
)
from .memory_store import MemoryStore, build_memory_context_for_llm


logger = logging.getLogger("MemoryRetrieval")


class MemoryRetrieval:
    """Context-aware memory retrieval system."""
    
    def __init__(
        self,
        decay_calculator: Optional[MemoryDecayCalculator] = None,
        weights: Optional[RetrievalWeights] = None,
        embedding_func: Optional[Callable[[str], List[float]]] = None
    ):
        self.decay_calculator = decay_calculator or MemoryDecayCalculator()
        self.weights = weights or RetrievalWeights()
        self.embedding_func = embedding_func
        self._embedding_cache: Dict[str, List[float]] = {}
    
    def retrieve(
        self,
        memories: List[Memory],
        context: RetrievalContext
    ) -> List[Memory]:
        """Retrieve the most relevant memories for the given context."""
        if not memories:
            return []
        
        candidates = self._filter_candidates(memories, context)
        
        if not candidates:
            return []
        
        scored = self._score_candidates(candidates, context)
        scored.sort(key=lambda x: x.total_score, reverse=True)
        top_memories = [s.memory for s in scored[:context.limit]]
        
        for memory in top_memories:
            memory.record_access(context.current_tick)
        
        return top_memories
    
    def retrieve_with_scores(
        self,
        memories: List[Memory],
        context: RetrievalContext
    ) -> List[ScoredMemory]:
        """Retrieve memories with detailed score breakdown."""
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
        """Filter memories by minimum criteria."""
        candidates = []
        
        for memory in memories:
            if self.decay_calculator.should_prune(memory, context.current_tick):
                continue
            
            effective_importance = self.decay_calculator.effective_importance(
                memory, context.current_tick
            )
            if effective_importance < context.min_importance:
                continue
            
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
        """Score each memory candidate using weighted factors."""
        scored = []
        
        for memory in memories:
            semantic_score = self._semantic_similarity(memory, context)
            participant_score = self._participant_match(memory, context)
            importance_score = self._decay_adjusted_importance(memory, context)
            emotional_score = self._emotional_similarity(memory, context)
            recency_score = self._recency_score(memory, context)
            
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
        """Calculate semantic similarity between memory and context."""
        if self.embedding_func and memory.embedding:
            try:
                if context.situation not in self._embedding_cache:
                    self._embedding_cache[context.situation] = self.embedding_func(context.situation)
                
                situation_embedding = self._embedding_cache[context.situation]
                return self._cosine_similarity(memory.embedding, situation_embedding)
            except Exception as e:
                logger.debug(f"Embedding similarity failed: {e}")
        
        if not context.keywords and context.situation:
            context.keywords = self._extract_keywords(context.situation)
        
        if not context.keywords:
            return 0.0
        
        memory_keywords = set(memory.keywords) | set(k.lower() for k in memory.tags)
        context_keywords = set(k.lower() for k in context.keywords)
        
        if not memory_keywords or not context_keywords:
            return 0.0
        
        intersection = len(memory_keywords & context_keywords)
        union = len(memory_keywords | context_keywords)
        
        return intersection / union if union > 0 else 0.0
    
    def _participant_match(self, memory: Memory, context: RetrievalContext) -> float:
        """Calculate participant match score."""
        if not context.participants or not memory.context.participants:
            return 0.0
        
        memory_participants = set(p.lower() for p in memory.context.participants)
        context_participants = set(p.lower() for p in context.participants)
        
        intersection = memory_participants & context_participants
        
        if not intersection:
            return 0.0
        
        return len(intersection) / len(context_participants)
    
    def _decay_adjusted_importance(
        self, 
        memory: Memory, 
        context: RetrievalContext
    ) -> float:
        """Calculate decay-adjusted importance score."""
        effective = self.decay_calculator.effective_importance(
            memory, context.current_tick
        )
        return min(1.0, effective)
    
    def _emotional_similarity(
        self, 
        memory: Memory, 
        context: RetrievalContext
    ) -> float:
        """Calculate emotional similarity score."""
        if not context.emotional_state:
            return memory.importance.emotional_weight
        
        context_valence = context.emotional_state.get("valence", 0.0)
        memory_valence = memory.importance.emotional_valence
        
        valence_similarity = 1.0 - abs(context_valence - memory_valence) / 2.0
        
        return valence_similarity * memory.importance.emotional_weight
    
    def _recency_score(self, memory: Memory, context: RetrievalContext) -> float:
        """Calculate recency score."""
        if context.current_tick <= 0:
            return 0.5
        
        age = context.current_tick - memory.access.creation_tick
        
        if age <= 0:
            return 1.0
        
        return math.exp(-age / 200.0)
    
    def _cosine_similarity(
        self, 
        vec1: List[float], 
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return (similarity + 1.0) / 2.0
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for keyword matching."""
        words = re.findall(r'\b\w+\b', text.lower())
        
        stop_words = {
            'the', 'a', 'an', 'is', 'was', 'at', 'on', 'in', 'to', 'for',
            'of', 'and', 'or', 'but', 'with', 'by', 'from', 'that', 'this',
            'it', 'he', 'she', 'they', 'we', 'i', 'you', 'be', 'been',
        }
        
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return list(set(keywords))
