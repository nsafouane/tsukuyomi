"""
Emotional Impact Rules
======================

Maps events to PAD deltas for emotional processing.
"""

from typing import Optional, Dict, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .types import EmotionalImpact

EVENT_IMPACTS: Dict[str, tuple] = {
    "criticized": (-0.2, +0.15, -0.1, "anger"),
    "praised": (+0.2, +0.1, +0.05, "joy"),
    "agreed_with": (+0.15, +0.05, +0.1, "content"),
    "contradicted": (-0.15, +0.1, -0.05, "frustration"),
    "ignored": (-0.1, +0.1, -0.15, "sadness"),
    "interrupted": (-0.1, +0.2, -0.1, "annoyance"),
    "contradicted_by_evidence": (-0.25, +0.2, -0.2, "surprise"),
    "evidence_supports_belief": (+0.15, +0.1, +0.1, "satisfaction"),
    "realized_mistake": (-0.2, +0.3, -0.15, "embarrassment"),
    "physical_threat": (-0.5, +0.8, -0.3, "fear"),
    "witnessed_violence": (-0.3, +0.6, -0.2, "fear"),
    "injured": (-0.4, +0.7, -0.25, "pain"),
    "succeeded": (+0.25, +0.15, +0.2, "joy"),
    "failed": (-0.2, +0.2, -0.1, "frustration"),
    "discovered_something_new": (+0.1, +0.15, +0.05, "curiosity"),
    "made_connection": (+0.15, +0.1, +0.15, "insight"),
    "recalled_painful_memory": (-0.15, +0.1, 0.0, "sadness"),
    "recalled_happy_memory": (+0.1, +0.05, 0.0, "nostalgia"),
    "persuaded": (-0.3, 0.2, -0.2, "uncertainty"),
    "persuaded_other": (0.4, 0.1, 0.3, "confidence"),
    "threatened": (-0.7, 0.8, -0.4, "fear"),
    "supported": (0.4, -0.1, 0.2, "relief"),
    "success": (0.6, 0.3, 0.4, "pride"),
    "failure": (-0.5, 0.2, -0.3, "shame"),
    "progress": (0.3, 0.1, 0.1, "optimism"),
    "setback": (-0.4, 0.3, -0.2, "frustration"),
    "insight": (0.3, 0.2, 0.2, "clarity"),
    "confusion": (-0.2, 0.3, -0.2, "uncertainty"),
    "certainty": (0.2, -0.1, 0.3, "confidence"),
    "doubt": (-0.2, 0.2, -0.2, "anxiety"),
    "existential_challenge": (-0.3, 0.5, -0.3, "crisis"),
    "revelation": (-0.2, 0.6, 0.0, "awe"),
    "identity_crisis": (-0.6, 0.7, -0.5, "distress"),
}


def get_impact(event_type: str) -> Optional[tuple]:
    """Get emotional impact tuple for an event type."""
    return EVENT_IMPACTS.get(event_type)


def create_emotional_impact(event_type: str):
    """Create an EmotionalImpact dataclass from event type."""
    from .types import EmotionalImpact
    
    impact_data = EVENT_IMPACTS.get(event_type)
    if impact_data:
        return EmotionalImpact(
            valence_delta=impact_data[0],
            arousal_delta=impact_data[1],
            dominance_delta=impact_data[2],
            emotion_label=impact_data[3]
        )
    return None


class EmotionalImpactRules:
    """Maps events to PAD deltas."""
    
    IMPACTS = {k: create_emotional_impact(k) for k in EVENT_IMPACTS.keys()}
    
    @classmethod
    def get_impact(cls, event_type: str):
        """Get emotional impact for an event type."""
        return cls.IMPACTS.get(event_type)
    
    @classmethod
    def classify_percept_impact(cls, percept) -> Optional['EmotionalImpact']:
        """Classify the emotional impact of a percept."""
        try:
            from tsukuyomi.agents.cognitive.perception_channels import PerceptChannel
            
            if hasattr(percept, 'channel'):
                if percept.channel == PerceptChannel.SPEECH:
                    if hasattr(percept, 'speech'):
                        content = percept.speech.content.lower()
                        
                        negative_words = ['hate', 'stupid', 'wrong', 'bad', 'terrible',
                                         'idiot', 'fool', 'never', 'worst']
                        positive_words = ['good', 'great', 'right', 'excellent',
                                         'smart', 'love', 'best', 'wonderful']
                        
                        neg_score = sum(1 for word in negative_words if word in content)
                        pos_score = sum(1 for word in positive_words if word in content)
                        
                        is_direct = hasattr(percept.speech, 'is_direct_address') and percept.speech.is_direct_address
                        
                        if neg_score > pos_score:
                            intensity = min(0.5, neg_score * 0.1)
                            if is_direct:
                                intensity *= 1.5
                            from .types import EmotionalImpact
                            return EmotionalImpact(
                                valence_delta=-intensity,
                                arousal_delta=+intensity * 0.8,
                                dominance_delta=-intensity * 0.5,
                                emotion_label="anger" if neg_score > 2 else "annoyance"
                            )
                        elif pos_score > neg_score:
                            intensity = min(0.4, pos_score * 0.1)
                            from .types import EmotionalImpact
                            return EmotionalImpact(
                                valence_delta=+intensity,
                                arousal_delta=+intensity * 0.5,
                                dominance_delta=+intensity * 0.3,
                                emotion_label="joy"
                            )
                
                elif percept.channel == PerceptChannel.EVENT:
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
            return None
