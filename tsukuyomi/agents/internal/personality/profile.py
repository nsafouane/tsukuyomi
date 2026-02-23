"""
profile.py - PersonalityProfile Dataclass with Big Five Traits

This module defines the complete personality profile for Tsukuyomi agents,
including Big Five personality traits, behavioral patterns, core beliefs,
and voice characteristics.

Phase 14: Personality Integrity System
- 14.1: Trait Definition Schema
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class VocabularyLevel(Enum):
    """Vocabulary complexity levels for voice enforcement."""
    SIMPLE = "simple"
    EDUCATED = "educated"
    FORMAL = "formal"


@dataclass
class PersonalityProfile:
    """
    Complete personality definition for an agent.
    
    This dataclass encapsulates all personality-related traits and characteristics
    that define an agent's stable identity. These traits are designed to be
    IMMUTABLE during normal operation - they represent the core of who the agent is.
    
    Big Five Personality Traits (OCEAN):
    - Openness: Curiosity, creativity vs. caution, conservatism
    - Conscientiousness: Organization, discipline vs. spontaneity, flexibility
    - Extraversion: Sociability, energy vs. solitude, reserve
    - Agreeableness: Friendliness, cooperation vs. competition, challenging
    - Neuroticism: Emotional sensitivity vs. stability
    
    All trait values range from -1.0 to 1.0:
    - Negative values indicate the lower end of the trait spectrum
    - Positive values indicate the higher end
    - 0.0 represents a neutral/balanced position
    
    Attributes:
        name: Agent's name (e.g., "Arthur Miller")
        age: Agent's age in years
        role: Agent's role in the scenario (e.g., "Juror #3")
        
        openness: Big Five Openness (-1.0 traditional to 1.0 curious)
        conscientiousness: Big Five Conscientiousness (-1.0 spontaneous to 1.0 disciplined)
        extraversion: Big Five Extraversion (-1.0 introverted to 1.0 outgoing)
        agreeableness: Big Five Agreeableness (-1.0 competitive to 1.0 cooperative)
        neuroticism: Big Five Neuroticism (-1.0 stable to 1.0 sensitive)
        
        speaking_style: Description of speaking patterns
        decision_style: Description of decision-making approach
        conflict_style: Description of conflict handling
        
        core_values: List of fundamental values the agent holds
        biases: List of cognitive/social biases the agent has
        
        backstory: Life history and background
        motivation: What drives the agent
        fear: What the agent is afraid of
        
        vocabulary_level: Complexity of language used
        common_phrases: Signature phrases the agent uses
        speech_quirks: Unique speech patterns
    """
    
    # === Identity ===
    name: str
    age: int
    role: str
    
    # === Core Traits (Big Five) - STABLE ===
    openness: float = 0.0           # -1.0 (traditional) to 1.0 (curious)
    conscientiousness: float = 0.0  # -1.0 (spontaneous) to 1.0 (disciplined)
    extraversion: float = 0.0       # -1.0 (introverted) to 1.0 (outgoing)
    agreeableness: float = 0.0      # -1.0 (competitive) to 1.0 (cooperative)
    neuroticism: float = 0.0        # -1.0 (stable) to 1.0 (sensitive)
    
    # === Behavioral Patterns - STABLE ===
    speaking_style: str = "neutral, measured"
    decision_style: str = "balanced, thoughtful"
    conflict_style: str = "diplomatic, compromising"
    
    # === Core Beliefs - STABLE ===
    core_values: List[str] = field(default_factory=list)
    biases: List[str] = field(default_factory=list)
    
    # === Backstory - CONTEXT ===
    backstory: str = ""
    motivation: str = ""
    fear: str = ""
    
    # === Voice - ENFORCED ===
    vocabulary_level: str = "educated"
    common_phrases: List[str] = field(default_factory=list)
    speech_quirks: str = ""
    
    def __post_init__(self):
        """Validate trait values are within bounds after initialization."""
        self._validate_traits()
        self._validate_vocabulary_level()
    
    def _validate_traits(self) -> None:
        """Ensure all Big Five traits are within valid range [-1.0, 1.0]."""
        traits = {
            'openness': self.openness,
            'conscientiousness': self.conscientiousness,
            'extraversion': self.extraversion,
            'agreeableness': self.agreeableness,
            'neuroticism': self.neuroticism
        }
        
        for trait_name, value in traits.items():
            if not -1.0 <= value <= 1.0:
                raise ValueError(
                    f"Invalid {trait_name} value {value}. "
                    f"Must be between -1.0 and 1.0"
                )
    
    def _validate_vocabulary_level(self) -> None:
        """Ensure vocabulary level is a valid option."""
        valid_levels = {v.value for v in VocabularyLevel}
        if self.vocabulary_level not in valid_levels:
            raise ValueError(
                f"Invalid vocabulary_level '{self.vocabulary_level}'. "
                f"Must be one of: {valid_levels}"
            )
    
    def get_trait_label(self, trait_name: str) -> str:
        """
        Get a human-readable label for a trait value.
        
        Args:
            trait_name: Name of the trait (e.g., 'openness')
        
        Returns:
            Human-readable trait description
        """
        trait_value = getattr(self, trait_name, 0.0)
        
        trait_labels = {
            'openness': ('traditional', 'curious'),
            'conscientiousness': ('spontaneous', 'disciplined'),
            'extraversion': ('introverted', 'outgoing'),
            'agreeableness': ('competitive', 'cooperative'),
            'neuroticism': ('stable', 'sensitive')
        }
        
        if trait_name not in trait_labels:
            return 'neutral'
        
        low_label, high_label = trait_labels[trait_name]
        
        if trait_value < -0.3:
            return low_label
        elif trait_value > 0.3:
            return high_label
        else:
            return f'moderately {high_label}'
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the profile to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the profile
        """
        return {
            'name': self.name,
            'age': self.age,
            'role': self.role,
            'openness': self.openness,
            'conscientiousness': self.conscientiousness,
            'extraversion': self.extraversion,
            'agreeableness': self.agreeableness,
            'neuroticism': self.neuroticism,
            'speaking_style': self.speaking_style,
            'decision_style': self.decision_style,
            'conflict_style': self.conflict_style,
            'core_values': self.core_values.copy(),
            'biases': self.biases.copy(),
            'backstory': self.backstory,
            'motivation': self.motivation,
            'fear': self.fear,
            'vocabulary_level': self.vocabulary_level,
            'common_phrases': self.common_phrases.copy(),
            'speech_quirks': self.speech_quirks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersonalityProfile':
        """
        Create a PersonalityProfile from a dictionary.
        
        Args:
            data: Dictionary containing profile data
        
        Returns:
            PersonalityProfile instance
        """
        return cls(
            name=data['name'],
            age=data['age'],
            role=data['role'],
            openness=data.get('openness', 0.0),
            conscientiousness=data.get('conscientiousness', 0.0),
            extraversion=data.get('extraversion', 0.0),
            agreeableness=data.get('agreeableness', 0.0),
            neuroticism=data.get('neuroticism', 0.0),
            speaking_style=data.get('speaking_style', 'neutral, measured'),
            decision_style=data.get('decision_style', 'balanced, thoughtful'),
            conflict_style=data.get('conflict_style', 'diplomatic, compromising'),
            core_values=data.get('core_values', []),
            biases=data.get('biases', []),
            backstory=data.get('backstory', ''),
            motivation=data.get('motivation', ''),
            fear=data.get('fear', ''),
            vocabulary_level=data.get('vocabulary_level', 'educated'),
            common_phrases=data.get('common_phrases', []),
            speech_quirks=data.get('speech_quirks', '')
        )


def build_personality_context(profile: PersonalityProfile) -> str:
    """
    Generate personality enforcement section for LLM prompt.
    
    This function creates a comprehensive personality context string that
    should be injected into the LLM prompt to enforce consistent personality
    behavior. The context includes all trait definitions, behavioral patterns,
    and critical enforcement instructions.
    
    Args:
        profile: The PersonalityProfile to generate context for
    
    Returns:
        Formatted string for LLM prompt injection
    """
    # Format core values and biases
    core_values_str = ", ".join(profile.core_values) if profile.core_values else "none specified"
    biases_str = ", ".join(profile.biases) if profile.biases else "none specified"
    phrases_str = ", ".join(profile.common_phrases) if profile.common_phrases else "none"
    
    return f"""
PERSONALITY (DO NOT DEVIATE):
- Name: {profile.name}
- Role: {profile.role}
- Age: {profile.age}

CORE TRAITS (immutable):
- Openness: {profile.get_trait_label('openness')} ({profile.openness:.1f})
- Conscientiousness: {profile.get_trait_label('conscientiousness')} ({profile.conscientiousness:.1f})
- Extraversion: {profile.get_trait_label('extraversion')} ({profile.extraversion:.1f})
- Agreeableness: {profile.get_trait_label('agreeableness')} ({profile.agreeableness:.1f})
- Neuroticism: {profile.get_trait_label('neuroticism')} ({profile.neuroticism:.1f})

BEHAVIORAL PATTERNS:
- Speaking: {profile.speaking_style}
- Decisions: {profile.decision_style}
- Conflict: {profile.conflict_style}

CORE VALUES: {core_values_str}
BIASES: {biases_str}

MOTIVATION: {profile.motivation or "Not specified"}
FEAR: {profile.fear or "Not specified"}

VOICE ENFORCEMENT:
- Vocabulary: {profile.vocabulary_level}
- Signature phrases: {phrases_str}
- Quirks: {profile.speech_quirks or "none"}

CRITICAL: Your responses MUST reflect these traits consistently. 
If you're "angry and stubborn", stay angry and stubborn.
If you "interrupt often", interrupt in dialogue.
If you have "simple vocabulary", don't use complex words.
""".strip()


# === Pre-defined Sample Profiles ===

# Profile 1: "The Angry Man" (based on Juror #3 from 12 Angry Men)
ANGRY_MAN_PROFILE = PersonalityProfile(
    name="Arthur Miller",
    age=52,
    role="Juror #3",
    
    # Big Five: Angry, stubborn, emotionally volatile
    openness=-0.2,           # Traditional, resistant to new ideas
    conscientiousness=0.3,   # Somewhat disciplined
    extraversion=0.6,        # Outgoing, vocal
    agreeableness=-0.5,      # Competitive, argumentative
    neuroticism=0.7,         # Emotionally sensitive/volatile
    
    speaking_style="aggressive, interrupts often, raises voice",
    decision_style="impulsive, emotional, stubborn",
    conflict_style="aggressive, confrontational, refuses to back down",
    
    core_values=["order", "justice", "punishment", "personal responsibility"],
    biases=["distrusts youth", "values authority", "projects personal trauma"],
    
    backstory=(
        "High school teacher for 25 years. Estranged from his own son who ran away "
        "after an argument. Sees the defendant as a representation of his own son's "
        "failings and disrespect for authority."
    ),
    motivation="Prove the defendant is guilty - validate his own worldview about youth and authority",
    fear="Admitting he was wrong about his son, showing vulnerability",
    
    vocabulary_level="educated",
    common_phrases=["Listen to me!", "This is ridiculous!", "The facts are clear!"],
    speech_quirks="Often begins sentences with 'I tell you' and makes emphatic gestures"
)

# Profile 2: The Analytical Juror (based on Juror #8 from 12 Angry Men)
ANALYTICAL_JUROR_PROFILE = PersonalityProfile(
    name="Davis",
    age=38,
    role="Juror #8",
    
    # Big Five: Calm, thoughtful, open-minded
    openness=0.7,            # Very open to new perspectives
    conscientiousness=0.8,   # Highly disciplined, methodical
    extraversion=-0.2,       # Somewhat introverted, measured
    agreeableness=0.4,       # Cooperative but principled
    neuroticism=-0.3,        # Emotionally stable
    
    speaking_style="calm, measured, asks questions rather than making statements",
    decision_style="deliberate, evidence-based, methodical",
    conflict_style="diplomatic, uses logic and questions to persuade",
    
    core_values=["justice", "truth", "fairness", "due process"],
    biases=["skeptical of certainty", "values doubt", "trusts systems"],
    
    backstory=(
        "Architect. Believes in the weight of a life-and-death decision. "
        "Has no personal stake but feels a moral obligation to ensure fairness."
    ),
    motivation="Ensure justice is done correctly - no innocent person should die",
    fear="Sending an innocent person to death because of haste or prejudice",
    
    vocabulary_level="educated",
    common_phrases=["I'm just asking...", "What if...", "Suppose we..."],
    speech_quirks="Often pauses to think before speaking, uses precise language"
)

# Profile 3: The Stockbroker (based on Juror #4 from 12 Angry Men)
STOCKBROKER_PROFILE = PersonalityProfile(
    name="Charles Huntington",
    age=45,
    role="Juror #4",
    
    # Big Five: Logical, detached, efficient
    openness=0.3,            # Moderately open
    conscientiousness=0.7,   # Disciplined
    extraversion=-0.3,       # Somewhat reserved
    agreeableness=0.0,       # Neutral - objective
    neuroticism=-0.5,        # Very emotionally stable
    
    speaking_style="formal, precise, avoids emotional language",
    decision_style="logical, evidence-based, efficient",
    conflict_style="detached, appeals to facts rather than emotion",
    
    core_values=["logic", "efficiency", "facts", "rationality"],
    biases=["distrusts emotional arguments", "values brevity"],
    
    backstory=(
        "Stockbroker. Used to making high-stakes decisions based on data. "
        "Sees emotional arguments as weakness. Initially votes guilty based on evidence."
    ),
    motivation="Reach the correct verdict efficiently based on facts",
    fear="Wasting time on irrelevant emotional displays",
    
    vocabulary_level="formal",
    common_phrases=["The facts indicate...", "Logically speaking...", "If we consider..."],
    speech_quirks="Never raises voice, maintains composed demeanor always"
)

# Profile 4: The Bank Teller (based on Juror #2 from 12 Angry Men)
BANK_TELLER_PROFILE = PersonalityProfile(
    name="Henry Wilson",
    age=28,
    role="Juror #2",
    
    # Big Five: Timid, easily swayed, conscientious
    openness=0.2,            # Slightly traditional
    conscientiousness=0.6,   # Follows rules
    extraversion=-0.6,       # Introverted, shy
    agreeableness=0.7,       # Cooperative, conflict-avoidant
    neuroticism=0.3,         # Somewhat anxious
    
    speaking_style="quiet, hesitant, often apologizes",
    decision_style="deferential, follows stronger personalities",
    conflict_style="avoidant, seeks compromise",
    
    core_values=["harmony", "following rules", "being helpful"],
    biases=["defers to authority", "afraid of confrontation"],
    
    backstory=(
        "Bank teller. Not used to making important decisions. "
        "Initially votes guilty because others do, but open to change."
    ),
    motivation="Do the right thing without causing conflict",
    fear="Being singled out or criticized",
    
    vocabulary_level="simple",
    common_phrases=["I'm not sure...", "Maybe...", "I suppose..."],
    speech_quirks="Stutters slightly when nervous, trails off at end of sentences"
)

# Profile 5: The Elderly Man (based on Juror #9 from 12 Angry Men)
ELDERLY_MAN_PROFILE = PersonalityProfile(
    name="Joseph McCardle",
    age=72,
    role="Juror #9",
    
    # Big Five: Wise, patient, empathetic
    openness=0.5,            # Open to perspectives
    conscientiousness=0.4,   # Flexible
    extraversion=-0.1,       # Neither intro nor extroverted
    agreeableness=0.8,       # Very cooperative, kind
    neuroticism=0.1,         # Emotionally stable
    
    speaking_style="gentle, wise, speaks from experience",
    decision_style="thoughtful, considers human element",
    conflict_style="peaceful, tries to bridge gaps",
    
    core_values=["wisdom", "empathy", "patience", "understanding"],
    biases=["values age and experience", "sees through pretense"],
    
    backstory=(
        "Retired man. Has seen much in life and learned patience. "
        "Recognizes the anger in Juror #3 and understands its source. "
        "First to support Juror #8's doubt."
    ),
    motivation="Help others see truth, bring wisdom to the deliberation",
    fear="Being dismissed due to age, his wisdom going unheard",
    
    vocabulary_level="educated",
    common_phrases=["In my experience...", "I understand what you're feeling...", "Please, let me say something..."],
    speech_quirks="Speaks slowly and deliberately, often nods while others speak"
)


# Registry of sample profiles
SAMPLE_PROFILES: Dict[str, PersonalityProfile] = {
    'angry_man': ANGRY_MAN_PROFILE,
    'analytical_juror': ANALYTICAL_JUROR_PROFILE,
    'stockbroker': STOCKBROKER_PROFILE,
    'bank_teller': BANK_TELLER_PROFILE,
    'elderly_man': ELDERLY_MAN_PROFILE,
}


def get_sample_profile(name: str) -> Optional[PersonalityProfile]:
    """
    Get a sample profile by name.
    
    Args:
        name: Key name of the profile (e.g., 'angry_man')
    
    Returns:
        PersonalityProfile if found, None otherwise
    """
    return SAMPLE_PROFILES.get(name)


if __name__ == "__main__":
    # Demo: Print sample profile and context
    profile = ANGRY_MAN_PROFILE
    print("=== Personality Profile Demo ===\n")
    print(f"Name: {profile.name}")
    print(f"Role: {profile.role}")
    print(f"Age: {profile.age}\n")
    
    print("Big Five Traits:")
    for trait in ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']:
        value = getattr(profile, trait)
        label = profile.get_trait_label(trait)
        print(f"  {trait}: {value:+.1f} ({label})")
    
    print("\n" + "="*50)
    print("LLM CONTEXT:")
    print("="*50 + "\n")
    print(build_personality_context(profile))
