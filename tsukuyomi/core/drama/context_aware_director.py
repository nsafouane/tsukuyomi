"""
Context-Aware Drama Director - Enhanced DramaDirector with context-aware events.

Extends the base DramaDirector with scenario-driven narrative beats,
context-aware event injection, and branching narrative support.

Author: Tanit (OpenClaw Agent)
Date: February 17, 2026
"""

import logging
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from datetime import datetime

from .event_library import EventLibrary, Event, EventCategory
from .branch_manager import BranchManager, ConditionEvaluator

# Import base DramaDirector if available
try:
    from tsukuyomi.brain.DramaDirector import DramaDirector, TensionVector
except ImportError:
    # Define placeholder for standalone testing
    @dataclass
    class TensionVector:
        conflict: float = 0.0
        mystery: float = 0.0
        social: float = 0.0
        emotion: float = 0.0
        aggregate: float = 0.0
    
    class DramaDirector:
        """Placeholder base class."""
        def __init__(self, fate_engine=None, **kwargs):
            self.current_tension = TensionVector()
            self.boredom_threshold = 0.2
        
        def get_status(self) -> Dict:
            return {"aggregate": self.current_tension.aggregate}

logger = logging.getLogger("ContextAwareDramaDirector")


@dataclass
class TensionSnapshot:
    """Snapshot of tension at a specific tick."""
    tick: int
    aggregate: float
    components: Dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class NarrativeBeat:
    """Represents a narrative beat for the director."""
    id: str
    tick: int
    beat_type: str
    description: str
    triggered: bool = False
    trigger_tick: Optional[int] = None


