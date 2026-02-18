"""
Belief Dynamics System
======================

Manages agent beliefs with:
- Belief tracking with confidence levels
- Evidence-based belief updates
- Contradiction detection and resolution
- Integration with memory and identity

This is the foundation for agent reasoning and decision-making.
"""

import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger("BeliefSystem")


class BeliefType(Enum):
    """Types of beliefs an agent can hold."""
    FACTUAL = "factual"        # Beliefs about facts (can be verified)
    OPINION = "opinion"        # Personal opinions (subjective)
    VALUE = "value"            # Core values (from identity)
    PREDICTION = "prediction"  # Beliefs about future events
    SOCIAL = "social"          # Beliefs about other agents


# Saturation constants
MAX_CONFIDENCE = 0.95  # Beliefs can never reach 100%
MIN_CONFIDENCE = 0.05  # Beliefs can never reach 0%
ENTRENCHED_THRESHOLD = 0.85  # Above this, beliefs become resistant
SATURATION_DECAY = 0.002  # Decay per tick for saturated beliefs


class EvidenceStrength(Enum):
    """Strength levels for evidence."""
    STRONG = 0.9
    MODERATE = 0.6
    WEAK = 0.3
    SPECULATIVE = 0.1


@dataclass
class Evidence:
    """
    A piece of evidence that affects a belief.
    
    Evidence can support or contradict a belief.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""                    # What the evidence says
    supports_belief: bool = True         # True = supports, False = contradicts
    strength: float = 0.5                # How strong is this evidence (0.0-1.0)
    source: str = ""                     # Where evidence came from
    source_reliability: float = 0.5      # How reliable is the source (0.0-1.0)
    tick: int = 0                        # When evidence was added
    emotional_weight: float = 0.0        # Emotional impact (-1.0 to 1.0)
    
    def __post_init__(self):
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(f"Evidence strength must be 0.0-1.0, got {self.strength}")
        if not 0.0 <= self.source_reliability <= 1.0:
            raise ValueError(f"Source reliability must be 0.0-1.0, got {self.source_reliability}")
        if not -1.0 <= self.emotional_weight <= 1.0:
            raise ValueError(f"Emotional weight must be -1.0 to 1.0, got {self.emotional_weight}")
    
    @property
    def effective_strength(self) -> float:
        """Calculate effective strength considering source reliability."""
        return self.strength * self.source_reliability
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "supports_belief": self.supports_belief,
            "strength": self.strength,
            "source": self.source,
            "source_reliability": self.source_reliability,
            "tick": self.tick,
            "emotional_weight": self.emotional_weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Evidence':
        return cls(**data)


@dataclass
class Belief:
    """
    A belief held by an agent.
    
    Beliefs have confidence levels that can be updated by evidence.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    statement: str = ""                   # What the agent believes
    belief_type: BeliefType = BeliefType.OPINION
    
    # Confidence tracking
    confidence: float = 0.5               # Current confidence (0.0-1.0)
    initial_confidence: float = 0.5       # Confidence when first formed
    confidence_history: List[Tuple[int, float]] = field(default_factory=list)
    
    # Evidence
    supporting_evidence: List[str] = field(default_factory=list)   # Evidence IDs
    contradicting_evidence: List[str] = field(default_factory=list)  # Evidence IDs
    
    # Metadata
    source: str = ""                      # Where belief originated
    formed_tick: int = 0                  # When belief was formed
    last_updated: int = 0                 # Last update tick
    update_count: int = 0                 # How many times updated
    
    # Mutability
    mutable: bool = True                  # Can this belief change?
    is_core_value: bool = False           # Is this a core value from identity?
    
    # Tags for retrieval
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if not 0.0 <= self.initial_confidence <= 1.0:
            raise ValueError(f"Initial confidence must be 0.0-1.0, got {self.initial_confidence}")
    
    @property
    def is_certain(self) -> bool:
        """Check if belief is held with high certainty."""
        return self.confidence >= 0.8
    
    @property
    def is_doubtful(self) -> bool:
        """Check if belief is held with doubt."""
        return self.confidence <= 0.3
    
    @property
    def evidence_count(self) -> int:
        """Total evidence count."""
        return len(self.supporting_evidence) + len(self.contradicting_evidence)
    
    def record_confidence(self, tick: int):
        """Record current confidence in history."""
        self.confidence_history.append((tick, self.confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "belief_type": self.belief_type.value,
            "confidence": self.confidence,
            "initial_confidence": self.initial_confidence,
            "confidence_history": self.confidence_history,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "source": self.source,
            "formed_tick": self.formed_tick,
            "last_updated": self.last_updated,
            "update_count": self.update_count,
            "mutable": self.mutable,
            "is_core_value": self.is_core_value,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Belief':
        data = data.copy()
        data["belief_type"] = BeliefType(data["belief_type"])
        return cls(**data)


@dataclass
class BeliefUpdate:
    """Records a belief update event."""
    belief_id: str
    old_confidence: float
    new_confidence: float
    evidence_id: str
    reason: str
    tick: int
    
    @property
    def change(self) -> float:
        """Magnitude of confidence change."""
        return abs(self.new_confidence - self.old_confidence)
    
    @property
    def direction(self) -> str:
        """Direction of change."""
        if self.new_confidence > self.old_confidence:
            return "increased"
        elif self.new_confidence < self.old_confidence:
            return "decreased"
        return "unchanged"


class BeliefSystem:
    """
    Manages beliefs for an agent.
    
    Key capabilities:
    - Add and track beliefs
    - Update beliefs based on evidence
    - Detect contradictions
    - Integrate with memory and identity
    
    Usage:
        bs = BeliefSystem(agent_id="juror_08")
        bs.add_belief("The defendant is guilty", confidence=0.7)
        bs.add_evidence(belief_id, evidence)
        bs.update_belief(belief_id)
    """
    
    def __init__(
        self,
        agent_id: str,
        confirmation_bias: float = 1.0,
        openness: float = 0.5
    ):
        """
        Initialize belief system.
        
        Args:
            agent_id: ID of the agent this system belongs to
            confirmation_bias: How much to favor evidence supporting existing beliefs (1.0 = no bias)
            openness: How easily the agent changes beliefs (0.0-1.0)
        """
        self.agent_id = agent_id
        self.confirmation_bias = max(0.5, min(2.0, confirmation_bias))
        self.openness = max(0.0, min(1.0, openness))
        
        # Storage
        self.beliefs: Dict[str, Belief] = {}
        self.evidence_store: Dict[str, Evidence] = {}
        
        # Indexing
        self._belief_by_statement: Dict[str, str] = {}  # statement -> belief_id
        self._belief_by_tag: Dict[str, Set[str]] = {}   # tag -> set of belief_ids
        
        # History
        self.update_history: List[BeliefUpdate] = []
        
        logger.info(f"BeliefSystem initialized for {agent_id}")
    
    # ========================
    # Belief Management
    # ========================
    
    def add_belief(
        self,
        statement: str,
        confidence: float = 0.5,
        belief_type: BeliefType = BeliefType.OPINION,
        source: str = "internal",
        tick: int = 0,
        tags: List[str] = None,
        mutable: bool = True,
        is_core_value: bool = False
    ) -> str:
        """
        Add a new belief to the system.
        
        Args:
            statement: What the agent believes
            confidence: Initial confidence (0.0-1.0)
            belief_type: Type of belief
            source: Where this belief came from
            tick: When belief was formed
            tags: Tags for retrieval
            mutable: Can this belief change?
            is_core_value: Is this from agent's identity?
        
        Returns:
            Belief ID
        """
        # Check if similar belief already exists
        existing_id = self.find_belief(statement)
        if existing_id:
            logger.debug(f"Similar belief already exists: {existing_id}")
            return existing_id
        
        belief = Belief(
            statement=statement,
            belief_type=belief_type,
            confidence=confidence,
            initial_confidence=confidence,
            source=source,
            formed_tick=tick,
            last_updated=tick,
            tags=tags or [],
            mutable=mutable,
            is_core_value=is_core_value
        )
        
        self.beliefs[belief.id] = belief
        self._belief_by_statement[statement.lower()] = belief.id
        
        # Index by tags
        for tag in (tags or []):
            if tag not in self._belief_by_tag:
                self._belief_by_tag[tag] = set()
            self._belief_by_tag[tag].add(belief.id)
        
        logger.debug(f"Added belief '{statement[:50]}...' with confidence {confidence:.2f}")
        return belief.id
    
    def get_belief(self, belief_id: str) -> Optional[Belief]:
        """Get a belief by ID."""
        return self.beliefs.get(belief_id)
    
    def find_belief(self, statement: str) -> Optional[str]:
        """Find a belief by statement (case-insensitive)."""
        return self._belief_by_statement.get(statement.lower())
    
    def get_beliefs_by_tag(self, tag: str) -> List[Belief]:
        """Get all beliefs with a specific tag."""
        belief_ids = self._belief_by_tag.get(tag, set())
        return [self.beliefs[bid] for bid in belief_ids if bid in self.beliefs]
    
    def get_beliefs_by_type(self, belief_type: BeliefType) -> List[Belief]:
        """Get all beliefs of a specific type."""
        return [b for b in self.beliefs.values() if b.belief_type == belief_type]
    
    def get_certain_beliefs(self, threshold: float = 0.8) -> List[Belief]:
        """Get beliefs held with high certainty."""
        return [b for b in self.beliefs.values() if b.confidence >= threshold]
    
    def get_doubtful_beliefs(self, threshold: float = 0.3) -> List[Belief]:
        """Get beliefs held with doubt."""
        return [b for b in self.beliefs.values() if b.confidence <= threshold]
    
    # ========================
    # Evidence Management
    # ========================
    
    def add_evidence(
        self,
        belief_id: str,
        content: str,
        supports_belief: bool,
        strength: float = 0.5,
        source: str = "unknown",
        source_reliability: float = 0.5,
        tick: int = 0,
        emotional_weight: float = 0.0
    ) -> Optional[str]:
        """
        Add evidence to a belief.
        
        Args:
            belief_id: ID of the belief this evidence relates to
            content: What the evidence says
            supports_belief: Does this support or contradict the belief?
            strength: How strong is this evidence (0.0-1.0)
            source: Source of the evidence
            source_reliability: How reliable is the source (0.0-1.0)
            tick: When evidence was added
            emotional_weight: Emotional impact (-1.0 to 1.0)
        
        Returns:
            Evidence ID, or None if belief not found
        """
        belief = self.beliefs.get(belief_id)
        if not belief:
            logger.warning(f"Cannot add evidence to non-existent belief: {belief_id}")
            return None
        
        evidence = Evidence(
            content=content,
            supports_belief=supports_belief,
            strength=strength,
            source=source,
            source_reliability=source_reliability,
            tick=tick,
            emotional_weight=emotional_weight
        )
        
        self.evidence_store[evidence.id] = evidence
        
        if supports_belief:
            belief.supporting_evidence.append(evidence.id)
        else:
            belief.contradicting_evidence.append(evidence.id)
        
        logger.debug(f"Added {'supporting' if supports_belief else 'contradicting'} evidence to belief {belief_id}")
        return evidence.id
    
    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID."""
        return self.evidence_store.get(evidence_id)
    
    def get_belief_evidence(self, belief_id: str) -> Tuple[List[Evidence], List[Evidence]]:
        """Get all evidence for a belief (supporting, contradicting)."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            return [], []
        
        supporting = [self.evidence_store[eid] for eid in belief.supporting_evidence if eid in self.evidence_store]
        contradicting = [self.evidence_store[eid] for eid in belief.contradicting_evidence if eid in self.evidence_store]
        
        return supporting, contradicting
    
    # ========================
    # Belief Updates
    # ========================
    
    def update_belief(
        self,
        belief_id: str,
        tick: int = 0,
        min_change: float = 0.01
    ) -> Optional[BeliefUpdate]:
        """
        Recalculate belief confidence based on all evidence.
        
        Uses a Bayesian-like update where:
        - Supporting evidence increases confidence
        - Contradicting evidence decreases confidence
        - Confirmation bias modulates the impact
        - Openness affects overall change magnitude
        
        Args:
            belief_id: ID of belief to update
            tick: Current tick
            min_change: Minimum change to record as update
        
        Returns:
            BeliefUpdate record, or None if no change
        """
        belief = self.beliefs.get(belief_id)
        if not belief:
            return None
        
        if not belief.mutable:
            logger.debug(f"Cannot update immutable belief: {belief_id}")
            return None
        
        old_confidence = belief.confidence
        
        # Calculate evidence scores
        supporting, contradicting = self.get_belief_evidence(belief_id)
        
        support_score = sum(e.effective_strength for e in supporting)
        contradict_score = sum(e.effective_strength for e in contradicting)
        
        # SATURATION RESISTANCE: Higher confidence = harder to change
        if old_confidence > ENTRENCHED_THRESHOLD:
            # Entrenched belief - much more resistant to change
            resistance = 1.0 - ((1.0 - old_confidence) / (1.0 - ENTRENCHED_THRESHOLD))
            # resistance goes from 0 at ENTRENCHED_THRESHOLD to ~0.67 at 0.95
            change_dampener = 1.0 - (resistance * 0.8)  # Up to 80% reduction
        else:
            change_dampener = 1.0
        
        # Apply confirmation bias
        if old_confidence > 0.5:  # Already leaning towards belief
            # Supporting evidence is amplified
            support_score *= self.confirmation_bias
            # Contradicting evidence is dampened
            contradict_score /= self.confirmation_bias
        else:  # Leaning against or neutral
            # Contradicting evidence is amplified (inverse confirmation bias)
            contradict_score *= self.confirmation_bias
            support_score /= self.confirmation_bias
        
        # Calculate new confidence
        total_evidence = support_score + contradict_score
        if total_evidence == 0:
            # No evidence, maintain current confidence
            return None
        
        # Bayesian-like update
        evidence_ratio = support_score / total_evidence
        
        # Weight the evidence by openness
        # High openness = evidence affects belief more
        # Low openness = belief stays closer to initial
        evidence_weight = self.openness * 0.5  # Max 50% influence from evidence
        
        # Apply saturation resistance
        evidence_weight *= change_dampener
        
        # Blend initial confidence with evidence ratio
        new_confidence = (
            (1 - evidence_weight) * belief.initial_confidence +
            evidence_weight * evidence_ratio
        )
        
        # Apply change gradually (belief inertia)
        max_change = 0.3 * self.openness * change_dampener  # Reduced max change for entrenched
        change = new_confidence - old_confidence
        if abs(change) > max_change:
            new_confidence = old_confidence + (max_change if change > 0 else -max_change)
        
        # SATURATION CAP: Prevent beliefs from reaching 100%
        new_confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, new_confidence))
        
        # Check if change is significant
        if abs(new_confidence - old_confidence) < min_change:
            return None
        
        # Record update
        belief.confidence = new_confidence
        belief.last_updated = tick
        belief.update_count += 1
        belief.record_confidence(tick)
        
        update = BeliefUpdate(
            belief_id=belief_id,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            evidence_id="",  # Aggregate update
            reason=f"Evidence recalculation: {len(supporting)} supporting, {len(contradicting)} contradicting",
            tick=tick
        )
        
        self.update_history.append(update)
        logger.info(f"Belief '{belief.statement[:30]}...' updated: {old_confidence:.2f} -> {new_confidence:.2f}")
        
        return update
    
    def evaluate_evidence(
        self,
        belief_id: str,
        evidence_id: str,
        tick: int = 0,
        influence_weight: float = 0.5
    ) -> Optional[BeliefUpdate]:
        """
        Evaluate a single piece of evidence and update belief.
        
        More targeted update than update_belief().
        
        Args:
            belief_id: ID of belief to update
            evidence_id: ID of evidence to evaluate
            tick: Current tick
            influence_weight: How much the evidence source influences this agent (0-1)
                             0.5 = neutral/average, 1.0 = strong influence
        """
        belief = self.beliefs.get(belief_id)
        evidence = self.evidence_store.get(evidence_id)
        
        if not belief or not evidence:
            return None
        
        if not belief.mutable:
            return None
        
        old_confidence = belief.confidence
        
        # SATURATION RESISTANCE
        if old_confidence > ENTRENCHED_THRESHOLD:
            resistance = 1.0 - ((1.0 - old_confidence) / (1.0 - ENTRENCHED_THRESHOLD))
            saturation_factor = 1.0 - (resistance * 0.8)
        else:
            saturation_factor = 1.0
        
        # Calculate impact
        impact = evidence.effective_strength * saturation_factor
        
        # Apply confirmation bias
        if (evidence.supports_belief and old_confidence > 0.5) or \
           (not evidence.supports_belief and old_confidence < 0.5):
            # Evidence aligns with current stance - amplify
            impact *= self.confirmation_bias
        else:
            # Evidence contradicts current stance - dampen
            impact /= self.confirmation_bias
        
        # Apply openness
        impact *= self.openness
        
        # NEW: Apply asymmetric influence weight
        # Scale from 0.5 (neutral) to full range
        # influence_weight 0.0 = no influence, 1.0 = full influence
        # Map to 0.0-1.5 range for impact scaling
        influence_multiplier = influence_weight * 1.5  # 0 to 1.5
        impact *= influence_multiplier
        
        # Calculate direction
        if evidence.supports_belief:
            # Move towards MAX_CONFIDENCE, not 1.0
            target = MAX_CONFIDENCE
            new_confidence = old_confidence + (impact * (target - old_confidence))
        else:
            # Move towards MIN_CONFIDENCE, not 0.0
            target = MIN_CONFIDENCE
            new_confidence = old_confidence - (impact * (old_confidence - target))
        
        # Apply saturation cap
        new_confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, new_confidence))
        
        if abs(new_confidence - old_confidence) < 0.01:
            return None
        
        # Record update
        belief.confidence = new_confidence
        belief.last_updated = tick
        belief.update_count += 1
        belief.record_confidence(tick)
        
        update = BeliefUpdate(
            belief_id=belief_id,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            evidence_id=evidence_id,
            reason=f"Evidence: '{evidence.content[:50]}...'",
            tick=tick
        )
        
        self.update_history.append(update)
        logger.debug(f"Belief updated by evidence: {old_confidence:.2f} -> {new_confidence:.2f}")
        
        return update
    
    # ========================
    # Contradiction Detection
    # ========================
    
    def find_contradictions(self) -> List[Tuple[Belief, Belief]]:
        """
        Find pairs of contradictory beliefs.
        
        Returns:
            List of (belief1, belief2) pairs that contradict each other
        """
        contradictions = []
        beliefs_list = list(self.beliefs.values())
        
        for i, b1 in enumerate(beliefs_list):
            for b2 in beliefs_list[i+1:]:
                if self._are_contradictory(b1, b2):
                    contradictions.append((b1, b2))
        
        return contradictions
    
    def _are_contradictory(self, b1: Belief, b2: Belief) -> bool:
        """Check if two beliefs contradict each other."""
        # Same type, high confidence, opposite positions
        if b1.belief_type != b2.belief_type:
            return False
        
        if not (b1.is_certain and b2.is_certain):
            return False
        
        # Simple keyword contradiction check
        negation_words = {"not", "never", "no", "isn't", "doesn't", "won't", "can't"}
        
        s1_words = set(b1.statement.lower().split())
        s2_words = set(b2.statement.lower().split())
        
        # Check if one has negation and other doesn't
        s1_negations = s1_words & negation_words
        s2_negations = s2_words & negation_words
        
        if bool(s1_negations) != bool(s2_negations):
            # One has negation, check if content is similar
            s1_content = s1_words - negation_words
            s2_content = s2_words - negation_words
            overlap = len(s1_content & s2_content)
            if overlap >= 2:  # At least 2 words overlap
                return True
        
        return False
    
    def resolve_contradiction(
        self,
        b1: Belief,
        b2: Belief,
        tick: int = 0
    ) -> Optional[str]:
        """
        Attempt to resolve a contradiction between two beliefs.
        
        Strategy:
        1. Keep belief with more evidence
        2. Reduce confidence in the other
        3. If equal, reduce both slightly
        
        Returns:
            ID of the belief that was weakened, or None
        """
        if b1.evidence_count > b2.evidence_count:
            # Weaken b2
            b2.confidence *= 0.7
            b2.last_updated = tick
            logger.info(f"Resolved contradiction: weakened '{b2.statement[:30]}...'")
            return b2.id
        elif b2.evidence_count > b1.evidence_count:
            # Weaken b1
            b1.confidence *= 0.7
            b1.last_updated = tick
            logger.info(f"Resolved contradiction: weakened '{b1.statement[:30]}...'")
            return b1.id
        else:
            # Equal evidence - weaken both
            b1.confidence *= 0.85
            b2.confidence *= 0.85
            b1.last_updated = tick
            b2.last_updated = tick
            logger.info("Resolved contradiction: weakened both equally")
            return None
    
    # ========================
    # Utility Methods
    # ========================
    
    def format_beliefs(self, topics: Optional[List[str]] = None) -> str:
        """
        Format beliefs for LLM prompt context.
        
        Args:
            topics: Specific topics (tags) to include. If None, includes all.
        """
        if topics:
            beliefs = []
            for tag in topics:
                beliefs.extend(self.get_beliefs_by_tag(tag))
            beliefs = list({b.id: b for b in beliefs}.values())  # Dedupe
        else:
            beliefs = list(self.beliefs.values())
        
        if not beliefs:
            return "CURRENT BELIEFS: No strong beliefs held."
        
        # Sort by confidence
        beliefs.sort(key=lambda b: b.confidence, reverse=True)
        
        parts = ["CURRENT BELIEFS:"]
        for b in beliefs[:10]:  # Top 10 most confident
            confidence_label = "CERTAIN" if b.is_certain else "DOUBTFUL" if b.is_doubtful else "UNCERTAIN"
            parts.append(f"  - {b.statement}: {confidence_label} ({b.confidence:.0%})")
            if b.evidence_count > 0:
                parts.append(f"    Evidence: {len(b.supporting_evidence)} supporting, {len(b.contradicting_evidence)} contradicting")
        
        return "\n".join(parts)
    
    def get_belief_summary(self, belief_id: str) -> str:
        """Get a detailed summary of a single belief."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            return f"Belief not found: {belief_id}"
        
        supporting, contradicting = self.get_belief_evidence(belief_id)
        
        lines = [
            f"BELIEF: {belief.statement}",
            f"Type: {belief.belief_type.value.upper()}",
            f"Confidence: {belief.confidence:.0%} (initially {belief.initial_confidence:.0%})",
            f"Formed: tick {belief.formed_tick}, Updated: {belief.update_count} times",
            f"Mutable: {belief.mutable}, Core Value: {belief.is_core_value}",
            "",
            f"SUPPORTING EVIDENCE ({len(supporting)}):"
        ]
        
        for e in supporting[:5]:
            lines.append(f"  - {e.content[:60]}... (strength: {e.strength:.0%})")
        
        lines.append(f"\nCONTRADICTING EVIDENCE ({len(contradicting)}):")
        for e in contradicting[:5]:
            lines.append(f"  - {e.content[:60]}... (strength: {e.strength:.0%})")
        
        return "\n".join(lines)
    
    def retrieve_relevant(
        self,
        query: str,
        limit: int = 5,
        min_confidence: float = 0.3
    ) -> List[Belief]:
        """
        Retrieve beliefs relevant to a query.
        
        This enables agents to recall relevant beliefs when making decisions.
        Uses keyword matching for retrieval.
        
        Args:
            query: Search query (statement or topic)
            limit: Maximum number of beliefs to return
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of relevant beliefs, sorted by relevance
        """
        if not self.beliefs:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        candidates = []
        
        for belief in self.beliefs.values():
            # Filter by confidence
            if belief.confidence < min_confidence:
                continue
            
            # Calculate relevance score
            score = 0.0
            
            # Direct statement match
            if query_lower in belief.statement.lower():
                score += 0.5
            
            # Keyword match
            if belief.tags:
                belief_words = set(t.lower() for t in belief.tags)
                keyword_overlap = query_words & belief_words
                if keyword_overlap:
                    score += 0.3 * (len(keyword_overlap) / len(belief_words))
            
            # Confidence weight (higher confidence = more relevant)
            score += 0.2 * belief.confidence
            
            if score > 0:
                candidates.append((score, belief))
        
        # Sort by score descending
        candidates.sort(key=lambda x: -x[0])
        
        return [belief for _, belief in candidates[:limit]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize belief system to dict."""
        return {
            "agent_id": self.agent_id,
            "confirmation_bias": self.confirmation_bias,
            "openness": self.openness,
            "beliefs": {bid: b.to_dict() for bid, b in self.beliefs.items()},
            "evidence_store": {eid: e.to_dict() for eid, e in self.evidence_store.items()},
            "update_history": [
                {
                    "belief_id": u.belief_id,
                    "old_confidence": u.old_confidence,
                    "new_confidence": u.new_confidence,
                    "evidence_id": u.evidence_id,
                    "reason": u.reason,
                    "tick": u.tick
                }
                for u in self.update_history
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BeliefSystem':
        """Deserialize belief system from dict."""
        bs = cls(
            agent_id=data["agent_id"],
            confirmation_bias=data.get("confirmation_bias", 1.0),
            openness=data.get("openness", 0.5)
        )
        
        # Restore beliefs
        for bid, bdata in data.get("beliefs", {}).items():
            bs.beliefs[bid] = Belief.from_dict(bdata)
            bs._belief_by_statement[bdata["statement"].lower()] = bid
            for tag in bdata.get("tags", []):
                if tag not in bs._belief_by_tag:
                    bs._belief_by_tag[tag] = set()
                bs._belief_by_tag[tag].add(bid)
        
        # Restore evidence
        for eid, edata in data.get("evidence_store", {}).items():
            bs.evidence_store[eid] = Evidence.from_dict(edata)
        
        # Restore history
        for udata in data.get("update_history", []):
            bs.update_history.append(BeliefUpdate(**udata))
        
        return bs
    
    def apply_saturation_decay(self, tick: int = 0) -> List[str]:
        """
        Apply decay to saturated beliefs (above ENTRENCHED_THRESHOLD).
        
        This prevents beliefs from staying at maximum confidence indefinitely.
        Beliefs near the cap slowly drift towards the threshold.
        
        Returns:
            List of belief IDs that were decayed
        """
        decayed = []
        
        for belief in self.beliefs.values():
            if belief.confidence > ENTRENCHED_THRESHOLD and belief.mutable:
                # Decay towards threshold
                decay_amount = SATURATION_DECAY * (belief.confidence - ENTRENCHED_THRESHOLD)
                belief.confidence -= decay_amount
                belief.last_updated = tick
                decayed.append(belief.id)
                logger.debug(f"Decayed belief {belief.id[:8]}: {belief.confidence:.3f}")
        
        return decayed
    
    def is_belief_saturated(self, belief_id: str) -> bool:
        """Check if a belief is at or near saturation."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            return False
        return belief.confidence >= ENTRENCHED_THRESHOLD
    
    def get_saturation_level(self, belief_id: str) -> float:
        """Get how saturated a belief is (0.0 = not saturated, 1.0 = max saturated)."""
        belief = self.beliefs.get(belief_id)
        if not belief:
            return 0.0
        if belief.confidence <= ENTRENCHED_THRESHOLD:
            return 0.0
        return (belief.confidence - ENTRENCHED_THRESHOLD) / (MAX_CONFIDENCE - ENTRENCHED_THRESHOLD)
    
    def prune(self, max_beliefs: int = 100, max_evidence_per_belief: int = 20):
        """
        Remove low-importance beliefs and evidence to prevent bloat.
        
        Args:
            max_beliefs: Maximum number of beliefs to keep
            max_evidence_per_belief: Max evidence per belief
        """
        # Sort beliefs by importance (confidence * evidence_count)
        sorted_beliefs = sorted(
            self.beliefs.values(),
            key=lambda b: b.confidence * (1 + b.evidence_count * 0.1),
            reverse=True
        )
        
        # Keep only top beliefs
        kept_ids = {b.id for b in sorted_beliefs[:max_beliefs]}
        
        for bid in list(self.beliefs.keys()):
            if bid not in kept_ids:
                belief = self.beliefs[bid]
                # Clean up indexes
                self._belief_by_statement.pop(belief.statement.lower(), None)
                for tag in belief.tags:
                    self._belief_by_tag.get(tag, set()).discard(bid)
                # Remove belief
                del self.beliefs[bid]
        
        # Prune evidence per belief
        for belief in self.beliefs.values():
            if len(belief.supporting_evidence) > max_evidence_per_belief:
                # Keep strongest evidence
                supporting = sorted(
                    [self.evidence_store.get(eid) for eid in belief.supporting_evidence if eid in self.evidence_store],
                    key=lambda e: e.effective_strength if e else 0,
                    reverse=True
                )
                belief.supporting_evidence = [e.id for e in supporting[:max_evidence_per_belief] if e]
            
            if len(belief.contradicting_evidence) > max_evidence_per_belief:
                contradicting = sorted(
                    [self.evidence_store.get(eid) for eid in belief.contradicting_evidence if eid in self.evidence_store],
                    key=lambda e: e.effective_strength if e else 0,
                    reverse=True
                )
                belief.contradicting_evidence = [e.id for e in contradicting[:max_evidence_per_belief] if e]
        
        # Clean up orphaned evidence
        used_evidence_ids = set()
        for belief in self.beliefs.values():
            used_evidence_ids.update(belief.supporting_evidence)
            used_evidence_ids.update(belief.contradicting_evidence)
        
        for eid in list(self.evidence_store.keys()):
            if eid not in used_evidence_ids:
                del self.evidence_store[eid]
        
        logger.debug(f"Pruned belief system: {len(self.beliefs)} beliefs, {len(self.evidence_store)} evidence")
    
    def apply_memory_decay(
        self, 
        tick: int = 0,
        decay_rate: float = 0.0005,
        min_confidence: float = 0.3
    ) -> List[str]:
        """
        Apply general memory decay to all mutable beliefs.
        
        Beliefs that aren't reinforced gradually decay towards a minimum.
        This simulates how memories fade without reinforcement.
        
        Args:
            tick: Current tick for timestamp
            decay_rate: How much confidence decays per call
            min_confidence: Floor for decay (beliefs won't go below this)
        
        Returns:
            List of belief IDs that were decayed
        """
        decayed = []
        
        for belief in self.beliefs.values():
            if not belief.mutable:
                continue
            
            # Skip recently updated beliefs (within last 100 ticks)
            if tick - belief.last_updated < 100:
                continue
            
            # Apply decay
            if belief.confidence > min_confidence:
                old_conf = belief.confidence
                belief.confidence = max(min_confidence, belief.confidence - decay_rate)
                
                if belief.confidence < old_conf:
                    decayed.append(belief.id)
                    logger.debug(
                        f"Memory decay on {belief.id[:8]}: "
                        f"{old_conf:.3f} -> {belief.confidence:.3f}"
                    )
        
        return decayed
    
    def apply_social_pressure(
        self,
        my_stance: str,
        vote_distribution: Dict[str, int],
        tick: int = 0,
        pressure_strength: float = 0.02
    ) -> List[str]:
        """
        Apply social pressure to beliefs when agent is in minority.
        
        Being in the minority should increase doubt in held beliefs.
        
        Args:
            my_stance: Agent's current stance ("guilty" or "not_guilty")
            vote_distribution: Dict like {"guilty": 3, "not_guilty": 2}
            tick: Current tick
            pressure_strength: Base pressure per tick
        
        Returns:
            List of belief IDs affected
        """
        affected = []
        
        my_count = vote_distribution.get(my_stance, 0)
        total = sum(vote_distribution.values())
        
        if total == 0:
            return affected
        
        minority_ratio = my_count / total
        
        # Only apply pressure if in significant minority (< 40%)
        if minority_ratio >= 0.4:
            return affected
        
        # Calculate pressure (stronger minority = more pressure)
        pressure = pressure_strength * (0.4 - minority_ratio)
        
        for belief in self.beliefs.values():
            if not belief.mutable:
                continue
            
            # Only affect beliefs related to the case
            if "verdict" in belief.tags or "case" in belief.tags:
                old_conf = belief.confidence
                belief.confidence = max(0.2, belief.confidence - pressure)
                belief.last_updated = tick
                
                if belief.confidence < old_conf:
                    affected.append(belief.id)
                    logger.debug(
                        f"Social pressure on {belief.id[:8]}: "
                        f"{old_conf:.3f} -> {belief.confidence:.3f} "
                        f"(minority ratio: {minority_ratio:.1%})"
                    )
        
        return affected
    
    def calculate_influence_weight(
        self,
        speaker_personality: Dict[str, float],
        speaker_credibility: float = 0.5,
        relationship_trust: float = 0.5,
        argument_strength: float = 0.5
    ) -> float:
        """
        Calculate how much influence a speaker has on this agent.
        
        This creates ASYMMETRIC influence - A→B ≠ B→A
        
        Args:
            speaker_personality: Speaker's Big Five traits
            speaker_credibility: Speaker's credibility/track record (0-1)
            relationship_trust: Trust between speaker and listener (0-1)
            argument_strength: Strength of the argument (0-1)
        
        Returns:
            Influence weight (0-1), where 0.5 is neutral
        """
        # Import here to avoid circular imports
        from .influence import InfluenceWeightCalculator
        
        # Build listener personality from belief system attributes
        listener_personality = {
            "openness": self.openness,
            "conscientiousness": getattr(self, 'conscientiousness', 0.5),
            "agreeableness": getattr(self, 'agreeableness', 0.5),
            "neuroticism": getattr(self, 'neuroticism', 0.5),
            "extraversion": getattr(self, 'extraversion', 0.5)
        }
        
        calc = InfluenceWeightCalculator()
        weight, _ = calc.calculate(
            speaker_personality=speaker_personality,
            listener_personality=listener_personality,
            speaker_credibility=speaker_credibility,
            relationship_trust=relationship_trust,
            argument_strength=argument_strength
        )
        
        return weight


# ========================
# Integration Helpers
# ========================

def create_belief_from_core_value(
    value: str,
    source: str,
    intensity: float
) -> Belief:
    """
    Create a belief from an agent's core value.
    
    Core values become immutable, high-confidence beliefs.
    """
    return Belief(
        statement=value,
        belief_type=BeliefType.VALUE,
        confidence=min(1.0, intensity + 0.3),  # Boost confidence for core values
        source=f"Core value: {source}",
        mutable=False,
        is_core_value=True,
        tags=["core_value"]
    )


def belief_strength_category(confidence: float) -> str:
    """Categorize belief strength for display."""
    if confidence >= 0.9:
        return "ABSOLUTE"
    elif confidence >= 0.7:
        return "STRONG"
    elif confidence >= 0.5:
        return "MODERATE"
    elif confidence >= 0.3:
        return "WEAK"
    else:
        return "DOUBTFUL"
