"""
Tsukuyomi V2 - Agent Needs System

This module implements the internal motivational model for agents.
Needs drive agent behavior, preventing the "Static Loop" where agents
do nothing because no external stimulus exists.

Core Needs:
- Hunger: Physical drive to eat/drink
- Fatigue: Physical drive to rest
- Boredom: Cognitive drive to explore/socialize
- Social: Psychological drive to interact with others
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple
from enum import Enum
import time
import math

logger = logging.getLogger(__name__)


class NeedType(Enum):
    """Types of needs an agent can have."""
    HUNGER = "hunger"
    FATIGUE = "fatigue"
    BOREDOM = "boredom"
    SOCIAL = "social"


@dataclass
class Need:
    """A single need with its current value and decay rate."""
    need_type: NeedType
    value: float = 0.0  # 0.0 (satisfied) to 1.0 (critical)
    decay_rate: float = 0.001  # How fast need increases per tick
    threshold: float = 0.8  # Threshold above which action is motivated

    def update(self, dt: float) -> None:
        """
        Update need value based on time delta.

        Args:
            dt: Time delta in seconds since last update
        """
        self.value = min(1.0, self.value + self.decay_rate * dt)
        logger.debug(f"Need {self.need_type.value} updated to {self.value:.3f}")

    def satisfy(self, amount: float = 0.5) -> None:
        """
        Reduce need value by specified amount.

        Args:
            amount: Amount to reduce (0.0 to 1.0)
        """
        self.value = max(0.0, self.value - amount)
        logger.debug(f"Need {self.need_type.value} satisfied by {amount:.3f}, now {self.value:.3f}")

    def is_critical(self) -> bool:
        """Check if need is above critical threshold."""
        return self.value >= self.threshold

    def get_motivation(self) -> float:
        """
        Get motivation score (0.0 to 1.0).
        Higher values indicate stronger drive to act.

        Returns:
            float: Motivation score
        """
        if self.value < self.threshold * 0.5:
            return 0.0
        # Linear scaling from threshold to 1.0
        return min(1.0, (self.value - self.threshold * 0.5) / (1.0 - self.threshold * 0.5))

    def to_dict(self) -> Dict:
        """Convert need to dictionary for serialization."""
        return {
            "type": self.need_type.value,
            "value": self.value,
            "threshold": self.threshold,
            "is_critical": self.is_critical()
        }


@dataclass
class NeedsSystem:
    """
    Manages all needs for an agent.

    This system drives agent behavior by increasing needs over time.
    When needs reach critical thresholds, agents are motivated to act.
    """

    hunger: Need = field(default_factory=lambda: Need(
        NeedType.HUNGER, decay_rate=0.0005, threshold=0.8
    ))
    fatigue: Need = field(default_factory=lambda: Need(
        NeedType.FATIGUE, decay_rate=0.0003, threshold=0.85
    ))
    boredom: Need = field(default_factory=lambda: Need(
        NeedType.BOREDOM, decay_rate=0.0008, threshold=0.75
    ))
    social: Need = field(default_factory=lambda: Need(
        NeedType.SOCIAL, decay_rate=0.0004, threshold=0.7
    ))

    _last_update: float = field(default_factory=time.time)

    def update_all(self, tick_rate: float = 20.0) -> None:
        """
        Update all needs based on time since last update.

        Args:
            tick_rate: Engine tick rate (ticks per second)
        """
        current_time = time.time()
        dt = current_time - self._last_update
        self._last_update = current_time

        # Update each need
        self.hunger.update(dt)
        self.fatigue.update(dt)
        self.boredom.update(dt)
        self.social.update(dt)

        logger.debug(f"All needs updated after {dt:.3f}s")

    def get_dominant_need(self) -> Optional[NeedType]:
        """
        Get the most pressing need based on motivation scores.

        Returns:
            NeedType of the dominant need, or None if no need is critical
        """
        needs = [
            (self.hunger, self.hunger.get_motivation()),
            (self.fatigue, self.fatigue.get_motivation()),
            (self.boredom, self.boredom.get_motivation()),
            (self.social, self.social.get_motivation()),
        ]

        # Sort by motivation (descending)
        needs.sort(key=lambda x: x[1], reverse=True)

        dominant, motivation = needs[0]

        if motivation > 0.5:
            return dominant.need_type

        return None

    def get_critical_needs(self) -> List[NeedType]:
        """
        Get list of all needs that are currently critical.

        Returns:
            List of NeedType that exceed thresholds
        """
        critical = []
        if self.hunger.is_critical():
            critical.append(NeedType.HUNGER)
        if self.fatigue.is_critical():
            critical.append(NeedType.FATIGUE)
        if self.boredom.is_critical():
            critical.append(NeedType.BOREDOM)
        if self.social.is_critical():
            critical.append(NeedType.SOCIAL)

        return critical

    def satisfy_need(self, need_type: NeedType, amount: float = 0.5) -> None:
        """
        Satisfy a specific need.

        Args:
            need_type: The need to satisfy
            amount: Amount to reduce (0.0 to 1.0)
        """
        if need_type == NeedType.HUNGER:
            self.hunger.satisfy(amount)
        elif need_type == NeedType.FATIGUE:
            self.fatigue.satisfy(amount)
        elif need_type == NeedType.BOREDOM:
            self.boredom.satisfy(amount)
        elif need_type == NeedType.SOCIAL:
            self.social.satisfy(amount)
        else:
            logger.warning(f"Unknown need type: {need_type}")

    def get_prompt_context(self) -> str:
        """
        Generate a human-readable summary of needs for LLM prompt.

        Returns:
            str: Formatted need description for agent prompt
        """
        dominant = self.get_dominant_need()
        critical = self.get_critical_needs()

        context_parts = []

        # List all needs with their values
        context_parts.append(f"Physical Needs:")
        context_parts.append(f"  - Hunger: {self.hunger.value*100:.0f}% (Critical at {self.hunger.threshold*100:.0f}%)")
        context_parts.append(f"  - Fatigue: {self.fatigue.value*100:.0f}% (Critical at {self.fatigue.threshold*100:.0f}%)")
        context_parts.append(f"Cognitive Needs:")
        context_parts.append(f"  - Boredom: {self.boredom.value*100:.0f}% (Critical at {self.boredom.threshold*100:.0f}%)")
        context_parts.append(f"  - Social: {self.social.value*100:.0f}% (Critical at {self.social.threshold*100:.0f}%)")

        # Add motivation context
        if dominant:
            context_parts.append(f"\nDominant Motivation: {dominant.value.upper()}")
        elif critical:
            context_parts.append(f"\nCritical Needs: {', '.join([n.value for n in critical])}")
        else:
            context_parts.append(f"\nStatus: All needs are manageable.")

        return "\n".join(context_parts)

    def to_dict(self) -> Dict:
        """Convert entire needs system to dictionary for serialization."""
        return {
            "hunger": self.hunger.to_dict(),
            "fatigue": self.fatigue.to_dict(),
            "boredom": self.boredom.to_dict(),
            "social": self.social.to_dict(),
            "dominant_need": self.get_dominant_need().value if self.get_dominant_need() else None,
            "critical_needs": [n.value for n in self.get_critical_needs()]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'NeedsSystem':
        """
        Create NeedsSystem from dictionary (for deserialization).

        Args:
            data: Dictionary representation of needs

        Returns:
            NeedsSystem instance
        """
        system = cls()

        # Restore individual needs
        for key, need_data in data.items():
            if key in ["hunger", "fatigue", "boredom", "social"]:
                need_type = NeedType(key)
                if need_type == NeedType.HUNGER:
                    system.hunger = Need(
                        need_type,
                        need_data["value"],
                        need_data.get("decay_rate", 0.001),
                        need_data.get("threshold", 0.8)
                    )
                elif need_type == NeedType.FATIGUE:
                    system.fatigue = Need(
                        need_type,
                        need_data["value"],
                        need_data.get("decay_rate", 0.001),
                        need_data.get("threshold", 0.8)
                    )
                elif need_type == NeedType.BOREDOM:
                    system.boredom = Need(
                        need_type,
                        need_data["value"],
                        need_data.get("decay_rate", 0.001),
                        need_data.get("threshold", 0.8)
                    )
                elif need_type == NeedType.SOCIAL:
                    system.social = Need(
                        need_type,
                        need_data["value"],
                        need_data.get("decay_rate", 0.001),
                        need_data.get("threshold", 0.8)
                    )

        return system
