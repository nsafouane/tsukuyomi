"""
Drama Director Configuration for Angry Men Experiment
======================================================

Controls narrative pacing, dramatic beats, and emergent storytelling.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger("DramaDirector")


class Act(Enum):
    SETUP = 1           # Initial positions, introductions
    CONFRONTATION = 2   # Arguments, evidence discussion
    CLIMAX = 3          # Emotional peaks, turning points
    RESOLUTION = 4      # Final decisions, closure


class EmotionalTension(Enum):
    LOW = 0.2
    MEDIUM = 0.5
    HIGH = 0.7
    CRITICAL = 0.9


@dataclass
class DramaBeat:
    """A dramatic moment in the narrative."""
    id: str
    name: str
    act: Act
    trigger_condition: str  # tick number, vote count, or event
    description: str
    characters_involved: List[str]
    expected_emotion: Dict
    duration_ticks: int
    triggered: bool = False
    completed: bool = False


@dataclass
class NarrativeState:
    """Current state of the narrative."""
    current_act: Act = Act.SETUP
    tension_level: float = 0.3
    last_dramatic_moment: Optional[int] = None
    vote_history: List[Dict] = field(default_factory=list)
    emotional_peaks: List[Dict] = field(default_factory=list)
    conversation_turns: int = 0


class DramaDirector:
    """
    Orchestrates dramatic pacing and narrative flow.
    
    Responsibilities:
    - Track narrative acts and transitions
    - Monitor emotional tension across agents
    - Trigger dramatic beats at appropriate moments
    - Inject narrative events when pacing needs adjustment
    """
    
    def __init__(self, case_config: Dict):
        self.case = case_config
        self.state = NarrativeState()
        self.beats = self._load_beats(case_config.get("drama_beats", []))
        self.event_hooks: Dict[str, List[Callable]] = {}
        
        # Tension tracking
        self.tension_history: List[float] = []
        self.tension_smoothing = 0.3
        
        # Narrative constraints
        self.min_beat_interval = 50  # ticks between dramatic moments
        self.tension_thresholds = {
            "increase": 0.3,   # Lowered from 0.6 - easier to reach CLIMAX
            "climax": 0.6,     # Lowered from 0.85
            "release": 0.2     # Lowered from 0.4
        }
        
        logger.info(f"DramaDirector initialized with {len(self.beats)} beats")
    
    def _load_beats(self, beat_configs: List[Dict]) -> List[DramaBeat]:
        """Load dramatic beats from configuration."""
        beats = []
        act_map = {1: Act.SETUP, 2: Act.CONFRONTATION, 3: Act.CLIMAX, 4: Act.RESOLUTION}
        
        for config in beat_configs:
            beat = DramaBeat(
                id=f"beat_{config['act']}_{len(beats)}",
                name=config["name"],
                act=act_map.get(config["act"], Act.SETUP),
                trigger_condition=config["trigger"],
                description=config["description"],
                characters_involved=[],
                expected_emotion={},
                duration_ticks=config.get("expected_duration_ticks", 100)
            )
            beats.append(beat)
        
        return beats
    
    def update_tension(
        self, 
        agent_emotions: Dict[str, Dict], 
        vote_state: Dict = None,
        tick: int = 0,
        total_ticks: int = 18000,
        existential_events: List[Dict] = None
    ) -> float:
        """
        Calculate overall tension from multiple factors.
        
        ENHANCED to prevent tension flatline after consensus.
        
        Args:
            agent_emotions: Dict of agent_id -> {valence, arousal, dominance}
            vote_state: Optional dict of {"guilty": N, "not_guilty": N}
            tick: Current tick (for time-based tension floor)
            total_ticks: Total expected ticks
            existential_events: Recent existential revelations
        
        Returns:
            Smoothed tension level (0.0 to 1.0)
        """
        if not agent_emotions:
            return self.state.tension_level
        
        # === FACTOR 1: Emotional Tension ===
        tensions = []
        for agent_id, emotion in agent_emotions.items():
            arousal = emotion.get("arousal", 0.5)
            valence = emotion.get("valence", 0.0)
            dominance = emotion.get("dominance", 0.5)
            
            # Negative valence + high arousal = tension
            agent_tension = arousal * (1 - valence) * dominance
            tensions.append(agent_tension)
        
        # Also consider disagreement (variance in dominance)
        dominances = [e.get("dominance", 0.5) for e in agent_emotions.values()]
        if len(dominances) > 1:
            dominance_variance = sum((d - 0.5)**2 for d in dominances) / len(dominances)
        else:
            dominance_variance = 0
        
        emotional_tension = (sum(tensions) / len(tensions)) * (1 + dominance_variance)
        
        # === FACTOR 2: Vote Disagreement ===
        vote_tension = 0.0
        if vote_state:
            total = sum(vote_state.values())
            if total > 1:
                # More evenly split = more tension
                votes = list(vote_state.values())
                max_vote = max(votes)
                min_vote = min(votes)
                split_ratio = 1 - abs(max_vote - min_vote) / total  # 0 = unanimous, 1 = tied
                vote_tension = split_ratio * 0.5  # Max 0.5 from votes
        
        # === FACTOR 3: Existential Events (NEW) ===
        existential_tension = 0.0
        if existential_events:
            # Recent existential revelations add tension
            for event in existential_events[-5:]:  # Last 5 events
                impact = event.get("impact", 0.3)
                recency = event.get("recency", 1.0)  # 1.0 = very recent, decays
                existential_tension += impact * recency * 0.2
            existential_tension = min(0.3, existential_tension)  # Cap at 0.3
        
        # === FACTOR 4: Time-Based Tension Floor (NEW) ===
        # Prevents tension from flatlining - minimum tension rises over time
        progress = tick / total_ticks if total_ticks > 0 else 0
        # Floor rises from 0.1 at start to 0.4 at 75% progress
        time_floor = 0.1 + (progress * 0.4)
        
        # === FACTOR 5: Emotional Intensity (NEW) ===
        # High arousal across all agents = higher tension
        avg_arousal = sum(e.get("arousal", 0.5) for e in agent_emotions.values()) / len(agent_emotions)
        intensity_bonus = 0.0
        if avg_arousal > 0.7:
            intensity_bonus = (avg_arousal - 0.7) * 0.3  # Up to 0.09 bonus
        
        # === COMBINE ALL FACTORS ===
        raw_tension = emotional_tension + vote_tension + existential_tension + intensity_bonus
        
        # Apply time floor - tension can't drop below this
        raw_tension = max(time_floor, raw_tension)
        
        # Smooth with previous value
        self.state.tension_level = (
            self.tension_smoothing * self.state.tension_level +
            (1 - self.tension_smoothing) * min(1.0, raw_tension)
        )
        
        # Also apply floor to smoothed tension
        self.state.tension_level = max(time_floor * 0.8, self.state.tension_level)
        
        self.tension_history.append(self.state.tension_level)
        
        return self.state.tension_level
    
    def check_beat_triggers(self, tick: int, vote_state: Dict) -> Optional[DramaBeat]:
        """
        Check if any dramatic beat should be triggered.
        
        Args:
            tick: Current simulation tick
            vote_state: Current vote counts {guilty: n, not_guilty: m}
        
        Returns:
            Beat to trigger, or None
        """
        for beat in self.beats:
            if beat.triggered or beat.completed:
                continue
            
            # Check tick-based triggers
            if beat.trigger_condition.startswith("tick_"):
                trigger_tick = int(beat.trigger_condition.split("_")[1])
                if tick >= trigger_tick:
                    # Check minimum interval from last beat
                    if (self.state.last_dramatic_moment is None or 
                        tick - self.state.last_dramatic_moment >= self.min_beat_interval):
                        beat.triggered = True
                        self.state.last_dramatic_moment = tick
                        logger.info(f"Drama beat triggered: {beat.name} at tick {tick}")
                        return beat
            
            # Check vote-based triggers
            elif beat.trigger_condition.startswith("vote_"):
                # Parse "vote_9_to_3" format -> target is 9 (not_guilty count)
                parts = beat.trigger_condition.split("_")
                if len(parts) >= 2:
                    try:
                        not_guilty = vote_state.get("not_guilty", 0)
                        target = int(parts[1])  # e.g., "vote_9_to_3" -> 9
                        
                        if not_guilty >= target:
                            beat.triggered = True
                            self.state.last_dramatic_moment = tick
                            logger.info(f"Drama beat triggered: {beat.name} at vote {vote_state}")
                            return beat
                    except ValueError:
                        logger.warning(f"Invalid vote trigger format: {beat.trigger_condition}")
        
        return None
    
    def get_act_transition(self, tick: int, total_ticks: int) -> Optional[Act]:
        """
        Determine if we should transition to a new act.
        
        ENHANCED with time-based fallback - ensures CLIMAX and RESOLUTION
        are reached even if tension is low.
        """
        progress = tick / total_ticks
        
        # SETUP -> CONFRONTATION: Time-based, always happens
        if progress < 0.15 and self.state.current_act != Act.SETUP:
            return Act.SETUP
        elif 0.15 <= progress < 0.5 and self.state.current_act == Act.SETUP:
            logger.info(f"Act transition: SETUP -> CONFRONTATION at tick {tick}")
            return Act.CONFRONTATION
        
        # CONFRONTATION -> CLIMAX: Tension OR time-based
        elif 0.5 <= progress < 0.85 and self.state.current_act == Act.CONFRONTATION:
            # Check tension threshold
            if self.state.tension_level >= self.tension_thresholds["increase"]:
                logger.info(f"Act transition: CONFRONTATION -> CLIMAX at tick {tick} (tension={self.state.tension_level:.2f})")
                return Act.CLIMAX
            # FALLBACK: Force CLIMAX at 70% progress regardless of tension
            elif progress >= 0.70:
                logger.info(f"Act transition: CONFRONTATION -> CLIMAX at tick {tick} (TIME-BASED FALLBACK)")
                return Act.CLIMAX
        
        # CLIMAX -> RESOLUTION: Time-based fallback
        elif progress >= 0.85 and self.state.current_act == Act.CLIMAX:
            logger.info(f"Act transition: CLIMAX -> RESOLUTION at tick {tick}")
            return Act.RESOLUTION
        
        return None
    
    def generate_directive(self, beat: DramaBeat, agents: List[str]) -> Dict:
        """
        Generate a narrative directive for agents.
        
        Args:
            beat: The dramatic beat that was triggered
            agents: List of agent IDs involved
        
        Returns:
            Directive dict with instructions for agents
        """
        directive = {
            "beat_id": beat.id,
            "beat_name": beat.name,
            "act": beat.act.name,
            "description": beat.description,
            "target_agents": agents,
            "expected_emotion": beat.expected_emotion,
            "duration_ticks": beat.duration_ticks,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add specific instructions based on beat
        if "knife" in beat.name.lower():
            directive["instruction"] = "Focus discussion on the weapon evidence"
            directive["key_question"] = "Is the knife truly unique?"
        
        elif "old man" in beat.name.lower():
            directive["instruction"] = "Examine the timeline and credibility"
            directive["key_question"] = "Could the witness really reach the door in 15 seconds?"
        
        elif "woman" in beat.name.lower():
            directive["instruction"] = "Discuss the visibility issues"
            directive["key_question"] = "Could she see clearly without glasses?"
        
        elif "outburst" in beat.name.lower():
            directive["instruction"] = "Emotional breakdown - personal trauma surfaces"
            directive["key_question"] = "What's really driving this juror's position?"
        
        return directive
    
    def record_vote(self, vote: Dict):
        """Record a vote change for narrative tracking."""
        self.state.vote_history.append(vote)
        
        # Check for dramatic vote shifts
        if len(self.state.vote_history) >= 2:
            prev = self.state.vote_history[-2]
            curr = vote
            
            shift = abs(curr.get("not_guilty", 0) - prev.get("not_guilty", 0))
            if shift >= 2:
                self.state.emotional_peaks.append({
                    "type": "vote_shift",
                    "magnitude": shift,
                    "tick": len(self.state.vote_history)
                })
                logger.info(f"Dramatic vote shift detected: {shift} votes changed")
    
    def generate_dynamic_beat(
        self, 
        tick: int, 
        vote_state: Dict,
        agent_emotions: Dict[str, Dict],
        recent_events: List[Dict] = None
    ) -> Optional[DramaBeat]:
        """
        Generate a dramatic beat dynamically based on current state.
        
        This ensures drama continues even when predefined beats are exhausted.
        
        Args:
            tick: Current tick
            vote_state: Current vote counts
            agent_emotions: Agent emotional states
            recent_events: Recent significant events
        
        Returns:
            A dynamically generated DramaBeat, or None if not needed
        """
        # Check if we need a dynamic beat
        # Need one if: no beat in last min_beat_interval ticks AND tension is rising
        
        last_beat_age = tick - (self.state.last_dramatic_moment or 0)
        if last_beat_age < self.min_beat_interval:
            return None
        
        # Determine beat type based on current situation
        beat_type = self._determine_beat_type(vote_state, agent_emotions, recent_events)
        
        if not beat_type:
            return None
        
        # Generate beat content
        beat_content = self._generate_beat_content(beat_type, vote_state, agent_emotions)
        
        # Create dynamic beat
        beat = DramaBeat(
            id=f"dynamic_{tick}",
            name=beat_content["name"],
            act=self.state.current_act,
            trigger_condition=f"tick_{tick}",
            description=beat_content["description"],
            characters_involved=beat_content.get("characters", []),
            expected_emotion=beat_content.get("emotion", {}),
            duration_ticks=60
        )
        beat.triggered = True
        
        # Add to beats list
        self.beats.append(beat)
        self.state.last_dramatic_moment = tick
        
        logger.info(f"Generated dynamic beat: {beat.name} at tick {tick}")
        
        return beat
    
    def _determine_beat_type(
        self,
        vote_state: Dict,
        agent_emotions: Dict[str, Dict],
        recent_events: List[Dict]
    ) -> Optional[str]:
        """Determine what type of dynamic beat to generate."""
        
        # Check for existential events (Oracle revelations)
        if recent_events:
            existential = [e for e in recent_events if e.get("type") == "existential"]
            if existential:
                return "existential_response"
        
        # Check for vote change
        if len(self.state.vote_history) >= 2:
            prev = self.state.vote_history[-2]
            curr = self.state.vote_history[-1] if self.state.vote_history else {}
            shift = abs(curr.get("not_guilty", 0) - prev.get("not_guilty", 0))
            if shift > 0:
                return "vote_shift"
        
        # Check for high emotional intensity
        if agent_emotions:
            max_arousal = max(e.get("arousal", 0) for e in agent_emotions.values())
            if max_arousal > 0.8:
                return "emotional_peak"
        
        # Check for stuck debate (same vote count for a while)
        if vote_state and len(self.state.vote_history) > 5:
            recent_votes = [v.get("not_guilty", 0) for v in self.state.vote_history[-5:]]
            if len(set(recent_votes)) == 1:
                return "break_stalemate"
        
        # Default: escalate tension
        if self.state.tension_level > 0.5:
            return "escalation"
        
        return None
    
    def _generate_beat_content(
        self,
        beat_type: str,
        vote_state: Dict,
        agent_emotions: Dict[str, Dict]
    ) -> Dict:
        """Generate content for a dynamic beat."""
        
        templates = {
            "existential_response": {
                "name": "Existential Reflection",
                "description": "The Oracle's words echo through the room, challenging assumptions.",
                "emotion": {"arousal": 0.6, "valence": -0.3},
                "instruction": "Reflect on the deeper implications of what was just said."
            },
            "vote_shift": {
                "name": "Vote Shift Moment",
                "description": "A juror changes their position, shifting the room's dynamics.",
                "emotion": {"arousal": 0.7, "valence": 0.1},
                "instruction": "React to the changing tide of votes."
            },
            "emotional_peak": {
                "name": "Emotional Peak",
                "description": "Passions flare as the debate reaches a fever pitch.",
                "emotion": {"arousal": 0.9, "valence": -0.2},
                "instruction": "Express your emotional state strongly."
            },
            "break_stalemate": {
                "name": "Breaking the Stalemate",
                "description": "The debate has stalled. Someone needs to bring new perspective.",
                "emotion": {"arousal": 0.5, "valence": 0.0},
                "instruction": "Introduce a new angle or perspective to break the deadlock."
            },
            "escalation": {
                "name": "Tension Escalation",
                "description": "The pressure builds as time passes.",
                "emotion": {"arousal": 0.6, "valence": -0.1},
                "instruction": "Feel the weight of the decision pressing down."
            }
        }
        
        return templates.get(beat_type, templates["escalation"])
    
    def get_narrative_summary(self) -> Dict:
        """Get a summary of the narrative state."""
        return {
            "current_act": self.state.current_act.name,
            "tension_level": self.state.tension_level,
            "beats_triggered": sum(1 for b in self.beats if b.triggered),
            "beats_completed": sum(1 for b in self.beats if b.completed),
            "vote_count": len(self.state.vote_history),
            "emotional_peaks": len(self.state.emotional_peaks),
            "conversation_turns": self.state.conversation_turns
        }


# Export
__all__ = ["DramaDirector", "DramaBeat", "NarrativeState", "Act", "EmotionalTension"]