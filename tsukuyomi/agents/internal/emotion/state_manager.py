"""
State Manager - Emotional Core
==============================

Manages dynamic emotional states based on the PAD model.
"""

from typing import List, Optional, Dict
import logging

from .types import (
    EmotionalState, EmotionalEpisode, EmotionalImpact, MoodLabel
)
from .personality import PersonalityBaseline
from .impact_rules import EmotionalImpactRules

logger = logging.getLogger("StateManager")


class StateManager:
    """
    The Emotional Core of the agent.
    
    Manages dynamic emotional states based on the PAD model, handles
    event processing, regression to personality baseline, and
    emotional inertia (shifts scaled by arousal).
    """
    
    def __init__(self, baseline: PersonalityBaseline, initial_state: Optional[EmotionalState] = None):
        self.baseline = baseline
        
        if initial_state:
            self.state = initial_state
        else:
            self.state = EmotionalState(
                valence=baseline.valence_baseline,
                arousal=baseline.arousal_baseline,
                dominance=baseline.dominance_baseline,
                mood_label=MoodLabel.CALM.value
            )
        
        self._clamp_state()
        self.state.mood_label = self._derive_mood_label()
    
    def update(self, tick_number: int, percepts: List) -> None:
        """Update emotional state based on percepts and time."""
        for percept in percepts:
            impact = EmotionalImpactRules.classify_percept_impact(percept)
            
            if impact:
                inertia_factor = 0.5 + (self.state.arousal * 0.5)
                
                valence_shift = impact.valence_delta * inertia_factor
                arousal_shift = impact.arousal_delta * inertia_factor
                dominance_shift = impact.dominance_delta * inertia_factor
                
                self.state.valence += valence_shift
                self.state.arousal += arousal_shift
                self.state.dominance += dominance_shift
                
                self._clamp_state()
                
                intensity = max(abs(valence_shift), abs(arousal_shift), abs(dominance_shift))
                if intensity > 0.3:
                    event_id = getattr(percept, 'percept_id', f"tick_{tick_number}")
                    self.state.active_episodes.append(EmotionalEpisode(
                        trigger_event_id=event_id,
                        emotion_type=impact.emotion_label,
                        intensity=min(1.0, intensity),
                        onset_tick=tick_number,
                        decay_rate=200
                    ))
        
        self._decay_episodes()
        self._regress_to_baseline()
        self.state.mood_label = self._derive_mood_label()
    
    def apply_event(self, event_type: str, tick_number: int) -> None:
        """Apply a direct emotional event (not from perception)."""
        impact = EmotionalImpactRules.get_impact(event_type)
        
        if impact:
            inertia_factor = 0.5 + (self.state.arousal * 0.5)
            
            self.state.valence += impact.valence_delta * inertia_factor
            self.state.arousal += impact.arousal_delta * inertia_factor
            self.state.dominance += impact.dominance_delta * inertia_factor
            
            self._clamp_state()
            
            intensity = max(abs(impact.valence_delta), abs(impact.arousal_delta))
            if intensity > 0.3:
                self.state.active_episodes.append(EmotionalEpisode(
                    trigger_event_id=event_type,
                    emotion_type=impact.emotion_label,
                    intensity=min(1.0, intensity),
                    onset_tick=tick_number,
                    decay_rate=200
                ))
            
            self.state.mood_label = self._derive_mood_label()
    
    def _clamp_state(self) -> None:
        """Clamp all PAD values to valid ranges."""
        self.state.valence = max(-1.0, min(1.0, self.state.valence))
        self.state.arousal = max(0.0, min(1.0, self.state.arousal))
        self.state.dominance = max(-1.0, min(1.0, self.state.dominance))
    
    def _decay_episodes(self) -> None:
        """Decay active emotional episodes and remove weak ones."""
        decay_factor = 0.995
        
        for episode in self.state.active_episodes:
            episode.intensity *= decay_factor
        
        self.state.active_episodes = [
            ep for ep in self.state.active_episodes
            if ep.intensity > 0.1
        ]
    
    def _regress_to_baseline(self) -> None:
        """Regress emotional state towards personality baseline."""
        rate = self.baseline.regression_rate
        
        self.state.valence += (self.baseline.valence_baseline - self.state.valence) * rate
        self.state.arousal += (self.baseline.arousal_baseline - self.state.arousal) * rate
        self.state.dominance += (self.baseline.dominance_baseline - self.state.dominance) * rate
    
    def _derive_mood_label(self) -> str:
        """Derive a mood label from current PAD values."""
        if self.state.valence > 0.3:
            valence_category = "positive"
        elif self.state.valence < -0.3:
            valence_category = "negative"
        else:
            valence_category = "neutral"
        
        if self.state.arousal > 0.6:
            arousal_category = "high"
        elif self.state.arousal < 0.4:
            arousal_category = "low"
        else:
            arousal_category = "medium"
        
        if self.state.dominance > 0.2:
            dominance_category = "dominant"
        elif self.state.dominance < -0.2:
            dominance_category = "submissive"
        else:
            dominance_category = "neutral"
        
        if valence_category == "positive":
            if arousal_category == "high":
                return MoodLabel.ELATED.value if dominance_category == "dominant" else MoodLabel.EXCITED.value
            elif arousal_category == "low":
                if dominance_category == "dominant":
                    return MoodLabel.CONFIDENT.value
                elif dominance_category == "submissive":
                    return MoodLabel.CONTENT.value
                else:
                    return MoodLabel.RELAXED.value
            else:
                return MoodLabel.HAPPY.value if dominance_category == "dominant" else MoodLabel.CONTENT.value
        
        elif valence_category == "negative":
            if arousal_category == "high":
                return MoodLabel.HOSTILE.value if dominance_category == "dominant" else MoodLabel.FRUSTRATED.value
            elif arousal_category == "low":
                if dominance_category == "submissive":
                    return MoodLabel.INSECURE.value
                elif dominance_category == "dominant":
                    return MoodLabel.ANGRY.value
                else:
                    return MoodLabel.TIRED.value
            else:
                if dominance_category == "dominant":
                    return MoodLabel.ANGRY.value
                elif dominance_category == "submissive":
                    return MoodLabel.ANXIOUS.value
                else:
                    return MoodLabel.FRUSTRATED.value
        
        else:
            if arousal_category == "high":
                return MoodLabel.ASSERTIVE.value if dominance_category == "dominant" else MoodLabel.FEARFUL.value
            elif arousal_category == "low":
                return MoodLabel.DROWSY.value
            else:
                return MoodLabel.CALM.value
    
    def get_emotional_context(self) -> str:
        """Generate a human-readable description of the current emotional state."""
        context_parts = []
        
        context_parts.append(f"Mood: {self.state.mood_label}")
        
        state_desc = f"Emotional State: Valence={self.state.valence:.2f}, Arousal={self.state.arousal:.2f}, Dominance={self.state.dominance:.2f}"
        context_parts.append(state_desc)
        
        modifiers = []
        
        if self.state.arousal > 0.7:
            modifiers.append("highly agitated")
            modifiers.append("focus on the most pressing issue")
        elif self.state.arousal < 0.3:
            modifiers.append("calm and thoughtful")
        
        if self.state.valence < -0.5:
            modifiers.append("feeling defensive and frustrated")
            modifiers.append("perceive threats more readily")
        elif self.state.valence > 0.5:
            modifiers.append("feeling optimistic")
            modifiers.append("more open to new ideas")
        
        if self.state.dominance > 0.5:
            modifiers.append("assertive and confident")
            modifiers.append("take charge in conversations")
        elif self.state.dominance < -0.5:
            modifiers.append("submissive and deferential")
            modifiers.append("seek guidance from others")
        
        if self.state.active_episodes:
            episode_desc = "You are experiencing: " + ", ".join(
                f"{ep.emotion_type} (intensity {ep.intensity:.2f})"
                for ep in self.state.active_episodes
            )
            modifiers.append(episode_desc)
        
        if modifiers:
            context_parts.append("\nEmotional Modifiers:\n" + "\n".join(f"- {m}" for m in modifiers))
        
        return "\n".join(context_parts)
    
    def get_state_dict(self) -> Dict:
        """Get emotional state as a dictionary for serialization."""
        return {
            'valence': self.state.valence,
            'arousal': self.state.arousal,
            'dominance': self.state.dominance,
            'mood_label': self.state.mood_label,
            'active_episodes': [
                {
                    'trigger_event_id': ep.trigger_event_id,
                    'emotion_type': ep.emotion_type,
                    'intensity': ep.intensity,
                    'onset_tick': ep.onset_tick,
                    'decay_rate': ep.decay_rate
                }
                for ep in self.state.active_episodes
            ]
        }
    
    def reset_to_baseline(self) -> None:
        """Reset emotional state to personality baseline."""
        self.state.valence = self.baseline.valence_baseline
        self.state.arousal = self.baseline.arousal_baseline
        self.state.dominance = self.baseline.dominance_baseline
        self.state.active_episodes.clear()
        self.state.mood_label = self._derive_mood_label()


def create_state_manager_from_big_five(
    openness: float,
    conscientiousness: float,
    extraversion: float,
    agreeableness: float,
    neuroticism: float,
    regression_rate: float = 0.01
) -> StateManager:
    """Create a StateManager directly from Big Five trait values."""
    baseline = PersonalityBaseline.from_big_five(
        openness=openness,
        conscientiousness=conscientiousness,
        extraversion=extraversion,
        agreeableness=agreeableness,
        neuroticism=neuroticism,
        regression_rate=regression_rate
    )
    
    return StateManager(baseline)
