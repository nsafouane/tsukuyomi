"""
Drama Director - Advanced Narrative & Social Dynamics

Monitors the simulation's 'Tension Vector' and manages catalyst injections.
Ensures the narrative maintains an appropriate pace and engagement level.

Tension Vector components:
- Conflict: Based on damage/aggressive events.
- Mystery: Based on unresolved information or knowledge gaps.
- Social: Based on dialogue frequency and gossip propagation.
- Emotion: Based on aggregate sentiment of agent deliberations.

Author: Tanit (OpenClaw Agent)
Date: February 8, 2026
"""

import logging
import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

# Import generated protobuf classes
from tsukuyomi.proto import core_pb2
from tsukuyomi.brain.CatalystSystem import CatalystSystem

logger = logging.getLogger("DramaDirector")

@dataclass
class TensionVector:
    """
    Numeric representation of the simulation's narrative tension.
    Values are typically 0.0 to 1.0.
    """
    conflict: float = 0.0
    mystery: float = 0.0
    social: float = 0.0
    emotion: float = 0.0
    aggregate: float = 0.0

class DramaDirector:
    """
    The Drama Director monitors world events and computes the Tension Vector.
    It can trigger Catalyst events when tension falls below certain thresholds.
    """

    def __init__(
        self,
        fate_engine,
        boredom_threshold: float = 0.2,
        tension_decay_rate: float = 0.001,  # per tick
        window_size_ticks: int = 400,       # ~20 seconds at 20 TPS
    ):
        self.fate_engine = fate_engine
        self.boredom_threshold = boredom_threshold
        self.tension_decay_rate = tension_decay_rate
        self.window_size_ticks = window_size_ticks

        # Initialize Catalyst System
        self.catalyst_system = CatalystSystem(fate_engine)

        # Current tension state
        self.current_tension = TensionVector()
        
        # Historical metrics for rolling averages
        self.event_counts = {
            "conflict": 0,
            "social": 0,
            "mystery": 0
        }
        self.sentiment_sum = 0.0
        self.sentiment_count = 0
        
        self.last_catalyst_tick = 0
        self.catalyst_cooldown = 1200  # 1 minute at 20 TPS

    async def on_tick_resolved(self, tick: int, resolutions: List[core_pb2.Resolution]):
        """
        Post-resolution hook to update tension based on what just happened.
        """
        # 1. Update raw event counts
        for res in resolutions:
            if not res.success:
                continue
            
            action_type = res.outcome.get("action")
            
            # Conflict detection (basic)
            if action_type in ("attack", "damage"): # Future actions
                self.event_counts["conflict"] += 1
            
            # Social detection
            if action_type in ("speak", "emote", "interact"):
                self.event_counts["social"] += 1
                
            # Mystery/Discovery
            if action_type in ("examine", "search"):
                self.event_counts["mystery"] += 1

        # 2. Recompute Tension Vector periodically
        if tick % 20 == 0: # Once per second
            self._update_tension_vector()
            self._check_for_catalysts(tick)

    def _update_tension_vector(self):
        """Compute the Tension Vector based on rolling metrics."""
        
        # Conflict Tension (normalized by window)
        # Assuming 1 major conflict event per 10 seconds is 'High' (1.0)
        conf_val = (self.event_counts["conflict"] / (self.window_size_ticks / 200)) 
        self.current_tension.conflict = min(1.0, conf_val)
        
        # Social Tension
        # Assuming 1 social event per second is 'High'
        soc_val = (self.event_counts["social"] / (self.window_size_ticks / 20))
        self.current_tension.social = min(1.0, soc_val)
        
        # Mystery Tension
        mys_val = (self.event_counts["mystery"] / (self.window_size_ticks / 100))
        self.current_tension.mystery = min(1.0, mys_val)
        
        # Emotion Tension (from sentiment)
        if self.sentiment_count > 0:
            self.current_tension.emotion = abs(self.sentiment_sum / self.sentiment_count)
        
        # Aggregate Tension (Simple average for now)
        self.current_tension.aggregate = (
            self.current_tension.conflict + 
            self.current_tension.social + 
            self.current_tension.mystery + 
            self.current_tension.emotion
        ) / 4.0
        
        # Reset counters for decay simulation (or use actual rolling window in future)
        # Simple decay: reduce counts by 10% every second
        for key in self.event_counts:
            self.event_counts[key] = int(self.event_counts[key] * 0.9)
        
        if self.sentiment_count > 0:
            self.sentiment_sum *= 0.9
            self.sentiment_count = int(self.sentiment_count * 0.9)

        logger.info(
            f"📊 Tension Update: aggregate={self.current_tension.aggregate:.2f} "
            f"(C:{self.current_tension.conflict:.2f}, S:{self.current_tension.social:.2f}, "
            f"M:{self.current_tension.mystery:.2f}, E:{self.current_tension.emotion:.2f})"
        )

    def _check_for_catalysts(self, tick: int):
        """Check if tension is too low and trigger a catalyst if needed."""
        if tick - self.last_catalyst_tick < self.catalyst_cooldown:
            return

        if self.current_tension.aggregate < self.boredom_threshold:
            logger.warning(f"⚠️ Tension too low ({self.current_tension.aggregate:.2f}). TRIGGERING CATALYST.")
            self._trigger_catalyst(tick)
            self.last_catalyst_tick = tick

    def _trigger_catalyst(self, tick: int):
        """Infect a catalyst event into the simulation."""
        event_str = self.catalyst_system.trigger_random_catalyst(tick)
        logger.info(f"🎭 DramaDirector -> CatalystSystem: {event_str[:50]}...")

    def update_sentiment(self, sentiment_score: float):
        """Update the aggregate sentiment metric (called by AgentBrain/LLMService)."""
        self.sentiment_sum += sentiment_score
        self.sentiment_count += 1

    def get_status(self) -> Dict:
        """Return current tension data."""
        return asdict(self.current_tension)
