"""
Personality Baseline System
===========================

Big Five personality traits mapped to PAD baseline values.
Each agent has a baseline personality that their emotional state
regresses towards over time.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PersonalityBaseline:
    """
    Big Five personality traits mapped to PAD baseline values.
    
    Big Five Traits:
    - Openness: Curious, creative vs. cautious, conservative
    - Conscientiousness: Organized, disciplined vs. spontaneous, flexible
    - Extraversion: Outgoing, energetic vs. solitary, reserved
    - Agreeableness: Friendly, compassionate vs. competitive, challenging
    - Neuroticism: Sensitive, nervous vs. secure, confident
    """
    valence_baseline: float
    arousal_baseline: float
    dominance_baseline: float
    regression_rate: float = 0.01
    openness: float = 0.0
    conscientiousness: float = 0.0
    extraversion: float = 0.0
    agreeableness: float = 0.0
    neuroticism: float = 0.0
    
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
        valence_baseline = (agreeableness * 0.3) - (neuroticism * 0.3)
        
        arousal_baseline = 0.5 + (extraversion * 0.25) + (neuroticism * 0.2)
        arousal_baseline = max(0.0, min(1.0, arousal_baseline))
        
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


ANGRY_MAN = PersonalityBaseline(
    valence_baseline=-0.3,
    arousal_baseline=0.7,
    dominance_baseline=0.6,
    regression_rate=0.005,
    openness=-0.2,
    conscientiousness=0.3,
    extraversion=0.6,
    agreeableness=-0.5,
    neuroticism=0.7
)

BANK_TELLER = PersonalityBaseline(
    valence_baseline=0.1,
    arousal_baseline=0.3,
    dominance_baseline=-0.4,
    regression_rate=0.02,
    openness=0.0,
    conscientiousness=0.7,
    extraversion=-0.3,
    agreeableness=0.6,
    neuroticism=0.2
)

STOCKBROKER = PersonalityBaseline(
    valence_baseline=0.2,
    arousal_baseline=0.5,
    dominance_baseline=0.3,
    regression_rate=0.015,
    openness=0.3,
    conscientiousness=0.6,
    extraversion=0.4,
    agreeableness=-0.1,
    neuroticism=0.1
)

ANALYTICAL_JUROR = PersonalityBaseline(
    valence_baseline=0.0,
    arousal_baseline=0.4,
    dominance_baseline=0.1,
    regression_rate=0.01,
    openness=0.5,
    conscientiousness=0.8,
    extraversion=-0.2,
    agreeableness=0.3,
    neuroticism=-0.2
)

EMPATHETIC_JUROR = PersonalityBaseline(
    valence_baseline=0.3,
    arousal_baseline=0.4,
    dominance_baseline=-0.1,
    regression_rate=0.015,
    openness=0.8,
    conscientiousness=0.5,
    extraversion=0.2,
    agreeableness=0.8,
    neuroticism=0.0
)

PRESET_PROFILES = {
    'angry_man': ANGRY_MAN,
    'bank_teller': BANK_TELLER,
    'stockbroker': STOCKBROKER,
    'analytical_juror': ANALYTICAL_JUROR,
    'empathetic_juror': EMPATHETIC_JUROR,
}
