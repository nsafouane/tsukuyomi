"""
Decision Record - Phase 17: Reasoning Transparency

This module implements the DecisionRecord dataclass that captures the complete
reasoning process of an agent when making a decision. It provides full context
for debugging, analysis, and transparency.

Core Components:
- DecisionRecord: Complete record of an agent's decision process
- DecisionContext: Input context for the decision
- ReasoningStep: Individual reasoning step in the chain
- ConsideredAction: Actions considered and their evaluation
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class DecisionType(Enum):
    """Types of decisions an agent can make."""
    ACTION = "action"           # Physical action (MOVE, INTERACT, EMOTE)
    REFLECT = "reflect"         # Internal reflection on beliefs
    SPEAK = "speak"             # Speech/conversation
    IDLE = "idle"               # No action chosen
    ABORT = "abort"             # Decision aborted due to error


@dataclass
class ReasoningStep:
    """
    A single step in the reasoning chain.

    Captures the thought process at each stage, making the reasoning
    transparent and auditable.
    """

    step_number: int
    step_type: str              # "perception", "emotion", "memory", "options", "filter", "decision"
    content: str                # The actual reasoning content
    confidence: float = 1.0     # Confidence in this step's conclusion
    duration_ms: float = 0.0    # Time spent on this step
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_number": self.step_number,
            "step_type": self.step_type,
            "content": self.content,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReasoningStep':
        """Create from dictionary."""
        return cls(
            step_number=data["step_number"],
            step_type=data["step_type"],
            content=data["content"],
            confidence=data.get("confidence", 1.0),
            duration_ms=data.get("duration_ms", 0.0),
            metadata=data.get("metadata", {})
        )


@dataclass
class ConsideredAction:
    """
    An action that was considered during decision-making.

    Tracks why actions were considered and why they were accepted or rejected.
    """

    action: str                 # The action name
    params: Dict[str, Any]      # Action parameters
    score: float = 0.0          # Evaluation score (0.0 to 1.0)
    accepted: bool = False      # Whether this action was accepted
    rejection_reason: Optional[str] = None  # Why rejected (if applicable)
    personality_alignment: float = 0.0  # How well it aligns with personality
    need_addressal: List[str] = field(default_factory=list)  # Needs this addresses
    risks: List[str] = field(default_factory=list)  # Potential risks

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "action": self.action,
            "params": self.params,
            "score": self.score,
            "accepted": self.accepted,
            "rejection_reason": self.rejection_reason,
            "personality_alignment": self.personality_alignment,
            "need_addressal": self.need_addressal,
            "risks": self.risks
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConsideredAction':
        """Create from dictionary."""
        return cls(
            action=data["action"],
            params=data.get("params", {}),
            score=data.get("score", 0.0),
            accepted=data.get("accepted", False),
            rejection_reason=data.get("rejection_reason"),
            personality_alignment=data.get("personality_alignment", 0.0),
            need_addressal=data.get("need_addressal", []),
            risks=data.get("risks", [])
        )


@dataclass
class DecisionContext:
    """
    Input context for a decision.

    Captures everything the agent perceived and considered before reasoning.
    """

    # Perception
    perception_summary: str = ""
    perceived_entities: List[str] = field(default_factory=list)
    perceived_objects: List[str] = field(default_factory=list)
    location: str = ""

    # Emotional state
    emotional_state: str = "neutral"
    valence: float = 0.0
    arousal: float = 0.5
    dominance: float = 0.0

    # Memories
    relevant_memories: List[str] = field(default_factory=list)
    memory_count: int = 0

    # Conversation
    conversation_context: str = ""
    current_topic: str = ""
    conversation_heat: float = 0.0

    # Needs
    critical_needs: List[str] = field(default_factory=list)
    dominant_need: Optional[str] = None

    # Beliefs (relevant topics)
    belief_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "perception_summary": self.perception_summary,
            "perceived_entities": self.perceived_entities,
            "perceived_objects": self.perceived_objects,
            "location": self.location,
            "emotional_state": self.emotional_state,
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "relevant_memories": self.relevant_memories,
            "memory_count": self.memory_count,
            "conversation_context": self.conversation_context,
            "current_topic": self.current_topic,
            "conversation_heat": self.conversation_heat,
            "critical_needs": self.critical_needs,
            "dominant_need": self.dominant_need,
            "belief_summary": self.belief_summary
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionContext':
        """Create from dictionary."""
        return cls(
            perception_summary=data.get("perception_summary", ""),
            perceived_entities=data.get("perceived_entities", []),
            perceived_objects=data.get("perceived_objects", []),
            location=data.get("location", ""),
            emotional_state=data.get("emotional_state", "neutral"),
            valence=data.get("valence", 0.0),
            arousal=data.get("arousal", 0.5),
            dominance=data.get("dominance", 0.0),
            relevant_memories=data.get("relevant_memories", []),
            memory_count=data.get("memory_count", 0),
            conversation_context=data.get("conversation_context", ""),
            current_topic=data.get("current_topic", ""),
            conversation_heat=data.get("conversation_heat", 0.0),
            critical_needs=data.get("critical_needs", []),
            dominant_need=data.get("dominant_need"),
            belief_summary=data.get("belief_summary", "")
        )


@dataclass
class DecisionRecord:
    """
    Complete record of an agent's decision process.

    This is the core transparency artifact - it captures everything about
    how an agent reached a decision, making reasoning visible and auditable.

    Attributes:
        record_id: Unique identifier for this decision record
        agent_name: Name of the agent making the decision
        agent_id: Agent's unique identifier
        tick: Simulation tick when decision was made
        timestamp: Wall-clock timestamp

        context: Input context (perception, emotion, memories, etc.)
        decision_type: Type of decision made

        deliberation_trigger: Why the agent needed to deliberate
        reasoning_steps: Chain of thought during reasoning
        considered_actions: Actions considered and evaluated
        rejected_actions: Actions explicitly rejected

        final_action: The action that was chosen
        action_params: Parameters for the chosen action
        raw_confidence: Agent's self-reported confidence (0.0 to 1.0)
        calibrated_confidence: Confidence adjusted by calibration system

        personality_drivers: Which personality traits influenced this decision
        belief_influences: Which beliefs influenced this decision
        need_drivers: Which needs motivated this decision

        validation_passed: Whether the reasoning passed validation
        validation_violations: Any consistency violations detected

        processing_time_ms: Total time spent on decision
        llm_tokens_used: Tokens used for LLM calls (if applicable)
    """

    # Identity
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str = ""
    agent_id: str = ""
    tick: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Input
    context: DecisionContext = field(default_factory=DecisionContext)
    decision_type: DecisionType = DecisionType.ACTION

    # Process
    deliberation_trigger: str = ""
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    considered_actions: List[ConsideredAction] = field(default_factory=list)
    rejected_actions: List[str] = field(default_factory=list)

    # Output
    final_action: str = ""
    action_params: Dict[str, Any] = field(default_factory=dict)
    raw_confidence: float = 0.5
    calibrated_confidence: float = 0.5

    # Personality impact
    personality_drivers: List[str] = field(default_factory=list)
    belief_influences: List[str] = field(default_factory=list)
    need_drivers: List[str] = field(default_factory=list)

    # Validation
    validation_passed: bool = True
    validation_violations: List[str] = field(default_factory=list)

    # Metadata
    processing_time_ms: float = 0.0
    llm_tokens_used: int = 0

    def add_reasoning_step(
        self,
        step_type: str,
        content: str,
        confidence: float = 1.0,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ReasoningStep:
        """
        Add a reasoning step to the chain.

        Args:
            step_type: Type of reasoning step
            content: The reasoning content
            confidence: Confidence in this step
            duration_ms: Time spent on this step
            metadata: Additional metadata

        Returns:
            The created ReasoningStep
        """
        step = ReasoningStep(
            step_number=len(self.reasoning_steps) + 1,
            step_type=step_type,
            content=content,
            confidence=confidence,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        self.reasoning_steps.append(step)
        return step

    def add_considered_action(
        self,
        action: str,
        params: Dict[str, Any],
        score: float = 0.0,
        accepted: bool = False,
        rejection_reason: Optional[str] = None,
        personality_alignment: float = 0.0,
        need_addressal: Optional[List[str]] = None,
        risks: Optional[List[str]] = None
    ) -> ConsideredAction:
        """
        Add a considered action.

        Args:
            action: The action name
            params: Action parameters
            score: Evaluation score
            accepted: Whether accepted
            rejection_reason: Why rejected (if applicable)
            personality_alignment: How well it aligns with personality
            need_addressal: Needs this addresses
            risks: Potential risks

        Returns:
            The created ConsideredAction
        """
        considered = ConsideredAction(
            action=action,
            params=params,
            score=score,
            accepted=accepted,
            rejection_reason=rejection_reason,
            personality_alignment=personality_alignment,
            need_addressal=need_addressal or [],
            risks=risks or []
        )
        self.considered_actions.append(considered)

        if not accepted and rejection_reason:
            self.rejected_actions.append(f"{action}: {rejection_reason}")

        return considered

    def set_final_decision(
        self,
        action: str,
        params: Dict[str, Any],
        confidence: float,
        calibrated: Optional[float] = None
    ) -> None:
        """
        Set the final decision.

        Args:
            action: The chosen action
            params: Action parameters
            confidence: Self-reported confidence
            calibrated: Calibrated confidence (if available)
        """
        self.final_action = action
        self.action_params = params
        self.raw_confidence = confidence
        self.calibrated_confidence = calibrated if calibrated is not None else confidence

    def add_personality_driver(self, trait: str, influence: str) -> None:
        """
        Add a personality driver that influenced the decision.

        Args:
            trait: The personality trait (e.g., "extraversion", "neuroticism")
            influence: How it influenced the decision
        """
        self.personality_drivers.append(f"{trait}: {influence}")

    def add_belief_influence(self, topic: str, stance: str, influence: str) -> None:
        """
        Add a belief that influenced the decision.

        Args:
            topic: The belief topic
            stance: Agent's stance on the topic
            influence: How it influenced the decision
        """
        self.belief_influences.append(f"{topic} ({stance}): {influence}")

    def add_need_driver(self, need: str, urgency: float) -> None:
        """
        Add a need that motivated the decision.

        Args:
            need: The need type
            urgency: How urgent the need was (0.0 to 1.0)
        """
        self.need_drivers.append(f"{need} (urgency: {urgency:.0%})")

    def get_reasoning_summary(self) -> str:
        """
        Get a human-readable summary of the reasoning chain.

        Returns:
            str: Formatted reasoning summary
        """
        parts = []

        for step in self.reasoning_steps:
            parts.append(f"{step.step_number}. [{step.step_type.upper()}] {step.content}")

        return "\n".join(parts)

    def get_decision_summary(self) -> str:
        """
        Get a one-line summary of the decision.

        Returns:
            str: One-line decision summary
        """
        return f"{self.final_action} (confidence: {self.calibrated_confidence:.0%})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "record_id": self.record_id,
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "tick": self.tick,
            "timestamp": self.timestamp,
            "context": self.context.to_dict(),
            "decision_type": self.decision_type.value,
            "deliberation_trigger": self.deliberation_trigger,
            "reasoning_steps": [s.to_dict() for s in self.reasoning_steps],
            "considered_actions": [a.to_dict() for a in self.considered_actions],
            "rejected_actions": self.rejected_actions,
            "final_action": self.final_action,
            "action_params": self.action_params,
            "raw_confidence": self.raw_confidence,
            "calibrated_confidence": self.calibrated_confidence,
            "personality_drivers": self.personality_drivers,
            "belief_influences": self.belief_influences,
            "need_drivers": self.need_drivers,
            "validation_passed": self.validation_passed,
            "validation_violations": self.validation_violations,
            "processing_time_ms": self.processing_time_ms,
            "llm_tokens_used": self.llm_tokens_used
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionRecord':
        """Create from dictionary."""
        record = cls(
            record_id=data.get("record_id", str(uuid.uuid4())),
            agent_name=data.get("agent_name", ""),
            agent_id=data.get("agent_id", ""),
            tick=data.get("tick", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            context=DecisionContext.from_dict(data.get("context", {})),
            decision_type=DecisionType(data.get("decision_type", "action")),
            deliberation_trigger=data.get("deliberation_trigger", ""),
            reasoning_steps=[ReasoningStep.from_dict(s) for s in data.get("reasoning_steps", [])],
            considered_actions=[ConsideredAction.from_dict(a) for a in data.get("considered_actions", [])],
            rejected_actions=data.get("rejected_actions", []),
            final_action=data.get("final_action", ""),
            action_params=data.get("action_params", {}),
            raw_confidence=data.get("raw_confidence", 0.5),
            calibrated_confidence=data.get("calibrated_confidence", 0.5),
            personality_drivers=data.get("personality_drivers", []),
            belief_influences=data.get("belief_influences", []),
            need_drivers=data.get("need_drivers", []),
            validation_passed=data.get("validation_passed", True),
            validation_violations=data.get("validation_violations", []),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            llm_tokens_used=data.get("llm_tokens_used", 0)
        )
        return record

    def __repr__(self) -> str:
        return (
            f"DecisionRecord(agent={self.agent_name}, tick={self.tick}, "
            f"action={self.final_action}, confidence={self.calibrated_confidence:.2f})"
        )