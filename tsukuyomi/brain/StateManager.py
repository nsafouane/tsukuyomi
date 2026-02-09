"""
StateManager.py - The Emotional Core

This module implements the PAD (Pleasure-Arousal-Dominance) emotional model
for Tsukuyomi agents. It manages dynamic emotional states that evolve based
on events and influence perception and reasoning.

Key Features:
- PAD Emotional Model (Valence, Arousal, Dominance)
- Personality Baseline (Big Five mapping to PAD)
- Emotional Impact Rules (events to PAD deltas)
- Emotional Inertia (shifts scaled by Arousal - higher arousal = more volatile)
- Mood Label Derivation
- Emotional Episode Tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math


class MoodLabel(Enum):
    """Mood labels derived from PAD combinations."""
    SERENE = "serene"
    RELAXED = "relaxed"
    CONTENT = "content"
    HAPPY = "happy"
    EXCITED = "excited"
    ELATED = "elated"
    BORED = "bored"
    DROWSY = "drowsy"
    CALM = "calm"
    TIRED = "tired"
    ANGRY = "angry"
    ANXIOUS = "anxious"
    FEARFUL = "fearful"
    FRUSTRATED = "frustrated"
    HOSTILE = "hostile"
    SUBMISSIVE = "submissive"
    DOCILE = "docile"
    SHY = "shy"
    INSECURE = "insecure"
    CONFIDENT = "confident"
    ASSERTIVE = "assertive"
    DOMINANT = "dominant"


@dataclass
class EmotionalState:
    """
    Current emotional state of an agent based on the PAD model.
    
    PAD Dimensions:
    - Valence (Pleasure): -1.0 (distress) to +1.0 (joy)
    - Arousal: 0.0 (calm) to 1.0 (agitated/excited)
    - Dominance: -1.0 (submissive) to +1.0 (dominant)
    """
    valence: float = 0.0          # -1.0 to 1.0
    arousal: float = 0.5           # 0.0 to 1.0
    dominance: float = 0.0         # -1.0 to 1.0
    
    # Derived mood label for LLM context
    mood_label: str = MoodLabel.CALM.value
    
    # Active emotional episodes (temporary spikes)
    active_episodes: List['EmotionalEpisode'] = field(default_factory=list)


@dataclass
class EmotionalEpisode:
    """
    A temporary emotional spike triggered by a specific event.
    
    Episodes represent intense emotional reactions that decay over time.
    """
    trigger_event_id: str
    emotion_type: str           # "anger", "fear", "surprise", "contempt", "joy"
    intensity: float            # 0.0 to 1.0
    onset_tick: int
    decay_rate: float           # Ticks until intensity halves


@dataclass
class EmotionalImpact:
    """
    PAD delta representing an emotional impact from an event.
    """
    valence_delta: float
    arousal_delta: float
    dominance_delta: float
    emotion_label: str          # For episode creation


class PersonalityBaseline:
    """
    Big Five personality traits mapped to PAD baseline values.
    
    Each agent has a baseline personality that their emotional state
    regresses towards over time.
    
    Big Five Traits:
    - Openness: Curious, creative vs. cautious, conservative
    - Conscientiousness: Organized, disciplined vs. spontaneous, flexible
    - Extraversion: Outgoing, energetic vs. solitary, reserved
    - Agreeableness: Friendly, compassionate vs. competitive, challenging
    - Neuroticism: Sensitive, nervous vs. secure, confident
    """
    
    def __init__(
        self,
        valence_baseline: float,
        arousal_baseline: float,
        dominance_baseline: float,
        regression_rate: float = 0.01,
        # Big Five traits (-1.0 to 1.0)
        openness: float = 0.0,
        conscientiousness: float = 0.0,
        extraversion: float = 0.0,
        agreeableness: float = 0.0,
        neuroticism: float = 0.0
    ):
        self.valence_baseline = valence_baseline
        self.arousal_baseline = arousal_baseline
        self.dominance_baseline = dominance_baseline
        self.regression_rate = regression_rate
        
        # Big Five traits for personality-based reasoning
        self.openness = openness
        self.conscientiousness = conscientiousness
        self.extraversion = extraversion
        self.agreeableness = agreeableness
        self.neuroticism = neuroticism
    
    @classmethod
    def from_big_five(
        cls,
        openness: float,
        conscientiousness: float,
        extraversion: float,
        agreeableness: float,
        neuroticism: float,
        regression_rate: float = 0.01
    ) -> 'PersonalityBaseline':
        """
        Create a PersonalityBaseline from Big Five trait values.
        
        Mapping rules (based on psychological research):
        - Valence influenced by: Agreeableness (-Neuroticism)
        - Arousal influenced by: Extraversion + Neuroticism
        - Dominance influenced by: (-Agreeableness) + Extraversion
        """
        # Normalize traits from -1..1 to appropriate ranges
        
        # Valence: Agreeable and emotionally stable (low neuroticism) agents
        # tend to have more positive valence baselines
        valence_baseline = (agreeableness * 0.3) - (neuroticism * 0.3)
        
        # Arousal: Extraverted and neurotic agents tend to be more aroused
        arousal_baseline = 0.5 + (extraversion * 0.25) + (neuroticism * 0.2)
        arousal_baseline = max(0.0, min(1.0, arousal_baseline))
        
        # Dominance: Less agreeable and more extraverted agents tend to be dominant
        dominance_baseline = (extraversion * 0.3) - (agreeableness * 0.25)
        
        return cls(
            valence_baseline=valence_baseline,
            arousal_baseline=arousal_baseline,
            dominance_baseline=dominance_baseline,
            regression_rate=regression_rate,
            openness=openness,
            conscientiousness=conscientiousness,
            extraversion=extraversion,
            agreeableness=agreeableness,
            neuroticism=neuroticism
        )
    
    # Pre-defined personality profiles
    
    # Example: "The Angry Man" from 12 Angry Men
    ANGRY_MAN = None  # Will be initialized below
    
    # Example: "The Bank Teller" from 12 Angry Men
    BANK_TELLER = None
    
    # Example: "The Stockbroker" from 12 Angry Men
    STOCKBROKER = None
    
    # Example: Calm, analytical juror
    ANALYTICAL_JUROR = None
    
    # Example: Empathetic, open-minded juror
    EMPATHETIC_JUROR = None


# Initialize pre-defined profiles
PersonalityBaseline.ANGRY_MAN = PersonalityBaseline(
    valence_baseline=-0.3,   # Tends negative
    arousal_baseline=0.7,    # High energy
    dominance_baseline=0.6,  # Wants control
    regression_rate=0.005,   # Very slow return to baseline (stubborn)
    openness=-0.2,
    conscientiousness=0.3,
    extraversion=0.6,
    agreeableness=-0.5,
    neuroticism=0.7
)

PersonalityBaseline.BANK_TELLER = PersonalityBaseline(
    valence_baseline=0.1,    # Slightly positive
    arousal_baseline=0.3,    # Low energy
    dominance_baseline=-0.4, # Submissive
    regression_rate=0.02,    # Faster return to baseline (meek)
    openness=0.0,
    conscientiousness=0.7,
    extraversion=-0.3,
    agreeableness=0.6,
    neuroticism=0.2
)

PersonalityBaseline.STOCKBROKER = PersonalityBaseline(
    valence_baseline=0.2,    # Generally positive
    arousal_baseline=0.5,    # Moderate energy
    dominance_baseline=0.3,  # Somewhat dominant
    regression_rate=0.015,   # Moderate return
    openness=0.3,
    conscientiousness=0.6,
    extraversion=0.4,
    agreeableness=-0.1,
    neuroticism=0.1
)

PersonalityBaseline.ANALYTICAL_JUROR = PersonalityBaseline(
    valence_baseline=0.0,    # Neutral
    arousal_baseline=0.4,    # Calm but alert
    dominance_baseline=0.1,   # Somewhat assertive
    regression_rate=0.01,    # Standard return
    openness=0.5,
    conscientiousness=0.8,
    extraversion=-0.2,
    agreeableness=0.3,
    neuroticism=-0.2
)

PersonalityBaseline.EMPATHETIC_JUROR = PersonalityBaseline(
    valence_baseline=0.3,    # Positive
    arousal_baseline=0.4,    # Moderate energy
    dominance_baseline=-0.1, # Slightly submissive
    regression_rate=0.015,   # Moderate return
    openness=0.8,
    conscientiousness=0.5,
    extraversion=0.2,
    agreeableness=0.8,
    neuroticism=0.0
)


class EmotionalImpactRules:
    """
    Maps events to PAD deltas.
    
    Events can be external (percepts from the world) or internal
    (cognitive processes, memory recalls, etc.).
    """
    
    # Event type -> EmotionalImpact mapping
    IMPACTS = {
        # Social events
        "criticized": EmotionalImpact(
            valence_delta=-0.2,
            arousal_delta=+0.15,
            dominance_delta=-0.1,
            emotion_label="anger"
        ),
        "praised": EmotionalImpact(
            valence_delta=+0.2,
            arousal_delta=+0.1,
            dominance_delta=+0.05,
            emotion_label="joy"
        ),
        "agreed_with": EmotionalImpact(
            valence_delta=+0.15,
            arousal_delta=+0.05,
            dominance_delta=+0.1,
            emotion_label="content"
        ),
        "contradicted": EmotionalImpact(
            valence_delta=-0.15,
            arousal_delta=+0.1,
            dominance_delta=-0.05,
            emotion_label="frustration"
        ),
        "ignored": EmotionalImpact(
            valence_delta=-0.1,
            arousal_delta=+0.1,
            dominance_delta=-0.15,
            emotion_label="sadness"
        ),
        "interrupted": EmotionalImpact(
            valence_delta=-0.1,
            arousal_delta=+0.2,
            dominance_delta=-0.1,
            emotion_label="annoyance"
        ),
        
        # Evidence/belief events
        "contradicted_by_evidence": EmotionalImpact(
            valence_delta=-0.25,
            arousal_delta=+0.2,
            dominance_delta=-0.2,
            emotion_label="surprise"
        ),
        "evidence_supports_belief": EmotionalImpact(
            valence_delta=+0.15,
            arousal_delta=+0.1,
            dominance_delta=+0.1,
            emotion_label="satisfaction"
        ),
        "realized_mistake": EmotionalImpact(
            valence_delta=-0.2,
            arousal_delta=+0.3,
            dominance_delta=-0.15,
            emotion_label="embarrassment"
        ),
        
        # Physical/safety events
        "physical_threat": EmotionalImpact(
            valence_delta=-0.5,
            arousal_delta=+0.8,
            dominance_delta=-0.3,
            emotion_label="fear"
        ),
        "witnessed_violence": EmotionalImpact(
            valence_delta=-0.3,
            arousal_delta=+0.6,
            dominance_delta=-0.2,
            emotion_label="fear"
        ),
        "injured": EmotionalImpact(
            valence_delta=-0.4,
            arousal_delta=+0.7,
            dominance_delta=-0.25,
            emotion_label="pain"
        ),
        
        # Achievement events
        "succeeded": EmotionalImpact(
            valence_delta=+0.25,
            arousal_delta=+0.15,
            dominance_delta=+0.2,
            emotion_label="joy"
        ),
        "failed": EmotionalImpact(
            valence_delta=-0.2,
            arousal_delta=+0.2,
            dominance_delta=-0.1,
            emotion_label="frustration"
        ),
        
        # Discovery events
        "discovered_something_new": EmotionalImpact(
            valence_delta=+0.1,
            arousal_delta=+0.15,
            dominance_delta=+0.05,
            emotion_label="curiosity"
        ),
        "made_connection": EmotionalImpact(
            valence_delta=+0.15,
            arousal_delta=+0.1,
            dominance_delta=+0.15,
            emotion_label="insight"
        ),
        
        # Memory events
        "recalled_painful_memory": EmotionalImpact(
            valence_delta=-0.15,
            arousal_delta=+0.1,
            dominance_delta=0.0,
            emotion_label="sadness"
        ),
        "recalled_happy_memory": EmotionalImpact(
            valence_delta=+0.1,
            arousal_delta=+0.05,
            dominance_delta=0.0,
            emotion_label="nostalgia"
        ),
    }
    
    @classmethod
    def get_impact(cls, event_type: str) -> Optional[EmotionalImpact]:
        """Get emotional impact for an event type."""
        return cls.IMPACTS.get(event_type)
    
    @classmethod
    def classify_percept_impact(cls, percept) -> Optional[EmotionalImpact]:
        """
        Classify the emotional impact of a percept.
        
        This is a simplified classifier. In a production system,
        this would use NLP sentiment analysis on speech content,
        pattern matching on events, etc.
        """
        # Import here to avoid circular dependencies
        try:
            from .PerceptionPipeline import PerceptChannel
            
            # Check percept type and content
            if hasattr(percept, 'channel'):
                if percept.channel == PerceptChannel.SPEECH:
                    # Analyze speech content
                    if hasattr(percept, 'speech'):
                        content = percept.speech.content.lower()
                        
                        # Sentiment keywords (simplified)
                        negative_words = ['hate', 'stupid', 'wrong', 'bad', 'terrible', 
                                         'idiot', 'fool', 'never', 'worst']
                        positive_words = ['good', 'great', 'right', 'excellent', 
                                         'smart', 'love', 'best', 'wonderful']
                        
                        neg_score = sum(1 for word in negative_words if word in content)
                        pos_score = sum(1 for word in positive_words if word in content)
                        
                        # Check if directly addressed
                        is_direct = hasattr(percept.speech, 'is_direct_address') and percept.speech.is_direct_address
                        
                        if neg_score > pos_score:
                            intensity = min(0.5, neg_score * 0.1)
                            if is_direct:
                                intensity *= 1.5  # Direct criticism hits harder
                            return EmotionalImpact(
                                valence_delta=-intensity,
                                arousal_delta=+intensity * 0.8,
                                dominance_delta=-intensity * 0.5,
                                emotion_label="anger" if neg_score > 2 else "annoyance"
                            )
                        elif pos_score > neg_score:
                            intensity = min(0.4, pos_score * 0.1)
                            return EmotionalImpact(
                                valence_delta=+intensity,
                                arousal_delta=+intensity * 0.5,
                                dominance_delta=+intensity * 0.3,
                                emotion_label="joy"
                            )
                
                elif percept.channel == PerceptChannel.EVENT:
                    # Check event type
                    if hasattr(percept, 'event'):
                        event_type = percept.event.event_type
                        if event_type in ['attack', 'violence', 'threat']:
                            return cls.IMPACTS.get('physical_threat')
                        elif event_type == 'failed_action':
                            return cls.IMPACTS.get('failed')
                        elif event_type == 'succeeded_action':
                            return cls.IMPACTS.get('succeeded')
            
            return None
            
        except ImportError:
            # Fallback if PerceptionPipeline not available
            return None


class StateManager:
    """
    The Emotional Core of the agent.
    
    Manages dynamic emotional states based on the PAD model, handles
    event processing, regression to personality baseline, and
    emotional inertia (shifts scaled by arousal).
    """
    
    def __init__(self, baseline: PersonalityBaseline, initial_state: Optional[EmotionalState] = None):
        """
        Initialize the StateManager.
        
        Args:
            baseline: The agent's personality baseline
            initial_state: Optional initial emotional state (defaults to baseline)
        """
        self.baseline = baseline
        
        if initial_state:
            self.state = initial_state
        else:
            # Start at baseline with small random variation
            self.state = EmotionalState(
                valence=baseline.valence_baseline,
                arousal=baseline.arousal_baseline,
                dominance=baseline.dominance_baseline,
                mood_label=MoodLabel.CALM.value  # Temporary value, will be updated
            )
        
        # Ensure initial state is within valid bounds
        self._clamp_state()
        # Now we can derive the proper mood label since self.state exists
        self.state.mood_label = self._derive_mood_label()
    
    def update(self, tick_number: int, percepts: List) -> None:
        """
        Update emotional state based on percepts and time.
        
        This implements:
        1. Event processing with emotional inertia (arousal scaling)
        2. Decay of active emotional episodes
        3. Regression towards personality baseline
        4. Mood label derivation
        
        Args:
            tick_number: Current simulation tick
            percepts: List of percepts from the PerceptionPipeline
        """
        # 1. Process emotional impacts from percepts
        for percept in percepts:
            impact = EmotionalImpactRules.classify_percept_impact(percept)
            
            if impact:
                # **EMOTIONAL INERTIA: Scale shifts by current arousal**
                # Higher arousal = more volatile (larger shifts)
                # Lower arousal = more stable (smaller shifts)
                inertia_factor = 0.5 + (self.state.arousal * 0.5)  # 0.5 to 1.0
                
                valence_shift = impact.valence_delta * inertia_factor
                arousal_shift = impact.arousal_delta * inertia_factor
                dominance_shift = impact.dominance_delta * inertia_factor
                
                # Apply shifts
                self.state.valence += valence_shift
                self.state.arousal += arousal_shift
                self.state.dominance += dominance_shift
                
                # Clamp to valid ranges
                self._clamp_state()
                
                # Create emotional episode for intense events
                # Use absolute shifts to determine intensity
                intensity = max(abs(valence_shift), abs(arousal_shift), abs(dominance_shift))
                if intensity > 0.3:
                    event_id = getattr(percept, 'percept_id', f"tick_{tick_number}")
                    self.state.active_episodes.append(EmotionalEpisode(
                        trigger_event_id=event_id,
                        emotion_type=impact.emotion_label,
                        intensity=min(1.0, intensity),
                        onset_tick=tick_number,
                        decay_rate=200  # ~10 seconds at 20 TPS
                    ))
        
        # 2. Decay active episodes
        self._decay_episodes()
        
        # 3. Regress towards personality baseline
        self._regress_to_baseline()
        
        # 4. Derive mood label
        self.state.mood_label = self._derive_mood_label()
    
    def apply_event(self, event_type: str, tick_number: int) -> None:
        """
        Apply a direct emotional event (not from perception).
        
        Used for internal events like cognitive realizations, memory recalls, etc.
        
        Args:
            event_type: Type of event (must be in EmotionalImpactRules.IMPACTS)
            tick_number: Current simulation tick
        """
        impact = EmotionalImpactRules.get_impact(event_type)
        
        if impact:
            # Apply emotional inertia
            inertia_factor = 0.5 + (self.state.arousal * 0.5)
            
            self.state.valence += impact.valence_delta * inertia_factor
            self.state.arousal += impact.arousal_delta * inertia_factor
            self.state.dominance += impact.dominance_delta * inertia_factor
            
            self._clamp_state()
            
            # Create episode if intense
            intensity = max(abs(impact.valence_delta), abs(impact.arousal_delta))
            if intensity > 0.3:
                self.state.active_episodes.append(EmotionalEpisode(
                    trigger_event_id=event_type,
                    emotion_type=impact.emotion_label,
                    intensity=min(1.0, intensity),
                    onset_tick=tick_number,
                    decay_rate=200
                ))
            
            # Update mood label
            self.state.mood_label = self._derive_mood_label()
    
    def _clamp_state(self) -> None:
        """Clamp all PAD values to valid ranges."""
        self.state.valence = max(-1.0, min(1.0, self.state.valence))
        self.state.arousal = max(0.0, min(1.0, self.state.arousal))
        self.state.dominance = max(-1.0, min(1.0, self.state.dominance))
    
    def _decay_episodes(self) -> None:
        """Decay active emotional episodes and remove weak ones."""
        decay_factor = 0.995  # Per-tick decay
        
        # Decay intensity
        for episode in self.state.active_episodes:
            episode.intensity *= decay_factor
        
        # Remove episodes below threshold
        self.state.active_episodes = [
            ep for ep in self.state.active_episodes
            if ep.intensity > 0.1
        ]
    
    def _regress_to_baseline(self) -> None:
        """
        Regress emotional state towards personality baseline.
        
        The regression rate is determined by the baseline's regression_rate
        and is applied to all three PAD dimensions.
        """
        rate = self.baseline.regression_rate
        
        # Linear interpolation towards baseline
        self.state.valence += (self.baseline.valence_baseline - self.state.valence) * rate
        self.state.arousal += (self.baseline.arousal_baseline - self.state.arousal) * rate
        self.state.dominance += (self.baseline.dominance_baseline - self.state.dominance) * rate
    
    def _derive_mood_label(self) -> str:
        """
        Derive a mood label from current PAD values.
        
        Uses a quadrant-based approach:
        - High/Low Valence (positive/negative)
        - High/Low Arousal (energetic/calm)
        - High/Low Dominance (dominant/submissive)
        
        Returns:
            Mood label string
        """
        # Discretize dimensions
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
        
        # Map combinations to mood labels
        if valence_category == "positive":
            if arousal_category == "high":
                if dominance_category == "dominant":
                    return MoodLabel.ELATED.value
                else:
                    return MoodLabel.EXCITED.value
            elif arousal_category == "low":
                if dominance_category == "dominant":
                    return MoodLabel.CONFIDENT.value
                elif dominance_category == "submissive":
                    return MoodLabel.CONTENT.value
                else:
                    return MoodLabel.RELAXED.value
            else:  # medium arousal
                if dominance_category == "dominant":
                    return MoodLabel.HAPPY.value
                else:
                    return MoodLabel.CONTENT.value
        
        elif valence_category == "negative":
            if arousal_category == "high":
                if dominance_category == "dominant":
                    return MoodLabel.HOSTILE.value
                else:
                    return MoodLabel.FRUSTRATED.value
            elif arousal_category == "low":
                if dominance_category == "submissive":
                    return MoodLabel.INSECURE.value
                elif dominance_category == "dominant":
                    return MoodLabel.ANGRY.value  # Cold anger
                else:
                    return MoodLabel.TIRED.value
            else:  # medium arousal
                if dominance_category == "dominant":
                    return MoodLabel.ANGRY.value
                elif dominance_category == "submissive":
                    return MoodLabel.ANXIOUS.value
                else:
                    return MoodLabel.FRUSTRATED.value
        
        else:  # neutral valence
            if arousal_category == "high":
                if dominance_category == "dominant":
                    return MoodLabel.ASSERTIVE.value
                else:
                    return MoodLabel.FEARFUL.value
            elif arousal_category == "low":
                return MoodLabel.DROWSY.value
            else:
                return MoodLabel.CALM.value
    
    def get_emotional_context(self) -> str:
        """
        Generate a human-readable description of the current emotional state
        for use in LLM prompts.
        
        Returns:
            String describing current emotional state and its implications
        """
        context_parts = []
        
        # Basic mood
        context_parts.append(f"Mood: {self.state.mood_label}")
        
        # Emotional state description
        state_desc = f"Emotional State: Valence={self.state.valence:.2f}, Arousal={self.state.arousal:.2f}, Dominance={self.state.dominance:.2f}"
        context_parts.append(state_desc)
        
        # Emotional modifiers for reasoning
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
        
        # Active episodes
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


# Convenience functions for creating StateManagers

def create_state_manager_from_big_five(
    openness: float,
    conscientiousness: float,
    extraversion: float,
    agreeableness: float,
    neuroticism: float,
    regression_rate: float = 0.01
) -> StateManager:
    """
    Create a StateManager directly from Big Five trait values.
    
    Args:
        openness: Curiosity and creativity (-1.0 to 1.0)
        conscientiousness: Organization and discipline (-1.0 to 1.0)
        extraversion: Sociability and energy (-1.0 to 1.0)
        agreeableness: Friendliness and compassion (-1.0 to 1.0)
        neuroticism: Emotional stability (-1.0 to 1.0, negative = more stable)
        regression_rate: How fast emotions return to baseline
    
    Returns:
        Configured StateManager instance
    """
    baseline = PersonalityBaseline.from_big_five(
        openness=openness,
        conscientiousness=conscientiousness,
        extraversion=extraversion,
        agreeableness=agreeableness,
        neuroticism=neuroticism,
        regression_rate=regression_rate
    )
    
    return StateManager(baseline)


# Example usage and testing

if __name__ == "__main__":
    print("=== StateManager Demo ===\n")
    
    # Create an "Angry Man" style agent
    print("1. Creating 'Angry Man' agent:")
    angry_manager = StateManager(PersonalityBaseline.ANGRY_MAN)
    print(angry_manager.get_emotional_context())
    print()
    
    # Create a "Bank Teller" style agent
    print("2. Creating 'Bank Teller' agent:")
    teller_manager = StateManager(PersonalityBaseline.BANK_TELLER)
    print(teller_manager.get_emotional_context())
    print()
    
    # Create from Big Five traits
    print("3. Creating agent from Big Five traits:")
    custom_manager = create_state_manager_from_big_five(
        openness=0.5,
        conscientiousness=0.3,
        extraversion=0.2,
        agreeableness=0.6,
        neuroticism=-0.3
    )
    print(custom_manager.get_emotional_context())
    print()
    
    # Simulate event processing
    print("4. Simulating emotional events (Angry Man gets criticized):")
    angry_manager.apply_event("criticized", tick_number=100)
    print(f"State after criticism:")
    print(f"  Valence: {angry_manager.state.valence:.3f}")
    print(f"  Arousal: {angry_manager.state.arousal:.3f}")
    print(f"  Dominance: {angry_manager.state.dominance:.3f}")
    print(f"  Mood: {angry_manager.state.mood_label}")
    print(f"  Active Episodes: {len(angry_manager.state.active_episodes)}")
    print()
    
    # Simulate multiple ticks (regression and decay)
    print("5. Simulating 50 ticks of regression:")
    for tick in range(101, 151):
        angry_manager.update(tick, [])
    
    print(f"State after 50 ticks:")
    print(f"  Valence: {angry_manager.state.valence:.3f}")
    print(f"  Arousal: {angry_manager.state.arousal:.3f}")
    print(f"  Dominance: {angry_manager.state.dominance:.3f}")
    print(f"  Mood: {angry_manager.state.mood_label}")
    print(f"  Active Episodes: {len(angry_manager.state.active_episodes)}")
    print()
    
    # Test emotional inertia
    print("6. Testing Emotional Inertia:")
    calm_agent = StateManager(PersonalityBaseline(
        valence_baseline=0.0,
        arousal_baseline=0.2,  # Low arousal = stable
        dominance_baseline=0.0,
        regression_rate=0.01
    ))
    
    agitated_agent = StateManager(PersonalityBaseline(
        valence_baseline=0.0,
        arousal_baseline=0.8,  # High arousal = volatile
        dominance_baseline=0.0,
        regression_rate=0.01
    ))
    
    # Same event to both
    calm_agent.apply_event("criticized", tick_number=200)
    agitated_agent.apply_event("criticized", tick_number=200)
    
    print("Calm agent (low arousal baseline) after criticism:")
    print(f"  Valence shift: -0.2 -> {calm_agent.state.valence:.3f} (shift: {calm_agent.state.valence:.3f})")
    print()
    print("Agitated agent (high arousal baseline) after criticism:")
    print(f"  Valence shift: -0.2 -> {agitated_agent.state.valence:.3f} (shift: {agitated_agent.state.valence:.3f})")
    print("\nNote: High arousal agent experienced larger emotional shift (emotional inertia)")
