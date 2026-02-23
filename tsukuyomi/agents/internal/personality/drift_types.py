"""
Personality Drift Types
=======================

Type definitions for personality drift detection and evolution tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class BehaviorSnapshot:
    """Snapshot of agent behavior at a point in time."""
    tick: int
    response: str
    context: str
    action: Optional[str] = None
    action_params: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DriftReport:
    """Report of detected personality drift."""
    agent_name: str
    tick: int
    drifts: List[str]
    severity: float
    ema_severity: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def has_drift(self) -> bool:
        """Check if any drift was detected."""
        return len(self.drifts) > 0
    
    @property
    def consistency_score(self) -> float:
        """Calculate consistency score (inverse of EMA severity)."""
        return 1.0 - min(1.0, self.ema_severity)


@dataclass
class PersonalityEvolutionEvent:
    """Track intentional personality changes."""
    tick: int
    trait: str
    change: float
    reason: str
    trigger_event: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
