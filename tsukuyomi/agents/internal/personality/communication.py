"""
Communication Style & Personality
=================================

Defines agent communication styles and style injection for prompts.
This is a GENERAL system applicable to any social simulation.

Location: tsukuyomi/agent/personality.py
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from tsukuyomi.agents.social.conversation import ResponseHistory
import logging

logger = logging.getLogger("Personality")


@dataclass
class CommunicationStyle:
    """
    Defines how an agent communicates.
    
    This creates distinctive speaking patterns for each agent,
    making them feel unique and consistent.
    
    Applicable to ANY simulation where agents speak:
    - Jury: Formal vs casual, verbose vs concise
    - Marketplace: Persuasive, technical, friendly
    - Politics: Rhetorical, careful, assertive
    """
    
    # Vocabulary characteristics
    vocabulary_level: str = "medium"  # "simple", "medium", "complex"
    preferred_words: List[str] = field(default_factory=list)
    avoided_words: List[str] = field(default_factory=list)
    
    # Sentence structure
    avg_sentence_length: int = 15  # Target words per sentence
    uses_contractions: bool = True  # "don't" vs "do not"
    uses_fillers: bool = False  # "um", "well", "you know"
    filler_words: List[str] = field(default_factory=lambda: ["well", "you know", "I mean"])
    
    # Formality
    formality: float = 0.5  # 0=casual, 1=formal
    uses_slang: bool = False
    slang_words: List[str] = field(default_factory=list)
    
    # Expressiveness
    emotional_expression: float = 0.5  # How much emotion shows
    punctuation_style: str = "normal"  # "normal", "emphatic", "minimal"
    uses_rhetorical_questions: bool = True
    
    # Speech patterns
    verbosity: float = 0.5  # 0=concise, 1=verbose
    hedging: float = 0.3  # 0=direct, 1=hedged ("maybe", "perhaps")
    certainty_language: float = 0.5  # 0=uncertain, 1=certain
    
    def __post_init__(self):
        """Ensure lists are initialized."""
        if self.preferred_words is None:
            self.preferred_words = []
        if self.avoided_words is None:
            self.avoided_words = []
        if self.filler_words is None:
            self.filler_words = ["well", "you know", "I mean"]
        if self.slang_words is None:
            self.slang_words = []
    
    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "vocabulary_level": self.vocabulary_level,
            "preferred_words": self.preferred_words,
            "avoided_words": self.avoided_words,
            "avg_sentence_length": self.avg_sentence_length,
            "uses_contractions": self.uses_contractions,
            "uses_fillers": self.uses_fillers,
            "filler_words": self.filler_words,
            "formality": self.formality,
            "uses_slang": self.uses_slang,
            "slang_words": self.slang_words,
            "emotional_expression": self.emotional_expression,
            "punctuation_style": self.punctuation_style,
            "uses_rhetorical_questions": self.uses_rhetorical_questions,
            "verbosity": self.verbosity,
            "hedging": self.hedging,
            "certainty_language": self.certainty_language
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CommunicationStyle':
        """Deserialize from dict."""
        return cls(**data)


def inject_style_into_prompt(
    base_prompt: str,
    style: CommunicationStyle,
    recent_responses: Optional[ResponseHistory] = None
) -> str:
    """
    Inject communication style guidelines into LLM prompt.
    
    This modifies the prompt to encourage the LLM to speak in
    the agent's distinctive style.
    
    Args:
        base_prompt: The base prompt without style guidelines
        style: Communication style configuration
        recent_responses: Response history to check for repetition
    
    Returns:
        Prompt with style guidelines appended
    """
    style_guidelines = """
