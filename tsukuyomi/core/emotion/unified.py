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
            from .perception_pipeline import PerceptChannel
            
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


# --- FROM emotional_state.py ---

"""
Emotional State System
======================

PAD (Pleasure-Arousal-Dominance) emotional model for agents.
Provides categorical tone detection, emotional updates, and prompt integration.

This module is generic and applies to ANY social simulation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import math
import logging

logger = logging.getLogger("EmotionalState")


class EmotionalTone(Enum):
    """Categorical emotional tones for LLM prompts."""
    NEUTRAL = "neutral"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SAD = "sad"
    HAPPY = "happy"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    EXCITED = "excited"
    CALM = "calm"
    ANXIOUS = "anxious"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"


@dataclass
class EmotionalEvent:
    """Record of an emotional event."""
    tick: int
    event_type: str
    old_state: Tuple[float, float, float]
    new_state: Tuple[float, float, float]
    intensity: float
    source: Optional[str] = None


@dataclass
class ContagionEmotionalState:
    """
    Emotional state using PAD (Pleasure-Arousal-Dominance) model.
    
    Each dimension ranges from -1.0 to 1.0:
    - Pleasure: positive/negative affect (sad vs happy)
    - Arousal: activation level (calm vs excited)
    - Dominance: control/agency (submissive vs dominant)
    
    This is a GENERAL system applicable to any social simulation:
    - Jury: affects deliberation tone and decisiveness
    - Marketplace: affects negotiation behavior
    - Politics: affects debate style and coalition building
    - Social: affects conversation dynamics
    """
    pleasure: float = 0.0    # -1 to 1
    arousal: float = 0.0     # -1 to 1
    dominance: float = 0.0   # -1 to 1
    
    # Tracking for dynamics
    history: List[EmotionalEvent] = field(default_factory=list)
    max_history: int = 100
    
    # Emotional contagion parameters
    susceptibility: float = 0.3  # How easily affected by others' emotions
    expressiveness: float = 0.5  # How much emotion shows in behavior
    
    # Decay parameters
    decay_rate: float = 0.001  # How fast emotions return to baseline
    baseline_pleasure: float = 0.0
    baseline_arousal: float = 0.0
    baseline_dominance: float = 0.0
    
    def __post_init__(self):
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))
    
    @property
    def tone(self) -> EmotionalTone:
        """
        Determine categorical tone from PAD values.
        
        Uses a priority-based classification system.
        """
        # High arousal states (priority)
        if self.arousal > 0.5:
            if self.pleasure < -0.5:
                return EmotionalTone.ANGRY
            elif self.pleasure < -0.2:
                return EmotionalTone.ANXIOUS
            elif self.pleasure > 0.5:
                return EmotionalTone.EXCITED
            elif self.pleasure > 0.2:
                return EmotionalTone.HAPPY
        
        # High pleasure states
        if self.pleasure > 0.5:
            if self.arousal < -0.3:
                return EmotionalTone.CALM
            return EmotionalTone.HAPPY
        
        # Low pleasure states
        if self.pleasure < -0.5:
            if self.arousal < -0.3:
                return EmotionalTone.SAD
            return EmotionalTone.ANGRY if self.dominance > 0 else EmotionalTone.FEARFUL
        
        # Low arousal states
        if self.arousal < -0.5:
            if self.pleasure > 0.2:
                return EmotionalTone.CALM
            return EmotionalTone.SAD
        
        # Dominance-based states
        if self.dominance > 0.5:
            return EmotionalTone.CONFIDENT
        if self.dominance < -0.5:
            return EmotionalTone.UNCERTAIN
        
        return EmotionalTone.NEUTRAL
    
    def update(
        self,
        event_type: str,
        intensity: float = 0.1,
        tick: int = 0,
        source: Optional[str] = None,
        source_emotion: Optional['ContagionEmotionalState'] = None
    ) -> EmotionalEvent:
        """
        Update emotional state based on event.
        
        Args:
            event_type: Type of emotional event (see EVENT_EFFECTS)
            intensity: How strong the event was (0.0-1.0)
            tick: Current simulation tick
            source: Who/what caused the event
            source_emotion: Emotional state of source (for contagion)
        
        Returns:
            EmotionalEvent record
        """
        old_state = (self.pleasure, self.arousal, self.dominance)
        
        # Define event effects: (pleasure_delta, arousal_delta, dominance_delta)
        EVENT_EFFECTS = {
            # Persuasion events
            "persuaded": (-0.3, 0.2, -0.2),
            "persuaded_other": (0.4, 0.1, 0.3),
            "contradicted": (-0.4, 0.5, -0.3),
            "agreed_with": (0.5, -0.1, 0.2),
            "disagreed_with": (-0.2, 0.3, 0.0),
            
            # Social events
            "praised": (0.6, 0.2, 0.3),
            "criticized": (-0.5, 0.4, -0.2),
            "ignored": (-0.3, 0.1, -0.3),
            "threatened": (-0.7, 0.8, -0.4),
            "supported": (0.4, -0.1, 0.2),
            
            # Achievement events
            "success": (0.6, 0.3, 0.4),
            "failure": (-0.5, 0.2, -0.3),
            "progress": (0.3, 0.1, 0.1),
            "setback": (-0.4, 0.3, -0.2),
            
            # Cognitive events
            "insight": (0.3, 0.2, 0.2),
            "confusion": (-0.2, 0.3, -0.2),
            "certainty": (0.2, -0.1, 0.3),
            "doubt": (-0.2, 0.2, -0.2),
            
            # Existential events (for Oracle-type agents)
            "existential_challenge": (-0.3, 0.5, -0.3),
            "revelation": (-0.2, 0.6, 0.0),
            "identity_crisis": (-0.6, 0.7, -0.5),
            
            # Default
            "neutral": (0.0, 0.0, 0.0),
        }
        
        # Get effect for event type
        effect = EVENT_EFFECTS.get(event_type, EVENT_EFFECTS["neutral"])
        
        # Apply effect with intensity
        self.pleasure += effect[0] * intensity
        self.arousal += effect[1] * intensity
        self.dominance += effect[2] * intensity
        
        # Apply emotional contagion if source emotion provided
        if source_emotion:
            contagion = self._calculate_contagion(source_emotion, intensity)
            self.pleasure += contagion[0]
            self.arousal += contagion[1]
            self.dominance += contagion[2]
        
        # Clamp values
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))
        
        new_state = (self.pleasure, self.arousal, self.dominance)
        
        # Record event
        event = EmotionalEvent(
            tick=tick,
            event_type=event_type,
            old_state=old_state,
            new_state=new_state,
            intensity=intensity,
            source=source
        )
        self.history.append(event)
        
        # Trim history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        logger.debug(
            f"Emotional update: {event_type} @ {intensity:.2f} -> "
            f"P={self.pleasure:.2f} A={self.arousal:.2f} D={self.dominance:.2f}"
        )
        
        return event
    
    def _calculate_contagion(
        self,
        source_emotion: 'ContagionEmotionalState',
        intensity: float
    ) -> Tuple[float, float, float]:
        """
        Calculate emotional contagion from another agent.
        
        Higher susceptibility = more contagion.
        Higher expressiveness of source = more contagion.
        """
        factor = self.susceptibility * source_emotion.expressiveness * intensity
        
        return (
            source_emotion.pleasure * factor * 0.5,
            source_emotion.arousal * factor * 0.7,  # Arousal is more contagious
            source_emotion.dominance * factor * 0.3
        )
    
    def decay(self, tick: int = 0):
        """
        Apply decay towards baseline emotional state.
        
        Emotions naturally drift back to baseline over time.
        """
        # Exponential decay towards baseline
        decay_factor = 1.0 - self.decay_rate
        
        self.pleasure = self.baseline_pleasure + (self.pleasure - self.baseline_pleasure) * decay_factor
        self.arousal = self.baseline_arousal + (self.arousal - self.baseline_arousal) * decay_factor
        self.dominance = self.baseline_dominance + (self.dominance - self.baseline_dominance) * decay_factor
    
    def apply_to_prompt(self, base_prompt: str) -> str:
        """
        Add emotional context to LLM prompt.
        
        This injects emotional state into the prompt to influence
        the agent's response generation.
        
        Args:
            base_prompt: The base prompt without emotional context
        
        Returns:
            Prompt with emotional guidelines appended
        """
        tone = self.tone
        
        # Build emotional context
        context_parts = [
            "",
            "## CURRENT EMOTIONAL STATE",
            f"Your character is currently feeling: {tone.value.upper()}",
            ""
        ]
        
        # Add dimensional context if notable
        if self.arousal > 0.5:
            context_parts.append("- You are highly activated/tense. Your responses may be more brief and intense.")
        elif self.arousal < -0.5:
            context_parts.append("- You are calm/relaxed. Take your time with responses.")
        
        if self.pleasure > 0.5:
            context_parts.append("- You are in a positive mood. You may be more agreeable and optimistic.")
        elif self.pleasure < -0.5:
            context_parts.append("- You are in a negative mood. You may be more critical and skeptical.")
        
        if self.dominance > 0.5:
            context_parts.append("- You feel assertive and in control. You may take charge of the conversation.")
        elif self.dominance < -0.5:
            context_parts.append("- You feel uncertain and cautious. You may defer to others.")
        
        # Add specific tone guidance
        tone_guidance = self._get_tone_guidance(tone)
        if tone_guidance:
            context_parts.append("")
            context_parts.append(tone_guidance)
        
        return base_prompt + "\n".join(context_parts)
    
    def _get_tone_guidance(self, tone: EmotionalTone) -> str:
        """Get specific guidance for an emotional tone."""
        guidance = {
            EmotionalTone.ANGRY: "- Express frustration. Use shorter, more direct language. Don't hedge.",
            EmotionalTone.ANXIOUS: "- Show uncertainty. Ask questions. Consider multiple possibilities.",
            EmotionalTone.EXCITED: "- Show enthusiasm. Use energetic language. Be expressive.",
            EmotionalTone.CALM: "- Use measured, thoughtful language. Consider before responding.",
            EmotionalTone.SAD: "- Be subdued. Express disappointment or concern.",
            EmotionalTone.HAPPY: "- Be warm and approachable. Show optimism.",
            EmotionalTone.CONFIDENT: "- State positions clearly. Make definitive statements.",
            EmotionalTone.UNCERTAIN: "- Express doubt. Ask for others' opinions.",
            EmotionalTone.FEARFUL: "- Be cautious. Express concern about risks.",
            EmotionalTone.DISGUSTED: "- Show disapproval. Be critical of the source.",
            EmotionalTone.SURPRISED: "- React strongly. Express unexpectedness.",
        }
        return guidance.get(tone, "")
    
    def to_dict(self) -> Dict:
        """Serialize emotional state."""
        return {
            "pleasure": self.pleasure,
            "arousal": self.arousal,
            "dominance": self.dominance,
            "susceptibility": self.susceptibility,
            "expressiveness": self.expressiveness,
            "baseline": {
                "pleasure": self.baseline_pleasure,
                "arousal": self.baseline_arousal,
                "dominance": self.baseline_dominance
            },
            "history": [
                {
                    "tick": e.tick,
                    "event_type": e.event_type,
                    "old_state": e.old_state,
                    "new_state": e.new_state,
                    "intensity": e.intensity,
                    "source": e.source
                }
                for e in self.history[-20:]  # Last 20 events
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ContagionEmotionalState':
        """Deserialize emotional state."""
        state = cls(
            pleasure=data.get("pleasure", 0.0),
            arousal=data.get("arousal", 0.0),
            dominance=data.get("dominance", 0.0),
            susceptibility=data.get("susceptibility", 0.3),
            expressiveness=data.get("expressiveness", 0.5)
        )
        
        baseline = data.get("baseline", {})
        state.baseline_pleasure = baseline.get("pleasure", 0.0)
        state.baseline_arousal = baseline.get("arousal", 0.0)
        state.baseline_dominance = baseline.get("dominance", 0.0)
        
        return state
    
    def summary(self) -> str:
        """Get a human-readable summary."""
        return (
            f"ContagionEmotionalState(P={self.pleasure:.2f}, A={self.arousal:.2f}, "
            f"D={self.dominance:.2f}, tone={self.tone.value})"
        )


# ========================
# Emotional Contagion Functions
# ========================

def apply_group_contagion(
    agents: List[Dict],
    proximity_matrix: Dict[str, Dict[str, float]],
    tick: int
) -> List[str]:
    """
    Apply emotional contagion between nearby agents.
    
    Agents emotionally "catch" states from those they're near.
    Higher proximity = stronger contagion.
    
    This is a GENERAL social dynamics function applicable to any simulation.
    
    Args:
        agents: List of agent dicts with 'id' and 'emotional_state' (EmotionalState)
        proximity_matrix: Dict of agent_id -> {other_agent_id -> proximity (0-1)}
        tick: Current simulation tick
    
    Returns:
        List of agent IDs that were affected
    """
    affected = []
    
    for agent in agents:
        agent_id = agent.get("id")
        agent_state = agent.get("emotional_state")
        
        if not agent_state or not isinstance(agent_state, EmotionalState):
            continue
        
        total_weight = 0.0
        weighted_pleasure = 0.0
        weighted_arousal = 0.0
        weighted_dominance = 0.0
        
        # Sum emotional influence from nearby agents
        nearby = proximity_matrix.get(agent_id, {})
        
        for other_id, proximity in nearby.items():
            if proximity < 0.1:  # Skip distant agents
                continue
            
            # Find other agent's emotional state
            other_agent = next((a for a in agents if a.get("id") == other_id), None)
            if not other_agent:
                continue
            
            other_state = other_agent.get("emotional_state")
            if not other_state or not isinstance(other_state, EmotionalState):
                continue
            
            # Weight by proximity and susceptibility
            # Also weight by other's expressiveness
            weight = (
                proximity *
                agent_state.susceptibility *
                other_state.expressiveness
            )
            
            weighted_pleasure += other_state.pleasure * weight
            weighted_arousal += other_state.arousal * weight
            weighted_dominance += other_state.dominance * weight
            total_weight += weight
        
        # Apply averaged influence
        if total_weight > 0.01:
            # Gradual adjustment (not instant)
            adjustment_rate = 0.1
            
            target_pleasure = weighted_pleasure / total_weight
            target_arousal = weighted_arousal / total_weight
            target_dominance = weighted_dominance / total_weight
            
            # Move towards weighted average
            old_p = agent_state.pleasure
            old_a = agent_state.arousal
            old_d = agent_state.dominance
            
            agent_state.pleasure += (target_pleasure - agent_state.pleasure) * adjustment_rate
            agent_state.arousal += (target_arousal - agent_state.arousal) * adjustment_rate
            agent_state.dominance += (target_dominance - agent_state.dominance) * adjustment_rate
            
            # Clamp
            agent_state.pleasure = max(-1.0, min(1.0, agent_state.pleasure))
            agent_state.arousal = max(-1.0, min(1.0, agent_state.arousal))
            agent_state.dominance = max(-1.0, min(1.0, agent_state.dominance))
            
            # Check if meaningful change
            if (abs(agent_state.pleasure - old_p) > 0.01 or
                abs(agent_state.arousal - old_a) > 0.01 or
                abs(agent_state.dominance - old_d) > 0.01):
                affected.append(agent_id)
                logger.debug(
                    f"Emotional contagion: {agent_id} influenced by {len(nearby)} nearby agents"
                )
    
    return affected


def calculate_group_mood(agents: List[Dict]) -> Dict:
    """
    Calculate the overall group mood.
    
    Returns average PAD values and dominant tone.
    """
    if not agents:
        return {"pleasure": 0.0, "arousal": 0.0, "dominance": 0.0, "tone": "neutral"}
    
    valid_states = [
        a.get("emotional_state") for a in agents
        if a.get("emotional_state") and isinstance(a.get("emotional_state"), EmotionalState)
    ]
    
    if not valid_states:
        return {"pleasure": 0.0, "arousal": 0.0, "dominance": 0.0, "tone": "neutral"}
    
    avg_p = sum(s.pleasure for s in valid_states) / len(valid_states)
    avg_a = sum(s.arousal for s in valid_states) / len(valid_states)
    avg_d = sum(s.dominance for s in valid_states) / len(valid_states)
    
    # Create temporary state to get tone
    temp_state = ContagionEmotionalState(pleasure=avg_p, arousal=avg_a, dominance=avg_d)
    
    return {
        "pleasure": avg_p,
        "arousal": avg_a,
        "dominance": avg_d,
        "tone": temp_state.tone.value
    } 
