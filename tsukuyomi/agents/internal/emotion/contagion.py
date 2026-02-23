"""
Emotional Contagion System
==========================

Emotional state with contagion dynamics and group mood calculation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

from .types import EmotionalTone, EmotionalEvent

logger = logging.getLogger("EmotionalContagion")


@dataclass
class ContagionEmotionalState:
    """
    Emotional state using PAD (Pleasure-Arousal-Dominance) model with contagion.
    
    Each dimension ranges from -1.0 to 1.0:
    - Pleasure: positive/negative affect (sad vs happy)
    - Arousal: activation level (calm vs excited)
    - Dominance: control/agency (submissive vs dominant)
    """
    pleasure: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0
    
    history: List[EmotionalEvent] = field(default_factory=list)
    max_history: int = 100
    
    susceptibility: float = 0.3
    expressiveness: float = 0.5
    
    decay_rate: float = 0.001
    baseline_pleasure: float = 0.0
    baseline_arousal: float = 0.0
    baseline_dominance: float = 0.0
    
    def __post_init__(self):
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))
    
    @property
    def tone(self) -> EmotionalTone:
        """Determine categorical tone from PAD values."""
        if self.arousal > 0.5:
            if self.pleasure < -0.5:
                return EmotionalTone.ANGRY
            elif self.pleasure < -0.2:
                return EmotionalTone.ANXIOUS
            elif self.pleasure > 0.5:
                return EmotionalTone.EXCITED
            elif self.pleasure > 0.2:
                return EmotionalTone.HAPPY
        
        if self.pleasure > 0.5:
            if self.arousal < -0.3:
                return EmotionalTone.CALM
            return EmotionalTone.HAPPY
        
        if self.pleasure < -0.5:
            if self.arousal < -0.3:
                return EmotionalTone.SAD
            return EmotionalTone.ANGRY if self.dominance > 0 else EmotionalTone.FEARFUL
        
        if self.arousal < -0.5:
            if self.pleasure > 0.2:
                return EmotionalTone.CALM
            return EmotionalTone.SAD
        
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
        """Update emotional state based on event."""
        old_state = (self.pleasure, self.arousal, self.dominance)
        
        EVENT_EFFECTS = {
            "persuaded": (-0.3, 0.2, -0.2),
            "persuaded_other": (0.4, 0.1, 0.3),
            "contradicted": (-0.4, 0.5, -0.3),
            "agreed_with": (0.5, -0.1, 0.2),
            "disagreed_with": (-0.2, 0.3, 0.0),
            "praised": (0.6, 0.2, 0.3),
            "criticized": (-0.5, 0.4, -0.2),
            "ignored": (-0.3, 0.1, -0.3),
            "threatened": (-0.7, 0.8, -0.4),
            "supported": (0.4, -0.1, 0.2),
            "success": (0.6, 0.3, 0.4),
            "failure": (-0.5, 0.2, -0.3),
            "progress": (0.3, 0.1, 0.1),
            "setback": (-0.4, 0.3, -0.2),
            "insight": (0.3, 0.2, 0.2),
            "confusion": (-0.2, 0.3, -0.2),
            "certainty": (0.2, -0.1, 0.3),
            "doubt": (-0.2, 0.2, -0.2),
            "existential_challenge": (-0.3, 0.5, -0.3),
            "revelation": (-0.2, 0.6, 0.0),
            "identity_crisis": (-0.6, 0.7, -0.5),
            "neutral": (0.0, 0.0, 0.0),
        }
        
        effect = EVENT_EFFECTS.get(event_type, EVENT_EFFECTS["neutral"])
        
        self.pleasure += effect[0] * intensity
        self.arousal += effect[1] * intensity
        self.dominance += effect[2] * intensity
        
        if source_emotion:
            contagion = self._calculate_contagion(source_emotion, intensity)
            self.pleasure += contagion[0]
            self.arousal += contagion[1]
            self.dominance += contagion[2]
        
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))
        
        new_state = (self.pleasure, self.arousal, self.dominance)
        
        event = EmotionalEvent(
            tick=tick,
            event_type=event_type,
            old_state=old_state,
            new_state=new_state,
            intensity=intensity,
            source=source
        )
        self.history.append(event)
        
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
        """Calculate emotional contagion from another agent."""
        factor = self.susceptibility * source_emotion.expressiveness * intensity
        
        return (
            source_emotion.pleasure * factor * 0.5,
            source_emotion.arousal * factor * 0.7,
            source_emotion.dominance * factor * 0.3
        )
    
    def decay(self, tick: int = 0):
        """Apply decay towards baseline emotional state."""
        decay_factor = 1.0 - self.decay_rate
        
        self.pleasure = self.baseline_pleasure + (self.pleasure - self.baseline_pleasure) * decay_factor
        self.arousal = self.baseline_arousal + (self.arousal - self.baseline_arousal) * decay_factor
        self.dominance = self.baseline_dominance + (self.dominance - self.baseline_dominance) * decay_factor
    
    def apply_to_prompt(self, base_prompt: str) -> str:
        """Add emotional context to LLM prompt."""
        tone = self.tone
        
        context_parts = [
            "",
            "## CURRENT EMOTIONAL STATE",
            f"Your character is currently feeling: {tone.value.upper()}",
            ""
        ]
        
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
                for e in self.history[-20:]
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


def apply_group_contagion(
    agents: List[Dict],
    proximity_matrix: Dict[str, Dict[str, float]],
    tick: int
) -> List[str]:
    """
    Apply emotional contagion between nearby agents.
    
    Args:
        agents: List of agent dicts with 'id' and 'emotional_state'
        proximity_matrix: Dict of agent_id -> {other_agent_id -> proximity (0-1)}
        tick: Current simulation tick
    
    Returns:
        List of agent IDs that were affected
    """
    affected = []
    
    for agent in agents:
        agent_id = agent.get("id")
        agent_state = agent.get("emotional_state")
        
        if not agent_state or not isinstance(agent_state, ContagionEmotionalState):
            continue
        
        total_weight = 0.0
        weighted_pleasure = 0.0
        weighted_arousal = 0.0
        weighted_dominance = 0.0
        
        nearby = proximity_matrix.get(agent_id, {})
        
        for other_id, proximity in nearby.items():
            if proximity < 0.1:
                continue
            
            other_agent = next((a for a in agents if a.get("id") == other_id), None)
            if not other_agent:
                continue
            
            other_state = other_agent.get("emotional_state")
            if not other_state or not isinstance(other_state, ContagionEmotionalState):
                continue
            
            weight = (
                proximity *
                agent_state.susceptibility *
                other_state.expressiveness
            )
            
            weighted_pleasure += other_state.pleasure * weight
            weighted_arousal += other_state.arousal * weight
            weighted_dominance += other_state.dominance * weight
            total_weight += weight
        
        if total_weight > 0.01:
            adjustment_rate = 0.1
            
            target_pleasure = weighted_pleasure / total_weight
            target_arousal = weighted_arousal / total_weight
            target_dominance = weighted_dominance / total_weight
            
            old_p = agent_state.pleasure
            old_a = agent_state.arousal
            old_d = agent_state.dominance
            
            agent_state.pleasure += (target_pleasure - agent_state.pleasure) * adjustment_rate
            agent_state.arousal += (target_arousal - agent_state.arousal) * adjustment_rate
            agent_state.dominance += (target_dominance - agent_state.dominance) * adjustment_rate
            
            agent_state.pleasure = max(-1.0, min(1.0, agent_state.pleasure))
            agent_state.arousal = max(-1.0, min(1.0, agent_state.arousal))
            agent_state.dominance = max(-1.0, min(1.0, agent_state.dominance))
            
            if (abs(agent_state.pleasure - old_p) > 0.01 or
                abs(agent_state.arousal - old_a) > 0.01 or
                abs(agent_state.dominance - old_d) > 0.01):
                affected.append(agent_id)
                logger.debug(
                    f"Emotional contagion: {agent_id} influenced by {len(nearby)} nearby agents"
                )
    
    return affected


def calculate_group_mood(agents: List[Dict]) -> Dict:
    """Calculate the overall group mood."""
    if not agents:
        return {"pleasure": 0.0, "arousal": 0.0, "dominance": 0.0, "tone": "neutral"}
    
    valid_states = [
        a.get("emotional_state") for a in agents
        if a.get("emotional_state") and isinstance(a.get("emotional_state"), ContagionEmotionalState)
    ]
    
    if not valid_states:
        return {"pleasure": 0.0, "arousal": 0.0, "dominance": 0.0, "tone": "neutral"}
    
    avg_p = sum(s.pleasure for s in valid_states) / len(valid_states)
    avg_a = sum(s.arousal for s in valid_states) / len(valid_states)
    avg_d = sum(s.dominance for s in valid_states) / len(valid_states)
    
    temp_state = ContagionEmotionalState(pleasure=avg_p, arousal=avg_a, dominance=avg_d)
    
    return {
        "pleasure": avg_p,
        "arousal": avg_a,
        "dominance": avg_d,
        "tone": temp_state.tone.value
    }