## COMMUNICATION STYLE GUIDELINES
You are playing a character with the following communication traits:"""
    
    # Vocabulary level
    vocab_desc = {
        "simple": "Use simple, everyday language. Short words.",
        "medium": "Use normal conversational vocabulary.",
        "complex": "Use sophisticated vocabulary. Precise terminology."
    }
    style_guidelines += f"\n- Vocabulary: {vocab_desc.get(style.vocabulary_level, 'Normal conversational.')}"
    
    # Sentence length
    length_desc = "short" if style.avg_sentence_length < 10 else "medium-length" if style.avg_sentence_length < 20 else "longer"
    style_guidelines += f"\n- Sentence length: Aim for {length_desc} sentences (~{style.avg_sentence_length} words average)"
    
    # Formality
    if style.formality > 0.7:
        style_guidelines += "\n- Tone: FORMAL. Use proper grammar, no slang, professional language."
    elif style.formality < 0.3:
        style_guidelines += "\n- Tone: CASUAL. Use colloquial language, contractions, relaxed style."
    else:
        style_guidelines += "\n- Tone: CONVERSATIONAL. Balance formality and casualness."
    
    # Emotional expression
    if style.emotional_expression > 0.7:
        style_guidelines += "\n- Expressiveness: HIGH. Show your emotions openly in your language."
    elif style.emotional_expression < 0.3:
        style_guidelines += "\n- Expressiveness: LOW. Keep emotions understated, matter-of-fact."
    
    # Verbosity
    if style.verbosity > 0.7:
        style_guidelines += "\n- Length: VERBOSE. Elaborate on points, provide context and detail."
    elif style.verbosity < 0.3:
        style_guidelines += "\n- Length: CONCISE. Get to the point quickly, avoid unnecessary words."
    
    # Certainty
    if style.certainty_language > 0.7:
        style_guidelines += "\n- Certainty: Speak with CONFIDENCE. Make definite statements."
    elif style.certainty_language < 0.3:
        style_guidelines += "\n- Certainty: Show UNCERTAINTY. Use hedging language like 'perhaps', 'maybe'."
    
    # Preferred words
    if style.preferred_words:
        style_guidelines += f"\n- Your character tends to use these words: {', '.join(style.preferred_words[:5])}"
    
    # Avoided words
    if style.avoided_words:
        style_guidelines += f"\n- Avoid using these words: {', '.join(style.avoided_words[:5])}"
    
    # Fillers
    if style.uses_fillers and style.filler_words:
        style_guidelines += f"\n- Your character sometimes uses filler words: {', '.join(style.filler_words[:2])}"
    
    # Punctuation style
    if style.punctuation_style == "emphatic":
        style_guidelines += "\n- Use EMPHATIC punctuation (CAPS for emphasis, exclamation marks for strong feelings)"
    elif style.punctuation_style == "minimal":
        style_guidelines += "\n- Use MINIMAL punctuation. Short sentences. Periods mostly."
    
    # Rhetorical questions
    if style.uses_rhetorical_questions:
        style_guidelines += "\n- You sometimes use rhetorical questions for emphasis."
    
    # Add repetition warning if needed
    if recent_responses:
        repetitive = recent_responses.get_repetitive_phrases()
        if repetitive:
            style_guidelines += f"\n\n## VARIETY WARNING"
            style_guidelines += f"\n- AVOID these overused phrases: {', '.join(repetitive[:3])}"
            style_guidelines += "\n- Try to express the same ideas with DIFFERENT wording."
    
    return base_prompt + style_guidelines


# ========================
# Style Presets
# ========================

def create_style_from_traits(
    big_five: Dict[str, float],
    role: Optional[str] = None
) -> CommunicationStyle:
    """
    Create a communication style from Big Five personality traits.
    
    This provides sensible defaults based on personality.
    
    Args:
        big_five: Dict with openness, conscientiousness, extraversion,
                  agreeableness, neuroticism (0.0-1.0)
        role: Optional role hint (e.g., "leader", "skeptic", "diplomat")
    
    Returns:
        CommunicationStyle configured for the personality
    """
    # Base style
    style = CommunicationStyle()
    
    # Extraversion affects expressiveness
    extraversion = big_five.get("extraversion", 0.5)
    style.emotional_expression = 0.3 + extraversion * 0.4
    style.verbosity = 0.3 + extraversion * 0.4
    
    # Openness affects vocabulary
    openness = big_five.get("openness", 0.5)
    if openness > 0.7:
        style.vocabulary_level = "complex"
    elif openness < 0.3:
        style.vocabulary_level = "simple"
    
    # Agreeableness affects hedging and formality
    agreeableness = big_five.get("agreeableness", 0.5)
    style.hedging = 0.2 + (1 - agreeableness) * 0.3
    style.formality = 0.3 + agreeableness * 0.3
    
    # Neuroticism affects certainty
    neuroticism = big_five.get("neuroticism", 0.5)
    style.certainty_language = 0.7 - neuroticism * 0.4
    style.uses_fillers = neuroticism > 0.6
    
    # Role-based modifications
    if role:
        if role == "leader":
            style.certainty_language = 0.8
            style.formality = max(style.formality, 0.6)
        elif role == "skeptic":
            style.hedging = 0.6
            style.uses_rhetorical_questions = True
        elif role == "diplomat":
            style.hedging = 0.5
            style.agreeableness = 0.8
        elif role == "expert":
            style.vocabulary_level = "complex"
            style.formality = 0.7
    
    return style


# Predefined style presets
STYLE_PRESETS = {
    "formal": CommunicationStyle(
        vocabulary_level="complex",
        formality=0.9,
        uses_contractions=False,
        verbosity=0.4,
        emotional_expression=0.3
    ),
    "casual": CommunicationStyle(
        vocabulary_level="simple",
        formality=0.2,
        uses_contractions=True,
        uses_fillers=True,
        verbosity=0.6
    ),
    "analytical": CommunicationStyle(
        vocabulary_level="complex",
        formality=0.7,
        verbosity=0.7,
        certainty_language=0.6,
        uses_rhetorical_questions=True
    ),
    "emotional": CommunicationStyle(
        vocabulary_level="medium",
        emotional_expression=0.9,
        punctuation_style="emphatic",
        verbosity=0.6
    ),
    "concise": CommunicationStyle(
        avg_sentence_length=8,
        verbosity=0.2,
        punctuation_style="minimal"
    ),
    "verbose": CommunicationStyle(
        avg_sentence_length=25,
        verbosity=0.9,
        uses_rhetorical_questions=True
    )
}


def get_style_preset(name: str) -> Optional[CommunicationStyle]:
    """Get a predefined style preset by name."""
    return STYLE_PRESETS.get(name.lower())