class ContextAwareDramaDirector(DramaDirector):
    """
    Enhanced Drama Director with scenario awareness and context-aware event injection.
    
    Extends the base DramaDirector to:
    - Follow narrative beats from scenario definitions
    - Inject context-matched events based on world state
    - Support branching narratives with condition evaluation
    - Track tension history for pattern detection
    
    Usage:
        director = ContextAwareDramaDirector(scenario_config, fate_engine)
        event = director.evaluate_tick(tick, world_state)
        if event:
            # Inject event into simulation
    """
    
    def __init__(
        self,
        scenario_config: Optional[Any] = None,
        fate_engine=None,
        boredom_threshold: float = 0.2,
        tension_threshold_high: float = 0.8,
        tension_decay_rate: float = 0.001,
        window_size_ticks: int = 400,
    ):
        """
        Initialize the context-aware drama director.
        
        Args:
            scenario_config: ScenarioConfig from scenario schema.
            fate_engine: Reference to the fate engine for event injection.
            boredom_threshold: Tension level below which to inject events.
            tension_threshold_high: Tension level above which to slow injection.
            tension_decay_rate: Rate of tension decay per tick.
            window_size_ticks: Rolling window size for tension calculation.
        """
        super().__init__(
            fate_engine=fate_engine,
            boredom_threshold=boredom_threshold,
            tension_decay_rate=tension_decay_rate,
            window_size_ticks=window_size_ticks,
        )
        
        self.scenario_config = scenario_config
        self.tension_threshold_high = tension_threshold_high
        
        # Narrative beat tracking
        self._beat_index: int = 0
        self._completed_beats: Set[str] = set()
        self._beat_queue: List[Any] = []  # NarrativeBeat objects from scenario
        
        # Branch management
        self._branch_manager = BranchManager()
        self._condition_evaluator = ConditionEvaluator()
        self._active_branch: Optional[str] = None
        
        # Event library
        self._event_library = EventLibrary()
        
        # Tension history
        self._tension_history: List[TensionSnapshot] = []
        self._max_history_length: int = 1000
        
        # Event injection cooldown
        self._last_injection_tick: int = 0
        self._min_injection_interval: int = 100  # Minimum ticks between injections
        
        # World context
        self._world_context: Dict[str, Any] = {}
        self._agent_states: Dict[str, Dict[str, Any]] = {}
        
        # Initialize from scenario if provided
        if scenario_config:
            self._initialize_from_scenario(scenario_config)
    
    def _initialize_from_scenario(self, config):
        """Initialize director from scenario configuration."""
        
        # Load narrative beats
        if hasattr(config, 'narrative_beats'):
            self._beat_queue = list(config.narrative_beats)
            logger.info(f"Loaded {len(self._beat_queue)} narrative beats")
        
        # Configure event library
        if hasattr(config, 'drama_config'):
            drama_config = config.drama_config
            
            # Set thresholds
            self.boredom_threshold = drama_config.tension_threshold_low
            self.tension_threshold_high = drama_config.tension_threshold_high
            
            # Configure event library
            if hasattr(drama_config, 'event_library'):
                el = drama_config.event_library
                self._event_library.configure(
                    environmental=dict(el.environmental) if el.environmental else None,
                    social=dict(el.social) if el.social else None,
                    character_specific=dict(el.character_specific) if el.character_specific else None,
                    selection_mode=drama_config.event_selection.mode,
                    category_weights=dict(drama_config.event_selection.weights),
                    context_match_weights=dict(drama_config.event_selection.context_matching),
                )
        
        logger.info(f"Context-Aware Director initialized with "
                   f"boredom_threshold={self.boredom_threshold}, "
                   f"high_threshold={self.tension_threshold_high}")
    
    def evaluate_tick(
        self, 
        tick: int, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> Optional[Event]:
        """
        Evaluate the current tick for narrative intervention.
        
        This is the main entry point for the director. Call this each tick
        to check if a narrative event should be injected.
        
        Args:
            tick: Current simulation tick.
            world_state: Current world state dictionary.
            agent_states: Dictionary of agent_id -> agent_state.
            
        Returns:
            Event to inject, or None if no intervention needed.
        """
        
        # Update internal state
        self._world_context = world_state.get('environment_context', {})
        self._world_context['tension'] = self.current_tension.aggregate
        self._world_context['tick'] = tick
        self._agent_states = agent_states
        
        # Record tension snapshot
        self._record_tension(tick)
        
        # 1. Check for scheduled narrative beats
        beat_event = self._check_beats(tick, world_state, agent_states)
        if beat_event:
            return beat_event
        
        # 2. Check for tension-based intervention
        tension_event = self._check_tension(tick, world_state, agent_states)
        if tension_event:
            return tension_event
        
        return None
    
    def _record_tension(self, tick: int):
        """Record a tension snapshot for history tracking."""
        
        snapshot = TensionSnapshot(
            tick=tick,
            aggregate=self.current_tension.aggregate,
            components={
                "conflict": self.current_tension.conflict,
                "mystery": self.current_tension.mystery,
                "social": self.current_tension.social,
                "emotion": self.current_tension.emotion,
            },
        )
        
        self._tension_history.append(snapshot)
        
        # Trim history if needed
        if len(self._tension_history) > self._max_history_length:
            self._tension_history.pop(0)
    
    def _check_beats(
        self, 
        tick: int,
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> Optional[Event]:
        """Check if any narrative beats should trigger."""
        
        while self._beat_index < len(self._beat_queue):
            beat = self._beat_queue[self._beat_index]
            
            # Skip if already completed
            if beat.id in self._completed_beats:
                self._beat_index += 1
                continue
            
            # Check if tick has been reached
            if beat.tick > tick:
                break
            
            # Check prerequisite
            if hasattr(beat, 'prerequisite') and beat.prerequisite:
                if not self._branch_manager.is_beat_completed(beat.prerequisite):
                    logger.debug(f"Beat '{beat.id}' waiting for prerequisite '{beat.prerequisite}'")
                    self._beat_index += 1
                    continue
            
            # Check trigger conditions
            if self._should_trigger_beat(beat, world_state, agent_states):
                event = self._create_beat_event(beat, world_state)
                
                # Mark as completed
                self._completed_beats.add(beat.id)
                self._branch_manager.mark_beat_completed(beat.id)
                
                # Check for branching
                if hasattr(beat, 'branches') and beat.branches:
                    self._evaluate_branches(beat, world_state, agent_states, tick)
                
                self._beat_index += 1
                return event
            
            self._beat_index += 1
        
        return None
    
    def _should_trigger_beat(
        self, 
        beat: Any,
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> bool:
        """Check if a beat's trigger conditions are met."""
        
        # If no conditions, always trigger when tick is reached
        if not hasattr(beat, 'trigger_if') or not beat.trigger_if:
            return True
        
        # Evaluate each condition (AND logic)
        for tc in beat.trigger_if:
            condition = tc.condition if hasattr(tc, 'condition') else str(tc)
            if not self._condition_evaluator.evaluate(condition, world_state, agent_states):
                logger.debug(f"Beat '{beat.id}' condition not met: {condition}")
                return False
        
        return True
    
    def _create_beat_event(self, beat: Any, world_state: Dict[str, Any]) -> Event:
        """Create an event from a narrative beat."""
        
        description = beat.description
        
        # If beat has an action, use it
        if hasattr(beat, 'action') and beat.action:
            action = beat.action
            
            if action.type == 'inject_event' and action.event:
                description = action.event
            elif action.type == 'inject_thought' and action.thought:
                # Create thought event
                return Event(
                    id=f"thought_{beat.id}_{random.randint(10000, 99999)}",
                    category=EventCategory.NARRATIVE,
                    description=action.thought,
                    target_agent=action.target,
                    broadcast=False,
                    params={"thought": action.thought},
                )
        
        return Event(
            id=f"beat_{beat.id}_{random.randint(10000, 99999)}",
            category=EventCategory.NARRATIVE,
            description=description,
            context_tags=[beat.beat_type if hasattr(beat, 'beat_type') else beat.type.value if hasattr(beat.type, 'value') else str(beat.type)],
            broadcast=True,
        )
    
    def _evaluate_branches(
        self, 
        beat: Any,
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        tick: int
    ):
        """Evaluate branch conditions and set active branch."""
        
        if not hasattr(beat, 'branches') or not beat.branches:
            return
        
        # Convert branch configs to dict format
        branch_conditions = []
        for b in beat.branches:
            branch_conditions.append({
                "id": b.id if hasattr(b, 'id') else "",
                "condition": b.condition if hasattr(b, 'condition') else "",
                "then": b.then if hasattr(b, 'then') else "",
            })
        
        # Evaluate
        selected = self._branch_manager.evaluate_branch(
            branch_conditions, world_state, agent_states, tick
        )
        
        if selected:
            self._active_branch = selected
            logger.info(f"🌳 Narrative branched to: {selected}")
            
            # If the selected branch has nested beats, add them to queue
            if hasattr(beat, 'get_beat_by_id'):
                target_beat = self.scenario_config.get_beat_by_id(selected)
                if target_beat:
                    self._insert_beats_at_tick(target_beat, tick + 100)
    
    def _insert_beats_at_tick(self, beat: Any, start_tick: int):
        """Insert nested beats into the queue at appropriate ticks."""
        
        if hasattr(beat, 'beats') and beat.beats:
            for i, nested in enumerate(beat.beats):
                # Create a copy with adjusted tick
                nested.tick = start_tick + (i * 100)
                self._beat_queue.append(nested)
            
            # Re-sort by tick
            self._beat_queue.sort(key=lambda b: b.tick)
            logger.debug(f"Inserted {len(beat.beats)} nested beats starting at tick {start_tick}")
    
    def _check_tension(
        self, 
        tick: int,
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]]
    ) -> Optional[Event]:
        """Check if tension-based intervention is needed."""
        
        # Respect cooldown
        if tick - self._last_injection_tick < self._min_injection_interval:
            return None
        
        tension = self.current_tension.aggregate
        
        # Low tension - inject to raise
        if tension < self.boredom_threshold:
            logger.info(f"📉 Tension low ({tension:.2f}), injecting event")
            return self._inject_context_aware_event(world_state, agent_states)
        
        # High tension - possibly inject to redirect
        if tension > self.tension_threshold_high:
            # Only occasionally inject at high tension
            if random.random() < 0.1:
                logger.info(f"📈 Tension high ({tension:.2f}), considering redirect")
                return self._inject_context_aware_event(world_state, agent_states, prefer_calm=True)
        
        return None
    
    def _inject_context_aware_event(
        self, 
        world_state: Dict[str, Any],
        agent_states: Dict[str, Dict[str, Any]],
        prefer_calm: bool = False
    ) -> Event:
        """Select and create a context-aware event."""
        
        # Update world context with tension
        context = self._world_context.copy()
        context['tension'] = self.current_tension.aggregate
        
        # Select event from library
        event = self._event_library.select_event(context, self.current_tension.aggregate, agent_states)
        
        # Record injection
        self._last_injection_tick = self._world_context.get('tick', 0)
        
        logger.info(f"🎭 Injecting event: {event}")
        
        return event
    
    def update_tension_from_event(self, event: Event, delta: float = 0.0):
        """
        Update tension based on an injected event.
        
        Args:
            event: The event that was injected.
            delta: Optional manual delta to apply.
        """
        
        # Auto-calculate delta based on event category
        if delta == 0.0:
            if event.category == EventCategory.CONFLICT:
                delta = 0.15
            elif event.category == EventCategory.SOCIAL:
                delta = 0.08
            elif event.category == EventCategory.ENVIRONMENTAL:
                delta = 0.05
            elif event.category == EventCategory.NARRATIVE:
                delta = 0.1
        
        # Apply delta
        self.current_tension.aggregate = min(1.0, max(0.0, 
            self.current_tension.aggregate + delta))
        
        logger.debug(f"Tension updated to {self.current_tension.aggregate:.2f} (+{delta:.2f})")
    
    def get_tension_trend(self, window_ticks: int = 100) -> str:
        """
        Analyze tension trend over recent ticks.
        
        Returns:
            'rising', 'falling', or 'stable'
        """
        
        if len(self._tension_history) < 10:
            return 'stable'
        
        recent = self._tension_history[-min(window_ticks, len(self._tension_history)):]
        
        if len(recent) < 2:
            return 'stable'
        
        first_half = recent[:len(recent)//2]
        second_half = recent[len(recent)//2:]
        
        avg_first = sum(s.aggregate for s in first_half) / len(first_half)
        avg_second = sum(s.aggregate for s in second_half) / len(second_half)
        
        diff = avg_second - avg_first
        
        if diff > 0.05:
            return 'rising'
        elif diff < -0.05:
            return 'falling'
        else:
            return 'stable'
    
    def get_status(self) -> Dict[str, Any]:
        """Get current director status for debugging."""
        
        return {
            "tension": {
                "current": self.current_tension.aggregate,
                "trend": self.get_tension_trend(),
                "threshold_low": self.boredom_threshold,
                "threshold_high": self.tension_threshold_high,
            },
            "beats": {
                "current_index": self._beat_index,
                "completed": list(self._completed_beats),
                "total": len(self._beat_queue),
            },
            "branches": {
                "active": self._active_branch,
                "history": self._branch_manager.get_branch_history()[-5:],  # Last 5
            },
            "events": {
                "last_injection_tick": self._last_injection_tick,
                "history_length": len(self._tension_history),
            },
        }
    
    def reset(self):
        """Reset director state for a new simulation."""
        
        self._beat_index = 0
        self._completed_beats.clear()
        self._tension_history.clear()
        self._last_injection_tick = 0
        self._active_branch = None
        self._branch_manager.reset()
        self.current_tension = TensionVector()
        
        logger.info("Director state reset")