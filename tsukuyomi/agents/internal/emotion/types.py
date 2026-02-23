"""
Emotional Types and Data Structures
====================================

Core data types for the PAD (Pleasure-Arousal-Dominance) emotional model.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum


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
class EmotionalState:
    """
    Current emotional state of an agent based on the PAD model.
    
    PAD Dimensions:
    - Valence (Pleasure): -1.0 (distress) to +1.0 (joy)
    - Arousal: 0.0 (calm) to 1.0 (agitated/excited)
    - Dominance: -1.0 (submissive) to +1.0 (dominant)
    """
    valence: float = 0.0
    arousal: float = 0.5
    dominance: float = 0.0
    mood_label: str = MoodLabel.CALM.value
    active_episodes: List['EmotionalEpisode'] = field(default_factory=list)


@dataclass
class EmotionalEpisode:
    """
    A temporary emotional spike triggered by a specific event.
    
    Episodes represent intense emotional reactions that decay over time.
    """
    trigger_event_id: str
    emotion_type: str
    intensity: float
    onset_tick: int
    decay_rate: float


@dataclass
class EmotionalImpact:
    """PAD delta representing an emotional impact from an event."""
    valence_delta: float
    arousal_delta: float
    dominance_delta: float
    emotion_label: str


@dataclass
class EmotionalEvent:
    """Record of an emotional event."""
    tick: int
    event_type: str
    old_state: Tuple[float, float, float]
    new_state: Tuple[float, float, float]
    intensity: float
    source: Optional[str] = None
