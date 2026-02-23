"""
Reasoning Validation Types
==========================

Type definitions for reasoning validation.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class ViolationType(Enum):
    """Types of reasoning violations."""
    TRAIT_INCONSISTENCY = "trait_inconsistency"
    BELIEF_CONTRADICTION = "belief_contradiction"
    NEEDS_IGNORED = "needs_ignored"
    CONTEXT_MISMATCH = "context_mismatch"
    EMOTIONAL_INCOHERENCE = "emotional_incoherence"
    MEMORY_IGNORED = "memory_ignored"


class ViolationSeverity(Enum):
    """Severity levels for violations."""
    LOW = 0.1
    MEDIUM = 0.3
    HIGH = 0.5
    CRITICAL = 0.8


@dataclass
class ReasoningViolation:
    """A detected inconsistency in reasoning."""
    violation_type: ViolationType
    description: str
    severity: float
    trait: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    context: Optional[str] = None
    suggestion: Optional[str] = None

    def __str__(self) -> str:
        return f"[{self.violation_type.value}] {self.description} (severity: {self.severity:.2f})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "violation_type": self.violation_type.value,
            "description": self.description,
            "severity": self.severity,
            "trait": self.trait,
            "expected": self.expected,
            "actual": self.actual,
            "context": self.context,
            "suggestion": self.suggestion
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReasoningViolation':
        return cls(
            violation_type=ViolationType(data["violation_type"]),
            description=data["description"],
            severity=data["severity"],
            trait=data.get("trait"),
            expected=data.get("expected"),
            actual=data.get("actual"),
            context=data.get("context"),
            suggestion=data.get("suggestion")
        )


@dataclass
class ValidationResult:
    """Complete validation result for a decision."""
    valid: bool
    violations: List[ReasoningViolation] = field(default_factory=list)
    severity: float = 0.0
    trait_violations: int = 0
    belief_violations: int = 0
    needs_violations: int = 0
    recommendations: List[str] = field(default_factory=list)

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    @property
    def has_critical_violations(self) -> bool:
        return any(v.severity >= ViolationSeverity.CRITICAL.value for v in self.violations)

    def add_violation(self, violation: ReasoningViolation) -> None:
        self.violations.append(violation)
        self.severity += violation.severity

        if violation.violation_type == ViolationType.TRAIT_INCONSISTENCY:
            self.trait_violations += 1
        elif violation.violation_type == ViolationType.BELIEF_CONTRADICTION:
            self.belief_violations += 1
        elif violation.violation_type == ViolationType.NEEDS_IGNORED:
            self.needs_violations += 1

        if violation.severity >= ViolationSeverity.HIGH.value:
            self.valid = False

    def get_summary(self) -> str:
        if self.valid:
            return f"VALID (severity: {self.severity:.2f}, violations: {self.violation_count})"
        return (
            f"INVALID (severity: {self.severity:.2f}, violations: {self.violation_count})\n"
            f"  - Trait violations: {self.trait_violations}\n"
            f"  - Belief violations: {self.belief_violations}\n"
            f"  - Needs violations: {self.needs_violations}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "violations": [v.to_dict() for v in self.violations],
            "severity": self.severity,
            "trait_violations": self.trait_violations,
            "belief_violations": self.belief_violations,
            "needs_violations": self.needs_violations,
            "recommendations": self.recommendations
        }


@dataclass
class PersonalitySnapshot:
    """Snapshot of personality traits for validation."""
    openness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    agreeableness: float = 0.0
    neuroticism: float = 0.0
    speaking_style: str = ""
    decision_style: str = ""
    conflict_style: str = ""
    core_values: List[str] = field(default_factory=list)
    biases: List[str] = field(default_factory=list)
    vocabulary_level: str = "medium"


@dataclass
class BeliefSnapshot:
    """Snapshot of agent beliefs for validation."""
    stances: Dict[str, Tuple[str, float]] = field(default_factory=dict)

    def get_stance(self, topic: str) -> Optional[Tuple[str, float]]:
        return self.stances.get(topic)


@dataclass
class NeedsSnapshot:
    """Snapshot of agent needs for validation."""
    needs: Dict[str, Tuple[float, bool]] = field(default_factory=dict)
    dominant_need: Optional[str] = None

    def get_critical_needs(self) -> List[str]:
        return [n for n, (level, critical) in self.needs.items() if critical]
