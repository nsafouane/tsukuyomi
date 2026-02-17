"""
Decision Engine
===============

Models how agents make decisions with reasoning chains.

Key Features:
- Decision records with reasoning chains
- Decision factors (beliefs, goals, constraints)
- Multi-criteria decision analysis
- Decision history tracking
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, Set, Tuple
from datetime import datetime
import json
import random


class DecisionType(Enum):
    """Types of decisions agents make."""
    ACTION = "action"              # What to do
    JUDGMENT = "judgment"          # What to believe
    CHOICE = "choice"              # Pick option A or B
    PLAN = "plan"                  # Future action sequence
    VERDICT = "verdict"            # Final decision (e.g., guilty/not guilty)


class DecisionPriority(Enum):
    """Decision priority levels."""
    CRITICAL = "critical"    # Must decide now
    HIGH = "high"            # Important
    MEDIUM = "medium"        # Normal
    LOW = "low"              # Can wait


class DecisionOutcome(Enum):
    """How a decision turned out."""
    SUCCESS = "success"
    FAILURE = "failure"
    MIXED = "mixed"
    PENDING = "pending"
    UNKNOWN = "unknown"


@dataclass
class DecisionFactor:
    """
    A factor influencing a decision.
    """
    id: str = field(default_factory=lambda: f"df_{random.randint(100000, 999999)}")
    description: str = ""
    weight: float = 0.5              # How much this factors in (0-1)
    belief_id: Optional[str] = None   # Related belief
    source: str = ""                  # Where this factor came from
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "weight": self.weight,
            "belief_id": self.belief_id,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DecisionFactor":
        return cls(**data)


@dataclass
class ReasoningStep:
    """
    A step in the reasoning chain.
    """
    id: str = field(default_factory=lambda: f"rs_{random.randint(100000, 999999)}")
    step_number: int = 0
    premise: str = ""                # What we know/assume
    inference: str = ""              # What we infer from premise
    confidence: float = 0.5          # How confident in this step
    evidence_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "step_number": self.step_number,
            "premise": self.premise,
            "inference": self.inference,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ReasoningStep":
        return cls(**data)


@dataclass
class Decision:
    """
    A decision made by an agent.
    """
    id: str = field(default_factory=lambda: f"dec_{random.randint(100000, 999999)}")
    decision_type: DecisionType = DecisionType.ACTION
    question: str = ""               # What we're deciding
    choice: str = ""                  # The chosen option
    alternatives: List[str] = field(default_factory=list)  # Options considered
    
    # Reasoning
    reasoning_chain: List[ReasoningStep] = field(default_factory=list)
    factors: List[DecisionFactor] = field(default_factory=list)
    
    # Context
    tick: int = 0
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    priority: DecisionPriority = DecisionPriority.MEDIUM
    deadline_tick: Optional[int] = None
    
    # Outcome
    outcome: DecisionOutcome = DecisionOutcome.PENDING
    outcome_tick: Optional[int] = None
    evaluation: str = ""              # How decision was evaluated
    
    # Confidence
    confidence: float = 0.5
    
    @property
    def reasoning_text(self) -> str:
        """Get formatted reasoning chain."""
        if not self.reasoning_chain:
            return "No reasoning recorded."
        
        lines = []
        for step in self.reasoning_chain:
            lines.append(f"{step.step_number}. {step.premise}")
            if step.inference:
                lines.append(f"   → {step.inference}")
        return "\n".join(lines)
    
    @property
    def factors_summary(self) -> str:
        """Get summary of decision factors."""
        if not self.factors:
            return "No factors recorded."
        
        lines = []
        for f in sorted(self.factors, key=lambda x: x.weight, reverse=True):
            lines.append(f"- {f.description} (weight: {f.weight:.0%})")
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "decision_type": self.decision_type.value,
            "question": self.question,
            "choice": self.choice,
            "alternatives": self.alternatives,
            "reasoning_chain": [s.to_dict() for s in self.reasoning_chain],
            "factors": [f.to_dict() for f in self.factors],
            "tick": self.tick,
            "context": self.context,
            "priority": self.priority.value,
            "deadline_tick": self.deadline_tick,
            "outcome": self.outcome.value,
            "outcome_tick": self.outcome_tick,
            "evaluation": self.evaluation,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Decision":
        decision = cls(
            id=data["id"],
            decision_type=DecisionType(data["decision_type"]),
            question=data["question"],
            choice=data["choice"],
            alternatives=data.get("alternatives", []),
            tick=data["tick"],
            context=data.get("context", {}),
            priority=DecisionPriority(data.get("priority", "medium")),
            deadline_tick=data.get("deadline_tick"),
            outcome=DecisionOutcome(data.get("outcome", "pending")),
            outcome_tick=data.get("outcome_tick"),
            evaluation=data.get("evaluation", ""),
            confidence=data.get("confidence", 0.5)
        )
        decision.reasoning_chain = [
            ReasoningStep.from_dict(s) for s in data.get("reasoning_chain", [])
        ]
        decision.factors = [
            DecisionFactor.from_dict(f) for f in data.get("factors", [])
        ]
        return decision


class DecisionEngine:
    """
    Engine for making and tracking decisions.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.decisions: Dict[str, Decision] = {}
        self.pending_decisions: List[str] = []
        self.completed_decisions: List[str] = []
        
        # Decision patterns
        self.decision_patterns: Dict[str, int] = {}  # pattern -> count
        
        # Configuration
        self.max_reasoning_steps = 10
        self.max_factors = 8
    
    # ==================== DECISION CREATION ====================
    
    def create_decision(
        self,
        question: str,
        decision_type: DecisionType = DecisionType.ACTION,
        alternatives: Optional[List[str]] = None,
        priority: DecisionPriority = DecisionPriority.MEDIUM,
        deadline_tick: Optional[int] = None,
        context: Optional[Dict] = None,
        tick: int = 0
    ) -> Decision:
        """
        Create a new decision to be made.
        """
        decision = Decision(
            decision_type=decision_type,
            question=question,
            alternatives=alternatives or [],
            priority=priority,
            deadline_tick=deadline_tick,
            context=context or {},
            tick=tick
        )
        
        self.decisions[decision.id] = decision
        self.pending_decisions.append(decision.id)
        
        return decision
    
    def add_reasoning_step(
        self,
        decision_id: str,
        premise: str,
        inference: str,
        confidence: float = 0.5,
        evidence_ids: Optional[List[str]] = None,
        step_number: Optional[int] = None
    ) -> ReasoningStep:
        """
        Add a step to the reasoning chain.
        """
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        # Auto-number if not provided
        if step_number is None:
            step_number = len(decision.reasoning_chain) + 1
        
        # Check max steps
        if len(decision.reasoning_chain) >= self.max_reasoning_steps:
            raise ValueError(f"Max reasoning steps ({self.max_reasoning_steps}) reached")
        
        step = ReasoningStep(
            step_number=step_number,
            premise=premise,
            inference=inference,
            confidence=confidence,
            evidence_ids=evidence_ids or []
        )
        
        decision.reasoning_chain.append(step)
        
        # Update overall confidence
        self._update_decision_confidence(decision_id)
        
        return step
    
    def add_factor(
        self,
        decision_id: str,
        description: str,
        weight: float,
        belief_id: Optional[str] = None,
        source: str = ""
    ) -> DecisionFactor:
        """
        Add a factor influencing the decision.
        """
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        # Check max factors
        if len(decision.factors) >= self.max_factors:
            raise ValueError(f"Max factors ({self.max_factors}) reached")
        
        # Validate weight
        weight = max(0.0, min(1.0, weight))
        
        factor = DecisionFactor(
            description=description,
            weight=weight,
            belief_id=belief_id,
            source=source
        )
        
        decision.factors.append(factor)
        
        return factor
    
    # ==================== DECISION MAKING ====================
    
    def make_decision(
        self,
        decision_id: str,
        choice: str,
        confidence: float = 0.5,
        tick: int = 0
    ) -> Decision:
        """
        Record the final decision.
        """
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        decision.choice = choice
        decision.confidence = confidence
        
        # Move from pending to completed
        if decision_id in self.pending_decisions:
            self.pending_decisions.remove(decision_id)
        if decision_id not in self.completed_decisions:
            self.completed_decisions.append(decision_id)
        
        # Track pattern
        self._track_decision_pattern(choice)
        
        return decision
    
    def evaluate_decision(
        self,
        decision_id: str,
        outcome: DecisionOutcome,
        evaluation: str,
        tick: int = 0
    ):
        """
        Evaluate a decision after outcome is known.
        """
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        decision.outcome = outcome
        decision.outcome_tick = tick
        decision.evaluation = evaluation
    
    # ==================== MULTI-CRITERIA ANALYSIS ====================
    
    def score_alternatives(
        self,
        decision_id: str,
        score_functions: Dict[str, callable]
    ) -> Dict[str, float]:
        """
        Score alternatives using multiple criteria.
        
        Args:
            decision_id: The decision to score
            score_functions: Dict of {criterion_name: function(alternative) -> score}
        
        Returns:
            Dict of {alternative: total_score}
        """
        decision = self.decisions.get(decision_id)
        if not decision:
            raise ValueError(f"Decision {decision_id} not found")
        
        if not decision.factors:
            # Equal weights if no factors
            weights = {alt: 1.0 / len(decision.alternatives) for alt in decision.alternatives}
        else:
            # Use factor weights
            weights = {f.description: f.weight for f in decision.factors}
        
        scores = {}
        for alt in decision.alternatives:
            total = 0.0
            for criterion, score_fn in score_functions.items():
                criterion_weight = weights.get(criterion, 0.5)
                try:
                    score = score_fn(alt)
                    total += score * criterion_weight
                except:
                    pass
            scores[alt] = total
        
        return scores
    
    def recommend_choice(
        self,
        decision_id: str,
        score_functions: Dict[str, callable]
    ) -> Tuple[str, float]:
        """
        Recommend the best choice based on scoring.
        
        Returns:
            (recommended_choice, score)
        """
        scores = self.score_alternatives(decision_id, score_functions)
        
        if not scores:
            return "", 0.0
        
        best = max(scores.items(), key=lambda x: x[1])
        return best[0], best[1]
    
    # ==================== ANALYSIS ====================
    
    def get_pending_decisions(self) -> List[Decision]:
        """Get all pending decisions."""
        return [self.decisions[did] for did in self.pending_decisions]
    
    def get_completed_decisions(self) -> List[Decision]:
        """Get all completed decisions."""
        return [self.decisions[did] for did in self.completed_decisions]
    
    def get_decision_history(
        self,
        decision_type: Optional[DecisionType] = None,
        limit: int = 10
    ) -> List[Decision]:
        """Get decision history, optionally filtered by type."""
        decisions = self.get_completed_decisions()
        
        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]
        
        # Sort by tick descending
        decisions.sort(key=lambda d: d.tick, reverse=True)
        
        return decisions[:limit]
    
    def get_success_rate(
        self,
        decision_type: Optional[DecisionType] = None
    ) -> float:
        """Calculate decision success rate."""
        decisions = self.get_completed_decisions()
        
        if decision_type:
            decisions = [d for d in decisions if d.decision_type == decision_type]
        
        if not decisions:
            return 0.0
        
        successes = sum(
            1 for d in decisions 
            if d.outcome == DecisionOutcome.SUCCESS
        )
        
        return successes / len(decisions)
    
    def get_decision_summary(self) -> str:
        """Generate decision summary."""
        pending = self.get_pending_decisions()
        completed = self.get_completed_decisions()
        
        lines = [
            f"DECISION SUMMARY: {self.agent_id}",
            "=" * 40,
            f"Pending: {len(pending)}",
            f"Completed: {len(completed)}",
            f"Success Rate: {self.get_success_rate():.0%}",
            "",
        ]
        
        if pending:
            lines.append("PENDING DECISIONS:")
            for d in pending:
                lines.append(f"  - {d.question} [{d.priority.value}]")
        
        return "\n".join(lines)
    
    # ==================== INTERNAL ====================
    
    def _update_decision_confidence(self, decision_id: str):
        """Update decision confidence based on reasoning chain."""
        decision = self.decisions.get(decision_id)
        if not decision or not decision.reasoning_chain:
            return
        
        # Average confidence of reasoning steps
        avg_conf = sum(s.confidence for s in decision.reasoning_chain) / len(decision.reasoning_chain)
        
        # Weight by number of steps
        decision.confidence = avg_conf
    
    def _track_decision_pattern(self, choice: str):
        """Track decision patterns."""
        self.decision_patterns[choice] = self.decision_patterns.get(choice, 0) + 1
    
    def get_top_choices(self, n: int = 5) -> List[Tuple[str, int]]:
        """Get most common decisions."""
        sorted_patterns = sorted(
            self.decision_patterns.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_patterns[:n]
    
    # ==================== SERIALIZATION ====================
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "decisions": {did: d.to_dict() for did, d in self.decisions.items()},
            "pending_decisions": self.pending_decisions,
            "completed_decisions": self.completed_decisions,
            "decision_patterns": self.decision_patterns
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DecisionEngine":
        engine = cls(agent_id=data["agent_id"])
        engine.decisions = {
            did: Decision.from_dict(d) for did, d in data.get("decisions", {}).items()
        }
        engine.pending_decisions = data.get("pending_decisions", [])
        engine.completed_decisions = data.get("completed_decisions", [])
        engine.decision_patterns = data.get("decision_patterns", {})
        return engine


# ==================== HELPER FUNCTIONS ====================

def create_verdict_decision(
    engine: DecisionEngine,
    case: str,
    options: List[str] = None,
    factors: Optional[List[Dict]] = None,
    tick: int = 0
) -> Decision:
    """
    Create a verdict decision (e.g., guilty/not guilty).
    """
    if options is None:
        options = ["guilty", "not guilty"]
    
    decision = engine.create_decision(
        question=f"What is the verdict for {case}?",
        decision_type=DecisionType.VERDICT,
        alternatives=options,
        priority=DecisionPriority.CRITICAL,
        tick=tick
    )
    
    # Add factors if provided
    if factors:
        for f in factors:
            engine.add_factor(
                decision_id=decision.id,
                description=f["description"],
                weight=f.get("weight", 0.5),
                belief_id=f.get("belief_id"),
                source=f.get("source", "")
            )
    
    return decision


def create_action_decision(
    engine: DecisionEngine,
    action: str,
    alternatives: List[str] = None,
    context: Optional[Dict] = None,
    tick: int = 0
) -> Decision:
    """
    Create an action decision.
    """
    decision = engine.create_decision(
        question=f"What should I do about {action}?",
        decision_type=DecisionType.ACTION,
        alternatives=alternatives or [],
        context=context or {},
        tick=tick
    )
    
    return decision
